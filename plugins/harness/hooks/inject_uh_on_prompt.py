#!/usr/bin/env python3
"""UserPromptSubmit 훅: 사용자가 "적용" 의사를 표명하면 미독취 이벤트의 diff를 컨텍스트에 주입한다."""
import json
import sys
import os
import subprocess
from datetime import datetime, timezone

UH_DIR = os.path.expanduser("~/.claude/ultraharness")
EVENTS_PATH = os.path.join(UH_DIR, "events.jsonl")
CURSORS_DIR = os.path.join(UH_DIR, "read-cursors")
REGISTRY_PATH = os.path.join(UH_DIR, "registry.json")

APPLY_KEYWORDS = ("적용", "apply", "반영", "동기화", "sync")
SKIP_KEYWORDS = ("스킵", "skip", "무시", "ignore", "패스", "pass")

# ultraharness 디렉토리가 없으면 noop
if not os.path.isdir(UH_DIR):
    sys.exit(0)

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)


def get_user_message(data: dict) -> str:
    """훅 입력에서 사용자 메시지 텍스트를 추출한다."""
    # UserPromptSubmit 훅 입력 스키마: {"prompt": "...", "session_id": "...", ...}
    return data.get("prompt", "") or ""


def keyword_match(text: str, keywords: tuple) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in keywords)


def load_registry() -> dict:
    if not os.path.exists(REGISTRY_PATH):
        return {"sessions": []}
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sessions": []}


def get_worktree_for_session(registry: dict, session_id: str) -> str:
    """registry에서 세션의 project_dir(worktree 경로)을 반환한다."""
    for s in registry.get("sessions", []):
        if s.get("session_id") == session_id:
            return s.get("worktree_dir") or s.get("project_dir") or ""
    return ""


def extract_diff(worktree: str, file_path: str) -> str:
    """주어진 worktree에서 파일의 git diff HEAD를 추출한다."""
    if not worktree or not file_path:
        return ""
    try:
        result = subprocess.run(
            ["git", "-C", worktree, "diff", "HEAD", "--", file_path],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    except Exception:
        return ""


def update_cursor(session_id: str, max_event_id: int) -> None:
    """커서 파일을 최신 event_id로 갱신한다."""
    os.makedirs(CURSORS_DIR, exist_ok=True)
    cursor_path = os.path.join(CURSORS_DIR, f"{session_id}.txt")
    try:
        with open(cursor_path, "w", encoding="utf-8") as f:
            f.write(str(max_event_id))
    except Exception:
        pass


try:
    session_id = data.get("session_id", "")
    if not session_id:
        sys.exit(0)

    user_msg = get_user_message(data)

    is_apply = keyword_match(user_msg, APPLY_KEYWORDS)
    is_skip = keyword_match(user_msg, SKIP_KEYWORDS)

    # 키워드 없음 → 일반 메시지, 컨텍스트 주입 및 커서 갱신 없이 통과
    if not is_apply and not is_skip:
        sys.exit(0)

    # 커서 로드
    cursor_path = os.path.join(CURSORS_DIR, f"{session_id}.txt")
    last_seen_id = 0
    if os.path.exists(cursor_path):
        try:
            with open(cursor_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    last_seen_id = int(content)
        except Exception:
            last_seen_id = 0

    # 미독취 이벤트 수집
    if not os.path.exists(EVENTS_PATH):
        sys.exit(0)

    unseen = []
    max_event_id = last_seen_id
    try:
        with open(EVENTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                eid = ev.get("event_id", 0)
                if session_id in ev.get("target_sessions", []) and eid > last_seen_id:
                    unseen.append(ev)
                    if eid > max_event_id:
                        max_event_id = eid
    except Exception:
        sys.exit(0)

    # 스킵: 커서만 갱신하고 컨텍스트 주입 없이 종료
    if is_skip:
        if unseen:
            update_cursor(session_id, max_event_id)
        sys.exit(0)

    # 적용: 미독취 이벤트가 없으면 통과
    if not unseen:
        sys.exit(0)

    # diff 추출
    registry = load_registry()
    diff_blocks = []
    for ev in unseen:
        src_session = ev.get("source_session", "")
        file_path = ev.get("file", "")
        domain = ev.get("domain", "")
        worktree = get_worktree_for_session(registry, src_session)
        diff = extract_diff(worktree, file_path)
        diff_blocks.append({
            "file": file_path,
            "domain": domain,
            "source_session": src_session,
            "diff": diff,
        })

    # 컨텍스트 prepend 텍스트 구성
    lines = [
        "[ultraharness 적용 컨텍스트]",
        "다음은 다른 세션에서 발생한 변경입니다:",
        "",
    ]
    for block in diff_blocks:
        lines.append(f"• {block['file']} (도메인: {block['domain']}, 세션: {block['source_session'][:6]})")
        if block["diff"]:
            lines.append("```diff")
            lines.append(block["diff"])
            lines.append("```")
        else:
            lines.append("  (diff 없음 — 파일이 이미 동기화되었거나 접근 불가)")
        lines.append("")

    lines.append("위 변경이 현재 작업에 미치는 영향을 분석하고 필요한 코드를 수정하세요.")
    lines.append("")

    context_prefix = "\n".join(lines)

    # UserPromptSubmit 훅의 응답: {"prompt": "<prepend>\n<original>"} 형태로 stdout에 출력
    # Claude Code UserPromptSubmit 훅은 JSON 응답으로 프롬프트를 변경할 수 있다.
    output = {
        "prompt": context_prefix + "\n\n" + user_msg
    }
    print(json.dumps(output, ensure_ascii=False))

    # 커서 갱신
    update_cursor(session_id, max_event_id)

except Exception:
    pass

sys.exit(0)

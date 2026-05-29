#!/usr/bin/env python3
"""UserPromptSubmit 훅: 사용자가 "적용" 의사를 표명하면 미독취 이벤트의 diff를 컨텍스트에 주입한다."""
import json
import sys
import os
import subprocess
import time
from datetime import datetime, timezone

try:
    from uh_utils import warn_if_missing
except ImportError:
    def warn_if_missing(label: str = "") -> bool:  # type: ignore[misc]
        return False

UH_DIR = os.path.expanduser("~/.claude/ultraharness")
EVENTS_PATH = os.path.join(UH_DIR, "events.jsonl")
CURSORS_DIR = os.path.join(UH_DIR, "read-cursors")
REGISTRY_PATH = os.path.join(UH_DIR, "registry.json")

APPLY_KEYWORDS = ("적용", "apply", "반영")   # "sync", "동기화" 제거
SKIP_KEYWORDS = ("스킵", "skip", "무시", "ignore", "패스", "pass")

# 태스크 상태 갱신 키워드 — SKIP_KEYWORDS의 "스킵"/"skip"과 겹치지 않도록 한정
TASK_DONE_KEYWORDS = ("완료", "done", "complete", "태스크완료")
TASK_SKIP_KEYWORDS = ("태스크스킵", "task-skip")

# 사용자 메시지 TODO 캡처 — 명시적 prefix만 인식 (오탐 방지)
TODO_CAPTURE_PREFIXES = ("TODO:", "FIXME:", "나중에:", "할일:")

if warn_if_missing("inject_uh_on_prompt"):
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


def _handle_task_update(user_msg: str) -> None:
    """태스크 done/skip 키워드 + task-<id> 패턴이 있으면 manage_uh_tasks.py를 호출한다."""
    import re
    id_match = re.search(r'\btask-\d{8}-\d+\b', user_msg)
    if not id_match:
        return
    task_id = id_match.group(0)
    lower = user_msg.lower()
    is_task_done = any(kw in lower for kw in TASK_DONE_KEYWORDS)
    is_task_skip = any(kw in lower for kw in TASK_SKIP_KEYWORDS)
    if not is_task_done and not is_task_skip:
        return
    tasks_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manage_uh_tasks.py")
    if not os.path.exists(tasks_py):
        return
    subcmd = "done" if is_task_done else "skip"
    try:
        subprocess.run(
            ["python3", tasks_py, subcmd, "--id", task_id],
            timeout=5
        )
    except Exception:
        pass


def _handle_todo_capture(user_msg: str, session_id: str) -> None:
    """명시적 TODO prefix가 있는 사용자 메시지를 task로 등록한다.
    task-YYYYMMDD-NNN 패턴이 있는 메시지는 기존 태스크 업데이트이므로 건너뛴다."""
    import re
    import hashlib
    # 기존 task 업데이트 메시지는 건너뜀
    if re.search(r'\btask-\d{8}-\d+\b', user_msg):
        return
    stripped = user_msg.strip()
    matched_prefix = None
    for prefix in TODO_CAPTURE_PREFIXES:
        if stripped.startswith(prefix):
            matched_prefix = prefix
            break
    if matched_prefix is None:
        return
    title = stripped[len(matched_prefix):].strip().splitlines()[0][:120]
    if not title:
        return

    tasks_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manage_uh_tasks.py")
    if not os.path.exists(tasks_py):
        return

    # source_id: "msg:<session_id>:<title_hash>" — 동일 세션 내 중복 방지
    title_hash = hashlib.sha1(title.encode()).hexdigest()[:8]
    source_id = f"msg:{session_id}:{title_hash}"

    try:
        subprocess.run(
            ["python3", tasks_py, "add",
             "--title", title,
             "--priority", "P2",
             "--source", "user_message",
             "--source-id", source_id],
            timeout=5
        )
    except Exception:
        pass


try:
    session_id = data.get("session_id", "")
    if not session_id:
        sys.exit(0)

    user_msg = get_user_message(data)

    # 태스크 상태 갱신 처리 (이벤트 주입 흐름과 독립)
    _handle_task_update(user_msg)
    _handle_todo_capture(user_msg, session_id)

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

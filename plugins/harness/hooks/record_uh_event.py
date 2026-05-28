#!/usr/bin/env python3
"""PostToolUse 훅: 파일 변경을 ultraharness events.jsonl에 기록하고 7일 지난 이벤트를 prune한다.
기존 log_file_changes.py 기능을 흡수하여 단일 감사 로그로 일원화한다.
"""
import json
import sys
import os
from datetime import datetime, timezone, timedelta

UH_DIR = os.path.expanduser("~/.claude/ultraharness")
REGISTRY_PATH = os.path.join(UH_DIR, "registry.json")
EVENTS_PATH = os.path.join(UH_DIR, "events.jsonl")
PRUNE_DAYS = 7
MAX_EVENTS_SIZE = 1024 * 1024  # 1 MB 경고 임계값

# ultraharness 디렉토리가 없으면 noop (미사용 환경 호환)
if not os.path.isdir(UH_DIR):
    sys.exit(0)

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = data.get("tool_name", "")
if tool not in ("Edit", "Write", "MultiEdit"):
    sys.exit(0)

inp = data.get("tool_input", {}) or {}
resp = data.get("tool_response", {}) or {}
session_id = data.get("session_id", "")
cwd = data.get("cwd", os.getcwd())

ok = not (resp.get("is_error") or resp.get("error"))


def classify_domain(file_path: str) -> str:
    """파일 경로를 보고 도메인을 분류한다."""
    p = file_path.lower().replace("\\", "/")
    api_patterns = ("api/", "/api/", "contract", "schema", "openapi", "swagger")
    token_patterns = ("token", "theme", "design", "color", "typography")
    for pat in api_patterns:
        if pat in p:
            return "api_contract"
    for pat in token_patterns:
        if pat in p:
            return "design_token"
    return "general"


def load_registry() -> dict:
    """registry.json을 읽어 반환한다. 없거나 파싱 실패 시 빈 registry를 반환한다."""
    if not os.path.exists(REGISTRY_PATH):
        return {"sessions": []}
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sessions": []}


def find_target_sessions(registry: dict, source_session: str, source_project: str, domain: str) -> list:
    """같은 project_dir의 running 세션 중 stale이 아닌 것을 target으로 반환한다.
    api_contract / design_token 도메인만 전파 대상으로 삼는다.
    """
    if domain == "general":
        return []
    now = datetime.now(timezone.utc)
    stale_threshold = timedelta(hours=24)
    targets = []
    for s in registry.get("sessions", []):
        if s.get("session_id") == source_session:
            continue
        if s.get("status") != "running":
            continue
        if s.get("project_dir") != source_project:
            continue
        registered_at_str = s.get("registered_at", "")
        try:
            registered_at = datetime.fromisoformat(registered_at_str)
            if registered_at.tzinfo is None:
                registered_at = registered_at.replace(tzinfo=timezone.utc)
            if (now - registered_at) > stale_threshold:
                continue
        except Exception:
            continue
        targets.append(s["session_id"])
    return targets


def prune_old_events(lines: list) -> list:
    """7일 지난 이벤트를 제거한다."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=PRUNE_DAYS)
    kept = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
            ts_str = ev.get("ts", "")
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                kept.append(line)
        except Exception:
            kept.append(line)
    return kept


def get_next_event_id(lines: list) -> int:
    return len(lines) + 1


def append_events(file_entries: list) -> None:
    """events.jsonl에 이벤트를 append한다. prune을 먼저 실행한다."""
    os.makedirs(UH_DIR, exist_ok=True)

    # prune: 기존 이벤트를 읽고 7일 지난 항목 제거
    existing_lines: list = []
    if os.path.exists(EVENTS_PATH):
        try:
            with open(EVENTS_PATH, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()
        except Exception:
            existing_lines = []

    kept = prune_old_events(existing_lines)

    # 크기 경고 (prune 후에도 1MB 초과 시)
    total_size = sum(len(l.encode("utf-8")) for l in kept)
    if total_size > MAX_EVENTS_SIZE:
        # 표준 에러로 경고, 훅 실패는 아님
        print(f"[ultraharness] WARNING: events.jsonl이 {total_size} bytes로 크습니다.", file=sys.stderr)

    next_id = get_next_event_id(kept)

    new_lines = []
    for entry in file_entries:
        ev = {
            "event_id": next_id,
            "ts": entry["ts"],
            "source_session": entry["source_session"],
            "source_project": entry["source_project"],
            "target_sessions": entry["target_sessions"],
            "domain": entry["domain"],
            "file": entry["file"],
            "tool": entry["tool"],
            "ok": entry["ok"],
        }
        new_lines.append(json.dumps(ev, ensure_ascii=False))
        next_id += 1

    # prune 결과 + 신규 이벤트를 덮어쓰기
    with open(EVENTS_PATH, "w", encoding="utf-8") as f:
        for line in kept:
            f.write(line.rstrip("\n") + "\n")
        for line in new_lines:
            f.write(line + "\n")


try:
    # 파일 목록 수집
    file_paths = []
    if tool in ("Edit", "Write"):
        fp = inp.get("file_path", "")
        if fp:
            file_paths.append(fp)
    elif tool == "MultiEdit":
        for edit in inp.get("edits", []):
            fp = edit.get("file_path", "")
            if fp:
                file_paths.append(fp)

    if not file_paths:
        sys.exit(0)

    registry = load_registry()
    now_ts = datetime.now(timezone.utc).isoformat()

    entries = []
    for fp in file_paths:
        domain = classify_domain(fp)
        targets = find_target_sessions(registry, session_id, cwd, domain)
        entries.append({
            "ts": now_ts,
            "source_session": session_id,
            "source_project": cwd,
            "target_sessions": targets,
            "domain": domain,
            "file": fp,
            "tool": tool,
            "ok": ok,
        })

    append_events(entries)

except Exception:
    # 훅 실패가 하네스 동작을 막지 않도록 항상 0으로 종료
    pass

sys.exit(0)

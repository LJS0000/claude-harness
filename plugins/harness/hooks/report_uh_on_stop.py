#!/usr/bin/env python3
"""Stop 훅: 어시스턴트 응답 종료 시 미독취 ultraharness 이벤트를 사용자에게 요약 보고한다."""
import json
import sys
import os
import subprocess
from datetime import datetime, timezone

UH_DIR = os.path.expanduser("~/.claude/ultraharness")
EVENTS_PATH = os.path.join(UH_DIR, "events.jsonl")
CURSORS_DIR = os.path.join(UH_DIR, "read-cursors")

# ultraharness 디렉토리가 없으면 noop
if not os.path.isdir(UH_DIR):
    sys.exit(0)

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

# --- 태스크 큐 알림 (이벤트 로직과 독립) ---
try:
    _tasks_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manage_uh_tasks.py")
    if os.path.exists(_tasks_py):
        _top_raw = subprocess.run(
            ["python3", _tasks_py, "top"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
        if _top_raw:
            _top = json.loads(_top_raw)
            _pending_raw = subprocess.run(
                ["python3", _tasks_py, "list", "--status", "pending"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip()
            _pending_count = len(json.loads(_pending_raw)) if _pending_raw else 0
            print(f"\n대기 태스크 {_pending_count}건 | 최우선: [{_top['priority']}] {_top['title']}")
            print("  → 처리하려면 /harness:queue list 또는 /harness 새 세션에서 확인")
except Exception:
    pass
# --- 태스크 큐 알림 끝 ---

# --- 태스크 sync 백그라운드 트리거 ---
try:
    _sync_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync_uh_tasks.py")
    if os.path.exists(_sync_py):
        _project_dir = data.get("cwd", "") if isinstance(data, dict) else ""
        subprocess.Popen(
            ["python3", _sync_py, _project_dir],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
except Exception:
    pass
# --- 태스크 sync 백그라운드 트리거 끝 ---

try:
    session_id = data.get("session_id", "") if isinstance(data, dict) else ""
    if not session_id:
        sys.exit(0)

    # 커서 로드: 마지막으로 본 event_id (없으면 0)
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

    # events.jsonl에서 미독취 이벤트 수집
    if not os.path.exists(EVENTS_PATH):
        sys.exit(0)

    unseen = []
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
                # target_sessions에 현재 세션이 포함되어 있고 아직 읽지 않은 이벤트
                if session_id in ev.get("target_sessions", []) and ev.get("event_id", 0) > last_seen_id:
                    unseen.append(ev)
    except Exception:
        sys.exit(0)

    if not unseen:
        sys.exit(0)

    # 보고 출력
    print()
    print("┌─────────────────────────────────────────┐")
    print("│ [ultraharness] 다른 세션 변경 알림       │")
    for ev in unseen:
        src = ev.get("source_session", "?")[:6]
        file_path = ev.get("file", "?")
        domain = ev.get("domain", "?")
        print(f"│ • 세션 {src}: {file_path} ({domain})")
    print("│                                         │")
    print("│ 적용을 원하시면 다음 메시지로 \"적용\",   │")
    print("│ 무시하려면 \"스킵\"이라고 말씀해 주세요.  │")
    print("└─────────────────────────────────────────┘")
    print()

except Exception:
    pass

sys.exit(0)

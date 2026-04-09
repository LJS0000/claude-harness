#!/usr/bin/env python3
"""파일 변경을 JSONL로 기록하는 Audit Hook (PostToolUse)"""
import json, sys, os
from datetime import datetime, timezone

data = json.load(sys.stdin)
tool = data.get("tool_name", "")

if tool not in ("Edit", "Write", "MultiEdit"):
    sys.exit(0)

inp = data.get("tool_input", {})
resp = data.get("tool_response", {}) or {}
session_id = data.get("session_id", "")
cwd = data.get("cwd", os.getcwd())
project = os.path.basename(cwd)

# tool_response에서 에러 여부 판단 (is_error 또는 error 키 존재 시 실패)
ok = not (resp.get("is_error") or resp.get("error"))

def make_entry(file_path: str) -> dict:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "session": session_id,
        "tool": tool,
        "file": file_path,
        "project": project,
        "ok": ok,
    }

entries = []
if tool in ("Edit", "Write"):
    entries.append(make_entry(inp.get("file_path", "")))
elif tool == "MultiEdit":
    for edit in inp.get("edits", []):
        entries.append(make_entry(edit.get("file_path", "")))

log_dir = os.path.expanduser("~/.claude/logs")
os.makedirs(log_dir, exist_ok=True)
with open(os.path.join(log_dir, "file-changes.jsonl"), "a", encoding="utf-8") as f:
    for entry in entries:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

sys.exit(0)

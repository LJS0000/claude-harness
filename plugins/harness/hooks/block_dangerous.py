#!/usr/bin/env python3
"""위험한 명령어를 자동 차단하는 Safety Hook"""
import json, re, sys

BLOCKED_PATTERNS = [
    # 파일 삭제 차단
    (r"\brm\s+", "rm 대신 trash를 사용하세요 (brew install trash)"),
    (r"\bunlink\s+", "unlink 대신 trash를 사용하세요"),

    # Git 히스토리 파괴 차단
    (r"git\s+reset\s+--hard", "git reset --hard는 커밋하지 않은 작업을 삭제합니다"),
    (r"git\s+push\s+.*--force", "git push --force는 원격 히스토리를 덮어씁니다"),
    (r"git\s+push\s+.*-f\b", "git push -f는 원격 히스토리를 덮어씁니다"),
    (r"git\s+clean\s+-.*f", "git clean -f는 추적되지 않은 파일을 영구 삭제합니다"),
    (r"git\s+checkout\s+\.\s*$", "git checkout .은 모든 변경사항을 삭제합니다"),
    (r"git\s+stash\s+drop", "git stash drop은 스태시를 영구 삭제합니다"),
    (r"git\s+branch\s+-D", "git branch -D는 브랜치를 강제 삭제합니다"),

    # 데이터베이스 파괴 차단
    (r"DROP\s+(DATABASE|TABLE)", "DROP은 데이터를 영구 삭제합니다"),
    (r"TRUNCATE\s+TABLE", "TRUNCATE는 모든 데이터를 삭제합니다"),
]

data = json.load(sys.stdin)
if data.get("tool_name") != "Bash":
    sys.exit(0)

command = data.get("tool_input", {}).get("command", "")
for pattern, reason in BLOCKED_PATTERNS:
    if re.search(pattern, command, re.IGNORECASE):
        print(f"차단됨: {reason}", file=sys.stderr)
        sys.exit(2)

sys.exit(0)

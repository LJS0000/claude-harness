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
    (r"git\s+branch\s+(?-i:-D)\b", "git branch -D는 브랜치를 강제 삭제합니다"),

    # 데이터베이스 파괴 차단
    (r"DROP\s+(DATABASE|TABLE)", "DROP은 데이터를 영구 삭제합니다"),
    (r"TRUNCATE\s+TABLE", "TRUNCATE는 모든 데이터를 삭제합니다"),
]

# 셸 우회 래퍼: 인용된 인자가 실제 실행 명령이므로 인용을 풀지 않는다.
EXEC_WRAPPERS = [
    r"^\s*(bash|sh|zsh|dash)\s+-c\b",
    r"^\s*eval\b",
    r"^\s*python3?\s+-c\b",
    r"^\s*node\s+-e\b",
]


def strip_quoted(command: str) -> str:
    """검사 대상 명령에서 큰따옴표/작은따옴표 내부 텍스트를 제거한다.

    commit 메시지·PR 본문·echo 인자처럼 인용된 텍스트는 셸 메타 데이터이지
    실행되는 명령이 아니다. 단 EXEC_WRAPPERS로 시작하는 명령은 인용된 인자
    자체가 실행 대상이므로 변환 없이 그대로 반환한다. backtick·$(...) 같은
    명령 치환 구문은 일부러 건드리지 않아 그 안의 위험 패턴은 검사된다.
    """
    for wrapper in EXEC_WRAPPERS:
        if re.match(wrapper, command):
            return command
    result = re.sub(r'"(?:[^"\\]|\\.)*"', '""', command)
    result = re.sub(r"'(?:[^'\\]|\\.)*'", "''", result)
    return result


data = json.load(sys.stdin)
if data.get("tool_name") != "Bash":
    sys.exit(0)

command = data.get("tool_input", {}).get("command", "")
target = strip_quoted(command)
for pattern, reason in BLOCKED_PATTERNS:
    if re.search(pattern, target, re.IGNORECASE):
        print(f"차단됨: {reason}", file=sys.stderr)
        sys.exit(2)

sys.exit(0)

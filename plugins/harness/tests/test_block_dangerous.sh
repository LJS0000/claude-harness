#!/usr/bin/env bash
# block_dangerous.py hook의 동작 검증. 패턴 변경 시 회귀를 잡는다.
# 사용: bash plugins/harness/tests/test_block_dangerous.sh
# 종료 코드: 0 (모두 통과) / 1 (하나라도 실패)

set -u

HOOK="$(cd "$(dirname "$0")/.." && pwd)/hooks/block_dangerous.py"
if [ ! -f "$HOOK" ]; then
  echo "FATAL: hook 파일을 찾을 수 없음: $HOOK" >&2
  exit 1
fi

PASS=0
FAIL=0

check() {
  local name="$1"
  local cmd="$2"
  local expected="$3"  # "block" or "pass"
  local actual_exit
  printf '{"tool_name":"Bash","tool_input":{"command":%s}}' "$(printf '%s' "$cmd" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" \
    | python3 "$HOOK" >/dev/null 2>&1
  actual_exit=$?
  local actual
  if [ "$actual_exit" -eq 2 ]; then actual="block"; else actual="pass"; fi
  if [ "$actual" = "$expected" ]; then
    PASS=$((PASS+1))
    printf "  ok   %s\n" "$name"
  else
    FAIL=$((FAIL+1))
    printf "  FAIL %s — expected=%s actual=%s cmd=%s\n" "$name" "$expected" "$actual" "$cmd"
  fi
}

# 직접 위험 명령 — 차단되어야 함
check "C01 rm"                      "rm important.txt"             "block"
check "C02 git reset hard"          "git reset --hard"             "block"
check "C03 git push force"          "git push origin main --force" "block"
check "C04 git push -f"             "git push origin main -f"      "block"
check "C05 git branch -D"           "git branch -D feature"        "block"
check "C06 git stash drop"          "git stash drop"               "block"
check "C07 SQL DROP TABLE"          "DROP TABLE users"             "block"
check "C08 SQL drop lowercase"      "drop table users"             "block"
check "C09 SQL TRUNCATE"            "TRUNCATE TABLE logs"          "block"

# false positive 였던 케이스 — 통과해야 함
check "C10 git branch -d safe"      "git branch -d feature"        "pass"
check "C11 git branch --delete"     "git branch --delete feature"  "pass"
check "C12 git status"              "git status"                   "pass"

# 인용 안 텍스트 — 통과해야 함 (이번 fix 대상)
check "C13 commit msg w/ git reset" 'git commit -m "fix git reset --hard handling"' "pass"
check "C14 PR title w/ branch -d"   'gh pr create --title "fix git branch -d false positive"' "pass"
check "C15 echo rm"                 'echo "rm -rf /"'              "pass"
check "C16 commit msg w/ DROP"      'git commit -m "add DROP TABLE migration"' "pass"

# 셸 우회 래퍼 — 인용 안이 실제 실행 명령이므로 차단되어야 함
check "C17 bash -c wrapper"         'bash -c "git reset --hard"'   "block"
check "C18 sh -c wrapper"           'sh -c "rm important.txt"'     "block"
check "C19 eval"                    'eval "git reset --hard"'      "block"
check "C20 python -c"               'python3 -c "import os; os.system(\"rm x\")"' "block"

# 단일 따옴표 안 텍스트도 통과
check "C21 single quote rm"         "echo 'rm important.txt'"      "pass"

printf "\n결과: %d passed, %d failed\n" "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] || exit 1

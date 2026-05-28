---
name: queue
description: ultraharness 태스크 큐 관리. 태스크 추가/조회/완료/스킵 처리.
---

ultraharness 태스크 큐를 관리한다. 사용자 입력을 파싱하여 `manage_uh_tasks.py`를 호출하고 결과를 포매팅하여 출력한다.

## 사용법

```
/harness:queue add "태스크 제목" [--priority P0|P1|P2] [--desc "설명"] [--tags tag1,tag2]
/harness:queue list [--status pending|done|all]
/harness:queue done <task-id>
/harness:queue skip <task-id>
```

`priority` 기본값: `P1` (지정 없을 시)

## 처리 절차

### 1. manage_uh_tasks.py 경로 결정

```bash
_UH_TASKS_PY="$(python3 -c "
import os, glob
p = os.path.expandvars(os.path.expanduser('${CLAUDE_PLUGIN_ROOT:-~/.claude/plugins}'))
# CLAUDE_PLUGIN_ROOT 기준 탐색
candidates = glob.glob(os.path.join(p, '**', 'manage_uh_tasks.py'), recursive=True)
# 폴백: ~/.claude/plugins 하위 전체 탐색
if not candidates:
    p2 = os.path.expanduser('~/.claude/plugins')
    candidates = glob.glob(os.path.join(p2, '**', 'manage_uh_tasks.py'), recursive=True)
print(candidates[0] if candidates else '')
" 2>/dev/null)"
```

`_UH_TASKS_PY`가 비어 있으면:
```
ultraharness가 설정되지 않았습니다. /harness 세션을 먼저 실행하세요.
```
출력 후 종료.

### 2. 서브커맨드 파싱 및 실행

사용자 입력에서 서브커맨드와 인수를 추출하여 아래 형식으로 호출한다.

**add:**
```bash
python3 "$_UH_TASKS_PY" add --title "<제목>" --priority <P0|P1|P2> [--desc "<설명>"] [--tags "<태그>"]
```

**list:**
```bash
python3 "$_UH_TASKS_PY" list [--status pending|done|all]
```

**done:**
```bash
python3 "$_UH_TASKS_PY" done --id <task-id>
```

**skip:**
```bash
python3 "$_UH_TASKS_PY" skip --id <task-id>
```

### 3. 결과 출력

**list** 결과 포맷:
```
[P0] task-20260528-001 — 로그인 500 에러 조사 (2026-05-28)
[P1] task-20260528-002 — 결제 API 타임아웃 조사 (2026-05-28)
```
날짜는 `created_at` ISO8601 문자열의 앞 10자리(YYYY-MM-DD)를 사용한다.
결과가 비어 있으면: `대기 중인 태스크가 없습니다.`

**add** 결과: `태스크 추가됨: [<priority>] <task_id> — <title>`

**done / skip** 결과: `태스크 <task_id>를 <완료|스킵> 처리했습니다.`

오류(스크립트 non-zero 종료): stderr 내용을 그대로 출력.

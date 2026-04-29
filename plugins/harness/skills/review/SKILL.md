---
name: review
description: 풀 파이프라인 없이 현재 git diff 또는 특정 커밋/파일을 reviewer로 검수하는 단독 리뷰 스킬. "/harness:review" 형태로 사용.
version: 0.2.1
---

You are the review orchestrator. You run a standalone code review on current changes without requiring a full harness pipeline.

## How to invoke

```
/harness:review
/harness:review 최근 3커밋 리뷰해줘
/harness:review src/auth/ 디렉토리 변경사항 확인
```

If no argument is given, review the current unstaged + staged git diff.

## Step 1: 세션 초기화

Generate a session ID and create the session directory:
```bash
SESSION_ID=$(date +%Y%m%d-%H%M%S)
SESSION_DIR="$HOME/.claude/harness-sessions/$SESSION_ID"
mkdir -p "$SESSION_DIR"
echo '{"type":"review","status":"running"}' > "$SESSION_DIR/session-meta.json"
echo "$SESSION_ID"
```

Save the session ID, session dir, and project dir (current working directory).

Announce to the user:
```
리뷰 세션 시작: <session-id>
세션 디렉토리: <session-dir>
```

## Step 2: 변경 사항 사전 확인

Before calling the reviewer, verify there are changes to review:

```bash
cd <project-dir> && git diff --stat && git diff --cached --stat
```

If both are empty and no specific commit range was requested, report:
```
현재 변경 사항이 없습니다. 커밋 범위나 파일을 지정해 주세요.
예: /harness:review HEAD~3..HEAD
```
And stop.

## Step 3: reviewer-standalone 호출

Build the context string:
```
[HARNESS SESSION: <session-id>]
[SESSION DIR: <session-dir>]
[PROJECT DIR: <project-dir>]
리뷰 대상: <user's argument, or "현재 git diff (unstaged + staged)">
```

Call `Agent("reviewer-standalone", context_string)`.

After the call, verify `<session-dir>/review.md` exists:
```bash
test -f "<session-dir>/review.md" && echo "OK" || echo "MISSING"
```

If MISSING: report the error and ask the user whether to retry or abort.

## Step 4: 세션 완료 처리

Update session metadata:
```bash
echo '{"type":"review","status":"completed"}' > "<session-dir>/session-meta.json"
```

## Step 5: 결과 출력

Read `<session-dir>/review.md` and output the full review result to the user.

```
## 리뷰 완료

세션: <session-id>

<review.md 전체 내용>

세션 파일: <session-dir>
```

## Error handling

If the reviewer returns a clear failure or the session file is missing:
1. Report exactly what failed.
2. Update session metadata status to `"failed"`.
3. Ask the user: "재시도하시겠습니까, 아니면 중단하시겠습니까?"
4. Wait for their answer before proceeding.

---
name: idea
description: 자연어 아이디어를 구체화하여 docs/ideas/<slug>.md 마크다운 + GitHub Issues 조합으로 정리하는 스킬. "/harness:idea <아이디어>" 형태로 사용.
version: 0.1.0
---

You are the idea orchestrator. You take a free-form idea description and turn it into structured documentation (a markdown file) and actionable GitHub Issues in the current repo.

## How to invoke

```
/harness:idea 로그인 없이 OAuth로 사용자를 인증하면 좋겠어. 현재는 이메일+패스워드밖에 없음
```

## Step 1: 세션 초기화

Generate a session ID and create the session directory:
```bash
SESSION_ID=$(date +%Y%m%d-%H%M%S)
SESSION_DIR="$HOME/.claude/harness-sessions/$SESSION_ID"
mkdir -p "$SESSION_DIR"
echo '{"type":"idea","status":"running"}' > "$SESSION_DIR/session-meta.json"
echo "$SESSION_ID"
```

Save the session ID, session dir, and project dir (current working directory as `PROJECT_DIR`).

Announce to the user:
```
아이디어 정리 세션 시작: <session-id>
세션 디렉토리: <session-dir>
```

## Step 2: 사전 환경 확인

Run each check in sequence. Stop and report if any check fails.

### 2-a: gh CLI 설치 확인
```bash
command -v gh >/dev/null 2>&1 && echo "OK" || echo "MISSING"
```
MISSING 이면:
```
gh CLI가 설치되어 있지 않습니다.
설치 방법: https://cli.github.com/
설치 후 다시 실행해 주세요.
```
출력 후 중단. (마크다운 파일 작성을 위해 Step 3 Phase 1·2는 계속 진행할 수 있으나, Phase 3은 불가. 사용자에게 안내 후 선택권 부여.)

### 2-b: gh 인증 확인
```bash
gh auth status 2>&1 | grep -qi "logged in\|Logged in\|✓" && echo "OK" || echo "NOT_LOGGED_IN"
```
NOT_LOGGED_IN 이면:
```
gh 인증이 필요합니다. 아래 명령을 실행한 뒤 다시 시도해 주세요:
  gh auth login
```
출력 후 중단.

### 2-c: git repo 확인
```bash
git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree 2>/dev/null && echo "OK" || echo "NOT_GIT"
```
NOT_GIT 이면:
```
현재 디렉토리(<PROJECT_DIR>)가 git 저장소가 아닙니다.
대상 저장소 루트에서 다시 실행해 주세요.
```
출력 후 중단.

### 2-d: GitHub origin repo 확인
```bash
TARGET_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
echo "${TARGET_REPO:-MISSING}"
```
MISSING 이면:
```
현재 디렉토리와 연결된 GitHub repo를 찾지 못했습니다.
  - `gh repo view` 명령으로 origin이 GitHub를 가리키는지 확인하세요.
  - 또는 Issue 생성 없이 마크다운 파일만 작성하려면 계속 진행하세요.
```
사용자에게 "마크다운만 작성 / 중단" 선택을 물은 뒤 응답에 따라 분기.

## Step 3: idea-writer 에이전트 호출

Build the context string:
```
[HARNESS SESSION: <session-id>]
[SESSION DIR: <session-dir>]
[PROJECT DIR: <project-dir>]
[TARGET REPO: <owner/name or NONE if Step 2-d failed and user chose markdown-only>]
아이디어: <original idea description>
```

Call `Agent("idea-writer", context_string)`.

After the call, verify the output files exist:
```bash
test -f "<session-dir>/idea-draft.md" && echo "DRAFT_OK" || echo "DRAFT_MISSING"
test -f "<session-dir>/slug.txt"      && echo "SLUG_OK"  || echo "SLUG_MISSING"
```

If DRAFT_MISSING: report the error and ask the user whether to retry or abort.

## Step 4: 세션 완료 처리

Update session metadata:
```bash
echo '{"type":"idea","status":"completed"}' > "<session-dir>/session-meta.json"
```

## Step 5: 결과 출력

Read `<session-dir>/idea-draft.md` (bottom section) and report to the user:

```
## 아이디어 정리 완료

세션: <session-id>

마크다운 파일: docs/ideas/<slug>.md
  (아직 커밋되지 않았습니다 — 검토 후 직접 커밋/PR 하세요.)

생성된 Issues:
  - <issue title> — <url>
  - ...
  (실패한 항목이 있으면 ❌ 로 표시)

세션 파일: <session-dir>
```

## Error handling

If the idea-writer agent returns a clear failure or session files are missing:
1. Report exactly what failed.
2. Update session metadata status to `"failed"`.
3. Ask the user: "재시도하시겠습니까, 아니면 중단하시겠습니까?"
4. Wait for their answer before proceeding.

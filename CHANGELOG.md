# Changelog

## 0.6.0

- feat(harness): codex CLI 통합을 implementer에 재도입 — 0.3.1에서 제거되었던 경로를 오류 감소 중심으로 재설계
- 감지 강화: `command -v` 대신 `codex --version` 실행 + `codex exec --help` flag 표면 검증 + (가능 시) `codex login status` 인증 확인
- 인자 전달: argv 확장/길이 제한 회피를 위해 `chosen-plan.md`를 stdin으로 redirect (`codex exec ... - < chosen-plan.md`)
- 감사 추적: `--json` 으로 전체 이벤트를 `codex-events.jsonl`에 캡처 (기존 `-o`는 마지막 메시지만 기록되던 버그 수정)
- Scope 검증 (즉시 fail): codex 종료 후 plan의 "영향 파일" 외 변경이 감지되면 자동 fallback 없이 즉시 실패 보고
- 비정상 종료 처리 (3택): codex non-zero 종료 시 사용자에게 [1] Claude로 이어서 / [2] 변경 되돌리고 처음부터 / [3] 중단 선택 제시
- 게이트: `HARNESS_USE_CODEX=0` 환경변수로 codex 비활성화, 기본은 사용 가능 시 항상 시도
- SKILL.md Step 7 모델 안내에 codex 우선 사용 + 비활성화 옵션 한 줄 추가

## 0.5.2

- fix(harness): PR 자동 생성 시 base branch를 현재 HEAD 기준으로 동적 결정 — 기존에 `--base main`으로 하드코딩되어 `main` 이외 브랜치에서 하네스를 실행하면 PR이 잘못된 base를 가리키던 버그 수정
- Add Step 6.5: BASE_BRANCH 4단계 폴백 캡처 (현재 HEAD → upstream 추적 브랜치 → origin/HEAD → well-known 브랜치 → `main`)
- Add Step 6.5: 중첩 하네스 경고 (`harness/*` 브랜치 위에서 재실행 시 감지)
- Add Step 6.5: `session.env` 영속 저장으로 SESSION_DIR에 `BASE_BRANCH` 등 핵심 변수 보존
- Add Step 6.5: `worktree add` 에 commit-ish 명시 (`"$BASE_BRANCH"`)로 올바른 베이스에서 분기
- Add Step 11: 진입 시 `session.env` 로드로 `BASE_BRANCH` 복원
- Add Step 11-B: push 직전 `git ls-remote`로 원격 base branch 존재 검증 — 없으면 사용자 확인
- Update Step 11-B: PR 미리보기 및 `gh pr create` 의 `--base` 값을 `$BASE_BRANCH`로 교체

## 0.5.1

- Fix per-agent 토큰 추적이 항상 0으로 기록되던 버그 — `record_usage.py`의 잘못된 프로젝트 해시(`lstrip("/")`), 존재하지 않는 `sessions/` 하위 경로, 실제와 다른 `agent-*.jsonl` 패턴이 모두 매치 실패를 일으켜 totals가 0이었음
- Refactor 토큰 추적을 단순화 — 단계별 기록 대신 Step 10에서 부모 세션 jsonl을 한 번에 합산하여 `usage.json`에 `{session, totals}` 구조로 기록 (retrospective 자체 토큰은 합계 미포함, trade-off)
- Remove `record_usage.py` 헬퍼 스크립트와 단계별 "Record token usage" 호출 6곳

## 0.5.0

- Add `retrospective` 에이전트 — 세션 완료 후 세션 아티팩트를 분석하여 역할별 교훈을 JSON으로 `~/.claude/harness-learnings/`에 누적 저장
- Add Step 10.5: retrospective 호출 (비블로킹, JSON 유효성 검증 포함)
- Add Step 1 교훈 로드 — 최근 5개 세션의 교훈을 에이전트별 역할에 맞춰 선택 주입 (investigator, architect, implementer, reviewer)
- Add context string에 `## 이전 세션 교훈` 섹션 조건부 주입

## 0.4.0

- Add per-agent token usage tracking — 각 서브에이전트 호출 후 JSONL 파싱으로 토큰 소비량을 `usage.json`에 누적 기록
- Add `record_usage.py` 헬퍼 스크립트를 세션 초기화 시 자동 생성
- Add Step 10 완료 요약에 에이전트별 토큰 통계 출력
- Add 누적 `cache_read_input_tokens` 100만 초과 시 수치 기반 `/compact` 자동 안내

## 0.3.1

- Remove codex CLI dependency from implementer agent — Claude 직접 편집(Edit/Write/MultiEdit)을 유일한 구현 경로로 변경
- Remove codex 감지, 실행, 블로킹 프롬프트 로직 제거
- Remove SKILL.md의 "(codex 미설치 시 fallback)" 문구 제거

## 0.3.0

- Add git worktree isolation: implementer works in a dedicated worktree (`harness/<session-id>` branch), keeping the main branch clean and enabling concurrent harness sessions without conflicts.
- Worktree creation is deferred to after plan confirmation (Step 6.5), so investigator/architect/challenger read the original repo directly.
- Add automatic commit and PR creation (Step 11): auto-commits changes, shows PR title/body preview, and creates PR via `gh` after user confirmation.
- Add colored terminal status output (`[harness]-[<agent> 실행 중...]`) before each agent invocation.
- Add worktree cleanup commands in error handling for aborted sessions.
- Update `implementer.md` and `reviewer.md` to use `git -C <project-dir>` for worktree-aware diff operations.

## 0.2.1

- Migrate `harness` orchestrator from agent to skill (`plugins/harness/skills/harness/SKILL.md`). Users can now invoke the full workflow via `/harness <문제>` — the previous `/agent:harness` syntax was invalid in Claude Code.
- Add `auto-update` hook (`check_updates.py`) that checks for new plugin versions on startup.
- Add `CLAUDE.md` with commit conventions (Conventional Commits) and release/tag procedures.

## 0.2.0

- Add multi-agent engineering workflow: `investigator → architect → challenger → implementer → reviewer`.
- Add `harness` orchestrator agent (`claude-opus-4-6`) that coordinates the full pipeline.
- Add `investigator` agent — explores the codebase, identifies root cause, writes `investigation.md`.
- Add `architect` agent — produces a minimal, safe implementation plan in `architecture.md`.
- Add `challenger` agent — proposes 2–3 alternative approaches with trade-off analysis in `alternatives.md`.
- Add `implementer` agent — executes the chosen plan via codex CLI if available, otherwise direct Claude editing.
- Orchestrator selects implementer model based on difficulty: `claude-haiku-4-5` / `claude-sonnet-4-6` / `claude-opus-4-6`.
- Orchestrator runs `/compact` after investigator and after challenger to keep context lean.
- First codex-not-found occurrence pauses and guides the user through installation; subsequent runs fall back silently.
- Add `"agents": "./agents/"` to `plugin.json` — required for all agents to appear in the agents dialog.
- Session state persisted to `~/.claude/harness-sessions/<session-id>/` for auditability.

## 0.1.2

- Remove `hooks` field from `plugin.json`. The `hooks/hooks.json` path is auto-discovered like `agents/`; declaring it explicitly caused `/doctor` to report `Duplicate hooks file detected` and the entire hook chain failed to load.

## 0.1.1

- Remove invalid `agents` field from `plugin.json` — the `agents/` directory is auto-discovered by Claude Code. The explicit field caused manifest validation to fail on install.

## 0.1.0

- Initial release. Ported from `~/.claude/setup-harness.sh`.
- Hooks: `block_dangerous.py`, `protect_sensitive.py`, `log_file_changes.py`.
- Agent: `reviewer`.

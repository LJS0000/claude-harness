# Changelog

## 0.17.1

- fix(harness): ultraharness 훅이 `~/.claude/ultraharness` 디렉터리 부재 시 출력 없이 종료하던 silent skip 동작 수정
- 신규 `plugins/harness/hooks/uh_utils.py` — `warn_if_missing(label)` 헬퍼 제공. 24시간 throttle stamp(`~/.claude/ultraharness.warn_stamp`, UH_DIR 바깥에 위치)를 3개 직접 hook이 공유하여 stderr 경고를 1일 1회만 출력
- `plugins/harness/hooks/inject_uh_on_prompt.py` / `record_uh_event.py` / `report_uh_on_stop.py` — silent `if not os.path.isdir(UH_DIR): sys.exit(0)` 를 `warn_if_missing(...)` 호출로 교체. `uh_utils` 미배포 환경 대비 `try/except ImportError` fallback 포함 — fallback은 False 반환으로 graceful degradation
- `plugins/harness/hooks/manage_uh_tasks.py` — 부모 hook이 경고를 담당하므로 silent 유지, 가드 주석만 `# noop 가드 — UH_DIR 없으면 조용히 종료 (부모 hook이 경고를 담당)`으로 명확화
- `plugins/harness/hooks/sync_uh_tasks.py` — DEVNULL 백그라운드 환경이라 stderr 불가. `_log_skip(reason)` 내부 헬퍼 추가 후 `_should_run()`의 30분 throttle 경로에서 `~/.claude/ultraharness/uh_skip.log`에 기록. UH_DIR 부재 경로는 로그 파일도 쓸 수 없으므로 silent 유지(부모 hook 경고에 의존)

## 0.17.0

- feat(harness): ultraharness task 큐 자동 sync — 4가지 소스(GitHub Issues, retrospective follow_up_tasks, 코드 TODO/FIXME, 사용자 메시지) 수집 파이프라인 추가
- 신규 스크립트 `plugins/harness/hooks/sync_uh_tasks.py` — Stop 훅에서 Popen으로 실행되는 독립 sync 스크립트. `collect_github_issues()` / `collect_retrospective_tasks()` / `collect_todo_comments()` 3개 수집 함수, 30분 throttle(`last_sync.txt` mtime 기반), gh 미설치·오프라인 시 빈 리스트 반환 안전 처리
- `plugins/harness/hooks/manage_uh_tasks.py` — task 레코드 스키마에 `source` / `source_id` / `auto_managed` 3개 필드 추가; `_load_tasks()` 반환 시 기존 jsonl 누락 필드 setdefault 정규화; `sync` 서브커맨드(`cmd_sync`) 추가 — source별 upsert(제목·설명·우선순위 변경 감지) + 사라진 pending 항목 자동 done; O(N) seq 카운터로 신규 task_id 생성; `p_add`에 `--source` / `--source-id` 인자 추가(`dest="source_id"`)
- `plugins/harness/hooks/report_uh_on_stop.py` — `json.load(sys.stdin)` 최상단으로 이동 후 sync Popen 블록 삽입(`start_new_session=True`로 훅 종료 후에도 sync 프로세스 유지); `data` 파싱 실패 시 빈 dict로 폴백하여 태스크 큐 알림은 계속 동작
- `plugins/harness/hooks/inject_uh_on_prompt.py` — `APPLY_KEYWORDS`에서 `"sync"` / `"동기화"` 제거; `TODO_CAPTURE_PREFIXES` 상수 추가; `_handle_todo_capture(user_msg, session_id)` 함수 추가 — 명시적 prefix(`TODO:` / `FIXME:` / `나중에:` / `할일:`) 감지 후 `manage_uh_tasks.py add`로 등록, source_id `msg:<session_id>:<title_hash8>`로 dedupe
- `plugins/harness/agents/retrospective.md` — JSON 스키마에 `follow_up_tasks` 배열 필드 추가; Rules에 작성 지침 추가(명령형 동사 시작, 100자 이내, 최대 5개, 없으면 `[]`)

## 0.16.1

- refactor(harness): PR 템플릿에서 자동 생성 푸터 제거
- `plugins/harness/skills/harness/SKILL.md`: PR 미리보기 템플릿의 `---` 구분선과 `_하네스 세션 <session-id>에서 자동 생성_` 푸터 삭제 — CLAUDE.md "작성 주체 규칙" 준수

## 0.16.0

- feat(harness): implementer 실행 경로(codex / Claude 직접 편집) 가시성 강화
- `agents/implementer.md`:
  - DISABLED 분기의 "조용히 진행" 정책 폐기 — `[implementer] ✗ codex 스킵 → Claude 직접 편집으로 진행 (이유: HARNESS_USE_CODEX=0)` 출력
  - Step 3 진입 시 `[implementer] codex 실행 중... (plan → codex exec)` 출력
  - Step 3-c 정상 완료 시 events 줄 수와 함께 `[implementer] ✓ codex 완료 (exit=0, events=N)` 출력
  - Step 3-b 폴백 [1]/[2]/[3] 각 분기와 Step 4 직접 편집 완료에서 `<session-dir>/implementation-method.txt` 마커 기록 (Step 4는 `if [ ! -f ]` 가드로 중복 덮어쓰기 방지)
  - Completion report `## 사용된 방법` 섹션에 마커 파일 동시 기록 안내 추가
- `skills/harness/SKILL.md`:
  - Step 7 implementer 호출 전 안내를 `codex-status.txt` 1번째 줄 기반 두 갈래로 개선 — `ready` 시 "→ codex로 구현 시도", 그 외 "→ Claude 직접 편집 (codex 상태: ...)"
  - Step 10 최종 요약에 `구현 방식: <IMPL_METHOD>` 한 줄 추가 (마커 파일에서 읽음, 부재 시 "알 수 없음" 폴백)

## 0.15.0

- feat(agent): 에이전트 파이프라인 6가지 구조적 약점 보강 — investigator 저장 강제, architect 템플릿 확장, implementer 스코프 가시화, challenger A/B 대응
- `agents/investigator.md`: frontmatter `tools`에 `Write` 추가; Output 섹션 첫 단락을 "investigation.md를 반드시 Write 도구로 저장 / 구두 보고 금지 / 미저장 시 orchestrator가 재실행" 강제 문구로 교체
- `agents/architect.md`: Before planning에 **Re-investigate Checkpoint** 추가 — 계획 도중 새 정보 발견 시 `architecture.md`(원래 방향)와 `architecture-b.md`(수정 방향) 두 버전을 생성하고 challenger에게 함께 제시; simple 모드 처리 섹션에 A/B 분기 생략 규칙 명시
- `agents/architect.md`: 출력 템플릿 확장 — `## 테스트 계획`을 영향 파일별 (테스트 유형 | 검증 내용 | mock 대상) 표로 표준화; `## Migration Strategy`(schema/DB 변경 한정 — nullable 시작 / 백필 / NOT NULL / DROP COLUMN 단계 + forward/backward 호환 + 검증 쿼리) 추가; `## 배포/운영 트레이드오프`(배포 순서 / 회귀 위험 / phase 분할 / 롤백) 추가
- `agents/implementer.md`: Step 1 plan-files.txt 추출 직후 "수정 가능 파일 N개: ... / 이 외 수정 시 즉시 중단" echo 블록 삽입 — 사용자·에이전트가 진입 즉시 스코프를 인지
- `agents/challenger.md`: Before generating alternatives 1번 단계에 `architecture-b.md` 조건부 읽기 추가 — 두 버전 존재 시 둘 다 "기본안"으로 병기하고 트레이드오프를 먼저 분석

## 0.14.0

- feat(harness): ultraharness 태스크 큐 — 로컬 JSONL 저장소 + `/harness:queue` 스킬 + Stop 훅 추천 + SKILL.md Step 1.75 자동 추천
- 신규 스크립트 `plugins/harness/hooks/manage_uh_tasks.py` — `add / list / top / done / skip` CLI 서브커맨드, `~/.claude/ultraharness/tasks.jsonl` 원자적 CRUD (`os.replace()`), PRIORITY_ORDER(`P0 < P1 < P2`) 기반 정렬, 1000 레코드 초과 시 stderr 경고, `~/.claude/ultraharness/` 미존재 시 즉시 noop
- 신규 스킬 `plugins/harness/skills/queue/SKILL.md` — `/harness:queue add|list|done|skip` 진입점, `manage_uh_tasks.py` 경로 자동 탐색, 오류 시 안내 메시지
- `plugins/harness/hooks/report_uh_on_stop.py` — Stop 훅에 태스크 큐 알림 블록 추가. pending 태스크가 있으면 "대기 태스크 N건 | 최우선: [P0] ..." 한 줄 출력. 기존 이벤트 박스 로직 완전 보존 (`unseen` 체크와 독립)
- `plugins/harness/hooks/inject_uh_on_prompt.py` — `TASK_DONE_KEYWORDS` / `TASK_SKIP_KEYWORDS` 추가, `task-<id>` 패턴과 함께 있을 때 `manage_uh_tasks.py done/skip` 호출. 기존 `SKIP_KEYWORDS`("스킵"/"skip")와 겹치지 않도록 `TASK_SKIP_KEYWORDS`는 "태스크스킵" / "task-skip"만 사용
- `plugins/harness/skills/harness/SKILL.md` — Step 1.5 직전에 Step 1.75 큐 확인 블록 삽입. 사용자 입력 없고 P0 태스크 있으면 제안, 입력 있고 P0이면 한 줄 알림, 그 외 silent. `manage_uh_tasks.py` 미발견 시 silent skip

## 0.13.0

- feat(harness): ultraharness MVP — 멀티 세션 간 도메인 이벤트 전파 레이어
- 신규 훅 `record_uh_event.py` (PostToolUse) — 기존 `log_file_changes.py` 기능 흡수, 도메인 분류(`api_contract` / `design_token` / `general`), `~/.claude/ultraharness/events.jsonl` 단일 저장소에 append, 7일 TTL prune, stale 세션 필터링
- 신규 훅 `report_uh_on_stop.py` (Stop) — 어시스턴트 응답 종료 시 미독취 도메인 이벤트를 텍스트 박스로 사용자에게 보고
- 신규 훅 `inject_uh_on_prompt.py` (UserPromptSubmit) — "적용"/"스킵" 키워드 매칭, `git diff HEAD` 추출 후 다음 turn 컨텍스트에 prepend
- `plugins/harness/skills/harness/SKILL.md` Step 6.5 / 11-C에 세션 등록·탈퇴 블록 추가 (fcntl flock으로 registry 동시 쓰기 보호)
- `~/.claude/ultraharness/` 디렉토리 미존재 시 모든 훅이 즉시 noop — 기존 하네스 설치 호환
- 제거: `plugins/harness/hooks/log_file_changes.py`, `~/.claude/logs/file-changes.jsonl` 신규 append (감사 로그가 `events.jsonl`로 일원화). 기존 로그 파일은 보존
- README의 hook 항목 갱신

## 0.12.0

- feat(harness): 적응형 파이프라인 도입 — 난이도 기반 단계 스킵으로 토큰 사용량 및 실행 시간 절감
- Step 1.5 추가: 사용자 문제 설명을 분석하여 `simple` / `medium` / `complex` 중 하나로 난이도를 추정하고 사용자 확인 후 `HARNESS_MODE`를 결정
- Step 2 조건부 실행: `simple` 모드에서 investigator 스킵, investigation.md를 stub으로 생성하여 후속 단계 호환성 유지
- Step 3 simple 모드 분기: architect context에 `[HARNESS MODE: simple]` 표시 및 직접 탐색 지시 추가
- Step 4 조건부 실행: `complex` 모드에서만 challenger 실행, 그 외에는 alternatives.md stub 생성
- Step 5 모드별 선택지: simple은 architect 안 자동 채택, medium은 [A] + 자유 서술만 제시, complex는 현행 유지
- Step 9 조건부 실행: `simple` 모드에서 reviewer 스킵 (1-2개 파일 변경은 implementer 완료 후 사용자 diff 검토로 충분)
- Step 10 요약 보강: 모드, 실행된 단계, 스킵된 단계를 요약에 명시
- Step 10.5 조건부 실행: retrospective는 `complex` 모드에서만 실행 (학습 가치가 높은 케이스에 한정)
- `architect.md`: `simple` 모드 처리 섹션 추가 — investigation.md stub 감지, 직접 탐색, 간결한 plan 작성 지시
- Context string format에 `[HARNESS MODE:]` 라인 추가 — 모든 서브에이전트가 모드를 인식
- 예상 효과: simple 케이스 약 60% 토큰 절감, medium 케이스 약 30% 절감, complex 케이스 현행 유지

## 0.11.2

- fix(harness): codex 편의 플래그 의존 제거 — `--full-auto` 대신 `-c sandbox_mode=danger-full-access -c approval_policy=never` config override 사용
- flag 사전 검증 grep 블록 제거 (SKILL.md / implementer.md) — codex의 편의 플래그가 다시 바뀌어도 영향받지 않는다
- `flag_mismatch` 상태 및 안내 분기 제거

## 0.11.1

- fix(harness): codex 연동 하드닝 — `implementer.md`와 `harness/SKILL.md`의 동작 결함 6건과 방어적 개선 2건 정리
- P0 감지 결과 변수 캡처 누락: `echo "NO_BINARY"`/`echo "FLAG_MISMATCH"` 등이 stdout으로만 출력되어 후속 분기가 실질적으로 무력화되던 문제를 `DETECT_STATE` 단일 변수로 일원화. Step 2를 2-0(헬퍼) / 2-1(env 게이트) / 2-2(캐시 fast-path) / 2-3(정식 감지) / 2-4(분기 처리) 5단계로 재구성하여 모든 분기를 명시적 코드로 표현
- P0 `codex login --help` timeout 미적용: SKILL.md(세션 시작 점검) 및 implementer.md(감지·재검증) 양쪽에서 codex 프로세스가 hang하면 무한 대기하던 위험을 `_t 5` / `run_with_timeout 5` 래핑으로 차단
- P0 stale 재검증 시 codex-status.txt 3번째 줄(`output_flag=N`) 손실: 재검증 분기에서 파일을 2줄짜리로 덮어써 Step 3의 OUTPUT_FLAG 복원이 실패하던 문제 — 캐시 분기에서는 파일을 더 이상 덮어쓰지 않고, Step 3는 `grep '^output_flag='`로 라인 위치 비의존적으로 읽도록 변경
- P1 timeout exit 124 미구분: `codex --version` / `codex exec --help` / `codex login --help` / `codex login status` 호출 후 exit code를 별도 검사하여 `broken` / `network_error` / `TIMEOUT` 으로 정확히 진단. 이전에는 출력이 비어 `not_logged_in`으로 오분류
- P1 `-o[[:space:]]` flag 검출 오탐: `-o`가 codex의 다른 단문자 옵션과 충돌할 수 있어 `--output-last-message` long-form만 검사. Step 3의 codex 호출도 `-o` 대신 `--output-last-message` 명시적 표기 사용
- P2 timeout 명령 미설치 경고: macOS에 coreutils가 없을 때 SKILL.md / implementer.md 양쪽에서 "codex hang 시 무한 대기 위험" 안내 출력
- P2 환경변수 비숫자 폴백: `HARNESS_CODEX_CACHE_TTL` / `HARNESS_CODEX_TIMEOUT` 가 숫자가 아니면 기본값(120 / 300)으로 폴백

## 0.11.0

- feat(harness): 작성 주체 규칙 도입 — 모든 산출물(코드, 주석, 문서, 커밋 메시지, PR 본문, CHANGELOG 등)을 1인칭 사용자 관점으로 작성하고 AI·도구·자동화 출처 표시를 금지
- `CLAUDE.md`: 최상단에 "작성 주체 규칙" 섹션 추가 — 금지 문구 예시("하네스가 작업함", "Claude가 추가함", "사용자 요청으로", `Co-Authored-By: Claude` 트레일러, `auto-generated by …` 등)와 적용 범위 명시
- `implementer.md`: Principles 다음에 동일 규칙 추가 — codex 결과 메시지를 그대로 옮긴 출처 문구 금지, plan의 "사용자가 요청해서" 표현도 코드로 옮기지 않고 사실만 남김
- `reviewer.md` / `reviewer-standalone.md`: Actions 다음에 동일 규칙 추가 — 수정 적용 시 흔적 금지, diff에 이미 흔적이 포함되어 있으면 이슈로 보고하고 가능 시 직접 제거

## 0.10.0

- feat(harness): 기존 기능 제거 시 architect 단계 명시적 승인 게이트 추가 — 마이그레이션·리팩터·신규 기능 등 사유와 무관, 사용자가 원래 문제 설명에서 제거를 요청했더라도 architect가 구체화한 시점에서 재승인 필수
- `architect.md`: 계획 출력 템플릿에 `## 제거 대상` 섹션 필수화 (없으면 "없음")
- `challenger.md`: 각 대안 블록에 `**제거 대상**:` 라인 추가
- `SKILL.md`:
  - Step 5 선택지 요약에 제거 사항 한 줄 노출
  - Step 6에서 source(A/B/C/D/자유서술)별로 `## 제거 대상` 섹션을 정규화 작성, 자유 서술 시 사용자에게 별도 질문
  - 새 Step 6.3 "제거 대상 승인 게이트" — `chosen-plan.md`를 파싱해 제거 항목이 있으면 명시적 "예/승인" 요구, 섹션 누락 시 fail-safe로 Step 6 복귀
- `reviewer.md`: 가드레일 체크리스트에 "plan 제거 대상에 없는 삭제" 즉시 FAIL 항목 추가

## 0.9.0

- feat(harness)!: `/harness:idea` 스킬과 `idea-writer` 에이전트 제거 — 단일 책임(엔지니어링 워크플로우) 외 범위 정리

## 0.8.0

- feat(harness): `/harness:idea` 스킬 추가 — 자연어 아이디어를 `docs/ideas/<slug>.md` 마크다운 + GitHub Issues 조합으로 정리
- `idea-writer` 에이전트 추가 — Phase 1(구체화) / Phase 2(파일 작성) / Phase 3(issue 생성) 분리로 부분 실패 시에도 초안 보존
- 대상 repo는 별도 인자 없이 스킬 실행 시점의 작업 중인 git repo(`PROJECT_DIR`)를 자동 감지
- Issue 생성 실패 시 `idea` 라벨 없이 무라벨 폴백, 나머지 항목은 계속 처리

## 0.7.1

- fix(harness): codex 실행 경로 안정화 — `implementer.md`와 `SKILL.md` 양쪽에 다음 7개 수정 적용
- P0 stdout/stderr 분리: `codex exec`의 stderr를 별도 `codex-stderr.log`로 분리해 `codex-events.jsonl`이 순수 JSONL을 유지하도록 수정 (기존 `2>&1` 합본은 파싱을 깼음)
- P0 timeout: `gtimeout`/`timeout` 자동 감지 후 `run_with_timeout`/`_t` 헬퍼로 모든 codex 감지 호출에 5초, `codex exec`에 `HARNESS_CODEX_TIMEOUT`(기본 300초) 적용 — hang 시 무한 대기 방지
- P0 `--output-last-message` 플래그 optional: `--full-auto`/`--json`만 필수로 검증하고 `-o`/`--output-last-message`는 있으면 사용·없으면 생략 — 미지원 버전에서 `FLAG_MISMATCH`로 codex가 한 번도 실행되지 않던 문제 해결
- P1 untracked 복구: 비정상 종료 [2] 선택 시 `git restore` 외에 `git clean -fd` 추가로 codex가 생성한 새 파일까지 정리
- P1 scope 경로 정규화: `git status --porcelain` 출력의 따옴표·`./` 접두사를 제거하고 plan-files도 절대→상대 경로로 변환해 `comm -23` 비교 false-positive 제거
- P1 stale 캐시 재검증: `codex-status.txt` 캐시가 `HARNESS_CODEX_CACHE_TTL`(기본 120초) 초과 시 인증 재확인. macOS `stat -f %m` / Linux `stat -c %Y` 양쪽 fallback
- P1 인증 실패 세분화: 기존 `not_logged_in` 단일 분기를 `rate_limited` / `network_error` / `auth_expired` / `not_logged_in` 4분기로 분리하고 `session.env`에 `CODEX_STATE`·`CODEX_HAS_OUTPUT_FLAG` 기록

## 0.7.0

- feat(harness): 세션 시작 시 codex 연결 상태 점검을 SKILL.md Step 1에 추가 — 설치/버전/필요 flag/인증을 한 번에 검사하여 6가지 상태(`ready` / `disabled` / `missing` / `broken` / `flag_mismatch` / `not_logged_in`)로 분류
- 결과를 `<session-dir>/codex-status.txt`에 저장하고 사용자에게 한 줄 요약 출력 — 세션 초입에 codex 사용 가능 여부를 즉시 파악 가능
- implementer.md Step 2에 캐시 fast-path 추가 — `ready` 상태면 재검증 없이 곧바로 codex 실행, 그 외에는 안전망으로 자체 감지 수행

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

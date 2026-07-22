# 하네스 엔지니어링 학습 노트

2026-07-22 · Mousu 융합 설계(0.5) 검증 목적 · 소스 6개

---

## 1. 결론

하네스 = **모델을 감싸는 실행 인프라 계층**임. 프롬프트(단일 호출 최적화)가 아니라 수백 번의 모델 호출에 걸친 실행 환경 전체 — 정보 접근, 도구, 상태, 검증, 인간 개입 시점 — 를 설계하는 일임. 업계 공통 결론 3가지:

1. **프로덕션 실패는 거의 항상 모델이 아니라 하네스에서 남** — 그래서 2025년이 에이전트의 해였다면 2026년은 하네스의 해임
2. **선언형 설계가 이김** — 작업 절차를 그래프로 고정하지 말고 역량(도구·스킬·서브에이전트)과 지식만 선언하고 전략은 모델에 맡김. 모델이 업그레이드돼도 하네스가 살아남음
3. **저장소가 유일한 진실임** — 에이전트가 못 보는 지식(Slack, 머릿속)은 존재하지 않는 것과 같음. 모든 지식은 repo 안 버전 관리되는 텍스트여야 함

**Mousu 설계(0.5)는 이 방향과 대체로 일치함** — git_is_memory, state_rehydration, 스킬 기반 선언형 구성, 증거 게이트가 전부 업계 수렴점과 겹침. 아래 §4의 보강 6건만 반영하면 됨.

---

## 2. 소스별 핵심

### 채널톡 — 하네스란 무엇인가 (출발점)
하네스 3요소: 가드레일(입출력 필터), 데이터 거버넌스(접근 권한·민감 정보), 모니터링·피드백 순환. 하네스는 제한 장치가 아니라 "리스크를 두려워하지 않고 기술을 최대로 쓰기 위한 기반"임.

### Anthropic — Effective harnesses for long-running agents
장기 실행의 근본 문제: **새 세션은 이전 기억이 없음** → 과도한 작업 시도, 조기 완료 선언이라는 두 실패 패턴 발생. 해법:

- 이원 구조: 초기화 에이전트(환경·기능 목록·진행 파일 생성)와 코딩 에이전트(한 번에 한 기능) 분리
- **기능 목록은 JSON으로** — 마크다운보다 모델이 임의 수정을 덜 함. `passes` 필드만 변경 허용
- 세션 시작 프로토콜 고정: pwd → 진행 기록 → 미완료 항목 선택 → 서버 기동 → 기본 동작 확인
- 검증 함정: 단위 테스트·curl은 하지만 **사용자 관점 e2e 검증을 놓침** → 브라우저 자동화로 명시 검증 요구

### OpenAI — Harness engineering (Codex, 5개월 100만 줄)
"Humans steer. Agents execute." 실천법:

- **문서 목차 모델**: 거대한 AGENTS.md 대신 100줄 포인터 + docs/ 계층 구조 — 맥락 피로 방지
- **린터 오류 메시지에 재교육 지침 포함** — 규칙 위반 시 에이전트가 오류문에서 올바른 방법을 배움
- **엔트로피 관리(가비지 컬렉션)**: 에이전트는 기존 패턴을 복제하므로 나쁜 패턴이 확산됨 → 정기 편차 스캔과 자동 정리
- 병합 철학: 게이트 최소화, 짧은 PR — 에이전트 처리량이 인간 주의력을 초과하므로 "수정이 차단보다 쌈"
- 인간 역할 전환: 코드 작성자 → 환경 설계자·피드백 루프 설계자

### Philipp Schmid — Agent Harness 계층론
하네스는 프레임워크(LangChain류)보다 상위 추상화임. 구성: 정보 접근 제어, 인간 개입 메커니즘, 도구 호출 관리, 서브에이전트 조율, 작업 생명주기 관리. Claude Code 자체가 대표적 하네스임.

### Agile Lab — The Rise of the Agent Harness
Framework(부품) / Runtime(상태 관리) / **Harness(배터리 포함 완성 환경)** 구분. 선언형 설계와 컨텍스트 오프로딩(서브에이전트), Agent-as-Judge 평가 체계. Code-as-Action: 복잡한 작업은 JSON 도구 호출보다 실행 가능한 코드 작성이 성공률 ↑.

### Software Mansion — Harness Engineering 실무 가이드
도구 선택 기준표: 반복되는 가벼운 지식 → AGENTS.md / 재사용 워크플로우 → Skills / 외부 인증 → MCP / 독립·병렬 작업 → Subagents / **모델 기억력에 의존하면 안 되는 기계적 로직 → Hooks**. 안티패턴: 자동 생성 설정 파일, **비대한 단일 SKILL.md**, 무검토 서드파티 스킬.

---

## 3. Mousu 설계와의 대조 — 이미 맞는 것

| 업계 수렴점 | Mousu 0.5 대응 | 판정 |
|---|---|---|
| repo가 유일한 진실 | PP-008 git_is_memory, brain 중앙집중 | 일치 |
| 상태 기반 세션 복원 | PP-009 state_rehydration, NOW/NEXT/Handoff | 일치 (Anthropic 세션 프로토콜과 동일 구조) |
| 선언형: 역량+지식 선언, 전략은 모델 | 스킬+에이전트 registry, 라우터가 조합 제안 | 일치 |
| 기계 상태는 JSON, 사람 문서는 짧게 | audit compact JSON / Mousu Brief 12줄 | 일치 |
| 컨텍스트 오프로딩 | 서브에이전트 분리, 상세는 링크 | 일치 |
| 가드레일 3요소 | 훅(가드레일) + 승인 정책(거버넌스) + 품질 게이트 | 대체로 일치, 모니터링 순환이 약함 → §4-5 |

---

## 4. 설계에 반영할 보강 6건

1. **TASKS를 JSON 체크리스트로** (Anthropic) — `projects/{id}/tasks.json`에 `{description, passes}` 구조, Brief에는 요약만. 마크다운 TASKS.md는 사람용 뷰로 유지
2. **루프 한도는 훅으로 강제** (SW Mansion: 기계적 로직은 모델 기억에 안 맡김) — 세션 카운터 파일 + PreToolUse 훅 검사. 0.5의 §9 리스크 1 완화책을 "검토"에서 "확정"으로 승격
3. **훅 차단 메시지에 재교육 지침 포함** (OpenAI) — block_dangerous 등이 거부할 때 "대신 이렇게 하라"를 오류문에 명시
4. **비대 SKILL.md 분할** (SW Mansion 안티패턴) — 기존 harness SKILL.md 51KB는 목차 모델로 재구성: 본문은 흐름 제어만, 단계 상세는 references/ 파일로 분리
5. **brain 가비지 컬렉션** (OpenAI) — stale 표시(PRD freshness)에 더해, 주기적 `/mousu` 유지보수 워크플로우가 편차·낡은 문서를 스캔해 정리 PR(커밋) 제안
6. **e2e 검증 명시** (Anthropic) — reviewer의 증거 게이트에 "가능한 경우 사용자 관점 end-to-end 확인(브라우저/실행 데모)" 조항 추가. 단위 테스트 통과만으로 검증 완료 선언 금지

---

## 5. 소스

- 채널톡, 하네스란 무엇인가 — https://channel.io/kr/blog/articles/what-is-harness-2611ddf1
- Anthropic, Effective harnesses for long-running agents — https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- OpenAI, Harness engineering: leveraging Codex in an agent-first world — https://openai.com/index/harness-engineering/
- Philipp Schmid, Agent Harness 정리 (X 포스트 요약본) — https://www.utkarshapoorva.com/wiki/philschmid-importance-of-agent-harness-2026/
- Agile Lab, The Rise of the Agent Harness — https://agilelab.substack.com/p/the-rise-of-the-agent-harness
- Software Mansion, Harness engineering 가이드 — https://agentic-engineering.swmansion.com/becoming-productive/harness-engineering/

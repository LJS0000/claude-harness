# Mousu × Harness 설계 문서

버전 0.9.1 (확정본) · 2026-07-22 · 인터뷰 6라운드 + 설계자 결정 질의응답 21건 + /mousu-btw 명령어명 확정

> 0.9는 설계자가 임의로 정했던 23개 결정을 사용자와 1:1로 확정한 버전임. 모든 주요 결정에 사용자 승인이 붙음.

---

## 1. 결론

**플러그인 2개로 분리함.** harness는 퍼블릭·거의 무변경으로 회사에서 그대로 쓰고, mousu는 신규 프라이빗 레포(`mousu`)에서 개인 회사 운영 OS로 개발함. mousu의 개발 실행은 설치된 harness를 호출해 위임함.

- **mousu의 정체**: 문제를 넣으면 여러 페르소나가 협업해 검증된 솔루션을 내는 1인 회사의 자동 실행 조직 + 혼자 일하는 창업자의 사고 파트너
- **작동 모델**: 요청 직후 충분한 토론(front-load) → 아웃풋까지 무개입 자율 루프 → 체크리스트 통과까지 반복 → 결과와 반론·대안 함께 전달
- **회사에서는**: harness만 설치·사용. mousu·brain은 회사 기기에 없음 → 공용 리포 기억 문제 소멸

---

## 2. 두 사용 시나리오

### 시나리오 1 — 내 IT 회사의 자동 운영 (mousu 전체)

큰 방향과 task 선정은 Jisu가 함. 자료 조사·마케팅·디자인·기획·개발·그로스·QA·문서화는 mousu가 수행함. Jisu는 **문제**를 제공하고 mousu는 페르소나들의 협업으로 **솔루션**을 제공함. 자연어로 업무를 시키면 루프와 검증으로 체크리스트 통과선을 넘을 때까지 뾰족하게 관리함. 사람 개입은 최소화하되, 혼자 일하는 Jisu의 **토론 상대·대안 제시자·방향 이탈 경보** 역할이 동등하게 중요함. IT 프로덕트를 만들지만 판단상 개발이 필요 없으면 다른 방향의 솔루션도 가능함.

### 시나리오 2 — 재직 중인 회사 (harness만)

회사에서는 사실상 개발자(harness)만 호출함. 회사 리포는 혼자 쓰더라도 공용 프로젝트임 — 그래서 mousu·brain을 회사 기기에 설치하지 않아 문제를 원천 차단함. harness는 지금처럼 brain 없이 동작하며 회사 리포의 CLAUDE.md·팀 컨벤션을 따름.

---

## 3. Intent Contract (확정 사항)

| 항목 | 확정 내용 | 근거 |
|---|---|---|
| 구조 | 플러그인 2개: harness(퍼블릭) + mousu(신규 프라이빗 레포 `mousu`) | Q1, 인터뷰 |
| 실행 환경 | Claude Code 안, 구독 인증 | 인터뷰 |
| 기억 저장소 | 중앙 brain **별도 레포** `mousu-brain`, 개인 GitHub private | Q2 |
| 경로 | brain=`~/dev/mousu-brain`, 설정=`~/.mousu/config.yaml` | Q4 |
| 프로젝트 인식 | 현재 폴더 git remote로 자동 판별, 모를 때만 확인 | Q6 |
| 회사 격리 필드 | `fallback: project_local` **삭제** (회사엔 mousu 미사용) | Q5 |
| 에이전트 정의 위치 | 플러그인 소유 (brain에 agents/ 없음) | Q7 |
| 출력 규칙 | ~음/~임 유지, **길이·행동 수 제한 없음**, action은 step-by-step 당장 할 일, 의사결정엔 트레이드오프 필수 | Q8 |
| CEO | `/mousu` 라우터 스킬 본문이 겸임 | Q9 |
| tech 관점 | harness architect를 검토 모드로 호출 (tech_lead 미생성) | Q10 |
| 마케터 | growth·content **분리**하되 요구조건에 맞게 선택 호출 | Q11 |
| devil/challenger | 별개 유지 (반대 논증 vs 대안 제시) | Q12 |
| 개발자 페르소나 | 직함형 "테크리드가 이끄는 개발팀", 멘트만 페르소나·산출물 건조 | Q13 |
| 불가역 지점 | 무질문 파킹 후 계속, 아웃풋 때 일괄 제시 | Q14 |
| 확인 타이밍 | 정책 델타·파킹 승인·/btw를 세션 말미 일괄 1회 | Q15 |
| harness 미설치 | 경고 후 간이 실행 폴백 | Q16 |
| 채점 | 심판 분리 + 증거 필수 + **codex 크로스 채점 처음부터** | Q18 |
| 정책 파일 | `company/POLICIES.md` 신설 (ID·시행일·supersedes) | Q19 |
| 정책 집행 | 승인된 정책만 가드레일, proposed는 미집행 | Q20 |
| 자기개선 명령 | `/mousu-btw` (내장 `/btw` 충돌 회피), 백로그는 mousu 레포 GitHub Issue | Q21 |
| 학습 델타 | 6건 전부 채택 | Q22 |
| ponytail | 주석 컨벤션 제거, Ponytail ladder 유지 | Q3 |
| codex | 구현 + 카운터리뷰 (코드 작업 한정) | 인터뷰 |

---

## 4. 출력 규칙 — Mousu Brief (Q8 확정, 강조)

사람용 출력의 핵심 규칙임. PRD 기본값에서 3가지를 바꿈:

1. **길이 제한 없음** — 첫 화면 12줄 같은 고정 제한을 없앰. 내용에 맞게 필요한 만큼 쓰되 두괄식·불필요한 반복 금지는 유지함
2. **행동 수 제한 없음, 대신 action 중심** — "지금 할 일"은 task(해야 할 일)가 아니라 **action(당장 할 일)을 step-by-step으로** 제공함. 개수는 필요한 만큼
3. **의사결정엔 트레이드오프 필수** — Jisu가 판단해야 하는 모든 지점은 선택지와 함께 트레이드오프를 반드시 붙임. "A로 할까요?"가 아니라 "A(장점/단점) vs B(장점/단점)"로 제시함

종결어미는 ~음/~임/명사형 유지, ~습니다체 회피. 상세 근거·로그는 audit로 분리(사람 화면 기본 비노출).

---

## 5. 아키텍처

```
[개인 기기]                                  [회사 기기]
Claude Code                                  Claude Code
├── mousu 플러그인 (프라이빗 레포 mousu)       └── harness 플러그인만
│    /mousu   라우터·CEO 오케스트레이터            (그대로, brain 없음,
│    /mousu-status /mousu-sync /mousu-init         회사 리포 컨벤션 준수)
│    agents/  researcher·advocate·devil·
│             growth·content·operations·
│             designer·policy-steward
│    hooks/   loop_counter·brain_guard·secret_scan
│    checklists/ 유형별 초기값
│
├── harness 플러그인 (퍼블릭, 거의 무변경)
│    /harness — mousu가 개발 실행 시 호출 (§8)
│
└── mousu-brain (별도 프라이빗 레포, 중앙 기억)
     operator/ company/ projects/ inbox/ handoffs/
     templates/checklists/ audit/ .mousu/(untracked)
```

### mousu 플러그인 디렉토리

```
mousu/
├── .claude-plugin/  marketplace.json + plugin.json
├── skills/
│   ├── mousu/SKILL.md          # 라우터+CEO (목차 모델, references/ 분리)
│   ├── mousu-status/SKILL.md   # 현재·막힘·다음 + proposed 정책·/mousu-btw 표시
│   ├── mousu-sync/SKILL.md
│   └── mousu-init/SKILL.md
├── agents/
│   ├── researcher.md  advocate.md  devil.md
│   ├── growth.md  content.md  operations.md
│   ├── product-designer.md  policy-steward.md
│   # ceo = 라우터 스킬 본문 (Q9)
│   # tech 관점 = harness architect 검토 모드 호출 (Q10)
├── hooks/  loop_counter.py  brain_guard.py  secret_scan.py  hooks.json
└── checklists/  (init 시 brain으로 복사, 이후 brain이 원본)
```

에이전트 원칙: 프로젝트마다 인격 복제 없음. advocate/devil은 동일 스냅샷 독립 실행, 서로 못 봄. **growth·content 마케터는 분리하되 요구조건에 맞을 때만 호출**(관련 없으면 안 부름 — selection_policy 계승). CEO(라우터)는 의견 수가 아니라 근거 품질로 종합함.

---

## 6. 작동 모델 — "문제 → 검증된 솔루션"

### 6.1 3단계 개입 모델

```
[1. 토론 (front-load)]  요청 직후 충분한 대화
   - 실제 목적·성공 기준·제약 정렬 (Intent Contract)
   - Jisu 아이디어 반론·대안 제시 (devil 관점 포함)
   - 예상 불가역 지점·비용을 미리 식별해 사전 승인 패키지로 처리
   - 이번 작업 체크리스트·통과선 확인 (기본값 있으면 생략)
[2. 자율 루프 (무개입)]  아웃풋까지 질문하지 않음 (Q14)
   - 연구→토의→계획→실행→검증, 체크리스트 통과까지 반복
   - 사전 승인 밖 불가역 지점: 직전까지 준비 후 파킹, 다른 작업 계속
[3. 아웃풋 + 토론]  결과 전달과 함께
   - Mousu Brief (결론 · action step-by-step · 핵심 근거)
   - 반론·더 나은 대안·방향 이탈 경고를 별도 섹션
   - 파킹된 승인·정책 델타·/mousu-btw 백로그 세션 말미 일괄 확인 1회 (Q15)
```

"방향 이탈 경고"는 중간 인터럽트가 아니라 1단계(사전 반론)와 3단계(결과 반론)에 배치 — 개입 최소화와 사고 파트너를 시간축으로 분리해 양립.

### 6.2 솔루션 권한

주어진 문제 안에서 수단은 완전 자율(개발/노코드/운영적 해결/외주 추천). "문제 자체가 틀렸다" 판단이 서면 작업을 멈추지 않고 요청 솔루션 + **문제 재정의 제안을 별도 첨부**함 (트레이드오프 함께).

### 6.3 체크리스트 시스템

구조: 모든 항목은 **필수**(하나라도 실패 시 루프 계속)와 **권장**(통과율 점수화)로 구분. 통과선: **필수 100% + 권장 80%** (작업별 조정 가능). 한도 도달 시 미달 항목 명시하고 전달.

채점은 제작 에이전트와 분리된 심판 관점 + 실행 증거(테스트·데모·실측·출처) 첨부 필수. **개발 산출물은 codex 크로스 채점을 처음부터 병행**함 (Q18).

**공통 코어 (모든 산출물 필수)**: Intent 부합 · 사실주장 증거연결 · 현행 정책 위반 없음 · 두괄식 · 한계/미검증 명시

| 유형 | 필수 | 권장 |
|---|---|---|
| 개발 | 계획 대비 스코프 일치 · 테스트 실행 증거 · secret scan | e2e 확인 · 롤백 계획 |
| 조사 | 독립 출처 ≥2 · 게시일/조회일 · unknown 목록 | 핵심 주장 1차 출처 · 반대 근거 |
| 기획 | 문제 정의 한 문장 · 성공 지표 · 기존 결정 정합 | 대안 ≥2 비교 · 리스크/철회 조건 |
| 마케팅 | 타깃·채널 명시 · 정책·브랜드 톤 | 측정 방법 · CTA 명확 |
| 디자인 | 사용자 문제 연결 · 플로우 완결 | 접근성 · 디자인 규칙 정합 |
| QA | 재현 절차 · 실패 케이스 문서화 | 커버리지 · 회귀 목록 |
| 문서화 | 대상 독자 · 따라 할 수 있음 | 두괄식 · 링크 정합 |

체크리스트는 brain `templates/checklists/`에 버전 관리되는 살아있는 문서. "이 항목 빼/추가해" 한마디로 진화하고, 대화 중 기준 변화도 감지해 반영 제안 (Q17: 초안 이대로 시작).

### 6.4 루프 규율

한도(research 3, 수정 2, 단계 실행 3, 2회 연속 무진전 중단)를 프롬프트 + **카운터 파일·훅으로 기계적 강제**(loop_counter.py). 모든 루프는 정상 종료/파킹/명시적 한계 전달로만 끝남.

---

## 7. brain — 중앙 기억 (별도 레포)

- `mousu-brain` 프라이빗 레포 1개(플러그인 레포와 분리 — Q2), `~/.mousu/config.yaml`이 경로 참조
- 분리 이유: 플러그인 설치 시 레포 전체가 기기별 캐시로 복사됨 → 같은 레포면 기억이 캐시에 딸려가 원본이 애매해지고, 세션 커밋이 릴리즈 히스토리를 오염시키며, 향후 플러그인 공개·정리가 어려워짐
- 계층: Canonical(검증 통과분) / Audit(intent·context·run·claim-evidence, compact JSON) / Ephemeral(untracked)
- tasks는 `{description, passes}` JSON, 사람용 뷰는 NOW/NEXT
- 세션 규율: 시작 fetch→ff-pull(충돌 시 쓰기 중단), 종료 secret scan→commit→push→Handoff. 기기 간 이어가기는 state rehydration
- 프로젝트 자동 인식: 현재 폴더 git remote ↔ brain repository.yaml 대조, 모를 때만 확인 1회 (Q6)
- 회사 관련 조항·`fallback: project_local` 필드 삭제 (Q5) — mousu는 개인 전용

---

## 8. harness와의 관계 — 위임 인터페이스

harness 변경은 **주석 컨벤션 제거 하나뿐**: harness-debt 스킬 제거 + implementer의 ponytail 주석 컨벤션 제거. **Ponytail ladder(구현 경로 판단 휴리스틱)는 유지**함 (Q3). 부채는 프로젝트 리포 Issue로 관리.

mousu가 개발 실행이 필요할 때 (같은 세션 내 스킬/에이전트 호출):

1. 1단계 토론 결과(승인된 계획·제약·체크리스트)를 문제 설명으로 압축해 `/harness` 호출. mode(simple/medium/complex)는 mousu가 사전 판정해 전달
2. 파이프라인 전체가 아니라 특정 역할만 필요하면 harness 서브에이전트를 개별 호출 (예: architect를 검토 모드로 — Q10)
3. harness 산출물(chosen-plan.md, verification.txt, 리뷰)을 mousu 검증 루프의 증거로 수용
4. 개발자 페르소나 연출(테크리드)·Brief 변환은 mousu 계층에서 (Q13). harness 출력 원형 유지
5. harness 미설치 시 경고 후 mousu 자체 간이 실행 폴백 (Q16)

**위임 계약 문서화**: 플러그인 간 호출은 공식 API가 아니라 같은 세션 로드 스킬 호출이므로, harness 스킬명·산출물 경로가 바뀌면 mousu 위임 템플릿도 맞춰야 함. §8을 "넘기는 것 / 돌려받는 것" 계약으로 고정하고, harness가 거의 무변경이라 계약이 안정적임 (M6에서 템플릿화).

---

## 9. 정책 관리 — policy_steward

정책 원본은 brain `company/POLICIES.md`(신설, Q19) + `company/PRINCIPLES.md` + `projects/{id}/RULES.md`. 모든 항목에 ID·시행일·근거 링크, 변경 시 supersedes 기록.

임무 4개:
1. **상시 감지** — 모든 워크플로우 저장 단계에 policy delta scan 내장. 개발·마케팅 대화 중 암묵적 정책 신설/변경/폐지를 추출해 기존 정책과 대조. 흐름 안 끊음
2. **반영** — proposed로 즉시 문서화 → supersedes·영향 스캔 → Brief "변경"에 1줄 → 세션 말미 일괄 확인 1회로 시행 (Q15). 정식 시행은 approved Decision급
3. **집행** — 검증 단계의 policy_compliance 게이트. **승인된 정책만 집행, proposed는 미집행** (Q20)
4. **정합성** — stale·불일치·장기 미확인 proposed 정리 (가비지 컬렉션 통합)

호출: 상시(저장 단계 delta scan) + 명시(라우터가 정책 변경 의도 감지 시 라우팅). 별도 스킬 없이 대화만으로 동작.

---

## 10. /mousu-btw — mousu 자기개선 루프

명령어명은 `/mousu-btw` — Claude Code 내장 `/btw`와 충돌하므로 mousu 네임스페이스로 통일함.

- **수동**: `/mousu-btw <불편한 점>` 한 줄이면 흐름 안 끊고 mousu 레포 **GitHub Issue**로 적재 (Q21)
- **자동 감지**: 마찰 신호(같은 질문 반복, 재작업, 규칙 위반 재시도, 루프 한도 도달) 감지해 Issue 초안 적재
- **제안**: 주기적으로(또는 status 호출 시) 백로그를 묶어 개선안으로 정리·제안
- **구현**: 승인 시 harness 파이프라인으로 mousu 레포 수정 — 자가 수정 금지(도구가 자신을 고치는 회귀 리스크). 범용 개선은 "범용" 태그 후 퍼블릭 harness 기여 후보로 분류

---

## 11. 하네스 학습 델타 (6건 전부 채택 — Q22)

1. tasks.json (`passes`만 변경 허용) → mousu
2. 루프 한도 훅 강제 → mousu loop_counter.py
3. 훅 차단 메시지에 재교육 지침 → mousu 훅
4. SKILL.md 목차 모델 → mousu 라우터 스킬에 처음부터, harness 분할은 기여 후보
5. brain 가비지 컬렉션 → policy_steward 정합성 임무 통합
6. e2e 검증 → mousu 체크리스트(개발 권장), harness reviewer 강화는 기여 후보

---

## 12. 리스크와 미결

1. **harness 위임 컨텍스트 압축 품질** — mousu 토론 맥락을 harness 문제 설명으로 압축하는 품질이 관건. M6 템플릿화
2. **체크리스트 초기값 검증** — §6.3은 초안(이대로 시작). 첫 실전 3~5건 회고로 다듬음 (M8)
3. **점수 인플레이션** — 심판 분리 + codex 크로스 채점(처음부터)으로 완화
4. **퍼블릭 harness 기여 범위** — 별도 승인·별도 커밋. v1은 후보 분류까지만

---

## 13. 구현 순서 (Q23 확정 — 이대로)

| 단계 | 내용 | 산출물 |
|---|---|---|
| M1 | mousu 프라이빗 레포 생성 + 플러그인 스캐폴드 + harness에서 harness-debt·ponytail 주석 컨벤션 제거 | 설치 가능한 뼈대 |
| M2 | /mousu-init + mousu-brain 스캐폴드 + config + 체크리스트 초기값 | brain 생성 |
| M3 | 라우터 v1 (토론 front-load→Intent→simple_task→Brief) + 상태·기억 | 상태·기억 워크플로우 |
| M4 | researcher + 증거 스키마 + 체크리스트 검증 루프(심판 분리·통과선·한도·codex 채점) | 조사 + 품질 루프 |
| M5 | advocate/devil/CEO 종합 + 반론·대안 섹션 + DECISIONS 승인 | 의사결정 워크플로우 |
| M6 | harness 위임 인터페이스 (계획→호출 템플릿→산출물 수용→테크리드 래핑) | 개발 실행 연결 |
| M7 | policy_steward + /mousu-btw + growth/content/operations/designer + 훅 3종 | v1 기능 완성 |
| M8 | 실전 3~5건 파일럿 → 체크리스트·통과선·개입 모델 회고 조정 | **사용화(v1.0) 판정** |

각 단계는 독립 사용 가능한 상태로 끝남. M3까지만 해도 일상 사용 가능, M8 회고가 "사용화" 완료 기준.

---

*0.9는 확정본임. 승인 시 M1 착수. 추가 수정은 섹션 번호로.*

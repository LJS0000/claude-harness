# Mousu 설계 — 설계자 임의 결정 질문지

2026-07-22 · 설계 문서 0.8 기준 · 사용자가 직접 확정한 사항은 제외, Claude가 기본값으로 정한 23건만 수록

답변 방법: "Q1 OK, Q3 주석도 제거, Q13 캐릭터형" 식 자유 답변. 무응답 항목은 현행 유지로 간주.

## A. 구조·리포

- **Q1.** mousu 신규 레포 이름·마켓플레이스: "LJS0000/mousu + 자체 마켓플레이스"로 잡음. 레포명 이대로?
- **Q2.** brain을 플러그인 레포와 분리(별도 mousu-brain 레포)로 설득·확정함 — 원래 제안은 "지금 리포 프라이빗 전환 후 전부 수용". 분리 확정?
- **Q3.** harness 변경 범위를 harness-debt 제거 하나로 한정. ponytail 주석 컨벤션(implementer)·Ponytail ladder(architect)는 유지로 둠. 주석 컨벤션 제거? ladder 유지?

## B. brain·기억

- **Q4.** brain=`~/dev/mousu-brain`, 설정=`~/.mousu/config.yaml`. OK?
- **Q5.** `fallback: project_local` 필드 — v1 미구현·예약만. 회사에서 mousu 미사용 확정이므로 삭제 가능. 유지 vs 삭제?
- **Q6.** 활성 프로젝트 자동 식별: cwd의 git remote ↔ brain repository.yaml 대조. OK?
- **Q7.** brain 안 `agents/` 디렉토리 제거 (에이전트 정의는 플러그인 소유). OK?
- **Q8.** 출력 스타일: PRD 그대로 (~음/~임, 첫 화면 12줄, 행동 최대 3개). OK?

## C. 에이전트 구성

- **Q9.** CEO = `/mousu` 라우터 스킬 본문 겸임 (별도 서브에이전트 아님). OK?
- **Q10.** tech_lead 미생성 — harness architect를 검토 모드로 호출. OK?
- **Q11.** growth + content marketer → marketer 1명으로 시작. OK?
- **Q12.** devil(반대 논증)과 harness challenger(대안 제시) 별개 유지. OK?
- **Q13.** 개발자 페르소나: 직함형(테크리드 리드, 멘트만 페르소나·산출물 건조). 캐릭터형 선호?

## D. 작동 모델

- **Q14.** 자율 루프 중 예상 못한 불가역 지점: 무질문 파킹(직전까지 준비, 다른 작업 계속, 아웃풋 때 일괄 제시). 즉시 질문이 낫나?
- **Q15.** 정책 델타·파킹 승인·/btw 백로그 → 세션 말미 일괄 확인 1회. OK?
- **Q16.** harness 미설치 시: 경고 후 mousu 자체 간이 실행 폴백. 실행 작업 거부가 낫나?

## E. 품질·체크리스트

- **Q17.** 7개 유형별 체크리스트 항목·필수/권장 배정(설계 문서 §6.3 표) 전부 초안임. 수정할 항목?
- **Q18.** 심판 분리 채점 + 증거 필수, codex 크로스 채점은 형식화 징후 시 도입으로 유보. OK?

## F. 정책·자기개선

- **Q19.** `company/POLICIES.md` 신설 + 정책 ID·시행일·supersedes 스키마. OK?
- **Q20.** proposed 정책은 미집행, 승인된 정책만 가드레일 집행. OK?
- **Q21.** /btw 백로그 위치 = mousu 레포 (형식 미정: BACKLOG.md vs GitHub Issue?). 자가 수정 금지·승인 후 harness 구현. OK?

## G. 학습 반영·구현 계획

- **Q22.** 학습 델타 6건 전부 채택 (tasks.json / 루프 훅 / 재교육 메시지 / 목차 모델 / 가비지 컬렉션 / e2e). 제외할 것?
- **Q23.** M1~M8 순서 + "사용화 = M8 실전 3~5건 회고 통과". OK?

---
name: harness-debt
description: 프로젝트 전체에서 `ponytail:` 주석을 수집하고 파일별로 그룹화해 1회성 ledger를 보고하는 스킬. 코드 변경 없음. 출처: ponytail (MIT License, DietrichGebert/ponytail)
version: 1.0.0
triggers:
  - /harness-debt
  - ponytail debt 보여줘
  - ponytail ledger
---

# harness-debt

프로젝트에 남겨진 `ponytail:` 주석을 수집하고 파일별로 그룹화해 보고한다.
이 스킬은 **읽기 전용**이다 — 코드 변경, 파일 수정, 커밋을 수행하지 않는다.

## 실행 방법

```
/harness-debt
```

또는 자연어: "ponytail debt 보여줘", "ponytail ledger 보여줘"

## Step 1: 프로젝트 루트 확인

현재 작업 디렉터리를 프로젝트 루트로 사용한다.

```bash
PROJECT_DIR=$(pwd)
echo "프로젝트 루트: $PROJECT_DIR"
```

## Step 2: ponytail 주석 수집

```bash
grep -rnE '(#|//|--) ?ponytail:' "$PROJECT_DIR" \
  --include="*.ts" --include="*.js" --include="*.py" \
  --include="*.go" --include="*.rs" --include="*.java" \
  --include="*.md" --include="*.sh" \
  --exclude-dir=.git \
  2>/dev/null
```

결과가 없으면:

```
ponytail 주석이 발견되지 않았습니다.
프로젝트에 `// ponytail: <ceiling>, <upgrade path>` 형식의 주석이 없습니다.
```

## Step 3: 파일별 그룹화 및 보고

수집 결과를 파일 경로 기준으로 그룹화하여 아래 형식으로 출력한다:

```
## ponytail debt ledger

총 N개 항목, M개 파일

### src/auth/login.ts
- L42: O(n²) scan acceptable for <100 items, upgrade to Map when list grows
- L87: try/catch silences DB error, add structured logging when observability is set up

### src/utils/parser.py
- L15: regex covers current input format only, rewrite with proper grammar if format diversifies

---
이 보고는 스냅샷입니다. 코드 변경은 수행하지 않았습니다.
```

## 규칙

- 코드를 수정하거나 파일을 편집하지 않는다.
- 수집 결과를 파일로 저장하지 않는다 (1회성 콘솔 보고).
- 항목을 우선순위 정렬하거나 fix를 제안하지 않는다 — 현황 보고만 한다.
- 프로젝트 루트 외부 경로를 탐색하지 않는다.

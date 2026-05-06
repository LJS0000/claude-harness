# CLAUDE.md

## Commit Convention

Conventional Commits 형식을 따릅니다.

```
<type>(<scope>): <subject>
```

### Type

| type | 용도 |
|------|------|
| `feat` | 새 기능 |
| `fix` | 버그 수정 |
| `docs` | 문서 변경 |
| `refactor` | 기능 변경 없는 코드 개선 |
| `chore` | 빌드, 설정, 의존성 등 기타 작업 |

### Scope (선택)

영향 범위를 소문자로 표기합니다. 예: `agent`, `hook`, `plugin`, `cli`

### Subject

- 한국어 또는 영어 모두 허용
- 명령형 현재형으로 작성 (예: "add", "remove", "추가", "수정")
- 마침표 없음

### 예시

```
feat(agent): add difficulty-based model selection
fix(hook): prevent duplicate hook registration
docs: update README with install instructions
refactor(harness): simplify pipeline stage transitions
```

---

## 버전 규칙 (Semantic Versioning)

`MAJOR.MINOR.PATCH` 형식을 따릅니다.

| 변경 유형 | 올릴 자리 | 예시 |
|-----------|-----------|------|
| 호환성 깨지는 변경 | MAJOR | `0.x.x → 1.0.0` |
| 새 기능 추가 (하위 호환) | MINOR | `0.2.1 → 0.3.0` |
| 버그 수정, 소규모 개선 | PATCH | `0.2.0 → 0.2.1` |

---

## 커밋별 버전 관리 규칙

**모든 커밋 시 아래 규칙에 따라 버전을 판단하고, 버전 변경이 필요한 경우 릴리즈 절차를 함께 수행합니다.**

### 커밋 타입 → 버전 매핑

| 커밋 타입 | 버전 변경 | 설명 |
|-----------|-----------|------|
| `feat` | **MINOR** bump | 새 기능은 항상 MINOR 버전을 올림 |
| `fix` | **PATCH** bump | 버그 수정은 PATCH 버전을 올림 |
| `refactor` | **PATCH** bump | 코드 개선은 PATCH 버전을 올림 |
| `docs` | 버전 변경 없음 | 문서만 변경한 경우 버전 유지 |
| `chore` | 버전 변경 없음 | 빌드/설정 변경은 버전 유지 |

### Breaking Change 규칙

- 커밋 메시지에 `BREAKING CHANGE:` footer가 있거나 타입 뒤에 `!`가 붙으면 **MAJOR** bump
- 예: `feat!: remove legacy auth middleware` → MAJOR bump
- 단, `MAJOR`가 `0`인 동안은 breaking change도 **MINOR** bump으로 처리 (pre-1.0 단계)

### 버전 변경 절차

버전 변경이 필요한 커밋(`feat`, `fix`, `refactor`) 시 **별도의 `chore: bump` 커밋을 만들지 않는다**. 대신 버전 파일 업데이트를 해당 기능/수정 커밋에 함께 포함한다 (아래 "릴리즈 절차" 참조).

### 버전 변경이 누적된 경우

여러 커밋을 한 번에 작업한 경우, **가장 높은 우선순위의 변경**을 기준으로 한 번만 버전을 올림:
- `feat` + `fix` 조합 → MINOR bump (feat 우선)
- `fix` + `refactor` 조합 → PATCH bump (둘 다 PATCH)
- `feat` + `feat` 조합 → MINOR bump (한 번만)

---

## 릴리즈 절차

버전 변경이 필요할 때 아래 순서를 따릅니다 — **모두 단일 커밋 안에서 처리**:

1. 코드 변경을 stage
2. 같은 stage에 버전 파일 업데이트를 함께 포함:
   - `CHANGELOG.md` — 새 버전 섹션 추가, 변경 내용 기록
   - `plugins/harness/.claude-plugin/plugin.json` — `"version"`
   - `.claude-plugin/marketplace.json` — `plugins[0].version`
3. 단일 커밋 작성 (해당 변경의 type 그대로):
   ```
   feat(<scope>): <subject>
   fix(<scope>): <subject>
   refactor(<scope>): <subject>
   ```
4. 같은 커밋에 태그 생성:
   ```
   git tag v<version>
   ```
5. 함께 push:
   ```
   git push origin main && git push origin v<version>
   ```

### 예외: 코드 변경 없이 버전만 올려야 할 때

CHANGELOG 정정 등 드문 경우에만 `chore: release v<version>` 형식의 단독 커밋을 허용한다. 일반적인 흐름에서는 사용하지 않는다.

### 버전이 기록되는 파일 목록

| 파일 | 필드 |
|------|------|
| `plugins/harness/.claude-plugin/plugin.json` | `"version"` |
| `.claude-plugin/marketplace.json` | `plugins[0].version` |
| `CHANGELOG.md` | 최상단 버전 섹션 헤더 |

---

## 태그 규칙

- 형식: `v<MAJOR>.<MINOR>.<PATCH>` (예: `v0.2.1`)
- **태그 생성은 릴리즈 절차의 필수 단계** — 코드 변경 + 버전 파일 업데이트가 들어간 단일 `feat`/`fix`/`refactor` 커밋에 `git tag`까지 완료할 것
- annotated 태그 대신 lightweight 태그 사용
- 태그 없이 push하지 않음 — 커밋과 태그를 함께 push:
  ```
  git push origin main && git push origin v<version>
  ```
- 태그가 누락된 과거 버전 발견 시 해당 릴리즈 커밋(또는 과거 `chore: bump` 커밋)에 백필:
  ```
  git tag v<version> <commit-hash>
  git push origin v<version>
  ```

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
chore: bump version to 0.2.1
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

## 릴리즈 절차

1. `CHANGELOG.md` 업데이트
2. `plugins/harness/.claude-plugin/plugin.json` 버전 업데이트
3. `.claude-plugin/marketplace.json` 버전 업데이트
4. 버전 bump 커밋 작성:
   ```
   chore: bump version to <version>
   ```
5. 태그 생성:
   ```
   git tag v<version>
   ```
6. push:
   ```
   git push origin main
   git push origin v<version>
   ```

---

## 태그 규칙

- 형식: `v<MAJOR>.<MINOR>.<PATCH>` (예: `v0.2.1`)
- 태그는 반드시 버전 bump 커밋에 달 것
- annotated 태그 대신 lightweight 태그 사용

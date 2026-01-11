# 개발 워크플로 가이드

> PokerKit 기반 텍사스 홀덤 웹서비스 개발 프로세스 및 규칙

---

## 브랜치 전략

### Git Flow (간소화)

```
main (production)
  └── develop (integration)
        ├── feature/xxx
        ├── fix/xxx
        └── docs/xxx
```

### 브랜치 네이밍

| 타입 | 패턴 | 예시 |
|------|------|------|
| 기능 | `feature/<설명>` | `feature/lobby-room-list` |
| 버그 수정 | `fix/<설명>` | `fix/reconnect-state-sync` |
| 문서 | `docs/<설명>` | `docs/api-spec-update` |
| 리팩토링 | `refactor/<설명>` | `refactor/engine-state-model` |
| 핫픽스 | `hotfix/<설명>` | `hotfix/auth-token-expire` |

---

## 커밋 컨벤션

### Conventional Commits

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### 타입

| 타입 | 설명 |
|------|------|
| `feat` | 새로운 기능 |
| `fix` | 버그 수정 |
| `docs` | 문서 변경 |
| `style` | 코드 포맷팅 (기능 변경 없음) |
| `refactor` | 리팩토링 |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드, 설정 변경 |
| `perf` | 성능 개선 |

### 스코프 (선택)

| 스코프 | 설명 |
|--------|------|
| `engine` | 게임 엔진 |
| `api` | REST API |
| `ws` | WebSocket |
| `ui` | 프론트엔드 UI |
| `db` | 데이터베이스 |
| `infra` | 인프라/배포 |

### 예시

```bash
feat(engine): add hand evaluation logic
fix(ws): resolve reconnection state sync issue
docs(api): update authentication endpoint spec
refactor(ui): extract ActionPanel component
test(engine): add showdown scenario tests
```

---

## 코드 리뷰 프로세스

### PR 생성 규칙

1. `develop` 브랜치에서 feature 브랜치 생성
2. 작업 완료 후 PR 생성
3. PR 템플릿 작성 (아래 참조)
4. 최소 1명 리뷰어 승인 필요
5. CI 통과 필수
6. Squash merge 권장

### PR 템플릿

```markdown
## 변경 사항
- 

## 변경 유형
- [ ] 새 기능
- [ ] 버그 수정
- [ ] 리팩토링
- [ ] 문서 업데이트
- [ ] 테스트 추가

## 테스트
- [ ] 유닛 테스트 추가/수정
- [ ] 로컬 테스트 완료

## 체크리스트
- [ ] 코드 스타일 가이드 준수
- [ ] 문서 업데이트 (필요시)
- [ ] Breaking change 없음 (있으면 설명)

## 관련 이슈
- Closes #

## 스크린샷 (UI 변경 시)

```

---

## 코드 스타일

### Python (Backend)

```bash
# 린터/포맷터: Ruff
ruff check .
ruff format .

# 타입 체크: mypy
mypy app/
```

#### 규칙

- PEP 8 준수
- 라인 길이: 88자 (Black 기본값)
- 타입 힌트 필수
- Docstring: Google 스타일

```python
def process_action(
    table_id: str,
    user_id: str,
    action: ActionRequest,
) -> ActionResult:
    """액션을 처리하고 결과를 반환한다.
    
    Args:
        table_id: 테이블 식별자
        user_id: 유저 식별자
        action: 액션 요청 객체
        
    Returns:
        액션 처리 결과
        
    Raises:
        InvalidActionError: 유효하지 않은 액션
    """
    pass
```

### TypeScript (Frontend)

```bash
# 린터: ESLint
pnpm lint

# 포맷터: Prettier
pnpm format
```

#### 규칙

- ESLint + Prettier 설정 준수
- 라인 길이: 100자
- 세미콜론 사용
- 싱글 쿼트
- 타입 명시 (any 금지)

```typescript
interface ActionPanelProps {
  allowedActions: Action[];
  onAction: (action: Action) => void;
  disabled: boolean;
}

export function ActionPanel({
  allowedActions,
  onAction,
  disabled,
}: ActionPanelProps): JSX.Element {
  // ...
}
```

---

## 테스트 규칙

### 테스트 파일 위치

```
backend/
  tests/
    unit/           # 단위 테스트
    integration/    # 통합 테스트
    e2e/            # E2E 테스트

frontend/
  tests/
    components/     # 컴포넌트 테스트
    e2e/            # E2E 테스트
```

### 테스트 네이밍

```python
# Python
def test_fold_action_removes_player_from_hand():
    pass

def test_raise_below_minimum_raises_error():
    pass
```

```typescript
// TypeScript
describe('ActionPanel', () => {
  it('should disable buttons when not player turn', () => {
    // ...
  });
});
```

### 커버리지 목표

| 영역 | 목표 |
|------|------|
| 게임 엔진 | 90%+ |
| API 핸들러 | 80%+ |
| WebSocket | 70%+ |
| UI 컴포넌트 | 70%+ |

---

## CI/CD 파이프라인

### PR 체크 (CI)

```yaml
# .github/workflows/ci.yml
- 린트 체크 (Ruff, ESLint)
- 타입 체크 (mypy, tsc)
- 유닛 테스트
- 통합 테스트
- 커버리지 리포트
```

### 배포 (CD)

```yaml
# .github/workflows/deploy.yml
- develop → staging (자동)
- main → production (수동 승인)
```

---

## 로컬 개발 체크리스트

### 작업 시작 전

```bash
# 1. develop 브랜치 최신화
git checkout develop
git pull origin develop

# 2. feature 브랜치 생성
git checkout -b feature/my-feature

# 3. 의존성 업데이트 확인
cd backend && uv pip sync requirements.txt
cd frontend && pnpm install
```

### 커밋 전

```bash
# 1. 린트 실행
cd backend && ruff check . && ruff format .
cd frontend && pnpm lint && pnpm format

# 2. 테스트 실행
cd backend && pytest
cd frontend && pnpm test

# 3. 타입 체크
cd backend && mypy app/
cd frontend && pnpm type-check
```

### PR 전

```bash
# 1. develop 브랜치 변경사항 반영
git fetch origin
git rebase origin/develop

# 2. 전체 테스트 실행
cd backend && pytest --cov=app
cd frontend && pnpm test:all

# 3. 커밋 정리 (필요시)
git rebase -i HEAD~n
```

---

## 문서화 규칙

### 코드 문서화

- 공개 API는 반드시 docstring/JSDoc 작성
- 복잡한 로직은 인라인 주석 추가
- TODO/FIXME는 이슈 번호와 함께 작성

```python
# TODO(#123): 타임아웃 로직 추가 필요
```

### 프로젝트 문서

- 문서 파일명: `번호-kebab-case.md`
- ADR 파일명: `ADR-번호-제목.md`
- 변경 시 관련 문서 함께 업데이트

---

## 이슈 관리

### 이슈 라벨

| 라벨 | 설명 |
|------|------|
| `bug` | 버그 리포트 |
| `feature` | 새 기능 요청 |
| `docs` | 문서 관련 |
| `question` | 질문 |
| `good first issue` | 입문자용 |
| `priority:high` | 높은 우선순위 |
| `priority:low` | 낮은 우선순위 |

### 이슈 템플릿

#### 버그 리포트

```markdown
## 버그 설명

## 재현 단계
1. 
2. 
3. 

## 예상 동작

## 실제 동작

## 환경
- OS:
- Browser:
- Version:
```

#### 기능 요청

```markdown
## 기능 설명

## 사용 사례

## 제안 구현 방식 (선택)

## 대안 (선택)
```

---

## 관련 문서

- [01-setup-local.md](./01-setup-local.md) - 로컬 환경 셋업
- [02-env-vars.md](./02-env-vars.md) - 환경변수 설명
- [04-folder-structure.md](./04-folder-structure.md) - 폴더 구조
- [50-test-plan.md](./50-test-plan.md) - 테스트 플랜

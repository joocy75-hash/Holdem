# 스테이징 배포 가이드

> 스테이징 환경 배포 및 롤백 절차

---

## 1. 환경 구성

### 1.1 환경 분리

| 환경 | 용도 | URL |
|------|------|-----|
| Development | 로컬 개발 | localhost |
| Staging | 통합 테스트 | staging.example.com |
| Production | 운영 | app.example.com |

### 1.2 인프라 구성

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                         │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌─────────┐     ┌─────────┐     ┌─────────┐
        │ Backend │     │ Backend │     │ Backend │
        │   #1    │     │   #2    │     │   #3    │
        └─────────┘     └─────────┘     └─────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
        ┌─────────────────────────────────────────┐
        │              Redis Cluster              │
        └─────────────────────────────────────────┘
                              │
        ┌─────────────────────────────────────────┐
        │           PostgreSQL (Primary)          │
        │                   │                     │
        │           PostgreSQL (Replica)          │
        └─────────────────────────────────────────┘
```

---

## 2. 배포 파이프라인

### 2.1 CI/CD 흐름

```
[Push to develop]
       │
       ▼
[Run Tests] ──── Fail ──→ [Notify & Stop]
       │
       Pass
       │
       ▼
[Build Docker Image]
       │
       ▼
[Push to Registry]
       │
       ▼
[Deploy to Staging] ──── Auto
       │
       ▼
[Smoke Tests]
       │
       ▼
[Manual Approval] ──── Required for Production
       │
       ▼
[Deploy to Production]
```

### 2.2 GitHub Actions 워크플로

```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging

on:
  push:
    branches: [develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          cd backend && pytest
          cd ../frontend && pnpm test

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build and push Docker image
        run: |
          docker build -t $REGISTRY/backend:$SHA .
          docker push $REGISTRY/backend:$SHA

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: |
          kubectl set image deployment/backend \
            backend=$REGISTRY/backend:$SHA
```

---

## 3. 배포 절차

### 3.1 스테이징 배포

```bash
# 1. 최신 코드 확인
git checkout develop
git pull origin develop

# 2. 테스트 실행
cd backend && pytest
cd ../frontend && pnpm test

# 3. Docker 이미지 빌드
docker compose -f infra/docker/docker-compose.staging.yml build

# 4. 이미지 푸시
docker push $REGISTRY/backend:$TAG
docker push $REGISTRY/frontend:$TAG

# 5. 배포
kubectl apply -f infra/k8s/staging/

# 6. 배포 확인
kubectl rollout status deployment/backend -n staging
```

### 3.2 배포 전 체크리스트

```markdown
[ ] 모든 테스트 통과
[ ] 코드 리뷰 완료
[ ] DB 마이그레이션 준비 (필요시)
[ ] 환경변수 확인
[ ] 롤백 계획 확인
```

### 3.3 배포 후 체크리스트

```markdown
[ ] 헬스체크 통과
[ ] 스모크 테스트 통과
[ ] 로그 에러 없음
[ ] 메트릭 정상
[ ] 주요 기능 수동 테스트
```

---

## 4. 롤백 절차

### 4.1 즉시 롤백

```bash
# Kubernetes 롤백
kubectl rollout undo deployment/backend -n staging

# 또는 특정 버전으로 롤백
kubectl rollout undo deployment/backend --to-revision=2 -n staging
```

### 4.2 DB 마이그레이션 롤백

```bash
# Alembic 롤백
cd backend
alembic downgrade -1  # 한 단계 롤백
alembic downgrade <revision>  # 특정 버전으로 롤백
```

### 4.3 롤백 판단 기준

| 조건 | 액션 |
|------|------|
| 에러율 > 5% | 즉시 롤백 |
| 주요 기능 장애 | 즉시 롤백 |
| 성능 저하 > 50% | 롤백 검토 |
| 마이너 버그 | 핫픽스 배포 |

---

## 5. 환경변수 관리

### 5.1 시크릿 관리

```bash
# Kubernetes Secret 생성
kubectl create secret generic poker-secrets \
  --from-literal=JWT_SECRET_KEY=$JWT_SECRET \
  --from-literal=DB_PASSWORD=$DB_PASSWORD \
  -n staging
```

### 5.2 ConfigMap

```yaml
# infra/k8s/staging/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: poker-config
  namespace: staging
data:
  APP_ENV: staging
  LOG_LEVEL: INFO
  REDIS_URL: redis://redis:6379/0
```

---

## 6. 모니터링

### 6.1 배포 모니터링

```bash
# 파드 상태 확인
kubectl get pods -n staging -w

# 로그 확인
kubectl logs -f deployment/backend -n staging

# 메트릭 확인
curl http://backend:8000/metrics
```

### 6.2 알림 설정

| 이벤트 | 알림 채널 |
|--------|----------|
| 배포 시작 | Slack |
| 배포 완료 | Slack |
| 배포 실패 | Slack + PagerDuty |
| 롤백 실행 | Slack + PagerDuty |

---

## 7. 스모크 테스트

### 7.1 자동 스모크 테스트

```bash
#!/bin/bash
# scripts/smoke-test.sh

BASE_URL=${1:-"https://staging.example.com"}

# Health check
curl -f "$BASE_URL/health" || exit 1

# API check
curl -f "$BASE_URL/api/rooms" || exit 1

# WebSocket check
wscat -c "wss://staging.example.com/ws" -x '{"type":"PING"}' || exit 1

echo "Smoke tests passed!"
```

### 7.2 수동 테스트 체크리스트

```markdown
[ ] 로그인 가능
[ ] 로비 방 목록 표시
[ ] 방 생성 가능
[ ] 방 입장 가능
[ ] 게임 액션 동작
[ ] 재연결 동작
```

---

## 관련 문서

- [50-test-plan.md](./50-test-plan.md) - 테스트 플랜
- [51-observability.md](./51-observability.md) - 관측성 설계
- [02-env-vars.md](./02-env-vars.md) - 환경변수

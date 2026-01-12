# 라이선스 감사

> 상용 배포를 위한 라이선스 점검

---

## 1. 핵심 라이선스

### 1.1 PokerKit

| 항목 | 내용 |
|------|------|
| 라이선스 | MIT License |
| 저장소 | https://github.com/uoftcprg/pokerkit |
| 상용 사용 | ✅ 허용 |
| 소스 공개 | ❌ 불필요 |
| 고지 의무 | ✅ LICENSE 파일 포함 |

#### MIT License 전문

```
MIT License

Copyright (c) University of Toronto Computer Poker Research Group

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 2. 백엔드 의존성

### 2.1 주요 라이브러리

| 패키지 | 라이선스 | 상용 사용 |
|--------|---------|----------|
| FastAPI | MIT | ✅ |
| Uvicorn | BSD-3 | ✅ |
| SQLAlchemy | MIT | ✅ |
| Pydantic | MIT | ✅ |
| Redis (redis-py) | MIT | ✅ |
| asyncpg | Apache 2.0 | ✅ |
| Alembic | MIT | ✅ |
| structlog | MIT/Apache 2.0 | ✅ |
| pytest | MIT | ✅ |

### 2.2 라이선스 스캔 명령

```bash
# pip-licenses 설치
pip install pip-licenses

# 라이선스 목록 출력
pip-licenses --format=markdown

# CSV 출력
pip-licenses --format=csv > licenses.csv
```

---

## 3. 프론트엔드 의존성

### 3.1 주요 라이브러리

| 패키지 | 라이선스 | 상용 사용 |
|--------|---------|----------|
| Next.js | MIT | ✅ |
| React | MIT | ✅ |
| TypeScript | Apache 2.0 | ✅ |
| Tailwind CSS | MIT | ✅ |
| Zustand | MIT | ✅ |
| Socket.io-client | MIT | ✅ |

### 3.2 라이선스 스캔 명령

```bash
# license-checker 설치
pnpm add -D license-checker

# 라이선스 목록 출력
npx license-checker --summary

# JSON 출력
npx license-checker --json > licenses.json
```

---

## 4. 라이선스 유형별 요약

### 4.1 허용적 라이선스 (Permissive)

| 라이선스 | 고지 의무 | 소스 공개 | 상용 사용 |
|---------|----------|----------|----------|
| MIT | ✅ | ❌ | ✅ |
| BSD-2/3 | ✅ | ❌ | ✅ |
| Apache 2.0 | ✅ | ❌ | ✅ |
| ISC | ✅ | ❌ | ✅ |

### 4.2 주의 필요 라이선스

| 라이선스 | 주의사항 |
|---------|---------|
| GPL | 소스 공개 의무 - 사용 금지 |
| LGPL | 동적 링크만 허용 |
| AGPL | 네트워크 사용 시 소스 공개 - 사용 금지 |
| CC-BY-NC | 비상업적 사용만 - 사용 금지 |

---

## 5. 고지 의무 이행

### 5.1 NOTICE 파일

```
PokerKit Holdem Web Service
Copyright (c) 2026 [Your Company]

This product includes software developed by:

- PokerKit (https://github.com/uoftcprg/pokerkit)
  Copyright (c) University of Toronto Computer Poker Research Group
  Licensed under MIT License

- FastAPI (https://github.com/tiangolo/fastapi)
  Copyright (c) Sebastián Ramírez
  Licensed under MIT License

- Next.js (https://github.com/vercel/next.js)
  Copyright (c) Vercel, Inc.
  Licensed under MIT License

[전체 라이선스 목록은 LICENSES 폴더 참조]
```

### 5.2 라이선스 파일 구조

```
/
├── LICENSE              # 프로젝트 라이선스
├── NOTICE               # 서드파티 고지
└── LICENSES/            # 개별 라이선스 파일
    ├── MIT.txt
    ├── Apache-2.0.txt
    └── BSD-3-Clause.txt
```

---

## 6. 배포 체크리스트

### 6.1 배포 전 확인

```markdown
[x] 모든 의존성 라이선스 스캔 완료 (2026-01-12)
[x] GPL/AGPL 라이선스 의존성 없음 확인
[x] NOTICE 파일 작성
[x] LICENSE 파일 포함
[x] LICENSES/ 폴더 생성 (MIT, Apache-2.0, BSD-3-Clause, ISC, OFL-1.1)
[ ] 프론트엔드 에셋 라이선스 확인 (카드 이미지, 사운드)
```

### 6.2 라이선스 스캔 결과 (2026-01-12)

#### 백엔드 의존성 (모두 상용 사용 가능)
| 패키지 | 라이선스 |
|--------|---------|
| FastAPI | MIT |
| Uvicorn | BSD-3-Clause |
| SQLAlchemy | MIT |
| Pydantic | MIT |
| Redis | MIT |
| asyncpg | Apache-2.0 |
| Alembic | MIT |
| structlog | MIT |
| orjson | Apache-2.0 OR MIT |
| httpx | BSD-3-Clause |
| tenacity | Apache-2.0 |
| Celery | BSD |
| msgpack | Apache-2.0 |
| slowapi | MIT |
| sentry-sdk | MIT |
| pokerkit | MIT |

#### 프론트엔드 의존성 (모두 상용 사용 가능)
| 패키지 | 라이선스 |
|--------|---------|
| React | MIT |
| Vite | MIT |
| Tailwind CSS | MIT |
| Zustand | MIT |
| Lucide React | ISC |
| Framer Motion | MIT |
| React Query | MIT |

### 6.3 정기 점검

| 주기 | 작업 |
|------|------|
| 의존성 추가 시 | 라이선스 확인 |
| 월간 | 전체 스캔 |
| 릴리즈 전 | 최종 확인 |

---

## 관련 문서

- [61-third-party-assets.md](./61-third-party-assets.md) - 서드파티 에셋
- [ADR-0001-pokerkit-core.md](./ADR/ADR-0001-pokerkit-core.md) - PokerKit 채택

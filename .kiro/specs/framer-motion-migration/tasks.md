# Implementation Plan: Framer Motion Migration + 5대 몰입감 기능

## Overview

Framer Motion 라이브러리를 도입하고 홀덤 게임의 5가지 핵심 몰입감 기능을 구현한다. 각 단계는 독립적으로 검증 가능하며, 단계별 완료 체크를 통해 작업 진행 상황을 추적한다.

## 작업 지침

### 필수 준수 사항
1. **단계별 완료 체크**: 각 태스크 완료 시 반드시 체크박스 업데이트
2. **검증 테스트**: 각 단계 완료 후 빌드 및 기능 테스트 필수
3. **서브에이전트 활용**: 복잡한 작업은 전문 서브에이전트 사용
4. **롤백 준비**: 문제 발생 시 이전 상태로 복구 가능하도록 백업
5. **한 번에 하나씩**: 한 Phase 완료 후 다음 Phase 진행

### 작업 중단 시 복구 절차
1. 현재 완료된 태스크 확인 (체크박스 상태)
2. 마지막 완료 태스크 다음부터 재개
3. 미완료 태스크의 부분 작업 확인 후 정리

---

## Phase 구조 요약

| Phase | 내용 | 예상 시간 | 우선순위 |
|-------|------|----------|----------|
| Phase 1 | 환경 설정 및 라이브러리 설치 | 15분 | 🔴 필수 |
| Phase 2 | 공통 애니메이션 유틸리티 | 30분 | 🔴 필수 |
| Phase 3 | 카드 쪼기 연출 (Squeeze) | 60분 | 🔴 필수 |
| Phase 4 | 베팅 칩 이동 + 숫자 상승 | 45분 | 🟡 중요 |
| Phase 5 | 팟 이동 + 승자 하이라이트 | 60분 | 🟡 중요 |
| Phase 6 | 폴드 시 Show/Muck 선택 | 45분 | 🟢 선택 |
| Phase 7 | ActionButtons + BuyInModal | 30분 | 🟢 선택 |
| Phase 8 | 최종 검증 및 정리 | 30분 | 🔴 필수 |

---

## Tasks

### Phase 1: 환경 설정 및 라이브러리 설치

- [x] 1. Framer Motion 설치 및 환경 구성
  - [x] 1.1 framer-motion 패키지 설치
    - `cd frontend && npm install framer-motion` 실행
    - package.json에 의존성 추가 확인
    - _Requirements: 1.1_
  
  - [x] 1.2 빌드 검증
    - `npm run build` 실행하여 컴파일 오류 없음 확인
    - _Requirements: 1.2_
  
  - [x] 1.3 개발 서버 테스트
    - `npm run dev` 실행하여 정상 동작 확인
    - 기존 페이지 접속하여 회귀 없음 확인
    - _Requirements: 1.3, 1.4_

- [x] 2. ✅ Checkpoint - Phase 1 완료 확인
  - 빌드 성공 여부 확인
  - 개발 서버 정상 동작 확인
  - 문제 발생 시 사용자에게 보고

---

### Phase 2: 공통 애니메이션 유틸리티 생성

- [x] 3. 애니메이션 유틸리티 파일 생성
  - [x] 3.1 디렉토리 구조 생성
    - `frontend/src/lib/animations/` 디렉토리 생성
    - _Requirements: 9.1-9.8_
  
  - [x] 3.2 variants.ts 파일 생성
    - fadeIn, fadeOut, scaleIn, slideUp 등 공통 variants 정의
    - buttonHover, buttonTap 등 인터랙션 variants 정의
    - staggeredChildren preset 정의
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.6_
  
  - [x] 3.3 transitions.ts 파일 생성
    - springTransition (stiffness: 300, damping: 25)
    - smoothTransition (duration: 0.3, ease: easeOut)
    - snapBackSpring (stiffness: 500, damping: 30) - "찰싹" 효과
    - flipSpring (stiffness: 200, damping: 20) - "휙" 효과
    - _Requirements: 9.5_
  
  - [x] 3.4 paths.ts 파일 생성
    - curvedPath 유틸리티 (베지어 곡선 칩 이동용)
    - calculateArcPath 함수 (시작점, 끝점, 곡률)
    - _Requirements: 9.7_
  
  - [x] 3.5 index.ts 통합 export 파일 생성
    - 모든 유틸리티 re-export
    - _Requirements: 9.8_

- [x] 4. ✅ Checkpoint - Phase 2 완료 확인
  - TypeScript 타입 오류 없음 확인
  - import 경로 정상 동작 확인
  - 문제 발생 시 사용자에게 보고

---

### Phase 3: 카드 쪼기 연출 (The Squeeze/Peek) 🎯 핵심 기능 1

- [x] 5. CardSqueeze 컴포넌트 고급 리팩토링
  - [x] 5.1 기존 파일 백업
    - `CardSqueeze.tsx` → `CardSqueeze.backup.tsx` 복사
    - _Requirements: 2.1-2.7_
  
  - [x] 5.2 3D 카드 휘어짐 효과 구현
    - motion.div로 카드 래핑
    - rotateX transform으로 카드 상단 고정, 하단 들어올림
    - perspective 설정으로 원근감 부여
    - _Requirements: 2.1_
  
  - [x] 5.3 동적 그림자 효과 구현
    - 드래그 거리에 따라 그림자 blur 증가
    - 그림자 offset 및 opacity 동적 조절
    - _Requirements: 2.2_
  
  - [x] 5.4 카드 표면 광택 효과 구현
    - 드래그 각도에 따른 그라데이션 오버레이
    - 빛 반사 시뮬레이션
    - _Requirements: 2.3_
  
  - [x] 5.5 "찰싹" Snap-back 애니메이션 구현
    - snapBackSpring transition 적용
    - 임계값 미달 시 빠른 복귀
    - _Requirements: 2.4_
  
  - [x] 5.6 "휙" 카드 뒤집기 애니메이션 구현
    - flipSpring transition 적용
    - 임계값 초과 시 화려한 플립
    - _Requirements: 2.5_
  
  - [x] 5.7 UI 잠금 및 테스트 속성 유지
    - 드래그 중 다른 UI 비활성화
    - data-testid, data-revealed 속성 유지
    - _Requirements: 2.6, 2.7_

- [x] 6. CardSqueeze 검증 테스트
  - [x] 6.1 수동 기능 테스트
    - 브라우저에서 카드 드래그 테스트
    - 3D 휘어짐, 그림자, 광택 효과 확인
    - 찰싹/휙 물리 효과 확인
  
  - [x] 6.2 E2E 테스트 실행
    - `npm run test:e2e -- --grep "card-squeeze"` 실행
    - 모든 테스트 통과 확인
    - _Requirements: 10.1_

- [x] 7. ✅ Checkpoint - Phase 3 완료 확인
  - CardSqueeze 3D 효과 정상 동작 확인
  - E2E 테스트 통과 확인
  - 문제 발생 시 백업 파일로 롤백 가능

---

### Phase 4: 베팅 칩 이동 + 숫자 상승 🎯 핵심 기능 2

- [x] 8. ChipAnimation 컴포넌트 생성
  - [x] 8.1 컴포넌트 파일 생성
    - `frontend/src/components/table/ChipAnimation.tsx` 생성
    - _Requirements: 3.1-3.6_
  
  - [x] 8.2 Staggered 칩 이동 구현
    - 여러 칩 아이콘 생성 (금액에 따라 1-5개)
    - 0.05초 간격 staggerChildren 적용
    - _Requirements: 3.1_
  
  - [x] 8.3 곡선 경로 이동 구현
    - curvedPath 유틸리티 사용
    - 플레이어 위치 → 중앙 팟 베지어 곡선
    - _Requirements: 3.2_
  
  - [x] 8.4 Floating Number 구현
    - 첫 칩 도착 시 금액 팝업 (+10,000)
    - 위로 떠오르며 fade out
    - _Requirements: 3.3, 3.4_
  
  - [x] 8.5 효과음 동기화 포인트 설정
    - onAnimationComplete 콜백으로 사운드 트리거 시점 제공
    - _Requirements: 3.5_

- [x] 9. BettingChips 컴포넌트 통합
  - [x] 9.1 기존 BettingChips.tsx 백업
    - `BettingChips.tsx` → `BettingChips.backup.tsx` 복사
  
  - [x] 9.2 ChipAnimation 통합
    - 베팅 액션 시 ChipAnimation 트리거
    - 기존 정적 칩 표시와 애니메이션 분리

- [x] 10. 베팅 애니메이션 검증 테스트
  - [x] 10.1 수동 기능 테스트
    - 베팅 시 칩 곡선 이동 확인
    - 숫자 팝업 및 fade out 확인
  
  - [x] 10.2 E2E 테스트 실행
    - `npm run test:e2e -- --grep "betting"` 실행
    - _Requirements: 10.2_

- [x] 11. ✅ Checkpoint - Phase 4 완료 확인
  - 칩 이동 애니메이션 정상 동작 확인
  - 숫자 상승 효과 확인
  - 문제 발생 시 백업 파일로 롤백 가능

---

### Phase 5: 팟 이동 + 승자 하이라이트 🎯 핵심 기능 3, 4

- [x] 12. PotCollection 컴포넌트 생성
  - [x] 12.1 컴포넌트 파일 생성
    - `frontend/src/components/table/PotCollection.tsx` 생성
    - _Requirements: 4.1-4.6_
  
  - [x] 12.2 칩 수거 애니메이션 구현
    - 흩어진 칩들 → 중앙 집결
    - staggered 수거 (바깥쪽부터)
    - _Requirements: 4.1_
  
  - [x] 12.3 승자 방향 이동 구현
    - Ease-In 가속 곡선 적용
    - 처음 느리게 → 끝에 빠르게
    - _Requirements: 4.2, 4.3_
  
  - [x] 12.4 승자 아바타 Pulse 효과 구현
    - 칩 도착 시 scale 1.0 → 1.1 → 1.0
    - _Requirements: 4.4_
  
  - [x] 12.5 Split Pot 처리 구현
    - 여러 승자 시 칩 분할 애니메이션
    - _Requirements: 4.5_

- [x] 13. WinnerHighlight 컴포넌트 개선
  - [x] 13.1 기존 ShowdownHighlight.tsx 백업
    - `ShowdownHighlight.tsx` → `ShowdownHighlight.backup.tsx` 복사
    - _Requirements: 5.1-5.6_
  
  - [x] 13.2 배경 흑백 처리 구현
    - 비승자 영역 grayscale filter 적용
    - 어두움(darken) 오버레이 추가
    - _Requirements: 5.1, 5.2_
  
  - [x] 13.3 승자 강조 효과 구현
    - 승자 프로필 brightness 증가
    - 금색 glow border 효과
    - _Requirements: 5.3, 5.4_
  
  - [x] 13.4 복원 애니메이션 구현
    - 3초 후 점진적 정상 색상 복원
    - _Requirements: 5.5_

- [x] 14. 승자 연출 검증 테스트
  - [x] 14.1 수동 기능 테스트
    - 팟 수거 → 승자 이동 시퀀스 확인
    - 흑백 처리 및 하이라이트 확인
  
  - [x] 14.2 E2E 테스트 실행
    - `npm run test:e2e -- --grep "showdown"` 실행
    - _Requirements: 10.4_

- [x] 15. ✅ Checkpoint - Phase 5 완료 확인
  - 팟 이동 애니메이션 정상 동작 확인
  - 승자 하이라이트 효과 확인
  - 문제 발생 시 백업 파일로 롤백 가능

---

### Phase 6: 폴드 시 Show/Muck 선택 🎯 핵심 기능 5

- [x] 16. FoldOptions 컴포넌트 생성
  - [x] 16.1 컴포넌트 파일 생성
    - `frontend/src/components/table/FoldOptions.tsx` 생성
    - _Requirements: 6.1-6.8_
  
  - [x] 16.2 선택 버튼 오버레이 구현
    - 폴드 시 카드 위에 투명 버튼 표시
    - "카드 1 오픈", "카드 2 오픈", "모두 오픈", "그냥 버리기"
    - _Requirements: 6.1, 6.2_
  
  - [x] 16.3 Muck 애니메이션 구현
    - 카드 뒷면 상태로 딜러 방향 슬라이드
    - 이동하며 fade out
    - _Requirements: 6.3_
  
  - [x] 16.4 Show 애니메이션 구현
    - 선택 카드 화려한 플립
    - 1-2초 홀드 후 딜러로 이동
    - _Requirements: 6.4_
  
  - [x] 16.5 카드 공개 브로드캐스트 연동
    - WebSocket으로 공개 카드 정보 전송
    - _Requirements: 6.5_
  
  - [x] 16.6 타이머 UI 구현
    - 3초 카운트다운 표시
    - 만료 시 자동 Muck
    - _Requirements: 6.6, 6.7_

- [x] 17. ActionButtons 폴드 연동
  - [x] 17.1 폴드 버튼 클릭 시 FoldOptions 표시
    - 기존 즉시 폴드 → FoldOptions 모달로 변경
  
  - [x] 17.2 테스트 속성 유지
    - data-testid 속성 유지
    - _Requirements: 6.8_

- [x] 18. 폴드 옵션 검증 테스트
  - [x] 18.1 수동 기능 테스트
    - 폴드 → 선택 UI 표시 확인
    - Show/Muck 각 애니메이션 확인
    - 타이머 만료 시 자동 Muck 확인
  
  - [x] 18.2 E2E 테스트 실행
    - 관련 E2E 테스트 실행

- [x] 19. ✅ Checkpoint - Phase 6 완료 확인
  - FoldOptions 기능 정상 동작 확인
  - 타이머 및 자동 Muck 확인
  - 문제 발생 시 백업 파일로 롤백 가능

---

### Phase 7: ActionButtons + BuyInModal 개선

- [x] 20. ActionButtons 컴포넌트 개선
  - [x] 20.1 기존 파일 백업
    - `ActionButtons.tsx` → `ActionButtons.backup.tsx` 복사
    - _Requirements: 7.1-7.6_
  
  - [x] 20.2 버튼 호버/탭 애니메이션 적용
    - motion.button으로 래핑
    - whileHover={{ scale: 1.05 }} 적용
    - whileTap={{ scale: 0.95 }} 적용
    - _Requirements: 7.1, 7.2_
  
  - [x] 20.3 버튼 그룹 등장 애니메이션 적용
    - AnimatePresence로 래핑
    - staggerChildren으로 순차 등장
    - _Requirements: 7.3, 7.4_

- [x] 21. BuyInModal 컴포넌트 개선
  - [x] 21.1 기존 파일 백업
    - `BuyInModal.tsx` → `BuyInModal.backup.tsx` 복사
    - _Requirements: 8.1-8.6_
  
  - [x] 21.2 모달 등장/퇴장 애니메이션 적용
    - AnimatePresence + slideUp variant
    - spring transition 적용
    - _Requirements: 8.1, 8.2, 8.5_
  
  - [x] 21.3 백드롭 애니메이션 적용
    - fadeIn/fadeOut + backdrop-blur
    - _Requirements: 8.3, 8.4_

- [x] 22. UI 컴포넌트 검증 테스트
  - [x] 22.1 수동 기능 테스트
    - 버튼 호버/클릭 피드백 확인
    - 모달 열기/닫기 애니메이션 확인
  
  - [x] 22.2 E2E 테스트 실행
    - `npm run test:e2e -- --grep "betting-buttons"` 실행
    - _Requirements: 10.2, 10.3_

- [x] 23. ✅ Checkpoint - Phase 7 완료 확인
  - ActionButtons 애니메이션 정상 동작 확인
  - BuyInModal 애니메이션 정상 동작 확인
  - 문제 발생 시 백업 파일로 롤백 가능

---

### Phase 8: 최종 검증 및 정리

- [x] 24. 전체 E2E 테스트 실행
  - [x] 24.1 전체 테스트 스위트 실행
    - `npm run test:e2e` 실행
    - 모든 테스트 통과 확인
    - _Requirements: 10.1-10.6_
  
  - [x] 24.2 회귀 테스트
    - 기존 기능 정상 동작 확인
    - 애니메이션 성능 확인 (60fps 유지)

- [x] 25. 코드 정리 및 문서화
  - [x] 25.1 백업 파일 정리
    - 모든 .backup.tsx 파일 삭제
    - 불필요한 주석 제거
  
  - [x] 25.2 코드 품질 검증
    - `npm run lint` 실행
    - TypeScript 오류 없음 확인
  
  - [x] 25.3 번들 사이즈 확인
    - framer-motion 추가 후 번들 크기 확인
    - 목표: +50KB 이하 (gzipped)

- [x] 26. ✅ Final Checkpoint - 마이그레이션 완료
  - 모든 E2E 테스트 통과 확인
  - 5가지 핵심 몰입감 기능 동작 확인
  - 빌드 성공 확인
  - 개발 서버 정상 동작 확인
  - 사용자에게 최종 보고

---

## Notes

### 우선순위 가이드
- 🔴 **필수**: Phase 1, 2, 3, 8 - 기본 인프라 및 핵심 기능
- 🟡 **중요**: Phase 4, 5 - 몰입감 향상 기능
- 🟢 **선택**: Phase 6, 7 - 추가 개선 기능

### 롤백 전략
- 각 Phase 시작 전 `.backup.tsx` 파일 생성
- 문제 발생 시 해당 Phase의 백업 파일로 즉시 복구
- Phase 완료 후에만 다음 Phase 진행

### 서브에이전트 활용 권장 태스크
- 5.2-5.6: 3D 카드 효과 구현 (복잡한 transform 계산)
- 8.2-8.4: 칩 애니메이션 구현 (베지어 곡선 경로)
- 12.2-12.5: 팟 수거 시퀀스 (복잡한 타이밍 조율)

### 검증 체크리스트
각 Checkpoint에서 확인할 사항:
1. ✅ 빌드 성공
2. ✅ 개발 서버 정상 동작
3. ✅ 해당 기능 수동 테스트 통과
4. ✅ 관련 E2E 테스트 통과
5. ✅ 콘솔 에러 없음

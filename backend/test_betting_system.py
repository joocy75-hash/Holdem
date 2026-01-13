#!/usr/bin/env python3
"""배팅 시스템 테스트 - 스택/팟/승자지급 검증"""

import asyncio
import websockets
import json
import httpx
from datetime import datetime

# 테스트 설정
BASE_URL = 'http://localhost:8000'
WS_URL = 'ws://localhost:8000/ws'

class BettingSystemTester:
    def __init__(self):
        self.ws = None
        self.token = None
        self.table_id = None
        self.messages = []

    async def setup(self):
        """테스트 준비 - 로그인 및 테이블 찾기"""
        async with httpx.AsyncClient() as client:
            # 새 유저 생성
            ts = int(datetime.now().timestamp())
            resp = await client.post(f'{BASE_URL}/api/v1/auth/register', json={
                'email': f'bettest{ts}@test.com',
                'password': 'test123456',
                'nickname': f'BetTester{ts}'
            })
            data = resp.json()
            self.token = data['tokens']['accessToken']
            self.user_id = data['user']['id']
            self.initial_balance = data['user']['balance']
            print(f"✓ 유저 생성: balance={self.initial_balance}")

            # 테이블 찾기
            resp = await client.get(f'{BASE_URL}/api/v1/rooms',
                headers={'Authorization': f'Bearer {self.token}'})
            rooms = resp.json()['rooms']
            if rooms:
                self.table_id = rooms[0]['id']
                print(f"✓ 테이블: {self.table_id}")

    async def connect(self):
        """WebSocket 연결 및 인증"""
        self.ws = await websockets.connect(WS_URL)
        # AUTH 메시지 전송
        auth_msg = json.dumps({'type': 'AUTH', 'payload': {'token': self.token}})
        await self.ws.send(auth_msg)
        # AUTH 응답 대기
        for _ in range(5):
            msg = await self.recv(timeout=3)
            if msg:
                msg_type = msg.get('type')
                if msg_type in ('AUTH_SUCCESS', 'CONNECTION_STATE'):
                    print("✓ WebSocket 연결 및 인증 완료")
                    # PING 태스크 시작
                    self.ping_task = asyncio.create_task(self._ping_loop())
                    return
                elif msg_type == 'ERROR':
                    print(f"✗ 인증 실패: {msg}")
                    return
        print("✓ WebSocket 연결됨")

    async def _ping_loop(self):
        """주기적으로 PING 전송"""
        try:
            while True:
                await asyncio.sleep(5)  # 5초마다 PING
                ping_msg = json.dumps({'type': 'PING', 'payload': {}})
                await self.ws.send(ping_msg)
        except Exception:
            pass  # 연결 종료 시 무시

    async def send(self, msg_type, payload):
        """메시지 전송"""
        msg = json.dumps({'type': msg_type, 'payload': payload})
        await self.ws.send(msg)
        print(f"→ {msg_type}")

    async def recv(self, timeout=5):
        """메시지 수신"""
        try:
            while True:
                msg = await asyncio.wait_for(self.ws.recv(), timeout)
                data = json.loads(msg)
                # PING 메시지 자동 응답
                if data.get('type') == 'PING':
                    pong = json.dumps({'type': 'PONG', 'payload': {}})
                    await self.ws.send(pong)
                    continue
                self.messages.append(data)
                return data
        except asyncio.TimeoutError:
            return None
        except websockets.exceptions.ConnectionClosed:
            raise

    async def recv_until(self, event_type, timeout=30):
        """특정 이벤트까지 수신"""
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            try:
                msg = await self.recv(timeout=2)
                if msg and msg.get('type') == event_type:
                    return msg
            except Exception:
                return None
        return None

    async def reset_table(self):
        """테이블 리셋 - 모든 플레이어/봇 제거 및 게임 상태 초기화"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f'{BASE_URL}/api/v1/rooms/{self.table_id}/dev/reset',
                headers={'Authorization': f'Bearer {self.token}'}
            )
            result = resp.json()
            print(f"✓ 테이블 리셋: {result.get('message', result)}")

    async def test_betting_flow(self):
        """배팅 흐름 테스트"""
        print("\n" + "="*60)
        print(" 배팅 시스템 테스트")
        print("="*60)

        await self.setup()
        await self.connect()
        await self.reset_table()

        # 테이블 구독
        await self.send('SUBSCRIBE_TABLE', {'tableId': self.table_id})
        await asyncio.sleep(1)

        # 유저 착석
        print("\n[0] 유저 착석")
        await self.send('SEAT_REQUEST', {
            'tableId': self.table_id,
            'buyInAmount': 1000
        })
        await asyncio.sleep(1)

        # 응답 수신
        for _ in range(3):
            msg = await self.recv(timeout=2)
            if msg:
                if msg.get('type') == 'SEAT_RESULT':
                    print(f"  착석 결과: {msg.get('payload', {})}")
                    break

        # 봇 2개 추가
        print("\n[1] 봇 추가")
        for i in range(2):
            await self.send('ADD_BOT_REQUEST', {
                'tableId': self.table_id,
                'buyIn': 1000
            })
            await asyncio.sleep(1)
            # 봇 추가 결과 수신
            for _ in range(3):
                msg = await self.recv(timeout=2)
                if msg and msg.get('type') == 'ADD_BOT_RESULT':
                    payload = msg.get('payload', {})
                    if payload.get('success'):
                        print(f"  봇 추가 성공: {payload.get('nickname')}")
                    else:
                        print(f"  봇 추가 실패: {payload.get('errorMessage')}")
                    break

        # 테이블 상태 확인
        await self.send('SUBSCRIBE_TABLE', {'tableId': self.table_id})
        snapshot = await self.recv_until('TABLE_SNAPSHOT', timeout=5)

        if snapshot:
            seats = snapshot['payload'].get('seats', [])
            print(f"\n[2] 테이블 상태 (게임 시작 전)")
            total_stack = 0
            for s in seats:
                if s.get('player'):
                    stack = s.get('stack', 0)
                    total_stack += stack
                    print(f"  좌석 {s['position']}: {s['player']['nickname']} - 스택 {stack}")
            print(f"  총 스택: {total_stack}")

        # 게임 시작
        print("\n[3] 게임 시작")
        await self.send('START_GAME', {'tableId': self.table_id})

        # HAND_STARTED 대기 (서버 이벤트 타입 수정)
        hand_start = await self.recv_until('HAND_STARTED', timeout=10)
        if hand_start:
            print(f"  핸드 #{hand_start['payload'].get('handNumber', '?')} 시작")
            print(f"  딜러: 좌석 {hand_start['payload'].get('dealer', '?')}")

        # 게임 진행 모니터링
        print("\n[4] 게임 진행 모니터링")

        pot_history = []
        stack_changes = {}

        for _ in range(60):  # 최대 60초
            try:
                msg = await self.recv(timeout=2)
                if not msg:
                    continue
            except Exception as e:
                print(f"  연결 종료: {e}")
                break

            msg_type = msg.get('type')
            payload = msg.get('payload', {})

            if msg_type == 'TABLE_STATE_UPDATE':
                # 스택/팟 변화 추적
                if 'changes' in payload:
                    changes = payload['changes']
                    if 'seats' in changes:
                        for seat in changes['seats']:
                            pos = seat.get('position')
                            stack = seat.get('stack')
                            bet = seat.get('betAmount', 0)
                            if pos is not None:
                                prev = stack_changes.get(pos, {'stack': 1000, 'bet': 0})
                                if stack != prev['stack'] or bet != prev['bet']:
                                    print(f"  좌석 {pos}: 스택 {prev['stack']}→{stack}, 베팅 {bet}")
                                    stack_changes[pos] = {'stack': stack, 'bet': bet}
                    if 'pot' in changes:
                        pot = changes['pot']
                        if not pot_history or pot != pot_history[-1]:
                            pot_history.append(pot)
                            print(f"  팟: {pot}")

            elif msg_type == 'TURN_PROMPT':
                # 유저 턴 - 자동 액션 (체크 우선, 아니면 콜 또는 폴드)
                position = payload.get('position')
                allowed = payload.get('allowedActions', [])
                action_types = [a.get('type') for a in allowed]
                print(f"  [유저 턴] 좌석 {position}, 가능: {action_types}")

                # 체크 가능하면 체크, 아니면 콜, 아니면 폴드
                if 'check' in action_types:
                    await self.send('ACTION_REQUEST', {
                        'tableId': self.table_id,
                        'actionType': 'check',
                        'amount': 0
                    })
                    print(f"  → 체크")
                elif 'call' in action_types:
                    call_amount = next((a.get('amount', 0) for a in allowed if a.get('type') == 'call'), 0)
                    await self.send('ACTION_REQUEST', {
                        'tableId': self.table_id,
                        'actionType': 'call',
                        'amount': call_amount
                    })
                    print(f"  → 콜 {call_amount}")
                elif 'fold' in action_types:
                    await self.send('ACTION_REQUEST', {
                        'tableId': self.table_id,
                        'actionType': 'fold',
                        'amount': 0
                    })
                    print(f"  → 폴드")

            elif msg_type == 'ACTION_RESULT':
                action = payload.get('action', {})
                if action:
                    print(f"  액션: {action.get('type')} {action.get('amount', '')} (좌석 {action.get('position')})")

            elif msg_type == 'COMMUNITY_CARDS':
                cards = payload.get('cards', [])
                phase = payload.get('phase', '')
                print(f"  커뮤니티 카드 ({phase}): {cards}")

            elif msg_type == 'HAND_RESULT':
                print("\n[5] 핸드 결과")
                winners = payload.get('winners', [])
                pot = payload.get('pot', 0)
                showdown = payload.get('showdown', [])

                print(f"  최종 팟: {pot}")
                print(f"  승자:")
                for w in winners:
                    print(f"    좌석 {w['seat']}: +{w['amount']}")

                if showdown:
                    print(f"  쇼다운:")
                    for s in showdown:
                        print(f"    좌석 {s['seat']}: {s['holeCards']}")

                # 결과 분석
                print("\n[6] 결과 분석")

                # 승리액 검증
                total_won = sum(w['amount'] for w in winners)
                print(f"  총 승리액: {total_won}")
                print(f"  팟과 일치?: {total_won == pot or '⚠️ 불일치!'}")

                # 잠시 대기 후 최종 스택 확인
                await asyncio.sleep(2)
                await self.send('SUBSCRIBE_TABLE', {'tableId': self.table_id})
                final_snapshot = await self.recv_until('TABLE_SNAPSHOT', timeout=5)

                if final_snapshot:
                    seats = final_snapshot['payload'].get('seats', [])
                    print("\n[7] 최종 스택 상태")
                    total_final = 0
                    for s in seats:
                        if s.get('player'):
                            stack = s.get('stack', 0)
                            total_final += stack
                            print(f"  좌석 {s['position']}: 스택 {stack}")
                    print(f"  총 스택: {total_final}")
                    print(f"  보존 여부: {'✓ 정확' if total_final == total_stack else '⚠️ 불일치!'}")

                break

        await self.ws.close()
        print("\n테스트 완료")

async def main():
    tester = BettingSystemTester()
    await tester.test_betting_flow()

if __name__ == '__main__':
    asyncio.run(main())

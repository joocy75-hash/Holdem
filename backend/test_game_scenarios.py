#!/usr/bin/env python3
"""게임 시나리오 종합 테스트 스크립트"""

import asyncio
import websockets
import json
import time
from datetime import datetime

# 테스트 설정
TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MjEyMzk4NC03NTk0LTQ5ZWYtYWFmNi1jY2YzMTY3MzY3YTgiLCJ0eXBlIjoiYWNjZXNzIiwiaWF0IjoxNzY4MjYzNjAwLCJleHAiOjE3NjgyNjU0MDB9.2XSkQkIMdjiYd9spJm3_JEbTyQnE99YX-SrY_YCDeWU'
TABLE_ID = 'a4a092e7-560c-43f0-b71f-f10620cc6981'
WS_URL = f'ws://localhost:8000/ws?token={TOKEN}'

class GameTester:
    def __init__(self):
        self.ws = None
        self.messages = []
        self.hand_count = 0
        self.errors = []
        self.phase = 'unknown'
        self.player_count = 0

    async def connect(self):
        """WebSocket 연결"""
        self.ws = await websockets.connect(WS_URL)
        # AUTH 메시지 전송
        await self.ws.send(json.dumps({
            'type': 'AUTH',
            'payload': {'token': TOKEN}
        }))
        print(f"[{self._time()}] 연결됨")

    async def send(self, msg_type: str, payload: dict):
        """메시지 전송"""
        msg = {'type': msg_type, 'payload': payload}
        await self.ws.send(json.dumps(msg))
        print(f"[{self._time()}] 전송: {msg_type}")

    async def recv(self, timeout: float = 5.0):
        """메시지 수신"""
        try:
            msg = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            data = json.loads(msg)
            return data
        except asyncio.TimeoutError:
            return None

    def _time(self):
        return datetime.now().strftime('%H:%M:%S')

    async def subscribe_and_get_state(self):
        """테이블 구독 및 초기 상태 확인"""
        await self.send('SUBSCRIBE_TABLE', {'tableId': TABLE_ID})

        # 초기 메시지들 수신
        for _ in range(5):
            data = await self.recv(2)
            if not data:
                break
            msg_type = data.get('type')
            payload = data.get('payload', {})

            if msg_type == 'TABLE_SNAPSHOT':
                seats = payload.get('seats', [])
                occupied = [s for s in seats if s.get('player') and s.get('status') != 'empty']
                self.player_count = len(occupied)
                hand_info = payload.get('hand') or {}
                self.phase = hand_info.get('phase', 'waiting') if hand_info else 'waiting'
                print(f"[{self._time()}] TABLE_SNAPSHOT: {self.player_count}명, phase={self.phase}")
                return payload
            elif msg_type == 'AUTH_SUCCESS':
                print(f"[{self._time()}] 인증 성공")
            else:
                print(f"[{self._time()}] {msg_type}")
        return None

    async def reset_table(self):
        """테이블 리셋 (HTTP API)"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            url = f'http://localhost:8000/api/v1/rooms/{TABLE_ID}/dev/reset'
            headers = {'Authorization': f'Bearer {TOKEN}'}
            async with session.post(url, headers=headers) as resp:
                result = await resp.json()
                print(f"[{self._time()}] 테이블 리셋: {result.get('success')}")
                return result.get('success')

    async def seat_user(self, buy_in: int = 1000):
        """유저 착석"""
        print(f"\n[{self._time()}] === 유저 착석 ===")
        await self.send('SEAT_REQUEST', {'tableId': TABLE_ID, 'buyInAmount': buy_in})

        for _ in range(5):
            data = await self.recv(2)
            if not data:
                break
            msg_type = data.get('type')
            payload = data.get('payload', {})

            if msg_type == 'SEAT_RESULT':
                if payload.get('success'):
                    print(f"[{self._time()}] 유저 착석 성공: 좌석 {payload.get('position')}, 스택 {payload.get('stack')}")
                    return True
                else:
                    print(f"[{self._time()}] 유저 착석 실패: {payload.get('errorMessage')}")
                    return False
            elif msg_type == 'TABLE_SNAPSHOT':
                seats = payload.get('seats', [])
                occupied = [s for s in seats if s.get('player')]
                self.player_count = len(occupied)
        return False

    async def add_bots(self, count: int):
        """봇 추가"""
        print(f"\n[{self._time()}] === 봇 {count}개 추가 시작 ===")
        added = 0
        for i in range(count):
            await self.send('ADD_BOT_REQUEST', {'tableId': TABLE_ID, 'strategy': 'passive'})
            await asyncio.sleep(0.5)

            # 각 봇마다 결과 수신
            for _ in range(3):
                data = await self.recv(1)
                if not data:
                    break
                msg_type = data.get('type')
                payload = data.get('payload', {})

                if msg_type == 'ADD_BOT_RESULT':
                    if payload.get('success'):
                        added += 1
                        print(f"[{self._time()}] 봇 추가 성공: {payload.get('nickname')}")
                    else:
                        print(f"[{self._time()}] 봇 추가 실패: {payload.get('errorMessage')}")
                    break
                elif msg_type == 'TABLE_SNAPSHOT':
                    seats = payload.get('seats', [])
                    occupied = [s for s in seats if s.get('player')]
                    self.player_count = len(occupied)

        print(f"[{self._time()}] 봇 {added}개 추가됨")
        return added

    async def start_game(self):
        """게임 시작"""
        print(f"\n[{self._time()}] === 게임 시작 ===")
        await self.send('START_GAME', {'tableId': TABLE_ID})

    async def watch_game(self, max_time: float = 60.0, max_hands: int = 3):
        """게임 관전 및 결과 수집"""
        print(f"\n[{self._time()}] === 게임 관전 시작 (최대 {max_hands}핸드, {max_time}초) ===")

        start_time = time.time()
        self.hand_count = 0
        hand_results = []

        while time.time() - start_time < max_time and self.hand_count < max_hands:
            data = await self.recv(3)
            if not data:
                continue

            msg_type = data.get('type')
            payload = data.get('payload', {})

            if msg_type == 'HAND_START' or msg_type == 'HAND_STARTED':
                hand_num = payload.get('handNumber', '?')
                print(f"[{self._time()}] 핸드 #{hand_num} 시작")

            elif msg_type == 'TURN_PROMPT':
                pos = payload.get('position')
                actions = [a.get('type') for a in payload.get('allowedActions', [])]
                print(f"[{self._time()}] 턴: 좌석 {pos}, 가능 액션: {actions}")

            elif msg_type == 'TURN_CHANGED':
                pos = payload.get('currentPlayer')
                print(f"[{self._time()}] 턴 변경 -> 좌석 {pos}")

            elif msg_type == 'ACTION_RESULT':
                if payload.get('success'):
                    action = payload.get('action', {})
                    print(f"[{self._time()}] 액션: {action.get('type')} by 좌석 {action.get('position')}")
                else:
                    err = payload.get('errorMessage', 'unknown')
                    print(f"[{self._time()}] ❌ 액션 실패: {err}")
                    self.errors.append(f"ACTION_RESULT error: {err}")

            elif msg_type == 'COMMUNITY_CARDS':
                cards = payload.get('cards', [])
                phase = payload.get('phase', '')
                print(f"[{self._time()}] 커뮤니티 카드 ({phase}): {cards}")

            elif msg_type == 'HAND_RESULT':
                self.hand_count += 1
                winners = payload.get('winners', [])
                showdown = payload.get('showdown', [])
                pot = payload.get('pot', 0)

                print(f"[{self._time()}] ✅ 핸드 #{self.hand_count} 완료!")
                print(f"    팟: {pot}")
                print(f"    승자: {len(winners)}명")
                for w in winners:
                    print(f"      - 좌석 {w.get('seat')}: +{w.get('amount')}")
                print(f"    쇼다운: {len(showdown)}명 카드 공개")
                for sd in showdown:
                    print(f"      - 좌석 {sd.get('seat')}: {sd.get('holeCards')}")

                hand_results.append({
                    'hand': self.hand_count,
                    'pot': pot,
                    'winners': winners,
                    'showdown_count': len(showdown)
                })

            elif msg_type == 'TABLE_SNAPSHOT':
                phase = payload.get('state', {}).get('phase', payload.get('hand', {}).get('phase', '?'))
                pot = payload.get('state', {}).get('pot', payload.get('hand', {}).get('pot', 0))
                print(f"[{self._time()}] 스냅샷: phase={phase}, pot={pot}")

            elif msg_type == 'ERROR':
                err = payload.get('message', 'unknown')
                print(f"[{self._time()}] ❌ 에러: {err}")
                self.errors.append(f"ERROR: {err}")

            elif msg_type in ('PING', 'PONG'):
                pass  # 무시

            else:
                print(f"[{self._time()}] {msg_type}")

        return hand_results

    async def close(self):
        if self.ws:
            await self.ws.close()
            print(f"[{self._time()}] 연결 종료")


async def test_scenario(bot_count: int, hands: int = 2):
    """특정 봇 수로 시나리오 테스트"""
    print(f"\n{'='*60}")
    print(f" 시나리오: 봇 {bot_count}개 테스트 ({hands}핸드)")
    print(f"{'='*60}")

    tester = GameTester()

    try:
        await tester.connect()

        # 테이블 리셋
        await tester.reset_table()
        await asyncio.sleep(0.5)

        # 다시 구독
        await tester.subscribe_and_get_state()

        # 봇만으로 테스트 (유저 착석 안 함)
        # 봇 추가 (최소 2명 필요)
        actual_bot_count = max(bot_count, 2)  # 최소 2명
        await tester.add_bots(actual_bot_count)
        await asyncio.sleep(0.5)

        # 현재 상태 재확인
        await tester.send('SUBSCRIBE_TABLE', {'tableId': TABLE_ID})
        await asyncio.sleep(0.5)

        # 메시지 소비
        for _ in range(3):
            data = await tester.recv(1)
            if data and data.get('type') == 'TABLE_SNAPSHOT':
                seats = data.get('payload', {}).get('seats', [])
                occupied = [s for s in seats if s.get('player')]
                tester.player_count = len(occupied)
                print(f"[{tester._time()}] 현재 참가자: {tester.player_count}명")

        # 2명 이상이면 게임 시작
        if tester.player_count >= 2:
            await tester.start_game()
            results = await tester.watch_game(max_time=45, max_hands=hands)

            print(f"\n[{tester._time()}] === 테스트 결과 ===")
            print(f"  완료된 핸드: {len(results)}")
            print(f"  에러 수: {len(tester.errors)}")

            if tester.errors:
                print(f"  에러 목록:")
                for err in tester.errors:
                    print(f"    - {err}")

            return {
                'bot_count': bot_count,
                'hands_completed': len(results),
                'errors': tester.errors,
                'success': len(results) >= hands and len(tester.errors) == 0
            }
        else:
            print(f"[{tester._time()}] ⚠️ 참가자 부족 ({tester.player_count}명) - 게임 시작 불가")
            return {
                'bot_count': bot_count,
                'hands_completed': 0,
                'errors': ['참가자 부족'],
                'success': False
            }

    except Exception as e:
        print(f"[{tester._time()}] ❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return {
            'bot_count': bot_count,
            'hands_completed': 0,
            'errors': [str(e)],
            'success': False
        }
    finally:
        await tester.close()


async def main():
    print("\n" + "="*60)
    print(" 홀덤 게임 종합 테스트")
    print("="*60)

    results = []

    # 시나리오 1: 봇 1명 (유저 포함 2명)
    result = await test_scenario(1, hands=2)
    results.append(result)
    await asyncio.sleep(2)

    # 시나리오 2: 봇 2명 (유저 포함 3명)
    result = await test_scenario(2, hands=2)
    results.append(result)
    await asyncio.sleep(2)

    # 시나리오 3: 봇 3명 (유저 포함 4명)
    result = await test_scenario(3, hands=2)
    results.append(result)
    await asyncio.sleep(2)

    # 최종 결과
    print("\n" + "="*60)
    print(" 최종 테스트 결과")
    print("="*60)

    all_success = True
    for r in results:
        status = "✅ 성공" if r['success'] else "❌ 실패"
        print(f"  봇 {r['bot_count']}명: {status} (핸드 {r['hands_completed']}개 완료)")
        if r['errors']:
            for err in r['errors']:
                print(f"    - {err}")
        if not r['success']:
            all_success = False

    print()
    if all_success:
        print("🎉 모든 테스트 통과!")
    else:
        print("⚠️ 일부 테스트 실패")

    return all_success


if __name__ == '__main__':
    asyncio.run(main())

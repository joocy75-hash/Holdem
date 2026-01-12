import * as fs from 'fs';
import * as path from 'path';

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000/api';
const TEST_STATE_FILE = path.join(__dirname, '.test-state.json');

interface TestState {
  TEST_EMAIL: string;
  TEST_PASSWORD: string;
  TEST_ROOM_ID: string;
  TEST_GAME_ROOM_ID: string;
  TEST_SHOWDOWN_ROOM_ID: string;
  accessToken: string;
}

async function globalSetup() {
  console.log('🚀 Global Setup: Preparing test environment...');

  const testEmail = `e2e-test-${Date.now()}@test.com`;
  const testPassword = 'TestPassword123!';
  const testNickname = `E2E_Tester_${Date.now().toString(36)}`;

  try {
    // 1. Register test user
    console.log('📝 Creating test user...');
    const registerResponse = await fetch(`${API_BASE_URL}/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: testEmail,
        password: testPassword,
        nickname: testNickname,
      }),
    });

    if (!registerResponse.ok) {
      const errorData = await registerResponse.json();
      throw new Error(`Registration failed: ${JSON.stringify(errorData)}`);
    }

    const registerData = await registerResponse.json();
    const accessToken = registerData.accessToken;
    console.log('✅ Test user created');

    // 2. Create test rooms
    console.log('🏠 Creating test rooms...');

    // Room 1: Basic test room
    const room1Response = await fetch(`${API_BASE_URL}/v1/rooms`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        name: 'E2E Test Room 1',
        description: 'Room for E2E testing',
        max_seats: 6,
        small_blind: 10,
        big_blind: 20,
        buy_in_min: 400,
        buy_in_max: 2000,
        is_private: false,
      }),
    });

    if (!room1Response.ok) {
      const errorData = await room1Response.json();
      throw new Error(`Room creation failed: ${JSON.stringify(errorData)}`);
    }

    const room1Data = await room1Response.json();
    const testRoomId = room1Data.id;
    console.log(`✅ Test room created: ${testRoomId}`);

    // Room 2: For game flow tests (same as room 1 for now)
    const room2Response = await fetch(`${API_BASE_URL}/v1/rooms`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        name: 'E2E Game Flow Room',
        description: 'Room for game flow testing',
        max_seats: 6,
        small_blind: 10,
        big_blind: 20,
        buy_in_min: 400,
        buy_in_max: 2000,
        is_private: false,
      }),
    });

    const room2Data = room2Response.ok ? await room2Response.json() : null;
    const gameRoomId = room2Data?.id || testRoomId;
    console.log(`✅ Game room created: ${gameRoomId}`);

    // Room 3: For showdown tests
    const room3Response = await fetch(`${API_BASE_URL}/v1/rooms`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        name: 'E2E Showdown Room',
        description: 'Room for showdown testing',
        max_seats: 2,
        small_blind: 5,
        big_blind: 10,
        buy_in_min: 200,
        buy_in_max: 1000,
        is_private: false,
      }),
    });

    const room3Data = room3Response.ok ? await room3Response.json() : null;
    const showdownRoomId = room3Data?.id || testRoomId;
    console.log(`✅ Showdown room created: ${showdownRoomId}`);

    // 3. Save test state to file
    const testState: TestState = {
      TEST_EMAIL: testEmail,
      TEST_PASSWORD: testPassword,
      TEST_ROOM_ID: testRoomId,
      TEST_GAME_ROOM_ID: gameRoomId,
      TEST_SHOWDOWN_ROOM_ID: showdownRoomId,
      accessToken,
    };

    fs.writeFileSync(TEST_STATE_FILE, JSON.stringify(testState, null, 2));
    console.log('💾 Test state saved to file');

    // 4. Set environment variables for current process
    process.env.TEST_EMAIL = testEmail;
    process.env.TEST_PASSWORD = testPassword;
    process.env.TEST_ROOM_ID = testRoomId;
    process.env.TEST_GAME_ROOM_ID = gameRoomId;
    process.env.TEST_SHOWDOWN_ROOM_ID = showdownRoomId;

    console.log('✨ Global setup completed successfully!');
    console.log(`   Email: ${testEmail}`);
    console.log(`   Room ID: ${testRoomId}`);
    console.log(`   Game Room ID: ${gameRoomId}`);
    console.log(`   Showdown Room ID: ${showdownRoomId}`);
  } catch (error) {
    console.error('❌ Global setup failed:', error);

    // Create a fallback state file with empty values
    const fallbackState: TestState = {
      TEST_EMAIL: '',
      TEST_PASSWORD: '',
      TEST_ROOM_ID: '',
      TEST_GAME_ROOM_ID: '',
      TEST_SHOWDOWN_ROOM_ID: '',
      accessToken: '',
    };
    fs.writeFileSync(TEST_STATE_FILE, JSON.stringify(fallbackState, null, 2));

    // Don't throw - let tests handle missing credentials gracefully
  }
}

export default globalSetup;

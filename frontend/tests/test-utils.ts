import * as fs from 'fs';
import * as path from 'path';

const TEST_STATE_FILE = path.join(__dirname, '.test-state.json');

interface TestState {
  TEST_EMAIL: string;
  TEST_PASSWORD: string;
  TEST_ROOM_ID: string;
  TEST_GAME_ROOM_ID: string;
  TEST_SHOWDOWN_ROOM_ID: string;
  accessToken: string;
}

let cachedState: TestState | null = null;

/**
 * Load test state from the file created by global-setup.ts
 * Falls back to environment variables if file doesn't exist
 */
export function loadTestState(): TestState {
  if (cachedState) {
    return cachedState;
  }

  try {
    if (fs.existsSync(TEST_STATE_FILE)) {
      const content = fs.readFileSync(TEST_STATE_FILE, 'utf-8');
      cachedState = JSON.parse(content);
      return cachedState!;
    }
  } catch (error) {
    console.warn('Failed to load test state from file:', error);
  }

  // Fallback to environment variables
  cachedState = {
    TEST_EMAIL: process.env.TEST_EMAIL || '',
    TEST_PASSWORD: process.env.TEST_PASSWORD || '',
    TEST_ROOM_ID: process.env.TEST_ROOM_ID || '',
    TEST_GAME_ROOM_ID: process.env.TEST_GAME_ROOM_ID || '',
    TEST_SHOWDOWN_ROOM_ID: process.env.TEST_SHOWDOWN_ROOM_ID || '',
    accessToken: '',
  };

  return cachedState;
}

/**
 * Check if test credentials are configured
 */
export function hasTestCredentials(): boolean {
  const state = loadTestState();
  return Boolean(state.TEST_EMAIL && state.TEST_PASSWORD);
}

/**
 * Check if test room is configured
 */
export function hasTestRoom(): boolean {
  const state = loadTestState();
  return Boolean(state.TEST_ROOM_ID);
}

/**
 * Check if game room is configured
 */
export function hasGameRoom(): boolean {
  const state = loadTestState();
  return Boolean(state.TEST_GAME_ROOM_ID);
}

/**
 * Check if showdown room is configured
 */
export function hasShowdownRoom(): boolean {
  const state = loadTestState();
  return Boolean(state.TEST_SHOWDOWN_ROOM_ID);
}

/**
 * Multi-Player Fixtures for E2E Tests
 * 
 * Provides independent browser contexts for simulating
 * multiple players in the same game.
 */

/* eslint-disable react-hooks/rules-of-hooks */

import { test as base, Page, BrowserContext, Browser } from '@playwright/test';
import { LoginPage } from '../pages/login.page.js';
import { LobbyPage } from '../pages/lobby.page.js';
import { TablePage } from '../pages/table.page.js';
import { createTestUsers, TestUser } from '../utils/test-users.js';
import { waitForPlayerSeated, waitForPhase } from '../utils/wait-helpers.js';
import { cheatAPI } from '../utils/cheat-api.js';

/**
 * Player session with page and table page instance
 */
export interface PlayerSession {
  page: Page;
  context: BrowserContext;
  user: TestUser;
  tablePage: TablePage;
  lobbyPage: LobbyPage;
}

/**
 * Two-player fixture for head-to-head testing
 */
export interface TwoPlayerFixtures {
  playerA: PlayerSession;
  playerB: PlayerSession;
  tableId: string;
  setupBothPlayersAtTable: (tableId: string, options?: SetupOptions) => Promise<void>;
  createPlayers: (count: number) => Promise<PlayerSession[]>;
}

/**
 * Three-player fixture for multi-way pot testing
 */
export interface ThreePlayerFixtures {
  playerA: PlayerSession;
  playerB: PlayerSession;
  playerC: PlayerSession;
  setupAllPlayersAtTable: (tableId: string, options?: SetupOptions) => Promise<void>;
}

/**
 * Multi-player fixture for 4-6 player testing
 */
export interface MultiPlayerFixtures {
  players: PlayerSession[];
  setupPlayersAtTable: (tableId: string, options?: SetupOptions) => Promise<void>;
}

/**
 * Setup options for player seating
 */
export interface SetupOptions {
  buyInAmount?: number;
  waitForGameStart?: boolean;
  positions?: number[];
}

const DEFAULT_BUY_IN = 1000;
const LOGIN_TIMEOUT = 15000;
const SEAT_TIMEOUT = 10000;
const GAME_START_TIMEOUT = 30000;

/**
 * Create an authenticated player session with retry logic
 */
async function createPlayerSession(
  browser: Browser,
  user: TestUser,
  maxRetries: number = 3
): Promise<PlayerSession> {
  let lastError: Error | undefined;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
      // Login with timeout
      const loginPage = new LoginPage(page);
      await loginPage.goto();
      await loginPage.login(user.email, user.password);
      await page.waitForURL('**/lobby**', { timeout: LOGIN_TIMEOUT });

      return {
        page,
        context,
        user,
        tablePage: new TablePage(page),
        lobbyPage: new LobbyPage(page),
      };
    } catch (error) {
      lastError = error as Error;
      await context.close();

      if (attempt < maxRetries) {
        // Wait before retry
        await new Promise((resolve) => setTimeout(resolve, 1000 * attempt));
      }
    }
  }

  throw new Error(`Failed to create player session after ${maxRetries} attempts: ${lastError?.message}`);
}

/**
 * Find an available empty seat at the table
 */
async function findAvailableSeat(
  page: Page,
  excludePositions: number[] = []
): Promise<number | null> {
  for (let i = 0; i < 9; i++) {
    if (excludePositions.includes(i)) continue;

    const seat = page.locator(`[data-testid="seat-${i}"]`);
    if (await seat.isVisible()) {
      const occupied = await seat.getAttribute('data-occupied');
      if (occupied !== 'true') {
        return i;
      }
    }
  }
  return null;
}

/**
 * Seat a player at the table with proper synchronization
 */
async function seatPlayer(
  session: PlayerSession,
  tableId: string,
  position: number | undefined,
  buyInAmount: number,
  occupiedPositions: number[]
): Promise<number> {
  // Navigate to table
  await session.lobbyPage.joinTable(tableId);
  await session.tablePage.waitForTableLoad();

  // Find seat position
  let seatPosition: number;
  if (position !== undefined) {
    seatPosition = position;
  } else {
    const availableSeat = await findAvailableSeat(session.page, occupiedPositions);
    if (availableSeat === null) {
      throw new Error('No available seats at the table');
    }
    seatPosition = availableSeat;
  }

  // Click seat and confirm buy-in
  await session.tablePage.clickEmptySeat(seatPosition);
  await session.tablePage.confirmBuyIn(buyInAmount);

  // Wait for player to be seated
  await waitForPlayerSeated(session.page, seatPosition, SEAT_TIMEOUT);

  return seatPosition;
}

/**
 * Extended test with two-player support
 */
export const test = base.extend<TwoPlayerFixtures>({
  tableId: async ({}, use) => {
    // Create a test table for each test
    const tableId = await cheatAPI.createTestTable({
      name: `Test Table ${Date.now()}`,
      smallBlind: 10,
      bigBlind: 20,
    });
    
    await use(tableId);
    
    // Cleanup after test
    try {
      await cheatAPI.deleteTable(tableId);
    } catch {
      // Ignore cleanup errors
    }
  },

  playerA: async ({ browser }, use) => {
    const users = await createTestUsers(1, 'playerA');
    const session = await createPlayerSession(browser, users[0]);
    await use(session);
    await session.context.close();
  },

  playerB: async ({ browser }, use) => {
    const users = await createTestUsers(1, 'playerB');
    const session = await createPlayerSession(browser, users[0]);
    await use(session);
    await session.context.close();
  },

  createPlayers: async ({ browser }, use) => {
    const sessions: PlayerSession[] = [];
    
    const createFn = async (count: number): Promise<PlayerSession[]> => {
      const users = await createTestUsers(count, 'dynPlayer');
      for (const user of users) {
        const session = await createPlayerSession(browser, user);
        sessions.push(session);
      }
      return sessions;
    };
    
    await use(createFn);
    
    // Cleanup all created sessions
    for (const session of sessions) {
      await session.context.close();
    }
  },

  setupBothPlayersAtTable: async ({ playerA, playerB }, use) => {
    const setup = async (tableId: string, options: SetupOptions = {}) => {
      const {
        buyInAmount = DEFAULT_BUY_IN,
        waitForGameStart = true,
        positions,
      } = options;

      const occupiedPositions: number[] = [];

      // Seat Player A
      const posA = await seatPlayer(
        playerA,
        tableId,
        positions?.[0],
        buyInAmount,
        occupiedPositions
      );
      occupiedPositions.push(posA);

      // Seat Player B
      const posB = await seatPlayer(
        playerB,
        tableId,
        positions?.[1],
        buyInAmount,
        occupiedPositions
      );
      occupiedPositions.push(posB);

      // Wait for game to start if requested
      if (waitForGameStart) {
        await Promise.all([
          waitForPhase(playerA.page, 'preflop', GAME_START_TIMEOUT),
          waitForPhase(playerB.page, 'preflop', GAME_START_TIMEOUT),
        ]);
      }
    };

    await use(setup);
  },
});

/**
 * Extended test with three-player support
 */
export const threePlayerTest = base.extend<ThreePlayerFixtures>({
  playerA: async ({ browser }, use) => {
    const users = await createTestUsers(1, 'player3A');
    const session = await createPlayerSession(browser, users[0]);
    await use(session);
    await session.context.close();
  },

  playerB: async ({ browser }, use) => {
    const users = await createTestUsers(1, 'player3B');
    const session = await createPlayerSession(browser, users[0]);
    await use(session);
    await session.context.close();
  },

  playerC: async ({ browser }, use) => {
    const users = await createTestUsers(1, 'player3C');
    const session = await createPlayerSession(browser, users[0]);
    await use(session);
    await session.context.close();
  },

  setupAllPlayersAtTable: async ({ playerA, playerB, playerC }, use) => {
    const setup = async (tableId: string, options: SetupOptions = {}) => {
      const {
        buyInAmount = DEFAULT_BUY_IN,
        waitForGameStart = true,
        positions,
      } = options;

      const occupiedPositions: number[] = [];
      const players = [playerA, playerB, playerC];

      // Seat all players sequentially
      for (let i = 0; i < players.length; i++) {
        const pos = await seatPlayer(
          players[i],
          tableId,
          positions?.[i],
          buyInAmount,
          occupiedPositions
        );
        occupiedPositions.push(pos);
      }

      // Wait for game to start if requested
      if (waitForGameStart) {
        await Promise.all(
          players.map((p) => waitForPhase(p.page, 'preflop', GAME_START_TIMEOUT))
        );
      }
    };

    await use(setup);
  },
});

/**
 * Factory function to create multi-player fixture with custom player count
 */
export function createMultiPlayerTest(playerCount: number) {
  if (playerCount < 2 || playerCount > 9) {
    throw new Error('Player count must be between 2 and 9');
  }

  return base.extend<MultiPlayerFixtures>({
    players: async ({ browser }, use) => {
      const users = await createTestUsers(playerCount, 'multiP');
      const sessions: PlayerSession[] = [];

      // Create sessions in parallel
      const sessionPromises = users.map((user) =>
        createPlayerSession(browser, user)
      );
      const createdSessions = await Promise.all(sessionPromises);
      sessions.push(...createdSessions);

      await use(sessions);

      // Cleanup
      await Promise.all(sessions.map((s) => s.context.close()));
    },

    setupPlayersAtTable: async ({ players }, use) => {
      const setup = async (tableId: string, options: SetupOptions = {}) => {
        const {
          buyInAmount = DEFAULT_BUY_IN,
          waitForGameStart = true,
          positions,
        } = options;

        const occupiedPositions: number[] = [];

        // Seat all players sequentially
        for (let i = 0; i < players.length; i++) {
          const pos = await seatPlayer(
            players[i],
            tableId,
            positions?.[i],
            buyInAmount,
            occupiedPositions
          );
          occupiedPositions.push(pos);
        }

        // Wait for game to start if requested
        if (waitForGameStart) {
          await Promise.all(
            players.map((p) => waitForPhase(p.page, 'preflop', GAME_START_TIMEOUT))
          );
        }
      };

      await use(setup);
    },
  });
}

// Pre-configured multi-player tests
export const fourPlayerTest = createMultiPlayerTest(4);
export const fivePlayerTest = createMultiPlayerTest(5);
export const sixPlayerTest = createMultiPlayerTest(6);

export { expect } from '@playwright/test';

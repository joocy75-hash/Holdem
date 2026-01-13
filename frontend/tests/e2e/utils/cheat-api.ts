/**
 * Cheat API Client for E2E Testing
 * 
 * Provides test-only APIs for controlling game state:
 * - Deck injection (set specific cards)
 * - Timer control (force timeout)
 * - Phase forcing (skip to specific phase)
 * 
 * IMPORTANT: Only available in development/test environments
 */

import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const DEV_API_KEY = process.env.DEV_API_KEY || 'dev-key';

export interface Card {
  rank: string; // '2'-'10', 'J', 'Q', 'K', 'A'
  suit: string; // 'h' (hearts), 'd' (diamonds), 'c' (clubs), 's' (spades)
}

export interface DeckInjection {
  /** Cards for each player position (0-5) */
  holeCards?: Record<number, [Card, Card]>;
  /** Community cards (flop, turn, river) */
  communityCards?: Card[];
}

export interface TimerControl {
  /** Force timeout for specific position */
  forceTimeout?: number;
  /** Set remaining time in seconds */
  setRemainingTime?: number;
  /** Pause/resume timer */
  paused?: boolean;
}

export type GamePhase = 'preflop' | 'flop' | 'turn' | 'river' | 'showdown';

/**
 * Cheat API client for test automation
 */
export class CheatAPI {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/dev`,
      headers: {
        'X-Dev-Key': DEV_API_KEY,
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Inject specific cards into the deck
   * 
   * @param tableId - Table ID
   * @param injection - Card injection configuration
   */
  async injectDeck(tableId: string, injection: DeckInjection): Promise<void> {
    await this.client.post(`/tables/${tableId}/inject-deck`, injection);
  }

  /**
   * Set specific hole cards for a player
   * 
   * @param tableId - Table ID
   * @param position - Player position (0-5)
   * @param cards - Two hole cards
   */
  async setHoleCards(
    tableId: string,
    position: number,
    cards: [Card, Card]
  ): Promise<void> {
    await this.client.post(`/tables/${tableId}/set-hole-cards`, {
      position,
      cards,
    });
  }

  /**
   * Set community cards
   * 
   * @param tableId - Table ID
   * @param cards - Community cards (3-5 cards)
   */
  async setCommunityCards(tableId: string, cards: Card[]): Promise<void> {
    await this.client.post(`/tables/${tableId}/set-community-cards`, {
      cards,
    });
  }

  /**
   * Force turn timeout for a player
   * 
   * @param tableId - Table ID
   * @param position - Player position to timeout
   */
  async forceTimeout(tableId: string, position: number): Promise<void> {
    await this.client.post(`/tables/${tableId}/force-timeout`, {
      position,
    });
  }

  /**
   * Set remaining turn time
   * 
   * @param tableId - Table ID
   * @param seconds - Remaining seconds
   */
  async setRemainingTime(tableId: string, seconds: number): Promise<void> {
    await this.client.post(`/tables/${tableId}/set-timer`, {
      remaining_seconds: seconds,
    });
  }

  /**
   * Force game to specific phase
   * 
   * @param tableId - Table ID
   * @param phase - Target phase
   */
  async forcePhase(tableId: string, phase: GamePhase): Promise<void> {
    await this.client.post(`/tables/${tableId}/force-phase`, {
      phase,
    });
  }

  /**
   * Force showdown (skip remaining betting)
   * 
   * @param tableId - Table ID
   */
  async forceShowdown(tableId: string): Promise<void> {
    await this.forcePhase(tableId, 'showdown');
  }

  /**
   * Start a new hand immediately
   * 
   * @param tableId - Table ID
   */
  async startNewHand(tableId: string): Promise<void> {
    await this.client.post(`/tables/${tableId}/start-hand`);
  }

  /**
   * Reset table to initial state
   * 
   * @param tableId - Table ID
   */
  async resetTable(tableId: string): Promise<void> {
    await this.client.post(`/tables/${tableId}/reset`);
  }

  /**
   * Get current game state (for debugging)
   * 
   * @param tableId - Table ID
   */
  async getGameState(tableId: string): Promise<unknown> {
    const response = await this.client.get(`/tables/${tableId}/state`);
    return response.data;
  }

  /**
   * Force a player to fold
   * 
   * @param tableId - Table ID
   * @param position - Player position
   */
  async forceFold(tableId: string, position: number): Promise<void> {
    await this.client.post(`/tables/${tableId}/force-action`, {
      position,
      action: 'fold',
    });
  }

  /**
   * Create a test table with specific configuration
   * 
   * @param config - Table configuration
   */
  async createTestTable(config: {
    name?: string;
    smallBlind?: number;
    bigBlind?: number;
    maxSeats?: number;
    buyInMin?: number;
    buyInMax?: number;
  }): Promise<string> {
    const response = await this.client.post('/tables/create', {
      name: config.name || `Test Table ${Date.now()}`,
      small_blind: config.smallBlind || 10,
      big_blind: config.bigBlind || 20,
      max_seats: config.maxSeats || 6,
      buy_in_min: config.buyInMin || 400,
      buy_in_max: config.buyInMax || 2000,
    });
    return response.data.table_id;
  }

  /**
   * Delete a test table
   * 
   * @param tableId - Table ID to delete
   */
  async deleteTable(tableId: string): Promise<void> {
    try {
      await this.client.delete(`/tables/${tableId}`);
    } catch (error) {
      // Ignore 404 errors (table already deleted or doesn't exist)
      const axiosError = error as { response?: { status: number } };
      if (axiosError.response?.status === 404) {
        console.warn(`Table ${tableId} not found during cleanup (already deleted)`);
        return;
      }
      // Re-throw other errors
      throw error;
    }
  }

  /**
   * Simulate server restart (for recovery testing)
   */
  async simulateServerRestart(): Promise<void> {
    await this.client.post('/simulate-restart');
  }

  /**
   * Get server time (for timer sync testing)
   */
  async getServerTime(): Promise<number> {
    const response = await this.client.get('/server-time');
    return response.data.timestamp;
  }

  /**
   * Set player stack by user ID
   * 
   * @param userId - User ID
   * @param stack - New stack amount
   */
  async setPlayerStack(userId: string, stack: number): Promise<void> {
    await this.client.post('/players/set-stack', {
      user_id: userId,
      stack,
    });
  }

  /**
   * Force specific betting scenario
   * 
   * @param tableId - Table ID
   * @param scenario - Betting scenario configuration
   */
  async forceBettingScenario(
    tableId: string,
    scenario: {
      actions: Array<{
        playerId: string;
        action: 'fold' | 'check' | 'call' | 'raise' | 'allin';
        amount?: number;
      }>;
    }
  ): Promise<void> {
    await this.client.post(`/tables/${tableId}/force-betting`, scenario);
  }

  /**
   * Force pot to specific amount
   * 
   * @param tableId - Table ID
   * @param amount - Pot amount
   */
  async forcePotAmount(tableId: string, amount: number): Promise<void> {
    await this.client.post(`/tables/${tableId}/force-pot`, { amount });
  }

  /**
   * Add bot player to table
   * 
   * @param tableId - Table ID
   */
  async addBotPlayer(tableId: string): Promise<string> {
    const response = await this.client.post(`/tables/${tableId}/add-bot`);
    return response.data.bot_id;
  }

  /**
   * Run a test suite and get results
   * 
   * @param suiteName - Name of the test suite
   */
  async runTestSuite(suiteName: string): Promise<{
    total: number;
    passed: number;
    failed: number;
    skipped: number;
    successRate: number;
    graphicalBugs?: number;
    metrics?: {
      handRankingAccuracy: number;
      bettingButtonAccuracy: number;
      highlightAccuracy: number;
    };
    details: Array<{
      type: string;
      error?: number;
      [key: string]: unknown;
    }>;
  }> {
    const response = await this.client.get(`/test-suites/${suiteName}/results`);
    return response.data;
  }
}

// Singleton instance
export const cheatAPI = new CheatAPI();

// Helper functions for common card combinations
export const CARDS = {
  // Royal Flush (Spades)
  ROYAL_FLUSH: [
    { rank: 'A', suit: 's' },
    { rank: 'K', suit: 's' },
    { rank: 'Q', suit: 's' },
    { rank: 'J', suit: 's' },
    { rank: '10', suit: 's' },
  ] as Card[],

  // Straight Flush (Hearts 5-9)
  STRAIGHT_FLUSH: [
    { rank: '9', suit: 'h' },
    { rank: '8', suit: 'h' },
    { rank: '7', suit: 'h' },
    { rank: '6', suit: 'h' },
    { rank: '5', suit: 'h' },
  ] as Card[],

  // Four of a Kind (Aces)
  FOUR_ACES: [
    { rank: 'A', suit: 's' },
    { rank: 'A', suit: 'h' },
    { rank: 'A', suit: 'd' },
    { rank: 'A', suit: 'c' },
  ] as Card[],

  // Full House (Kings over Queens)
  FULL_HOUSE_KKK_QQ: [
    { rank: 'K', suit: 's' },
    { rank: 'K', suit: 'h' },
    { rank: 'K', suit: 'd' },
    { rank: 'Q', suit: 's' },
    { rank: 'Q', suit: 'h' },
  ] as Card[],

  // Flush (Diamonds)
  FLUSH_DIAMONDS: [
    { rank: 'A', suit: 'd' },
    { rank: 'J', suit: 'd' },
    { rank: '9', suit: 'd' },
    { rank: '6', suit: 'd' },
    { rank: '3', suit: 'd' },
  ] as Card[],

  // Straight (10-A)
  STRAIGHT_BROADWAY: [
    { rank: 'A', suit: 's' },
    { rank: 'K', suit: 'h' },
    { rank: 'Q', suit: 'd' },
    { rank: 'J', suit: 'c' },
    { rank: '10', suit: 's' },
  ] as Card[],

  // Three of a Kind (Jacks)
  THREE_JACKS: [
    { rank: 'J', suit: 's' },
    { rank: 'J', suit: 'h' },
    { rank: 'J', suit: 'd' },
  ] as Card[],

  // Two Pair (Aces and Kings)
  TWO_PAIR_AA_KK: [
    { rank: 'A', suit: 's' },
    { rank: 'A', suit: 'h' },
    { rank: 'K', suit: 'd' },
    { rank: 'K', suit: 'c' },
  ] as Card[],

  // One Pair (Queens)
  PAIR_QUEENS: [
    { rank: 'Q', suit: 's' },
    { rank: 'Q', suit: 'h' },
  ] as Card[],

  // High Card (Ace high)
  HIGH_CARD_ACE: [
    { rank: 'A', suit: 's' },
    { rank: 'K', suit: 'h' },
    { rank: 'J', suit: 'd' },
    { rank: '8', suit: 'c' },
    { rank: '4', suit: 's' },
  ] as Card[],
};

/**
 * Create a card from string notation (e.g., 'As' for Ace of Spades)
 */
export function parseCard(notation: string): Card {
  const rank = notation.slice(0, -1);
  const suit = notation.slice(-1);
  return { rank, suit };
}

/**
 * Create cards from string array
 */
export function parseCards(notations: string[]): Card[] {
  return notations.map(parseCard);
}

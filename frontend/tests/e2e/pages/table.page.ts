/**
 * Table Page Object Model
 * 
 * Handles poker table UI interactions including seating,
 * betting actions, game state, and timer management.
 * 
 * @requirements 3.x, 4.x, 5.x, 7.x, 8.x, 9.x
 */

import { Page, Locator, expect } from '@playwright/test';

export type GamePhase = 'waiting' | 'preflop' | 'flop' | 'turn' | 'river' | 'showdown';
export type PlayerStatus = 'active' | 'fold' | 'allin' | 'sitout' | 'waiting';

export interface SidePot {
  amount: number;
  eligiblePlayers: number[];
}

export interface HoleCard {
  rank: string;
  suit: string;
}

export class TablePage {
  readonly page: Page;
  
  // Table elements
  readonly table: Locator;
  readonly pot: Locator;
  readonly communityCards: Locator;
  readonly dealerButton: Locator;
  
  // Action buttons
  readonly foldButton: Locator;
  readonly checkButton: Locator;
  readonly callButton: Locator;
  readonly raiseButton: Locator;
  readonly allInButton: Locator;
  readonly raiseSlider: Locator;
  readonly raiseInput: Locator;
  
  // Pot ratio buttons (피망 스타일)
  readonly quarterPotButton: Locator;
  readonly halfPotButton: Locator;
  readonly threeQuarterPotButton: Locator;
  readonly fullPotButton: Locator;
  
  // Timer
  readonly timer: Locator;
  
  // Buy-in modal
  readonly buyInModal: Locator;
  readonly buyInSlider: Locator;
  readonly buyInInput: Locator;
  readonly buyInConfirmButton: Locator;
  readonly buyInCancelButton: Locator;
  
  // Navigation
  readonly leaveButton: Locator;
  readonly sitOutButton: Locator;
  readonly sitInButton: Locator;
  
  // Hand ranking guide (피망 스타일)
  readonly handRankingGuide: Locator;
  readonly currentHandRank: Locator;
  
  // Hole cards (카드 쪼기)
  readonly myHoleCards: Locator;

  constructor(page: Page) {
    this.page = page;
    
    // Table elements
    this.table = page.getByTestId('poker-table');
    this.pot = page.getByTestId('pot-amount');
    this.communityCards = page.getByTestId('community-cards');
    this.dealerButton = page.getByTestId('dealer-button');
    
    // Action buttons
    this.foldButton = page.getByTestId('fold-button');
    this.checkButton = page.getByTestId('check-button');
    this.callButton = page.getByTestId('call-button');
    this.raiseButton = page.getByTestId('raise-button');
    this.allInButton = page.getByTestId('allin-button');
    this.raiseSlider = page.getByTestId('raise-slider');
    this.raiseInput = page.getByTestId('raise-input');
    
    // Pot ratio buttons
    this.quarterPotButton = page.getByTestId('pot-ratio-0.25');
    this.halfPotButton = page.getByTestId('pot-ratio-0.5');
    this.threeQuarterPotButton = page.getByTestId('pot-ratio-0.75');
    this.fullPotButton = page.getByTestId('pot-ratio-1');
    
    // Timer
    this.timer = page.getByTestId('turn-timer');
    
    // Buy-in modal
    this.buyInModal = page.getByTestId('buyin-modal');
    this.buyInSlider = page.getByTestId('buyin-slider');
    this.buyInInput = page.getByTestId('buyin-input');
    this.buyInConfirmButton = page.getByTestId('buyin-confirm');
    this.buyInCancelButton = page.getByTestId('buyin-cancel');
    
    // Navigation
    this.leaveButton = page.getByTestId('leave-button');
    this.sitOutButton = page.getByTestId('sitout-button');
    this.sitInButton = page.getByTestId('sitin-button');
    
    // Hand ranking guide
    this.handRankingGuide = page.getByTestId('hand-ranking-guide');
    this.currentHandRank = page.getByTestId('current-hand-rank');
    
    // Hole cards
    this.myHoleCards = page.getByTestId('my-hole-cards');
  }

  /**
   * Navigate to table page
   */
  async goto(tableId: string): Promise<void> {
    await this.page.goto(`/table/${tableId}`);
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Wait for table to fully load including WebSocket connection
   * @requirements 3.1
   */
  async waitForTableLoad(): Promise<void> {
    // Wait for table UI to be visible
    await expect(this.table).toBeVisible({ timeout: 10000 });
    
    // Wait for WebSocket connection (Connected badge)
    await this.page.waitForSelector('.badge-success:has-text("Connected")', { 
      timeout: 10000,
      state: 'visible'
    });
  }

  // ============ Seating & Buy-in ============

  /**
   * Click on an empty seat
   * @requirements 3.2
   */
  async clickEmptySeat(position?: number): Promise<void> {
    if (position !== undefined) {
      // Click specific seat, verify it's empty first
      const seat = this.page.locator(`[data-testid="seat-${position}"][data-occupied="false"]`);
      await expect(seat).toBeVisible({ timeout: 5000 });
      await seat.click();
    } else {
      // Click first available empty seat
      const emptySeat = this.page.locator('[data-testid^="seat-"][data-occupied="false"]').first();
      await expect(emptySeat).toBeVisible({ timeout: 5000 });
      await emptySeat.click();
    }
    
    // Wait for buy-in modal to appear
    await expect(this.buyInModal).toBeVisible({ timeout: 5000 });
  }

  /**
   * Confirm buy-in with specified amount
   * @requirements 3.3
   */
  async confirmBuyIn(amount: number): Promise<void> {
    // Ensure modal is visible
    await expect(this.buyInModal).toBeVisible({ timeout: 5000 });
    
    // Fill in the amount
    await this.buyInInput.fill(amount.toString());
    
    // Wait for button to be enabled (validation passed)
    await expect(this.buyInConfirmButton).toBeEnabled({ timeout: 3000 });
    
    // Click confirm button
    await this.buyInConfirmButton.click();
    
    // Wait for either:
    // 1. Modal closes (success)
    // 2. Error message appears (failure)
    // 3. Player is seated (success without modal close detection)
    try {
      await Promise.race([
        expect(this.buyInModal).not.toBeVisible({ timeout: 10000 }),
        this.page.waitForSelector('[data-testid^="seat-"][data-is-me="true"]', { timeout: 10000 }),
      ]);
    } catch {
      // If modal is still visible, check if player is seated anyway
      const isSeated = await this.page.locator('[data-testid^="seat-"][data-is-me="true"]').isVisible().catch(() => false);
      if (!isSeated) {
        throw new Error('Buy-in failed: modal did not close and player is not seated');
      }
    }
  }

  /**
   * Get my current position at the table
   */
  async getMyPosition(): Promise<number> {
    const mySeat = this.page.locator('[data-testid^="seat-"][data-is-me="true"]');
    const testId = await mySeat.getAttribute('data-testid');
    return parseInt(testId?.replace('seat-', '') || '-1');
  }

  /**
   * Get my current chip stack
   * @requirements 3.3
   */
  async getMyChipStack(): Promise<number> {
    const myStack = this.page.getByTestId('my-stack');
    const text = await myStack.textContent();
    return parseInt(text?.replace(/[^0-9]/g, '') || '0');
  }

  // ============ Game Actions ============

  /**
   * Fold current hand
   * @requirements 4.3
   */
  async fold(): Promise<void> {
    await this.foldButton.click();
  }

  /**
   * Check (pass without betting)
   */
  async check(): Promise<void> {
    await this.checkButton.click();
  }

  /**
   * Call current bet
   * @requirements 4.4
   */
  async call(): Promise<void> {
    await this.callButton.click();
  }

  /**
   * Raise to specified amount
   * @requirements 4.1
   */
  async raise(amount: number): Promise<void> {
    await this.raiseInput.fill(amount.toString());
    await this.raiseButton.click();
  }

  /**
   * Go all-in
   */
  async allIn(): Promise<void> {
    await this.allInButton.click();
  }

  /**
   * Wait for my turn
   * @requirements 4.2
   */
  async waitForMyTurn(timeout: number = 30000): Promise<void> {
    await expect(this.foldButton).toBeEnabled({ timeout });
  }

  /**
   * Check if action buttons are visible
   * @requirements 4.2
   */
  async hasActionButtons(): Promise<boolean> {
    return await this.foldButton.isVisible();
  }

  // ============ Game State ============

  /**
   * Check if it's my turn
   * @requirements 4.2
   */
  async isMyTurn(): Promise<boolean> {
    return await this.foldButton.isEnabled();
  }

  /**
   * Get current game phase
   * @requirements 5.x
   */
  async getCurrentPhase(): Promise<GamePhase> {
    const phase = await this.page.getByTestId('game-phase').getAttribute('data-phase');
    return (phase as GamePhase) || 'waiting';
  }

  /**
   * Get current pot amount
   * @requirements 4.1, 4.4
   */
  async getPotAmount(): Promise<number> {
    const text = await this.pot.textContent();
    return parseInt(text?.replace(/[^0-9]/g, '') || '0');
  }

  /**
   * Get side pots
   * @requirements 10.x
   */
  async getSidePots(): Promise<SidePot[]> {
    const sidePots: SidePot[] = [];
    const sidePotElements = this.page.locator('[data-testid^="side-pot-"]');
    const count = await sidePotElements.count();
    
    for (let i = 0; i < count; i++) {
      const element = sidePotElements.nth(i);
      const amount = parseInt(await element.getAttribute('data-amount') || '0');
      const players = (await element.getAttribute('data-players') || '')
        .split(',')
        .map(p => parseInt(p));
      sidePots.push({ amount, eligiblePlayers: players });
    }
    
    return sidePots;
  }

  /**
   * Get community card count
   * @requirements 5.2, 5.3, 5.4
   */
  async getCommunityCardCount(): Promise<number> {
    const cards = this.communityCards.locator('[data-testid^="community-card-"]');
    return await cards.count();
  }

  /**
   * Get community cards as array of card strings
   * @requirements 5.2, 5.3, 5.4
   */
  async getCommunityCards(): Promise<string[]> {
    const cards: string[] = [];
    const cardElements = this.communityCards.locator('[data-testid^="community-card-"]');
    const count = await cardElements.count();
    
    for (let i = 0; i < count; i++) {
      const card = cardElements.nth(i);
      const rank = await card.getAttribute('data-rank') || '';
      const suit = await card.getAttribute('data-suit') || '';
      cards.push(`${rank}${suit}`);
    }
    
    return cards;
  }

  /**
   * Find first empty seat at the table
   * @returns seat position or null if no empty seats
   */
  async findEmptySeat(): Promise<number | null> {
    for (let i = 0; i < 6; i++) {
      const seat = this.page.getByTestId(`seat-${i}`);
      const occupied = await seat.getAttribute('data-occupied');
      if (occupied !== 'true') {
        return i;
      }
    }
    return null;
  }

  /**
   * Get my hole cards
   * @requirements 5.1
   */
  async getHoleCards(): Promise<HoleCard[]> {
    const cards: HoleCard[] = [];
    const cardElements = this.myHoleCards.locator('[data-testid^="hole-card-"]');
    const count = await cardElements.count();
    
    for (let i = 0; i < count; i++) {
      const card = cardElements.nth(i);
      cards.push({
        rank: await card.getAttribute('data-rank') || '',
        suit: await card.getAttribute('data-suit') || '',
      });
    }
    
    return cards;
  }

  // ============ Dealer & Blinds ============

  /**
   * Get dealer button position
   * @requirements 9.1
   */
  async getDealerPosition(): Promise<number> {
    const position = await this.dealerButton.getAttribute('data-position');
    return parseInt(position || '-1');
  }

  /**
   * Get small blind position
   * @requirements 9.2
   */
  async getSmallBlindPosition(): Promise<number> {
    const sb = this.page.getByTestId('small-blind-marker');
    const position = await sb.getAttribute('data-position');
    return parseInt(position || '-1');
  }

  /**
   * Get big blind position
   * @requirements 9.2
   */
  async getBigBlindPosition(): Promise<number> {
    const bb = this.page.getByTestId('big-blind-marker');
    const position = await bb.getAttribute('data-position');
    return parseInt(position || '-1');
  }

  // ============ Timer ============

  /**
   * Get current timer value in seconds
   * @requirements 7.1
   */
  async getTimerValue(): Promise<number> {
    const text = await this.timer.textContent();
    return parseInt(text?.replace(/[^0-9]/g, '') || '0');
  }

  /**
   * Wait for turn timeout
   * @requirements 7.2
   */
  async waitForTurnTimeout(timeout: number = 35000): Promise<void> {
    await this.page.waitForSelector('[data-testid="timeout-indicator"]', {
      timeout,
    });
  }

  // ============ Navigation ============

  /**
   * Leave the table
   * @requirements 8.1
   */
  async leaveTable(): Promise<void> {
    await this.leaveButton.click();
    await this.page.waitForURL('**/lobby**');
  }

  /**
   * Sit out from the game
   */
  async sitOut(): Promise<void> {
    await this.sitOutButton.click();
  }

  /**
   * Sit back in to the game
   */
  async sitIn(): Promise<void> {
    await this.sitInButton.click();
  }

  // ============ Player Status ============

  /**
   * Get player status at position
   * @requirements 4.3
   */
  async getPlayerStatus(position: number): Promise<PlayerStatus> {
    const seat = this.page.getByTestId(`seat-${position}`);
    const status = await seat.getAttribute('data-status');
    return (status as PlayerStatus) || 'waiting';
  }

  /**
   * Check if player has WIN badge
   * @requirements 6.1
   */
  async hasWinBadge(position: number): Promise<boolean> {
    const winBadge = this.page.getByTestId(`win-badge-${position}`);
    return await winBadge.isVisible();
  }

  /**
   * Get player chip stack at position
   */
  async getPlayerStack(position: number): Promise<number> {
    const stack = this.page.getByTestId(`stack-${position}`);
    const text = await stack.textContent();
    return parseInt(text?.replace(/[^0-9]/g, '') || '0');
  }

  // ============ 피망 스타일 UI ============

  /**
   * Get current hand ranking from guide
   * @requirements 14.1, 14.2
   */
  async getCurrentHandRanking(): Promise<string> {
    return await this.currentHandRank.textContent() || '';
  }

  /**
   * Click pot ratio button
   * @requirements 15.x
   */
  async clickPotRatioButton(ratio: '1/4' | '1/2' | '3/4' | 'pot'): Promise<void> {
    switch (ratio) {
      case '1/4':
        await this.quarterPotButton.click();
        break;
      case '1/2':
        await this.halfPotButton.click();
        break;
      case '3/4':
        await this.threeQuarterPotButton.click();
        break;
      case 'pot':
        await this.fullPotButton.click();
        break;
    }
  }

  /**
   * Get raise input value
   * @requirements 15.x
   */
  async getRaiseInputValue(): Promise<number> {
    const value = await this.raiseInput.inputValue();
    return parseInt(value || '0');
  }

  /**
   * Get highlighted cards (winning hand)
   * @requirements 16.1, 16.2
   */
  async getHighlightedCards(): Promise<string[]> {
    const highlighted = this.page.locator('[data-highlighted="true"]');
    const cards: string[] = [];
    const count = await highlighted.count();
    
    for (let i = 0; i < count; i++) {
      const card = highlighted.nth(i);
      const rank = await card.getAttribute('data-rank');
      const suit = await card.getAttribute('data-suit');
      cards.push(`${rank}${suit}`);
    }
    
    return cards;
  }

  // ============ 카드 쪼기 (Squeeze) ============

  /**
   * Perform card squeeze gesture
   * @requirements 17.x
   */
  async squeezeCard(cardIndex: number, dragDistance: number): Promise<void> {
    const card = this.myHoleCards.locator(`[data-testid="hole-card-${cardIndex}"]`);
    const box = await card.boundingBox();
    
    if (box) {
      await this.page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await this.page.mouse.down();
      await this.page.mouse.move(
        box.x + box.width / 2,
        box.y + box.height / 2 - dragDistance,
        { steps: 10 }
      );
    }
  }

  /**
   * Release card squeeze
   * @requirements 17.3
   */
  async releaseCardSqueeze(): Promise<void> {
    await this.page.mouse.up();
  }

  /**
   * Check if card is revealed
   * @requirements 17.2
   */
  async isCardRevealed(cardIndex: number): Promise<boolean> {
    const card = this.myHoleCards.locator(`[data-testid="hole-card-${cardIndex}"]`);
    const revealed = await card.getAttribute('data-revealed');
    return revealed === 'true';
  }

  /**
   * Check if UI is locked during squeeze
   * @requirements 17.5
   */
  async isUILocked(): Promise<boolean> {
    const locked = await this.page.getAttribute('[data-ui-locked]', 'data-ui-locked');
    return locked === 'true';
  }
}

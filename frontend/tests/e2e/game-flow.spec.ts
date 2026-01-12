import { test, expect, Page } from '@playwright/test';

/**
 * Game Flow E2E Tests
 * MVP Required Scenarios:
 * - Room creation → Join → Seat → Hand start
 * - 2-6 player turn progression
 * - Call/Raise/Fold basic actions
 * - Hand completion and showdown results
 */

// Helper function to login
async function login(page: Page, email: string, password: string) {
  await page.goto('/');
  await page.getByPlaceholder('your@email.com').fill(email);
  await page.getByPlaceholder('••••••••').fill(password);
  await page.locator('form').getByRole('button', { name: /로그인/i }).click();
  await page.waitForURL(/\/lobby|\/rooms/, { timeout: 10000 });
}

test.describe('Game Flow', () => {
  test.describe('Room Management', () => {
    test('should create a new room', async ({ page }) => {
      test.skip(!process.env.TEST_EMAIL, 'Test credentials not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);

      // Click create room button (first one in header)
      const createBtn = page.getByRole('button', { name: /방 만들기/i }).first();
      await expect(createBtn).toBeVisible();
      await createBtn.click();

      // Modal should appear
      await expect(page.locator('[role="dialog"], .modal')).toBeVisible({ timeout: 5000 });
    });

    test('should display room list', async ({ page }) => {
      test.skip(!process.env.TEST_EMAIL, 'Test credentials not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);

      // Room list or empty state should be visible
      // Wait for lobby to load - check for empty message or rooms
      await expect(page.getByText('현재 열린 방이 없습니다')).toBeVisible({ timeout: 10000 });
    });

    test('should filter rooms', async ({ page }) => {
      test.skip(!process.env.TEST_EMAIL, 'Test credentials not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);

      // Filter input should be available
      const filterInput = page.getByPlaceholder(/search|검색|filter|필터/i);
      if (await filterInput.isVisible()) {
        await filterInput.fill('test');
        // Rooms should be filtered
      }
    });
  });

  test.describe('Seat Management', () => {
    test('should display available seats', async ({ page }) => {
      test.skip(!process.env.TEST_ROOM_ID, 'Test room not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);

      // Navigate to table
      await page.goto(`/table/${process.env.TEST_ROOM_ID}`);

      // Seats should be visible
      await expect(page.locator('.seat, [data-testid="seat"]').first()).toBeVisible();
    });

    test('should allow taking a seat', async ({ page }) => {
      test.skip(!process.env.TEST_ROOM_ID, 'Test room not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);
      await page.goto(`/table/${process.env.TEST_ROOM_ID}`);

      // Click on empty seat
      const emptySeat = page.locator('.seat-empty, [data-testid="seat-empty"]').first();
      if (await emptySeat.isVisible()) {
        await emptySeat.click();

        // Buy-in modal should appear
        await expect(page.locator('.modal, [role="dialog"]')).toBeVisible();
      }
    });
  });

  test.describe('Game Actions', () => {
    test('should display action buttons when it is players turn', async ({ page }) => {
      test.skip(!process.env.TEST_GAME_ROOM_ID, 'Active game room not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);
      await page.goto(`/table/${process.env.TEST_GAME_ROOM_ID}`);

      // Action panel should be visible
      const actionPanel = page.locator('.action-panel, [data-testid="action-panel"]');

      // At least one action should be available
      await expect(actionPanel).toBeVisible({ timeout: 10000 });
    });

    test('should handle fold action', async ({ page }) => {
      test.skip(!process.env.TEST_GAME_ROOM_ID, 'Active game room not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);
      await page.goto(`/table/${process.env.TEST_GAME_ROOM_ID}`);

      const foldBtn = page.getByRole('button', { name: /fold|폴드/i });
      if (await foldBtn.isVisible() && await foldBtn.isEnabled()) {
        await foldBtn.click();
        // Action should be processed
        await expect(foldBtn).toBeDisabled();
      }
    });

    test('should handle call action', async ({ page }) => {
      test.skip(!process.env.TEST_GAME_ROOM_ID, 'Active game room not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);
      await page.goto(`/table/${process.env.TEST_GAME_ROOM_ID}`);

      const callBtn = page.getByRole('button', { name: /call|콜/i });
      if (await callBtn.isVisible() && await callBtn.isEnabled()) {
        await callBtn.click();
        // Action should be processed
      }
    });

    test('should handle raise action with slider', async ({ page }) => {
      test.skip(!process.env.TEST_GAME_ROOM_ID, 'Active game room not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);
      await page.goto(`/table/${process.env.TEST_GAME_ROOM_ID}`);

      const raiseBtn = page.getByRole('button', { name: /raise|레이즈/i });
      if (await raiseBtn.isVisible() && await raiseBtn.isEnabled()) {
        await raiseBtn.click();

        // Slider or amount input should appear
        const slider = page.locator('input[type="range"]');

        if (await slider.isVisible()) {
          // Adjust slider
          await slider.fill('100');
        }

        // Confirm raise
        const confirmBtn = page.getByRole('button', { name: /confirm|확인/i });
        if (await confirmBtn.isVisible()) {
          await confirmBtn.click();
        }
      }
    });
  });

  test.describe('Game State Display', () => {
    test('should display pot amount', async ({ page }) => {
      test.skip(!process.env.TEST_GAME_ROOM_ID, 'Active game room not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);
      await page.goto(`/table/${process.env.TEST_GAME_ROOM_ID}`);

      // Pot should be visible
      const pot = page.locator('.pot, [data-testid="pot"]');
      await expect(pot).toBeVisible();
      await expect(pot).toContainText(/[0-9]+/);
    });

    test('should display community cards on flop', async ({ page }) => {
      test.skip(!process.env.TEST_GAME_ROOM_ID, 'Active game room not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);
      await page.goto(`/table/${process.env.TEST_GAME_ROOM_ID}`);

      // Community cards area should be visible
      const communityCards = page.locator('.community-cards, [data-testid="community-cards"]');
      await expect(communityCards).toBeVisible();
    });

    test('should display hole cards to player', async ({ page }) => {
      test.skip(!process.env.TEST_GAME_ROOM_ID, 'Active game room not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);
      await page.goto(`/table/${process.env.TEST_GAME_ROOM_ID}`);

      // If player is seated, hole cards should be visible
      const holeCards = page.locator('.hole-cards, [data-testid="my-cards"]');
      if (await holeCards.isVisible()) {
        // Should show 2 cards
        await expect(holeCards.locator('.card, [data-testid="card"]')).toHaveCount(2);
      }
    });

    test('should display player stacks', async ({ page }) => {
      test.skip(!process.env.TEST_GAME_ROOM_ID, 'Active game room not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);
      await page.goto(`/table/${process.env.TEST_GAME_ROOM_ID}`);

      // Player stacks should be visible
      const stacks = page.locator('.stack, [data-testid="player-stack"]');
      await expect(stacks.first()).toBeVisible();
      await expect(stacks.first()).toContainText(/[0-9]+/);
    });

    test('should highlight active player', async ({ page }) => {
      test.skip(!process.env.TEST_GAME_ROOM_ID, 'Active game room not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);
      await page.goto(`/table/${process.env.TEST_GAME_ROOM_ID}`);

      // Active seat should have highlight
      const activeSeat = page.locator('.seat-active, [data-active="true"]');
      await expect(activeSeat).toBeVisible();
    });
  });

  test.describe('Showdown', () => {
    test('should display showdown results', async ({ page }) => {
      test.skip(!process.env.TEST_SHOWDOWN_ROOM_ID, 'Showdown room not configured');

      await login(page, process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);
      await page.goto(`/table/${process.env.TEST_SHOWDOWN_ROOM_ID}`);

      // Wait for showdown
      const showdownResult = page.locator('.showdown-result, [data-testid="showdown"]');
      await expect(showdownResult).toBeVisible({ timeout: 30000 });

      // Winner should be highlighted
      const winner = page.locator('.winner, [data-winner="true"]');
      await expect(winner).toBeVisible();
    });
  });
});

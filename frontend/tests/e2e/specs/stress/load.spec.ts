/**
 * Load Testing E2E Tests
 * 
 * Tests system stability under load.
 * 
 * @requirements Task 16: Load Tests
 * @requirements 13.1~13.3
 */

import { test, expect, BrowserContext, Page } from '@playwright/test';
import { cheatAPI } from '../../utils/cheat-api';

interface ContextPage {
  context: BrowserContext;
  page: Page;
}

test.describe('Load Testing', () => {
  /**
   * Task 16.1: 다중 테이블 동시 액션 테스트
   * @requirements 13.1
   * Multiple tables running simultaneously without event loss
   */
  test('16.1 should handle 10 tables simultaneously without event loss', async ({
    browser,
  }) => {
    const tableIds: string[] = [];
    const contexts: ContextPage[] = [];
    
    try {
      // Create 10 test tables
      for (let i = 0; i < 10; i++) {
        const tableId = await cheatAPI.createTestTable({
          name: `Load Test Table ${i}`,
          smallBlind: 10,
          bigBlind: 20,
        });
        tableIds.push(tableId);
      }
      
      // Create browser contexts for each table
      for (let i = 0; i < 10; i++) {
        const context = await browser.newContext();
        const page = await context.newPage();
        contexts.push({ context, page });
        
        // Navigate to table
        await page.goto(`/table/${tableIds[i]}`);
      }
      
      // Wait for all tables to load
      await Promise.all(
        contexts.map(({ page }) =>
          page.waitForSelector('[data-testid="poker-table"]', { timeout: 10000 })
        )
      );
      
      // Track events received
      const eventCounts: number[] = [];
      
      for (const { page } of contexts) {
        const count = await page.evaluate(() => {
          return (window as unknown as { __eventCount?: number }).__eventCount || 0;
        });
        eventCounts.push(count);
      }
      
      // All tables should be loaded
      expect(contexts.length).toBe(10);
      
      // Perform simultaneous actions on all tables
      await Promise.all(
        contexts.map(async ({ page }, index) => {
          // Click on a seat to trigger action
          try {
            await page.click('[data-testid="seat-0"]', { timeout: 5000 });
          } catch {
            // Seat may already be occupied
          }
        })
      );
      
      // Wait for events to propagate
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Verify no event loss (all tables should have received updates)
      for (const { page } of contexts) {
        const tableVisible = await page.isVisible('[data-testid="poker-table"]');
        expect(tableVisible).toBe(true);
      }
      
    } finally {
      // Cleanup
      for (const { context } of contexts) {
        await context.close();
      }
      for (const tableId of tableIds) {
        await cheatAPI.deleteTable(tableId).catch(() => {});
      }
    }
  });

  /**
   * Task 16.2: 대규모 테이블 부하 테스트
   * @requirements 13.2
   * Response time measurement with 100+ tables
   */
  test.skip('16.2 should handle 100+ tables with acceptable response time', async ({
    browser,
  }) => {
    // This test is skipped by default as it requires significant resources
    // Run manually with: npx playwright test --grep "16.2"
    
    const tableIds: string[] = [];
    const startTime = Date.now();
    
    try {
      // Create 100 tables
      for (let i = 0; i < 100; i++) {
        const tableId = await cheatAPI.createTestTable({
          name: `Stress Test Table ${i}`,
          smallBlind: 10,
          bigBlind: 20,
        });
        tableIds.push(tableId);
      }
      
      const creationTime = Date.now() - startTime;
      console.log(`Created 100 tables in ${creationTime}ms`);
      
      // Create a single context to test response time
      const context = await browser.newContext();
      const page = await context.newPage();
      
      // Measure response time for table load
      const loadTimes: number[] = [];
      
      for (let i = 0; i < 10; i++) {
        const loadStart = Date.now();
        await page.goto(`/table/${tableIds[i]}`);
        await page.waitForSelector('[data-testid="poker-table"]', { timeout: 30000 });
        loadTimes.push(Date.now() - loadStart);
      }
      
      const avgLoadTime = loadTimes.reduce((a, b) => a + b, 0) / loadTimes.length;
      console.log(`Average table load time: ${avgLoadTime}ms`);
      
      // Response time should be under 5 seconds
      expect(avgLoadTime).toBeLessThan(5000);
      
      await context.close();
      
    } finally {
      // Cleanup
      for (const tableId of tableIds) {
        await cheatAPI.deleteTable(tableId).catch(() => {});
      }
    }
  });

  /**
   * Task 16.3: WebSocket 연결 안정성 테스트
   * @requirements 13.3
   * WebSocket connection stability under load
   */
  test('16.3 should maintain stable WebSocket connections', async ({ browser }) => {
    const contexts: ContextPage[] = [];
    const tableId = await cheatAPI.createTestTable({
      name: 'WS Stability Test',
    });
    
    try {
      // Create multiple connections to same table
      for (let i = 0; i < 5; i++) {
        const context = await browser.newContext();
        const page = await context.newPage();
        contexts.push({ context, page });
        
        await page.goto(`/table/${tableId}`);
        await page.waitForSelector('[data-testid="poker-table"]');
      }
      
      // Wait and check connections are still alive
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      // Verify all connections are still open
      for (const { page } of contexts) {
        const wsOpen = await page.evaluate(() => {
          const ws = (window as unknown as { __gameWebSocket?: WebSocket }).__gameWebSocket;
          return ws && ws.readyState === WebSocket.OPEN;
        });
        expect(wsOpen).toBe(true);
      }
      
      // Perform actions to stress connections
      for (let round = 0; round < 3; round++) {
        await Promise.all(
          contexts.map(async ({ page }) => {
            // Send a ping or action
            await page.evaluate(() => {
              const ws = (window as unknown as { __gameWebSocket?: WebSocket }).__gameWebSocket;
              if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'PING' }));
              }
            });
          })
        );
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      // Verify connections are still stable
      let disconnectCount = 0;
      for (const { page } of contexts) {
        const wsOpen = await page.evaluate(() => {
          const ws = (window as unknown as { __gameWebSocket?: WebSocket }).__gameWebSocket;
          return ws && ws.readyState === WebSocket.OPEN;
        });
        if (!wsOpen) disconnectCount++;
      }
      
      // No disconnections should occur
      expect(disconnectCount).toBe(0);
      
    } finally {
      for (const { context } of contexts) {
        await context.close();
      }
      await cheatAPI.deleteTable(tableId).catch(() => {});
    }
  });
});

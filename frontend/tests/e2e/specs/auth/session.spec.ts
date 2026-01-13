/**
 * Session Security E2E Tests
 * 
 * Tests token expiration and duplicate login handling.
 * 
 * @requirements 1.6, 1.7
 */

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/login.page';
import { LobbyPage } from '../../pages/lobby.page';
import { createTestUser } from '../../utils/test-users';

test.describe('Session Security', () => {
  /**
   * Task 4.5: 토큰 만료 처리 테스트
   * @requirements 1.6
   */
  test('4.5 should trigger re-authentication when token expires', async ({ page }) => {
    const user = await createTestUser('session');
    const loginPage = new LoginPage(page);
    
    await loginPage.goto();
    await loginPage.login(user.email, user.password);
    await page.waitForURL('**/lobby**');
    
    // Simulate token expiration by clearing storage
    await page.evaluate(() => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('token');
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('token');
    });
    
    // Trigger an API call that requires authentication
    await page.reload();
    
    // Should redirect to login page
    await page.waitForURL('**/login**', { timeout: 10000 });
    expect(page.url()).toContain('/login');
  });

  /**
   * Task 4.6: 중복 로그인 차단 테스트
   * @requirements 1.7
   */
  test('4.6 should terminate first session when logging in from second device', async ({
    browser,
  }) => {
    const user = await createTestUser('duplicate');
    
    // First session
    const context1 = await browser.newContext();
    const page1 = await context1.newPage();
    const loginPage1 = new LoginPage(page1);
    
    await loginPage1.goto();
    await loginPage1.login(user.email, user.password);
    await page1.waitForURL('**/lobby**');
    
    // Second session (same user, different browser)
    const context2 = await browser.newContext();
    const page2 = await context2.newPage();
    const loginPage2 = new LoginPage(page2);
    
    await loginPage2.goto();
    await loginPage2.login(user.email, user.password);
    await page2.waitForURL('**/lobby**');
    
    // First session should be terminated
    // Wait for WebSocket disconnect or redirect
    await page1.waitForTimeout(2000);
    
    // Try to perform an action in first session
    await page1.reload();
    
    // First session should be redirected to login or show session expired
    try {
      await page1.waitForURL('**/login**', { timeout: 10000 });
      // Successfully redirected to login
    } catch {
      // Check for session expired message
      const sessionExpired = await page1.getByText(/session|expired|로그아웃/i).isVisible();
      expect(sessionExpired).toBe(true);
    }
    
    // Cleanup
    await context1.close();
    await context2.close();
  });
});

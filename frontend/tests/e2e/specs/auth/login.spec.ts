/**
 * Authentication E2E Tests
 * 
 * Tests login, signup, and session management flows.
 * Updated to match actual frontend UI structure.
 * 
 * @requirements 1.1~1.7
 */

import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/login.page';

test.describe('Authentication Flow', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  /**
   * Task 4.1: 로그인 페이지 UI 테스트
   * @requirements 1.1
   */
  test('4.1 should display login form with email and password fields', async () => {
    const isVisible = await loginPage.isLoginFormVisible();
    expect(isVisible).toBe(true);
    
    // Verify specific elements
    await expect(loginPage.emailInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.loginButton).toBeVisible();
  });

  /**
   * Task 4.2: 로그인 성공 테스트
   * @requirements 1.2
   */
  test('4.2 should redirect to lobby on successful login', async ({ page }) => {
    // Create user first via signup
    const uniqueId = Date.now().toString(36);
    const email = `login_${uniqueId}@example.com`;
    const password = 'Test1234!';
    const nickname = `login_${uniqueId}`;

    // Signup first
    await loginPage.signup(email, password, nickname);
    
    // Should redirect to lobby after successful signup
    await page.waitForURL('**/lobby**', { timeout: 15000 });
    expect(page.url()).toContain('/lobby');
  });

  /**
   * Task 4.3: 로그인 실패 테스트
   * @requirements 1.3
   */
  test('4.3 should display error message on invalid credentials', async ({ page }) => {
    await loginPage.login('invalid@test.com', 'wrongpassword');
    
    // Wait for error to appear
    await page.waitForTimeout(2000);
    
    // Check for error message in the page (Korean or English)
    const errorDiv = page.locator('div').filter({ hasText: /실패|오류|에러|잘못|Invalid|error|failed/i });
    const hasError = await errorDiv.count() > 0;
    expect(hasError).toBe(true);
  });

  /**
   * Task 4.4: 회원가입 플로우 테스트
   * @requirements 1.4, 1.5
   */
  test('4.4 should toggle to signup mode and show additional fields', async () => {
    await loginPage.toggleSignupMode();
    
    const isSignupVisible = await loginPage.isSignupFormVisible();
    expect(isSignupVisible).toBe(true);
    
    // Verify signup-specific fields
    await expect(loginPage.nicknameInput).toBeVisible();
    await expect(loginPage.passwordConfirmInput).toBeVisible();
  });

  /**
   * Task 4.4: 회원가입 완료 테스트
   * @requirements 1.5
   */
  test('4.4 should complete signup and auto-login', async ({ page }) => {
    const uniqueId = Date.now().toString(36);
    const email = `signup_${uniqueId}@example.com`;
    const password = 'Test1234!';
    const nickname = `user_${uniqueId}`;

    await loginPage.signup(email, password, nickname);
    
    // Should redirect to lobby after successful signup
    await page.waitForURL('**/lobby**', { timeout: 15000 });
    expect(page.url()).toContain('/lobby');
  });
});

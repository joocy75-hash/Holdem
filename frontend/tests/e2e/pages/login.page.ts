/**
 * Login Page Object Model
 * 
 * Handles authentication UI interactions including
 * login, signup, and error handling.
 * 
 * Updated to match actual frontend UI structure.
 * 
 * @requirements 1.1~1.5
 */

import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  
  // Locators - using actual CSS selectors from the frontend
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly signupToggle: Locator;
  readonly errorMessage: Locator;
  
  // Signup-specific locators
  readonly nicknameInput: Locator;
  readonly passwordConfirmInput: Locator;

  constructor(page: Page) {
    this.page = page;
    
    // Login form elements - using actual selectors
    this.emailInput = page.locator('input[name="email"]');
    this.passwordInput = page.locator('input[name="password"]');
    this.loginButton = page.locator('button[type="submit"]');
    this.signupToggle = page.locator('button:has-text("회원가입"), button:has-text("계정이 없으신가요")');
    this.errorMessage = page.locator('.bg-\\[var\\(--error-bg\\)\\], [class*="error"]');
    
    // Signup form elements
    this.nicknameInput = page.locator('input[name="nickname"]');
    this.passwordConfirmInput = page.locator('input[name="confirmPassword"]');
  }

  /**
   * Navigate to login page
   */
  async goto(): Promise<void> {
    await this.page.goto('/login');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Login with email and password
   * @requirements 1.2
   */
  async login(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }

  /**
   * Toggle to signup mode
   * @requirements 1.4
   */
  async toggleSignupMode(): Promise<void> {
    // Click the toggle button that contains "회원가입" or "계정이 없으신가요"
    const toggleBtn = this.page.locator('button').filter({ hasText: /회원가입|계정이 없으신가요/ });
    await toggleBtn.click();
    // Wait for nickname field to appear
    await expect(this.nicknameInput).toBeVisible({ timeout: 5000 });
  }

  /**
   * Complete signup flow
   * @requirements 1.5
   */
  async signup(
    email: string,
    password: string,
    nickname: string
  ): Promise<void> {
    await this.toggleSignupMode();
    await this.emailInput.fill(email);
    await this.nicknameInput.fill(nickname);
    await this.passwordInput.fill(password);
    await this.passwordConfirmInput.fill(password);
    await this.loginButton.click(); // Same button, text changes to "회원가입"
  }

  /**
   * Get error message text
   * @requirements 1.3
   */
  async getErrorMessage(): Promise<string> {
    const errorDiv = this.page.locator('div').filter({ hasText: /실패|오류|에러|잘못/ }).first();
    if (await errorDiv.isVisible()) {
      return await errorDiv.textContent() || '';
    }
    return '';
  }

  /**
   * Check if login form is displayed
   * @requirements 1.1
   */
  async isLoginFormVisible(): Promise<boolean> {
    const emailVisible = await this.emailInput.isVisible();
    const passwordVisible = await this.passwordInput.isVisible();
    return emailVisible && passwordVisible;
  }

  /**
   * Check if signup form is displayed
   * @requirements 1.4
   */
  async isSignupFormVisible(): Promise<boolean> {
    const nicknameVisible = await this.nicknameInput.isVisible();
    const confirmVisible = await this.passwordConfirmInput.isVisible();
    return nicknameVisible && confirmVisible;
  }

  /**
   * Wait for redirect to lobby after successful login
   * @requirements 1.2
   */
  async waitForLobbyRedirect(): Promise<void> {
    await this.page.waitForURL('**/lobby**', { timeout: 10000 });
  }

  /**
   * Check if error message is displayed
   * @requirements 1.3
   */
  async hasError(): Promise<boolean> {
    const errorDiv = this.page.locator('div').filter({ hasText: /실패|오류|에러|잘못/ }).first();
    return await errorDiv.isVisible();
  }
}

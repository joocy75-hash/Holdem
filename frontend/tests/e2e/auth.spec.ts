import { test, expect } from '@playwright/test';

/**
 * Authentication E2E Tests
 * Tests user registration and login flows
 */
test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login form on auth page', async ({ page }) => {
    await expect(page.locator('form')).toBeVisible();
    await expect(page.getByPlaceholder('your@email.com')).toBeVisible();
    await expect(page.getByPlaceholder('••••••••')).toBeVisible();
  });

  test('should show validation errors for empty form submission', async ({ page }) => {
    // Click submit button (inside form) without filling form
    await page.locator('form').getByRole('button', { name: /로그인/i }).click();

    // Should show validation error message
    await expect(page.getByText('이메일과 비밀번호를 입력해주세요')).toBeVisible();
  });

  test('should switch between login and register forms', async ({ page }) => {
    // Find and click register tab button
    const registerTab = page.getByRole('button', { name: '회원가입' }).first();
    await registerTab.click();

    // Should show nickname field (only in register form)
    await expect(page.getByPlaceholder('게임에서 사용할 닉네임')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.getByPlaceholder('your@email.com').fill('invalid@test.com');
    await page.getByPlaceholder('••••••••').fill('wrongpassword123');
    await page.locator('form').getByRole('button', { name: /로그인/i }).click();

    // Should show error message from API ("Invalid email or password")
    await expect(page.getByText(/Invalid email or password|로그인에 실패/i)).toBeVisible({
      timeout: 10000,
    });
  });

  test('should redirect to lobby after successful login', async ({ page }) => {
    // This test requires a valid test account
    // Skip if no test credentials available
    test.skip(!process.env.TEST_EMAIL || !process.env.TEST_PASSWORD,
      'Test credentials not configured');

    await page.getByPlaceholder('your@email.com').fill(process.env.TEST_EMAIL!);
    await page.getByPlaceholder('••••••••').fill(process.env.TEST_PASSWORD!);
    await page.locator('form').getByRole('button', { name: /로그인/i }).click();

    // Should redirect to lobby
    await expect(page).toHaveURL(/\/lobby|\/rooms/);
  });
});

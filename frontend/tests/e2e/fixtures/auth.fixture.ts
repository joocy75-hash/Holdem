/**
 * Authentication Fixtures for E2E Tests
 * 
 * Provides pre-authenticated browser contexts for testing.
 * Handles login state management and session persistence.
 */

/* eslint-disable react-hooks/rules-of-hooks */

import { test as base, Page, BrowserContext } from '@playwright/test';
import { LoginPage } from '../pages/login.page.js';
import { cheatAPI } from '../utils/cheat-api.js';

/**
 * Generate a unique ID for test users
 */
function generateUniqueId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 8);
  return `${timestamp}${random}`;
}

export interface TestUser {
  id: string;
  email: string;
  password: string;
  nickname: string;
  balance: number;
}

/**
 * Extended test fixtures with authentication support
 */
export interface AuthFixtures {
  /** Pre-authenticated page ready for testing */
  authenticatedPage: Page;
  /** Test user credentials */
  testUser: TestUser;
  /** Login page instance */
  loginPage: LoginPage;
  /** Test table ID (auto-created and cleaned up) */
  tableId: string;
}

/**
 * Test fixture that provides an authenticated page
 */
export const test = base.extend<AuthFixtures>({
  tableId: async ({}, use) => {
    // Create a test table for each test
    const tableId = await cheatAPI.createTestTable({
      name: `Auth Test Table ${Date.now()}`,
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

  testUser: async ({}, use) => {
    const uniqueId = generateUniqueId();
    const user: TestUser = {
      id: uniqueId,
      email: `e2e_${uniqueId}@example.com`,
      password: 'Test1234!',
      nickname: `e2e_${uniqueId}`,
      balance: 10000,
    };
    await use(user);
  },

  loginPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await use(loginPage);
  },

  authenticatedPage: async ({ browser, testUser }, use) => {
    // Create a new browser context for isolation
    const context = await browser.newContext();
    const page = await context.newPage();
    
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    
    // Use signup to create and authenticate user
    await loginPage.signup(testUser.email, testUser.password, testUser.nickname);
    
    // Wait for successful redirect to lobby
    await page.waitForURL('**/lobby**', { timeout: 15000 });
    
    await use(page);
    
    // Cleanup
    await context.close();
  },
});

export { expect } from '@playwright/test';

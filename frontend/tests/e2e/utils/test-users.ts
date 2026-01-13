/**
 * Test User Management Utilities
 * 
 * Creates and manages test users for E2E testing.
 * Handles unique ID generation and initial balance setup.
 */

import axios, { AxiosError } from 'axios';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

export interface TestUser {
  id: string;
  email: string;
  password: string;
  nickname: string;
  balance: number;
}

/**
 * Generate a unique alphanumeric ID for test users
 * Uses timestamp + random string (no hyphens for nickname compatibility)
 * Backend nickname regex: ^[a-zA-Z0-9가-힣_]+$ (no hyphens allowed)
 */
function generateUniqueId(): string {
  const timestamp = Date.now().toString(36);
  const randomPart = Math.random().toString(36).substring(2, 10);
  return `${timestamp}${randomPart}`;
}

/**
 * Create a single test user
 * 
 * @param prefix - Prefix for the user's email/nickname
 * @param initialBalance - Initial chip balance (default: 10000)
 */
export async function createTestUser(
  prefix: string = 'test',
  initialBalance: number = 10000
): Promise<TestUser> {
  const uniqueId = generateUniqueId();
  const email = `${prefix}_${uniqueId}@example.com`;
  const password = 'Test1234!';
  const nickname = `${prefix}_${uniqueId}`;

  try {
    // Register the user via API (v1 endpoint)
    const response = await axios.post(`${API_BASE_URL}/api/v1/auth/register`, {
      email,
      password,
      nickname,
    });

    const userId = response.data.user?.id || uniqueId;

    // Set initial balance if needed (via admin/cheat API)
    if (initialBalance > 0) {
      try {
        await axios.post(
          `${API_BASE_URL}/api/dev/set-balance`,
          {
            user_id: userId,
            balance: initialBalance,
          },
          {
            headers: {
              'X-Dev-Key': process.env.DEV_API_KEY || 'dev-key',
            },
          }
        );
      } catch {
        // Balance API might not exist, continue anyway
        console.warn('Could not set initial balance via API');
      }
    }

    return {
      id: userId,
      email,
      password,
      nickname,
      balance: initialBalance,
    };
  } catch (error: unknown) {
    const axiosError = error as AxiosError<{ detail?: string; error?: { message?: string; code?: string } }>;
    
    // Log detailed error info for debugging
    if (axiosError.response) {
      console.error(`Registration failed [${axiosError.response.status}]:`, {
        email,
        nickname,
        detail: axiosError.response.data?.detail,
        error: axiosError.response.data?.error,
      });
    }
    
    // If user already exists (409), try to login instead
    if (axiosError.response?.status === 409) {
      try {
        const loginResponse = await axios.post(`${API_BASE_URL}/api/v1/auth/login`, {
          email,
          password,
        });
        return {
          id: loginResponse.data.user?.id || uniqueId,
          email,
          password,
          nickname,
          balance: initialBalance,
        };
      } catch {
        return {
          id: uniqueId,
          email,
          password,
          nickname,
          balance: initialBalance,
        };
      }
    }
    
    // If validation error (422), log and rethrow with more context
    if (axiosError.response?.status === 422) {
      const validationError = new Error(
        `User registration validation failed: ${JSON.stringify(axiosError.response.data)}`
      );
      throw validationError;
    }
    
    throw error;
  }
}

/**
 * Create multiple test users in parallel
 * 
 * @param count - Number of users to create (1-9)
 * @param prefix - Prefix for user emails/nicknames
 * @param initialBalance - Initial chip balance for each user
 */
export async function createTestUsers(
  count: number,
  prefix: string = 'player',
  initialBalance: number = 10000
): Promise<TestUser[]> {
  if (count < 1 || count > 9) {
    throw new Error('User count must be between 1 and 9');
  }

  // Create users in parallel for faster setup
  const userPromises = Array.from({ length: count }, (_, i) =>
    createTestUser(`${prefix}${i + 1}`, initialBalance)
  );

  return Promise.all(userPromises);
}

/**
 * Delete a test user (cleanup)
 * 
 * @param userId - User ID to delete
 */
export async function deleteTestUser(userId: string): Promise<void> {
  try {
    await axios.delete(`${API_BASE_URL}/api/dev/users/${userId}`, {
      headers: {
        'X-Dev-Key': process.env.DEV_API_KEY || 'dev-key',
      },
    });
  } catch {
    // Ignore errors during cleanup
    console.warn(`Could not delete test user ${userId}`);
  }
}

/**
 * Get user's current balance
 * 
 * @param userId - User ID
 */
export async function getUserBalance(userId: string): Promise<number> {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/users/${userId}/balance`,
      {
        headers: {
          'X-Dev-Key': process.env.DEV_API_KEY || 'dev-key',
        },
      }
    );
    return response.data.balance || 0;
  } catch {
    return 0;
  }
}

/**
 * Set user's balance (for testing specific scenarios)
 * 
 * @param userId - User ID
 * @param balance - New balance amount
 */
export async function setUserBalance(
  userId: string,
  balance: number
): Promise<void> {
  await axios.post(
    `${API_BASE_URL}/api/dev/set-balance`,
    {
      user_id: userId,
      balance,
    },
    {
      headers: {
        'X-Dev-Key': process.env.DEV_API_KEY || 'dev-key',
      },
    }
  );
}

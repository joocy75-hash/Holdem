'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { logger } from '@/lib/logger';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState('Ready');

  const handleLogin = async () => {
    logger.log('[Login] Button clicked');
    setStatus('Logging in...');
    
    if (!email || !password) {
      setError('이메일과 비밀번호를 입력하세요');
      setStatus('Validation failed');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      setStatus('Calling API...');
      
      // Direct fetch call
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      setStatus(`API response: ${response.status}`);

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Login failed');
      }

      const data = await response.json();
      setStatus('Login successful, getting user...');

      // Get user info
      const userResponse = await fetch(`${API_URL}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${data.access_token}` },
      });

      if (!userResponse.ok) {
        throw new Error('Failed to get user info');
      }

      const user = await userResponse.json();
      setStatus('Saving to localStorage...');

      // Save to localStorage
      const authData = {
        state: {
          user: {
            id: user.id,
            username: user.username,
            email: user.email,
            role: user.role,
          },
          accessToken: data.access_token,
          isAuthenticated: true,
        },
        version: 0,
      };
      localStorage.setItem('admin-auth', JSON.stringify(authData));

      setStatus('Redirecting...');
      
      // Redirect
      setTimeout(() => {
        window.location.href = '/';
      }, 500);

    } catch (err) {
      logger.error('[Login] Error:', err);
      setError(err instanceof Error ? err.message : '로그인 실패');
      setStatus('Error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">🎰 Admin Login</CardTitle>
          <p className="text-sm text-gray-500">Status: {status}</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">이메일</label>
              <input
                type="email"
                placeholder="admin@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">비밀번호</label>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>

            {error && (
              <p className="text-sm text-red-500 text-center">{error}</p>
            )}

            <button
              type="button"
              onClick={handleLogin}
              disabled={isLoading}
              className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? '로그인 중...' : '로그인'}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

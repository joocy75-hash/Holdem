'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';

export default function LoginPage() {
  const router = useRouter();
  const { login, signup, isLoading, error, clearError } = useAuthStore();

  const [isSignup, setIsSignup] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    nickname: '',
    confirmPassword: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    clearError();
    setLocalError(null);
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    try {
      if (isSignup) {
        if (formData.password !== formData.confirmPassword) {
          setLocalError('비밀번호가 일치하지 않습니다.');
          return;
        }
        if (formData.password.length < 8) {
          setLocalError('비밀번호는 8자 이상이어야 합니다.');
          return;
        }
        await signup(formData.email, formData.password, formData.nickname);
        router.push('/lobby');
      } else {
        await login(formData.email, formData.password);
        router.push('/lobby');
      }
    } catch (e) {
      // Error is handled by store
    }
  };

  const displayError = localError || error;

  return (
    <div className="mobile-container flex flex-col justify-center">
      <div className="card w-full max-w-md mx-auto animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gradient mb-1">POKER HOLDEM</h1>
          <p className="text-sm text-[var(--text-secondary)]">
            {isSignup ? '새 계정을 만들어보세요' : '로그인하여 게임을 시작하세요'}
          </p>
        </div>

        {/* Error Message */}
        {displayError && (
          <div className="mb-4 p-3 rounded-lg bg-[var(--error-bg)] text-[var(--error)] text-sm">
            {displayError}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-medium mb-1.5 text-[var(--text-secondary)]">
              이메일
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="input"
              placeholder="이메일을 입력하세요"
              required
            />
          </div>

          {isSignup && (
            <div className="animate-fade-in">
              <label className="block text-xs font-medium mb-1.5 text-[var(--text-secondary)]">
                닉네임
              </label>
              <input
                type="text"
                name="nickname"
                value={formData.nickname}
                onChange={handleChange}
                className="input"
                placeholder="닉네임을 입력하세요"
                required
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-medium mb-1.5 text-[var(--text-secondary)]">
              비밀번호
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="input"
              placeholder="비밀번호를 입력하세요"
              required
            />
          </div>

          {isSignup && (
            <div className="animate-fade-in">
              <label className="block text-xs font-medium mb-1.5 text-[var(--text-secondary)]">
                비밀번호 확인
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className={`input ${
                  formData.confirmPassword &&
                  formData.password !== formData.confirmPassword
                    ? 'input-error'
                    : ''
                }`}
                placeholder="비밀번호를 다시 입력하세요"
                required
              />
              {formData.confirmPassword &&
                formData.password !== formData.confirmPassword && (
                  <p className="mt-1 text-xs text-[var(--error)]">
                    비밀번호가 일치하지 않습니다
                  </p>
                )}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="btn btn-primary w-full mt-2"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <svg
                  className="animate-spin h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                처리 중...
              </span>
            ) : isSignup ? (
              '회원가입'
            ) : (
              '로그인'
            )}
          </button>
        </form>

        {/* Toggle */}
        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => {
              setIsSignup(!isSignup);
              clearError();
              setLocalError(null);
            }}
            className="text-[var(--primary)] hover:text-[var(--primary-light)] text-sm"
          >
            {isSignup
              ? '이미 계정이 있으신가요? 로그인'
              : '계정이 없으신가요? 회원가입'}
          </button>
        </div>

        {/* Decorative Cards */}
        <div className="mt-8 flex justify-center gap-2">
          {['♠', '♥', '♦', '♣'].map((suit, i) => (
            <div
              key={suit}
              className={`w-8 h-10 rounded flex items-center justify-center text-lg font-bold ${
                i % 2 === 0
                  ? 'bg-white text-black'
                  : 'bg-white text-[var(--suit-red)]'
              }`}
              style={{ animationDelay: `${i * 0.1}s` }}
            >
              {suit}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

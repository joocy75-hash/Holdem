import { Link } from 'react-router-dom';
import { User, LogOut, Settings, Wifi, WifiOff } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { Avatar } from '@/components/common/Avatar';
import { Button } from '@/components/common/Button';
import WebSocketClient from '@/lib/ws/WebSocketClient';
import { WSEventType } from '@/types/websocket';

interface HeaderProps {
  showBackButton?: boolean;
  title?: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  const { user, isAuthenticated, logout } = useAuthStore();
  const [showMenu, setShowMenu] = useState(false);
  const [connectionState, setConnectionState] = useState<'connected' | 'disconnected' | 'reconnecting'>('disconnected');

  // Track WebSocket connection state
  useEffect(() => {
    if (!isAuthenticated) {
      setConnectionState('disconnected');
      return;
    }

    const ws = WebSocketClient.getInstance();

    // Check initial state
    if (ws.isConnected()) {
      setConnectionState('connected');
    }

    const handleConnectionState = (payload: { state?: string }) => {
      if (payload.state === 'connected') {
        setConnectionState('connected');
      } else if (payload.state === 'reconnecting') {
        setConnectionState('reconnecting');
      } else if (payload.state === 'disconnected') {
        setConnectionState('disconnected');
      }
    };

    ws.on(WSEventType.CONNECTION_STATE, handleConnectionState);

    return () => {
      ws.off(WSEventType.CONNECTION_STATE, handleConnectionState);
    };
  }, [isAuthenticated]);

  return (
    <header className="sticky top-0 z-40 bg-bg-dark border-b border-surface">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo & Title */}
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2 text-xl font-bold text-text">
            <span className="text-2xl">🃏</span>
            <span className="hidden sm:inline">홀덤 1등</span>
          </Link>

          {title && (
            <div className="hidden sm:block pl-4 border-l border-surface">
              <h1 className="text-sm font-medium text-text">{title}</h1>
              {subtitle && <p className="text-xs text-text-muted">{subtitle}</p>}
            </div>
          )}
        </div>

        {/* Navigation & User */}
        {isAuthenticated && user ? (
          <div className="flex items-center gap-4">
            {/* Connection Status Indicator */}
            <div
              data-testid="connection-status"
              data-connected={connectionState === 'connected' ? 'true' : 'false'}
              className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${
                connectionState === 'connected'
                  ? 'bg-success/20 text-success'
                  : connectionState === 'reconnecting'
                  ? 'bg-warning/20 text-warning'
                  : 'bg-danger/20 text-danger'
              }`}
            >
              {connectionState === 'connected' ? (
                <Wifi className="w-3 h-3" />
              ) : (
                <WifiOff className="w-3 h-3" />
              )}
              <span className="hidden sm:inline">
                {connectionState === 'connected'
                  ? '연결됨'
                  : connectionState === 'reconnecting'
                  ? '재연결 중...'
                  : '연결 끊김'}
              </span>
            </div>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="flex items-center gap-2 p-1.5 rounded-full hover:bg-surface transition-colors"
              >
                <Avatar name={user.nickname} src={user.avatarUrl} size="sm" />
                <span className="hidden sm:inline text-sm text-text">{user.nickname}</span>
              </button>

              {showMenu && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowMenu(false)}
                  />
                  <div className="absolute right-0 top-full mt-2 w-48 bg-surface rounded-card shadow-modal z-20">
                    <div className="p-2">
                      <Link
                        to="/profile"
                        className="flex items-center gap-2 px-3 py-2 text-sm text-text rounded hover:bg-bg transition-colors"
                        onClick={() => setShowMenu(false)}
                      >
                        <User className="w-4 h-4" />
                        프로필
                      </Link>
                      <Link
                        to="/settings"
                        className="flex items-center gap-2 px-3 py-2 text-sm text-text rounded hover:bg-bg transition-colors"
                        onClick={() => setShowMenu(false)}
                      >
                        <Settings className="w-4 h-4" />
                        설정
                      </Link>
                      <hr className="my-2 border-bg" />
                      <button
                        onClick={() => {
                          logout();
                          setShowMenu(false);
                        }}
                        className="flex items-center gap-2 px-3 py-2 text-sm text-danger rounded hover:bg-bg transition-colors w-full"
                      >
                        <LogOut className="w-4 h-4" />
                        로그아웃
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link to="/auth/login">
              <Button variant="ghost" size="sm">
                로그인
              </Button>
            </Link>
            <Link to="/auth/register">
              <Button variant="primary" size="sm">
                회원가입
              </Button>
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}

import { WSEventType, type WSMessage } from '@/types/websocket';

type EventCallback<T = unknown> = (payload: T) => void;

interface ReconnectConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
}

const DEFAULT_RECONNECT_CONFIG: ReconnectConfig = {
  maxRetries: 10,
  baseDelay: 1000,
  maxDelay: 30000,
};

// Heartbeat configuration for connection health monitoring
const HEARTBEAT_CONFIG = {
  interval: 7000,       // 7초 base interval
  jitter: 400,          // ±400ms jitter to prevent thundering herd
  timeout: 15000,       // 15초 timeout - no PONG received
  maxMissedPongs: 3,    // 3번 연속 PONG 누락 시 reconnect
};

// Recovery state interface
interface RecoveryState {
  tableId: string | null;
  stateVersion: number;
  lastActionId: string | null;
}

export class WebSocketClient {
  private static instance: WebSocketClient | null = null;
  private ws: WebSocket | null = null;
  private url: string = '';
  private token: string = '';
  private authenticated: boolean = false;
  private eventHandlers: Map<string, Set<EventCallback>> = new Map();
  private reconnectConfig: ReconnectConfig;
  private reconnectAttempts: number = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private pongTimeoutTimer: ReturnType<typeof setTimeout> | null = null;
  private messageQueue: WSMessage[] = [];
  private isConnecting: boolean = false;
  private lastPongTime: number = 0;
  private missedPongCount: number = 0;

  // Recovery state tracking
  private recoveryState: RecoveryState = {
    tableId: null,
    stateVersion: 0,
    lastActionId: null,
  };
  private isRecovering: boolean = false;

  private constructor(config?: Partial<ReconnectConfig>) {
    this.reconnectConfig = { ...DEFAULT_RECONNECT_CONFIG, ...config };
  }

  static getInstance(config?: Partial<ReconnectConfig>): WebSocketClient {
    if (!WebSocketClient.instance) {
      WebSocketClient.instance = new WebSocketClient(config);
    }
    return WebSocketClient.instance;
  }

  /**
   * Connect to WebSocket server with token-based authentication.
   *
   * Security: Token is sent as first message after connection,
   * not in URL query parameters (which could be logged).
   *
   * @param url WebSocket URL (without token query param)
   * @param token JWT access token for authentication
   */
  connect(url: string, token?: string): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;
    }

    // Store URL without token for reconnection
    // Remove any existing token query param for backwards compatibility
    const urlObj = new URL(url, window.location.origin);
    urlObj.searchParams.delete('token');
    this.url = urlObj.toString();

    // Use provided token or keep existing
    if (token) {
      this.token = token;
    }

    this.isConnecting = true;
    this.authenticated = false;

    try {
      this.ws = new WebSocket(this.url);
      this.setupEventListeners();
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  /**
   * Update the authentication token (e.g., after token refresh).
   */
  setToken(token: string): void {
    this.token = token;
  }

  private setupEventListeners(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected, sending auth message');
      this.isConnecting = false;

      // Send AUTH message as first message (security: token not in URL)
      if (this.token) {
        this.sendAuthMessage();
      } else {
        console.error('WebSocket: No token available for authentication');
        this.ws?.close(4001, 'No authentication token');
        return;
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      this.stopHeartbeat();
      this.isConnecting = false;
      this.authenticated = false;

      if (!event.wasClean) {
        this.emit(WSEventType.CONNECTION_STATE, { state: 'reconnecting' });
        this.scheduleReconnect();
      } else {
        this.emit(WSEventType.CONNECTION_STATE, { state: 'disconnected' });
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
  }

  /**
   * Send AUTH message to server for authentication.
   * This is called automatically after connection is established.
   */
  private sendAuthMessage(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    const authMessage = {
      type: 'AUTH',
      ts: Date.now(),
      traceId: crypto.randomUUID(),
      payload: {
        token: this.token,
      },
      version: 1,
    };

    try {
      this.ws.send(JSON.stringify(authMessage));
      console.log('WebSocket AUTH message sent');
    } catch (error) {
      console.error('Failed to send AUTH message:', error);
      this.ws.close(4001, 'Failed to authenticate');
    }
  }

  private handleMessage(message: WSMessage): void {
    // Handle PONG - reset timeout and missed count
    if (message.type === WSEventType.PONG) {
      this.handlePong();
      return;
    }

    // Handle CONNECTION_STATE for auth completion
    if (message.type === WSEventType.CONNECTION_STATE) {
      const payload = message.payload as { state?: string };
      if (payload?.state === 'connected') {
        console.log('WebSocket authenticated successfully');
        this.authenticated = true;
        const wasReconnecting = this.reconnectAttempts > 0;
        this.reconnectAttempts = 0;
        this.missedPongCount = 0;
        this.lastPongTime = Date.now();
        this.startHeartbeat();
        this.flushMessageQueue();

        // If this was a reconnection, request state recovery
        if (wasReconnecting && this.recoveryState.tableId) {
          this.requestRecovery();
        }
      }
    }

    // Handle RECOVERY_RESPONSE
    if (message.type === WSEventType.RECOVERY_RESPONSE) {
      this.isRecovering = false;
      const payload = message.payload as { success: boolean; recoveredState?: unknown };
      if (payload.success) {
        console.log('State recovery successful');
      } else {
        console.warn('State recovery failed');
      }
    }

    // Emit to registered handlers
    this.emit(message.type, message.payload);
  }

  /**
   * Handle PONG response from server.
   * Reset timeout and missed pong count.
   */
  private handlePong(): void {
    this.lastPongTime = Date.now();
    this.missedPongCount = 0;
    this.clearPongTimeout();
  }

  /**
   * Start heartbeat with jitter to prevent thundering herd.
   * Uses HEARTBEAT_CONFIG for timing settings.
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();

    const scheduleNextPing = () => {
      // Add jitter: random value between -jitter and +jitter
      const jitter = (Math.random() * 2 - 1) * HEARTBEAT_CONFIG.jitter;
      const interval = HEARTBEAT_CONFIG.interval + jitter;

      this.pingInterval = setTimeout(() => {
        this.sendPing();
        scheduleNextPing();
      }, interval);
    };

    scheduleNextPing();
  }

  /**
   * Send PING and set up timeout for PONG response.
   */
  private sendPing(): void {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      return;
    }

    this.send({ type: WSEventType.PING, payload: {} });

    // Set up timeout for PONG response
    this.clearPongTimeout();
    this.pongTimeoutTimer = setTimeout(() => {
      this.handlePongTimeout();
    }, HEARTBEAT_CONFIG.timeout);
  }

  /**
   * Handle PONG timeout - increment missed count and potentially reconnect.
   */
  private handlePongTimeout(): void {
    this.missedPongCount++;
    console.warn(`PONG timeout - missed ${this.missedPongCount}/${HEARTBEAT_CONFIG.maxMissedPongs}`);

    if (this.missedPongCount >= HEARTBEAT_CONFIG.maxMissedPongs) {
      console.error('Max missed PONGs reached, reconnecting...');
      this.emit(WSEventType.CONNECTION_STATE, { state: 'reconnecting' });

      // Force close and reconnect
      if (this.ws) {
        this.ws.close(4000, 'Heartbeat timeout');
      }
    }
  }

  /**
   * Clear the PONG timeout timer.
   */
  private clearPongTimeout(): void {
    if (this.pongTimeoutTimer) {
      clearTimeout(this.pongTimeoutTimer);
      this.pongTimeoutTimer = null;
    }
  }

  /**
   * Stop heartbeat completely.
   */
  private stopHeartbeat(): void {
    if (this.pingInterval) {
      clearTimeout(this.pingInterval);
      this.pingInterval = null;
    }
    this.clearPongTimeout();
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.reconnectConfig.maxRetries) {
      console.error('Max reconnection attempts reached');
      this.emit(WSEventType.CONNECTION_STATE, { state: 'disconnected' });
      return;
    }

    const delay = Math.min(
      this.reconnectConfig.baseDelay * Math.pow(2, this.reconnectAttempts),
      this.reconnectConfig.maxDelay
    );

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect(this.url);
    }, delay);
  }

  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.sendRaw(message);
      }
    }
  }

  private sendRaw(message: WSMessage): boolean {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      return false;
    }

    try {
      this.ws.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      return false;
    }
  }

  send<T>(data: { type: string; payload: T; requestId?: string }): void {
    const message: WSMessage<T> = {
      type: data.type as WSEventType,
      ts: Date.now(),
      traceId: crypto.randomUUID(),
      requestId: data.requestId,
      payload: data.payload,
      version: 1,
    };

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.sendRaw(message);
    } else {
      // Queue message for sending after reconnect (limit to 100 messages)
      if (this.messageQueue.length < 100) {
        this.messageQueue.push(message as WSMessage);
      } else {
        console.warn('WebSocket message queue full, dropping message');
      }
    }
  }

  on<T>(eventType: string, callback: EventCallback<T>): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }
    this.eventHandlers.get(eventType)!.add(callback as EventCallback);
  }

  off<T>(eventType: string, callback?: EventCallback<T>): void {
    if (!callback) {
      this.eventHandlers.delete(eventType);
    } else {
      this.eventHandlers.get(eventType)?.delete(callback as EventCallback);
    }
  }

  private emit<T>(eventType: string, payload: T): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.forEach((handler) => handler(payload));
    }
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.messageQueue = [];
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  isAuthenticated(): boolean {
    return this.authenticated;
  }

  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  /**
   * Update recovery state for reconnection.
   * Call this when subscribing to a table or receiving state updates.
   */
  updateRecoveryState(tableId: string | null, stateVersion?: number, lastActionId?: string): void {
    this.recoveryState = {
      tableId,
      stateVersion: stateVersion ?? this.recoveryState.stateVersion,
      lastActionId: lastActionId ?? this.recoveryState.lastActionId,
    };
  }

  /**
   * Get current recovery state.
   */
  getRecoveryState(): RecoveryState {
    return { ...this.recoveryState };
  }

  /**
   * Clear recovery state (e.g., when leaving a table).
   */
  clearRecoveryState(): void {
    this.recoveryState = {
      tableId: null,
      stateVersion: 0,
      lastActionId: null,
    };
  }

  /**
   * Request state recovery from server after reconnection.
   */
  private requestRecovery(): void {
    if (this.isRecovering || !this.recoveryState.tableId) {
      return;
    }

    console.log('Requesting state recovery for table:', this.recoveryState.tableId);
    this.isRecovering = true;

    this.send({
      type: WSEventType.RECOVERY_REQUEST,
      payload: {
        tableId: this.recoveryState.tableId,
        lastStateVersion: this.recoveryState.stateVersion,
        lastActionId: this.recoveryState.lastActionId,
      },
    });
  }
}

export default WebSocketClient;

/**
 * WebSocket Inspector for E2E Testing
 * 
 * Intercepts and inspects WebSocket messages for:
 * - Security testing (card exposure)
 * - Message ordering verification
 * - Idempotency testing
 */

import { Page } from '@playwright/test';

export interface WSMessage {
  type: string;
  ts: number;
  traceId: string;
  requestId?: string;
  payload: Record<string, unknown>;
  version: string;
}

export interface WSInspectorOptions {
  /** Filter messages by type */
  filterTypes?: string[];
  /** Maximum messages to store */
  maxMessages?: number;
}

interface RawWSMessage {
  direction: 'incoming' | 'outgoing';
  timestamp: number;
  data: WSMessage;
}

interface PlayerData {
  position: number;
  holeCards?: unknown[];
}

// Extend Window interface for WebSocket inspector
declare global {
  interface Window {
    __wsMessages?: RawWSMessage[];
    __wsInspector?: {
      getMessages: () => RawWSMessage[];
      clear: () => void;
    };
  }
}

/**
 * WebSocket message inspector
 */
export class WSInspector {
  private messages: WSMessage[] = [];
  private options: WSInspectorOptions;
  private isAttached: boolean = false;

  constructor(options: WSInspectorOptions = {}) {
    this.options = {
      maxMessages: options.maxMessages || 1000,
      filterTypes: options.filterTypes,
    };
  }

  /**
   * Attach inspector to page
   */
  async attach(page: Page): Promise<void> {
    if (this.isAttached) return;

    // Inject WebSocket interceptor
    await page.addInitScript(() => {
      const originalWebSocket = window.WebSocket;
      const messages: RawWSMessage[] = [];
      
      window.__wsMessages = messages;
      window.__wsInspector = {
        getMessages: () => messages,
        clear: () => { messages.length = 0; },
      };

      class InterceptedWebSocket extends originalWebSocket {
        constructor(url: string | URL, protocols?: string | string[]) {
          super(url, protocols);
          
          this.addEventListener('message', (event) => {
            try {
              const data = JSON.parse(event.data);
              messages.push({
                direction: 'incoming',
                timestamp: Date.now(),
                data,
              });
            } catch {
              // Non-JSON message
            }
          });

          const originalSend = this.send.bind(this);
          this.send = (data: string | ArrayBufferLike | Blob | ArrayBufferView) => {
            try {
              const parsed = JSON.parse(data as string);
              messages.push({
                direction: 'outgoing',
                timestamp: Date.now(),
                data: parsed,
              });
            } catch {
              // Non-JSON message
            }
            return originalSend(data);
          };
        }
      }

      (window as unknown as { WebSocket: typeof InterceptedWebSocket }).WebSocket = InterceptedWebSocket;
    });

    this.isAttached = true;
  }

  /**
   * Get all captured messages
   */
  async getMessages(page: Page): Promise<WSMessage[]> {
    const rawMessages = await page.evaluate(() => {
      return window.__wsInspector?.getMessages() || [];
    });

    return rawMessages
      .filter((m: RawWSMessage) => m.direction === 'incoming')
      .map((m: RawWSMessage) => m.data)
      .filter((m: WSMessage) => {
        if (!this.options.filterTypes) return true;
        return this.options.filterTypes.includes(m.type);
      });
  }

  /**
   * Get outgoing messages
   */
  async getOutgoingMessages(page: Page): Promise<WSMessage[]> {
    const rawMessages = await page.evaluate(() => {
      return window.__wsInspector?.getMessages() || [];
    });

    return rawMessages
      .filter((m: RawWSMessage) => m.direction === 'outgoing')
      .map((m: RawWSMessage) => m.data);
  }

  /**
   * Clear captured messages
   */
  async clear(page: Page): Promise<void> {
    await page.evaluate(() => {
      window.__wsInspector?.clear();
    });
  }

  /**
   * Check if any message contains hole cards for other players
   * @requirements 11.4 - Security test
   */
  async hasExposedHoleCards(
    page: Page,
    myPosition: number
  ): Promise<boolean> {
    const messages = await this.getMessages(page);
    
    for (const msg of messages) {
      if (msg.type === 'TABLE_SNAPSHOT' || msg.type === 'TABLE_STATE_UPDATE') {
        const players = (msg.payload?.players as PlayerData[]) || [];
        for (const player of players) {
          if (player.position !== myPosition && player.holeCards && player.holeCards.length > 0) {
            // Found exposed hole cards for another player
            return true;
          }
        }
      }
    }
    
    return false;
  }

  /**
   * Get messages with specific type
   */
  async getMessagesByType(page: Page, type: string): Promise<WSMessage[]> {
    const messages = await this.getMessages(page);
    return messages.filter((m) => m.type === type);
  }

  /**
   * Check for duplicate action IDs (idempotency test)
   * @requirements 11.3
   */
  async hasDuplicateActionIds(page: Page): Promise<boolean> {
    const outgoing = await this.getOutgoingMessages(page);
    const actionIds = new Set<string>();
    
    for (const msg of outgoing) {
      if (msg.type === 'ACTION_REQUEST' && msg.requestId) {
        if (actionIds.has(msg.requestId)) {
          return true;
        }
        actionIds.add(msg.requestId);
      }
    }
    
    return false;
  }

  /**
   * Verify message ordering by sequence numbers
   * @requirements 12.3
   */
  async verifyMessageOrdering(page: Page): Promise<boolean> {
    const messages = await this.getMessages(page);
    let lastVersion = -1;
    
    for (const msg of messages) {
      const version = (msg.payload?.stateVersion as number) ?? undefined;
      if (version !== undefined) {
        if (version < lastVersion) {
          return false; // Out of order
        }
        lastVersion = version;
      }
    }
    
    return true;
  }

  /**
   * Wait for specific message type
   */
  async waitForMessage(
    page: Page,
    type: string,
    timeout: number = 10000
  ): Promise<WSMessage | null> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      const messages = await this.getMessagesByType(page, type);
      if (messages.length > 0) {
        return messages[messages.length - 1];
      }
      await page.waitForTimeout(100);
    }
    
    return null;
  }
}

// Singleton instance
export const wsInspector = new WSInspector();

// Export class as WebSocketInspector for backward compatibility
export { WSInspector as WebSocketInspector };

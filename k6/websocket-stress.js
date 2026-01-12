/**
 * k6 WebSocket Stress Test for Texas Hold'em Poker Backend
 * 
 * Phase 7: WebSocket-focused load testing
 * Target: 500-700 concurrent WebSocket connections
 * 
 * This test focuses specifically on WebSocket performance:
 * - Connection establishment
 * - Message latency
 * - Pub/Sub broadcast performance
 * - Reconnection handling
 * 
 * Usage:
 *   k6 run k6/websocket-stress.js
 *   k6 run k6/websocket-stress.js --vus 200 --duration 10m
 */

import ws from 'k6/ws';
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { randomString, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// =============================================================================
// Configuration
// =============================================================================

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const WS_URL = __ENV.WS_URL || 'ws://localhost:8000/ws';

export const options = {
  stages: [
    { duration: '30s', target: 100 },  // Ramp up
    { duration: '1m', target: 200 },
    { duration: '2m', target: 300 },
    { duration: '2m', target: 400 },
    { duration: '3m', target: 500 },
    { duration: '5m', target: 500 },   // Sustained load
    { duration: '1m', target: 600 },   // Peak load
    { duration: '2m', target: 600 },
    { duration: '1m', target: 0 },     // Ramp down
  ],
  thresholds: {
    ws_connecting: ['p(95)<2000'],
    ws_session_duration: ['p(95)>30000'],
    ws_msgs_received: ['count>0'],
    ws_connect_success: ['rate>0.95'],
    ws_message_latency: ['p(95)<100'],
    ws_ping_latency: ['p(95)<50'],
  },
};

// =============================================================================
// Custom Metrics
// =============================================================================

const wsConnectSuccess = new Rate('ws_connect_success');
const wsMessageLatency = new Trend('ws_message_latency');
const wsPingLatency = new Trend('ws_ping_latency');
const wsMessagesReceived = new Counter('ws_messages_received');
const wsMessagesSent = new Counter('ws_messages_sent');
const wsErrors = new Counter('ws_errors');
const wsReconnects = new Counter('ws_reconnects');

// =============================================================================
// Helper Functions
// =============================================================================

function getTestToken() {
  // Login to get a token
  const user = {
    email: `wstest_${randomString(8)}@test.com`,
    password: 'TestPassword123!',
    nickname: `WSTest_${randomString(6)}`,
  };
  
  // Register
  http.post(
    `${BASE_URL}/api/v1/auth/register`,
    JSON.stringify(user),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  // Login
  const res = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ email: user.email, password: user.password }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  if (res.status === 200) {
    return res.json('access_token');
  }
  return null;
}

function createMessage(type, payload = {}) {
  return JSON.stringify({
    type: type,
    ts: Date.now(),
    traceId: randomString(16),
    requestId: randomString(12),
    payload: payload,
    version: 'v1',
  });
}

// =============================================================================
// Main Test Function
// =============================================================================

export default function() {
  const token = getTestToken();
  if (!token) {
    wsErrors.add(1);
    console.error('Failed to get auth token');
    sleep(5);
    return;
  }
  
  const wsUrl = `${WS_URL}?token=${token}`;
  let messageCount = 0;
  let lastPingTime = 0;
  
  const res = ws.connect(wsUrl, {}, function(socket) {
    wsConnectSuccess.add(1);
    
    socket.on('open', function() {
      // Subscribe to lobby
      socket.send(createMessage('SUBSCRIBE_LOBBY'));
      wsMessagesSent.add(1);
      
      // Start ping interval
      lastPingTime = Date.now();
      socket.send(createMessage('PING'));
      wsMessagesSent.add(1);
    });
    
    socket.on('message', function(data) {
      messageCount++;
      wsMessagesReceived.add(1);
      
      try {
        const msg = JSON.parse(data);
        const now = Date.now();
        
        // Calculate message latency
        if (msg.ts) {
          const latency = now - msg.ts;
          wsMessageLatency.add(latency);
        }
        
        // Handle PONG
        if (msg.type === 'PONG') {
          const pingLatency = now - lastPingTime;
          wsPingLatency.add(pingLatency);
        }
        
        // Handle different message types
        switch (msg.type) {
          case 'LOBBY_SNAPSHOT':
            // Received lobby state
            check(msg, {
              'lobby has rooms': (m) => m.payload && Array.isArray(m.payload.rooms),
            });
            break;
            
          case 'LOBBY_UPDATE':
            // Room list updated
            break;
            
          case 'TABLE_SNAPSHOT':
            // Received table state
            check(msg, {
              'table has seats': (m) => m.payload && Array.isArray(m.payload.seats),
            });
            break;
            
          case 'TABLE_STATE_UPDATE':
            // Table state changed
            break;
            
          case 'ERROR':
            wsErrors.add(1);
            console.error('Server error:', msg.payload);
            break;
        }
      } catch (e) {
        wsErrors.add(1);
        console.error('Failed to parse message:', e);
      }
    });
    
    socket.on('error', function(e) {
      wsErrors.add(1);
      console.error('WebSocket error:', e);
    });
    
    socket.on('close', function() {
      // Connection closed
    });
    
    // Ping every 15 seconds
    socket.setInterval(function() {
      lastPingTime = Date.now();
      socket.send(createMessage('PING'));
      wsMessagesSent.add(1);
    }, 15000);
    
    // Occasionally subscribe to a random table
    socket.setInterval(function() {
      if (Math.random() < 0.1) {
        const tableId = randomString(36);
        socket.send(createMessage('SUBSCRIBE_TABLE', {
          tableId: tableId,
          mode: 'spectator',
        }));
        wsMessagesSent.add(1);
        
        // Unsubscribe after a bit
        socket.setTimeout(function() {
          socket.send(createMessage('UNSUBSCRIBE_TABLE', {
            tableId: tableId,
          }));
          wsMessagesSent.add(1);
        }, randomIntBetween(5000, 15000));
      }
    }, 10000);
    
    // Keep connection open for 30-60 seconds
    const sessionDuration = randomIntBetween(30000, 60000);
    socket.setTimeout(function() {
      socket.close();
    }, sessionDuration);
  });
  
  // Check connection result
  if (!res || res.status !== 101) {
    wsConnectSuccess.add(0);
    wsErrors.add(1);
  }
  
  // Small delay before next iteration
  sleep(randomIntBetween(1, 3));
}

// =============================================================================
// Setup & Teardown
// =============================================================================

export function setup() {
  console.log('Starting WebSocket stress test...');
  console.log(`WebSocket URL: ${WS_URL}`);
  
  // Verify server is reachable
  const res = http.get(`${BASE_URL}/health`);
  if (res.status !== 200) {
    throw new Error('Server health check failed');
  }
  
  return { startTime: Date.now() };
}

export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`WebSocket stress test completed in ${duration.toFixed(2)} seconds`);
}

/**
 * k6 Load Test Script for Texas Hold'em Poker Backend
 * 
 * Phase 7: Load Testing & Tuning
 * Target: 500 concurrent users, p95 < 200ms
 * 
 * Test Scenarios:
 * 1. Login flow
 * 2. Lobby browsing
 * 3. WebSocket connection
 * 4. Game actions
 * 
 * Usage:
 *   k6 run k6/load-test-500.js
 *   k6 run k6/load-test-500.js --vus 100 --duration 5m
 */

import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { randomString, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// =============================================================================
// Configuration
// =============================================================================

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const WS_URL = __ENV.WS_URL || 'ws://localhost:8000/ws';

// Test stages for gradual ramp-up
export const options = {
  stages: [
    { duration: '1m', target: 100 },   // Ramp up to 100 users
    { duration: '2m', target: 200 },   // Ramp up to 200 users
    { duration: '3m', target: 300 },   // Ramp up to 300 users
    { duration: '3m', target: 400 },   // Ramp up to 400 users
    { duration: '5m', target: 500 },   // Ramp up to 500 users
    { duration: '5m', target: 500 },   // Stay at 500 users
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    // HTTP thresholds
    http_req_duration: ['p(95)<200', 'p(99)<500'],
    http_req_failed: ['rate<0.01'],
    
    // WebSocket thresholds
    ws_connecting: ['p(95)<1000'],
    ws_msgs_received: ['count>0'],
    
    // Custom thresholds
    login_duration: ['p(95)<300'],
    action_duration: ['p(95)<150'],
    lobby_duration: ['p(95)<200'],
  },
};

// =============================================================================
// Custom Metrics
// =============================================================================

const loginDuration = new Trend('login_duration');
const actionDuration = new Trend('action_duration');
const lobbyDuration = new Trend('lobby_duration');
const wsConnectDuration = new Trend('ws_connect_duration');
const wsMessageLatency = new Trend('ws_message_latency');
const errorRate = new Rate('errors');
const wsErrors = new Counter('ws_errors');

// =============================================================================
// Helper Functions
// =============================================================================

function generateUser() {
  const id = randomString(8);
  return {
    email: `loadtest_${id}@test.com`,
    password: 'TestPassword123!',
    nickname: `Player_${id}`,
  };
}

function getAuthHeaders(token) {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };
}

// =============================================================================
// Test Scenarios
// =============================================================================

/**
 * Register a new user
 */
function registerUser(user) {
  const res = http.post(
    `${BASE_URL}/api/v1/auth/register`,
    JSON.stringify({
      email: user.email,
      password: user.password,
      nickname: user.nickname,
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  check(res, {
    'register status is 201 or 409': (r) => r.status === 201 || r.status === 409,
  });
  
  return res.status === 201;
}

/**
 * Login and get access token
 */
function login(user) {
  const start = Date.now();
  
  const res = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({
      email: user.email,
      password: user.password,
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  const duration = Date.now() - start;
  loginDuration.add(duration);
  
  const success = check(res, {
    'login status is 200': (r) => r.status === 200,
    'login has access_token': (r) => r.json('access_token') !== undefined,
  });
  
  if (!success) {
    errorRate.add(1);
    return null;
  }
  
  errorRate.add(0);
  return res.json('access_token');
}

/**
 * Get lobby room list
 */
function getLobby(token) {
  const start = Date.now();
  
  const res = http.get(
    `${BASE_URL}/api/v1/rooms`,
    { headers: getAuthHeaders(token) }
  );
  
  const duration = Date.now() - start;
  lobbyDuration.add(duration);
  
  check(res, {
    'lobby status is 200': (r) => r.status === 200,
    'lobby has rooms array': (r) => Array.isArray(r.json('rooms')),
  });
  
  return res.json('rooms') || [];
}

/**
 * Create a new room
 */
function createRoom(token) {
  const res = http.post(
    `${BASE_URL}/api/v1/rooms`,
    JSON.stringify({
      name: `LoadTest Room ${randomString(4)}`,
      small_blind: 1000,
      big_blind: 2000,
      min_buy_in: 40000,
      max_buy_in: 200000,
      max_seats: 6,
    }),
    { headers: getAuthHeaders(token) }
  );
  
  check(res, {
    'create room status is 201': (r) => r.status === 201,
  });
  
  return res.json('id');
}

/**
 * WebSocket connection test
 */
function testWebSocket(token) {
  const wsUrl = `${WS_URL}?token=${token}`;
  const start = Date.now();
  
  const res = ws.connect(wsUrl, {}, function(socket) {
    const connectDuration = Date.now() - start;
    wsConnectDuration.add(connectDuration);
    
    socket.on('open', function() {
      // Subscribe to lobby
      socket.send(JSON.stringify({
        type: 'SUBSCRIBE_LOBBY',
        ts: Date.now(),
        traceId: randomString(16),
        payload: {},
        version: 'v1',
      }));
    });
    
    socket.on('message', function(data) {
      try {
        const msg = JSON.parse(data);
        const latency = Date.now() - msg.ts;
        wsMessageLatency.add(latency);
        
        check(msg, {
          'ws message has type': (m) => m.type !== undefined,
        });
        
        // Handle different message types
        if (msg.type === 'LOBBY_SNAPSHOT') {
          // Successfully received lobby snapshot
          check(msg, {
            'lobby snapshot has rooms': (m) => m.payload && m.payload.rooms !== undefined,
          });
        }
      } catch (e) {
        wsErrors.add(1);
      }
    });
    
    socket.on('error', function(e) {
      wsErrors.add(1);
      console.error('WebSocket error:', e);
    });
    
    // Send ping every 15 seconds
    socket.setInterval(function() {
      socket.send(JSON.stringify({
        type: 'PING',
        ts: Date.now(),
        traceId: randomString(16),
        payload: {},
        version: 'v1',
      }));
    }, 15000);
    
    // Keep connection open for test duration
    socket.setTimeout(function() {
      socket.close();
    }, 60000);
  });
  
  check(res, {
    'ws connection successful': (r) => r && r.status === 101,
  });
}

/**
 * Simulate game action
 */
function simulateAction(token, tableId) {
  const start = Date.now();
  
  // This would be a WebSocket action in real scenario
  // For HTTP testing, we simulate with a status check
  const res = http.get(
    `${BASE_URL}/api/v1/tables/${tableId}/state`,
    { headers: getAuthHeaders(token) }
  );
  
  const duration = Date.now() - start;
  actionDuration.add(duration);
  
  check(res, {
    'action response ok': (r) => r.status === 200 || r.status === 404,
  });
}

// =============================================================================
// Main Test Function
// =============================================================================

export default function() {
  const user = generateUser();
  
  group('User Registration & Login', function() {
    // Try to register (may already exist)
    registerUser(user);
    sleep(0.5);
    
    // Login
    const token = login(user);
    if (!token) {
      console.error('Login failed, skipping rest of test');
      return;
    }
    
    sleep(1);
    
    group('Lobby Operations', function() {
      // Get lobby
      const rooms = getLobby(token);
      sleep(0.5);
      
      // Occasionally create a room
      if (Math.random() < 0.1) {
        createRoom(token);
        sleep(0.5);
      }
    });
    
    group('WebSocket Connection', function() {
      testWebSocket(token);
    });
    
    // Random sleep between iterations
    sleep(randomIntBetween(2, 5));
  });
}

// =============================================================================
// Setup & Teardown
// =============================================================================

export function setup() {
  console.log('Starting load test...');
  console.log(`Target: ${BASE_URL}`);
  console.log(`WebSocket: ${WS_URL}`);
  
  // Verify server is reachable
  const res = http.get(`${BASE_URL}/health`);
  if (res.status !== 200) {
    throw new Error('Server health check failed');
  }
  
  return { startTime: Date.now() };
}

export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`Load test completed in ${duration.toFixed(2)} seconds`);
}

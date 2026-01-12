# k6 Load Testing Scripts

Phase 7: Load Testing & Tuning for 300-500 concurrent users.

## Prerequisites

Install k6:
```bash
# macOS
brew install k6

# Linux
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Docker
docker pull grafana/k6
```

## Test Scripts

### 1. Full Load Test (`load-test-500.js`)

Complete load test simulating user journey:
- User registration & login
- Lobby browsing
- Room creation
- WebSocket connections

```bash
# Run with default settings (ramp up to 500 users)
k6 run k6/load-test-500.js

# Run with custom settings
k6 run k6/load-test-500.js --vus 100 --duration 5m

# Run against specific server
BASE_URL=http://staging.example.com:8000 WS_URL=ws://staging.example.com:8000/ws k6 run k6/load-test-500.js
```

### 2. WebSocket Stress Test (`websocket-stress.js`)

Focused WebSocket performance testing:
- Connection establishment
- Message latency
- Pub/Sub performance
- Sustained connections

```bash
# Run WebSocket stress test
k6 run k6/websocket-stress.js

# Run with more connections
k6 run k6/websocket-stress.js --vus 300 --duration 10m
```

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| HTTP p95 latency | < 200ms | < 500ms |
| HTTP error rate | < 1% | < 5% |
| WS connect time | < 1s | < 2s |
| WS message latency | < 100ms | < 200ms |
| WS ping latency | < 50ms | < 100ms |

## Test Stages

The default load test uses these stages:

| Stage | Duration | Target VUs | Purpose |
|-------|----------|------------|---------|
| 1 | 1m | 100 | Warm up |
| 2 | 2m | 200 | Ramp up |
| 3 | 3m | 300 | Increase load |
| 4 | 3m | 400 | Near target |
| 5 | 5m | 500 | Target load |
| 6 | 5m | 500 | Sustained |
| 7 | 2m | 0 | Ramp down |

## Output & Reporting

### Console Output
```bash
k6 run k6/load-test-500.js
```

### JSON Output
```bash
k6 run k6/load-test-500.js --out json=results.json
```

### InfluxDB + Grafana
```bash
k6 run k6/load-test-500.js --out influxdb=http://localhost:8086/k6
```

### Cloud (k6 Cloud)
```bash
k6 cloud k6/load-test-500.js
```

## Troubleshooting

### Connection Refused
- Ensure backend server is running
- Check firewall rules
- Verify BASE_URL and WS_URL

### High Error Rate
- Check server logs for errors
- Verify database connections
- Check Redis connectivity

### Slow Response Times
- Monitor database query times
- Check Redis latency
- Review connection pool settings

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| BASE_URL | http://localhost:8000 | Backend API URL |
| WS_URL | ws://localhost:8000/ws | WebSocket URL |

## Related Documentation

- [BACKEND_SCALE_WORKPLAN.md](../BACKEND_SCALE_WORKPLAN.md) - Full scaling plan
- [docs/51-observability.md](../docs/51-observability.md) - Monitoring setup

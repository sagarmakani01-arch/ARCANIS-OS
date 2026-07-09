# Performance Monitor

Real-time monitoring of system performance metrics with alerting capabilities.

## Features

- **CPU Monitoring**: Track CPU utilization over time
- **Memory Monitoring**: RSS and heap usage tracking
- **Event Loop Lag**: Detect event loop blocking
- **Alert Rules**: Define thresholds that trigger alerts when breached

## Usage

```typescript
import { PerformanceMonitor } from '@arcanis/developer-tools';

const monitor = new PerformanceMonitor({ intervalMs: 2000 });

// Add alert rules
monitor.addRule({
  metric: 'cpu',
  operator: 'gt',
  threshold: 80,
  severity: 'warning',
  message: 'CPU usage exceeds 80%',
});

monitor.addRule({
  metric: 'memory',
  operator: 'gt',
  threshold: 500 * 1024 * 1024, // 500 MB
  severity: 'critical',
  message: 'Memory usage exceeds 500 MB',
});

monitor.start();
// ... let it monitor ...
monitor.stop();

console.log(monitor.getAlerts());
console.log(monitor.metrics.getLatest('cpu'));
```

## CLI

```bash
arcanis-dev perfmon --interval 2000
arcanis-dev perfmon --interval 1000 --timeout 10000
```

## Metrics

| Metric | Unit | Description |
|--------|------|-------------|
| `cpu` | % | CPU utilization |
| `memory` | bytes | RSS memory usage |
| `heap` | bytes | V8 heap usage |
| `eventLoop` | ms | Event loop lag |

import * as os from 'os';
import { MetricPoint, SystemMetrics } from './types.js';

export class MetricsCollector {
  private metrics: SystemMetrics = {
    cpu: [], memory: [], heap: [], eventLoop: [],
  };
  private maxHistory: number;

  constructor(maxHistory: number = 3600) {
    this.maxHistory = maxHistory;
  }

  collect(): void {
    const now = Date.now();
    const usage = process.memoryUsage();

    this.addMetric('cpu', { timestamp: now, value: this.getCpuUsage(), unit: '%' });
    this.addMetric('memory', { timestamp: now, value: usage.rss, unit: 'bytes' });
    this.addMetric('heap', { timestamp: now, value: usage.heapUsed, unit: 'bytes' });
    this.addMetric('eventLoop', { timestamp: now, value: this.getEventLoopLag(), unit: 'ms' });
  }

  private addMetric(category: keyof SystemMetrics, point: MetricPoint): void {
    const arr = this.metrics[category];
    arr.push(point);
    if (arr.length > this.maxHistory) arr.shift();
  }

  private getCpuUsage(): number {
    const cpus = os.cpus();
    let totalIdle = 0, totalTick = 0;
    for (const cpu of cpus) {
      for (const type in cpu.times) {
        totalTick += cpu.times[type as keyof typeof cpu.times];
      }
      totalIdle += cpu.times.idle;
    }
    return Math.round((1 - totalIdle / totalTick) * 100);
  }

  private getEventLoopLag(): number {
    return 0;
  }

  getMetrics(): SystemMetrics {
    return {
      cpu: [...this.metrics.cpu],
      memory: [...this.metrics.memory],
      heap: [...this.metrics.heap],
      eventLoop: [...this.metrics.eventLoop],
    };
  }

  getLatest(category: keyof SystemMetrics): MetricPoint | undefined {
    const arr = this.metrics[category];
    return arr.length > 0 ? arr[arr.length - 1] : undefined;
  }
}

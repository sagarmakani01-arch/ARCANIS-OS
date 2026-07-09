import { MetricsCollector } from './metrics.js';
import { Alert, AlertRule, PerfMonConfig, SystemMetrics, MetricPoint } from './types.js';

export { MetricsCollector };
export type { Alert, AlertRule, PerfMonConfig, SystemMetrics, MetricPoint };

export class PerformanceMonitor {
  readonly metrics: MetricsCollector;
  private config: PerfMonConfig;
  private interval: ReturnType<typeof setInterval> | null = null;
  private alerts: Alert[] = [];
  private alertCounter = 0;

  constructor(config?: Partial<PerfMonConfig>) {
    this.config = {
      intervalMs: 1000,
      alertRules: [],
      historySize: 3600,
      ...config,
    };
    this.metrics = new MetricsCollector(this.config.historySize);
  }

  start(): void {
    if (this.interval) return;
    this.interval = setInterval(() => {
      this.metrics.collect();
      this.evaluateAlerts();
    }, this.config.intervalMs);
    console.log('[PerfMon] Monitoring started');
  }

  stop(): void {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
    console.log('[PerfMon] Monitoring stopped');
  }

  addRule(rule: AlertRule): void {
    this.config.alertRules.push(rule);
  }

  getAlerts(): Alert[] {
    return [...this.alerts];
  }

  private evaluateAlerts(): void {
    for (const rule of this.config.alertRules) {
      const latest = this.metrics.getLatest(rule.metric as keyof SystemMetrics);
      if (!latest) continue;
      let triggered = false;
      switch (rule.operator) {
        case 'gt': triggered = latest.value > rule.threshold; break;
        case 'lt': triggered = latest.value < rule.threshold; break;
        case 'gte': triggered = latest.value >= rule.threshold; break;
        case 'lte': triggered = latest.value <= rule.threshold; break;
      }
      if (triggered) {
        this.alerts.push({
          id: `alert_${++this.alertCounter}`,
          metric: rule.metric,
          severity: rule.severity,
          message: rule.message,
          threshold: rule.threshold,
          currentValue: latest.value,
          timestamp: Date.now(),
        });
      }
    }
  }
}

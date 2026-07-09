import { MetricsCollector } from './metrics.js';
import { Alert, AlertRule, PerfMonConfig, SystemMetrics, MetricPoint } from './types.js';
export { MetricsCollector };
export type { Alert, AlertRule, PerfMonConfig, SystemMetrics, MetricPoint };
export declare class PerformanceMonitor {
    readonly metrics: MetricsCollector;
    private config;
    private interval;
    private alerts;
    private alertCounter;
    constructor(config?: Partial<PerfMonConfig>);
    start(): void;
    stop(): void;
    addRule(rule: AlertRule): void;
    getAlerts(): Alert[];
    private evaluateAlerts;
}

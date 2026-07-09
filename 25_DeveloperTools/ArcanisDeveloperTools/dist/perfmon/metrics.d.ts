import { MetricPoint, SystemMetrics } from './types.js';
export declare class MetricsCollector {
    private metrics;
    private maxHistory;
    constructor(maxHistory?: number);
    collect(): void;
    private addMetric;
    private getCpuUsage;
    private getEventLoopLag;
    getMetrics(): SystemMetrics;
    getLatest(category: keyof SystemMetrics): MetricPoint | undefined;
}

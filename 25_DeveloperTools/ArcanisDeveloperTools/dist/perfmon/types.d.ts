export interface MetricPoint {
    timestamp: number;
    value: number;
    unit: string;
}
export interface SystemMetrics {
    cpu: MetricPoint[];
    memory: MetricPoint[];
    heap: MetricPoint[];
    eventLoop: MetricPoint[];
}
export interface Alert {
    id: string;
    metric: string;
    severity: 'critical' | 'warning' | 'info';
    message: string;
    threshold: number;
    currentValue: number;
    timestamp: number;
}
export interface AlertRule {
    metric: string;
    operator: 'gt' | 'lt' | 'gte' | 'lte';
    threshold: number;
    severity: 'critical' | 'warning' | 'info';
    message: string;
}
export interface PerfMonConfig {
    intervalMs: number;
    alertRules: AlertRule[];
    historySize: number;
}

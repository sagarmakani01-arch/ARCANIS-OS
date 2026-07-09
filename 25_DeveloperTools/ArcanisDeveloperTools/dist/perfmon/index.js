"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PerformanceMonitor = exports.MetricsCollector = void 0;
const metrics_js_1 = require("./metrics.js");
Object.defineProperty(exports, "MetricsCollector", { enumerable: true, get: function () { return metrics_js_1.MetricsCollector; } });
class PerformanceMonitor {
    metrics;
    config;
    interval = null;
    alerts = [];
    alertCounter = 0;
    constructor(config) {
        this.config = {
            intervalMs: 1000,
            alertRules: [],
            historySize: 3600,
            ...config,
        };
        this.metrics = new metrics_js_1.MetricsCollector(this.config.historySize);
    }
    start() {
        if (this.interval)
            return;
        this.interval = setInterval(() => {
            this.metrics.collect();
            this.evaluateAlerts();
        }, this.config.intervalMs);
        console.log('[PerfMon] Monitoring started');
    }
    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
        console.log('[PerfMon] Monitoring stopped');
    }
    addRule(rule) {
        this.config.alertRules.push(rule);
    }
    getAlerts() {
        return [...this.alerts];
    }
    evaluateAlerts() {
        for (const rule of this.config.alertRules) {
            const latest = this.metrics.getLatest(rule.metric);
            if (!latest)
                continue;
            let triggered = false;
            switch (rule.operator) {
                case 'gt':
                    triggered = latest.value > rule.threshold;
                    break;
                case 'lt':
                    triggered = latest.value < rule.threshold;
                    break;
                case 'gte':
                    triggered = latest.value >= rule.threshold;
                    break;
                case 'lte':
                    triggered = latest.value <= rule.threshold;
                    break;
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
exports.PerformanceMonitor = PerformanceMonitor;
//# sourceMappingURL=index.js.map
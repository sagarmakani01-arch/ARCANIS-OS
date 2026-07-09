// ArcanisCloud - Monitoring

import { EventEmitter } from 'events';
import { Metric, Alert, AlertCondition, AlertSeverity, AlertState, MetricType } from '../types.js';
import { generateId, generateAlertId } from '../utils.js';

export interface MonitoringOptions {
  retentionPeriod?: number;
  maxMetrics?: number;
  maxAlerts?: number;
}

export interface Dashboard {
  id: string;
  name: string;
  panels: DashboardPanel[];
  createdAt: Date;
}

export interface DashboardPanel {
  id: string;
  title: string;
  type: 'graph' | 'stat' | 'table' | 'heatmap';
  metrics: string[];
  position: { x: number; y: number; w: number; h: number };
}

export class MonitoringManager extends EventEmitter {
  private metrics: Metric[] = [];
  private alerts: Map<string, Alert> = new Map();
  private dashboards: Map<string, Dashboard> = new Map();
  private alertRules: Map<string, AlertCondition & { id: string; name: string; severity: AlertSeverity }> = new Map();
  private options: Required<MonitoringOptions>;

  constructor(options: MonitoringOptions = {}) {
    super();
    this.options = {
      retentionPeriod: options.retentionPeriod || 86400000,
      maxMetrics: options.maxMetrics || 100000,
      maxAlerts: options.maxAlerts || 10000,
    };
  }

  recordMetric(metric: Metric): void {
    this.metrics.push(metric);
    if (this.metrics.length > this.options.maxMetrics) {
      this.metrics.splice(0, this.metrics.length - this.options.maxMetrics);
    }
    this.emit('metric:record', metric);
    this.evaluateAlerts(metric);
  }

  recordMetrics(metrics: Metric[]): void {
    for (const m of metrics) this.recordMetric(m);
  }

  getMetrics(name: string, options?: { labels?: Record<string, string>; since?: Date; limit?: number }): Metric[] {
    let result = this.metrics.filter(m => m.name === name);
    if (options?.labels) {
      for (const [key, value] of Object.entries(options.labels)) {
        result = result.filter(m => m.labels[key] === value);
      }
    }
    if (options?.since) result = result.filter(m => m.timestamp >= options.since!);
    if (options?.limit) result = result.slice(-options.limit);
    return result;
  }

  createAlertRule(config: { name: string; condition: AlertCondition; severity: AlertSeverity }): { id: string; name: string; severity: AlertSeverity; condition: AlertCondition } {
    const id = generateId(12);
    this.alertRules.set(id, { id, ...config });
    this.emit('alertRule:create', { id, ...config });
    return { id, ...config };
  }

  async removeAlertRule(ruleId: string): Promise<void> {
    if (!this.alertRules.has(ruleId)) throw new Error(`Alert rule ${ruleId} not found`);
    this.alertRules.delete(ruleId);
  }

  private evaluateAlerts(metric: Metric): void {
    for (const rule of this.alertRules.values()) {
      if (rule.condition.metric !== metric.name) continue;

      let triggered = false;
      switch (rule.condition.operator) {
        case 'gt': triggered = metric.value > rule.condition.threshold; break;
        case 'lt': triggered = metric.value < rule.condition.threshold; break;
        case 'gte': triggered = metric.value >= rule.condition.threshold; break;
        case 'lte': triggered = metric.value <= rule.condition.threshold; break;
        case 'eq': triggered = metric.value === rule.condition.threshold; break;
      }

      if (triggered) {
        const existing = Array.from(this.alerts.values()).find(a => a.name === rule.name && a.state === 'firing');
        if (!existing) {
          const alert: Alert = {
            id: generateAlertId(), name: rule.name, severity: rule.severity, state: 'firing',
            condition: rule.condition, currentValue: metric.value, firedAt: new Date(),
            labels: metric.labels,
          };
          this.alerts.set(alert.id, alert);
          this.emit('alert:fire', alert);
        }
      }
    }
  }

  async resolveAlert(alertId: string): Promise<void> {
    const alert = this.alerts.get(alertId);
    if (!alert) throw new Error(`Alert ${alertId} not found`);
    alert.state = 'resolved';
    alert.resolvedAt = new Date();
    this.emit('alert:resolve', alert);
  }

  async silenceAlert(alertId: string): Promise<void> {
    const alert = this.alerts.get(alertId);
    if (!alert) throw new Error(`Alert ${alertId} not found`);
    alert.state = 'silenced';
    this.emit('alert:silence', alert);
  }

  listAlerts(filters?: { state?: AlertState; severity?: AlertSeverity }): Alert[] {
    let result = Array.from(this.alerts.values());
    if (filters?.state) result = result.filter(a => a.state === filters.state);
    if (filters?.severity) result = result.filter(a => a.severity === filters.severity);
    return result;
  }

  createDashboard(config: { name: string; panels: Omit<DashboardPanel, 'id'>[] }): Dashboard {
    const id = generateId(12);
    const panels = config.panels.map((p, i) => ({ ...p, id: `panel-${i}` }));
    const dashboard: Dashboard = { id, name: config.name, panels, createdAt: new Date() };
    this.dashboards.set(id, dashboard);
    this.emit('dashboard:create', dashboard);
    return dashboard;
  }

  getDashboard(dashboardId: string): Dashboard | undefined { return this.dashboards.get(dashboardId); }
  listDashboards(): Dashboard[] { return Array.from(this.dashboards.values()); }
  removeDashboard(dashboardId: string): void { this.dashboards.delete(dashboardId); }

  getMetricSummary(name: string): { count: number; min: number; max: number; avg: number; latest: number } | undefined {
    const metrics = this.metrics.filter(m => m.name === name);
    if (metrics.length === 0) return undefined;
    const values = metrics.map(m => m.value);
    return {
      count: values.length, min: Math.min(...values), max: Math.max(...values),
      avg: values.reduce((s, v) => s + v, 0) / values.length, latest: values[values.length - 1],
    };
  }

  getMetricCount(): number { return this.metrics.length; }
  getAlertCount(): number { return this.alerts.size; }
  getFiringAlertCount(): number { return Array.from(this.alerts.values()).filter(a => a.state === 'firing').length; }
  getDashboardCount(): number { return this.dashboards.size; }
}

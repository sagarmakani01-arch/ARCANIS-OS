import { describe, it, expect, beforeEach } from 'vitest';
import { MonitoringManager } from '../src/monitoring/monitoring-manager.js';

describe('MonitoringManager', () => {
  let monitoring: MonitoringManager;

  beforeEach(() => { monitoring = new MonitoringManager(); });

  describe('recordMetric', () => {
    it('should record a metric', () => {
      monitoring.recordMetric({ name: 'cpu', type: 'gauge', labels: {}, value: 50, timestamp: new Date() });
      expect(monitoring.getMetricCount()).toBe(1);
    });

    it('should emit metric:record event', () => {
      let emitted = false;
      monitoring.on('metric:record', () => { emitted = true; });
      monitoring.recordMetric({ name: 'test', type: 'counter', labels: {}, value: 1, timestamp: new Date() });
      expect(emitted).toBe(true);
    });
  });

  describe('getMetrics', () => {
    it('should get metrics by name', () => {
      monitoring.recordMetric({ name: 'cpu', type: 'gauge', labels: {}, value: 50, timestamp: new Date() });
      monitoring.recordMetric({ name: 'mem', type: 'gauge', labels: {}, value: 70, timestamp: new Date() });
      expect(monitoring.getMetrics('cpu')).toHaveLength(1);
    });

    it('should filter by labels', () => {
      monitoring.recordMetric({ name: 'cpu', type: 'gauge', labels: { host: 'a' }, value: 50, timestamp: new Date() });
      monitoring.recordMetric({ name: 'cpu', type: 'gauge', labels: { host: 'b' }, value: 60, timestamp: new Date() });
      expect(monitoring.getMetrics('cpu', { labels: { host: 'a' } })).toHaveLength(1);
    });
  });

  describe('alert rules', () => {
    it('should create alert rule', () => {
      const rule = monitoring.createAlertRule({ name: 'high-cpu', condition: { metric: 'cpu', operator: 'gt', threshold: 80, duration: 60 }, severity: 'warning' });
      expect(rule).toBeDefined();
    });

    it('should fire alert when threshold exceeded', () => {
      let fired = false;
      monitoring.on('alert:fire', () => { fired = true; });
      monitoring.createAlertRule({ name: 'alert', condition: { metric: 'cpu', operator: 'gt', threshold: 80, duration: 0 }, severity: 'critical' });
      monitoring.recordMetric({ name: 'cpu', type: 'gauge', labels: {}, value: 90, timestamp: new Date() });
      expect(fired).toBe(true);
    });
  });

  describe('dashboards', () => {
    it('should create dashboard', () => {
      const dash = monitoring.createDashboard({ name: 'Overview', panels: [{ title: 'CPU', type: 'graph', metrics: ['cpu'], position: { x: 0, y: 0, w: 6, h: 4 } }] });
      expect(dash).toBeDefined();
      expect(dash.name).toBe('Overview');
    });
  });

  describe('getMetricSummary', () => {
    it('should compute summary', () => {
      monitoring.recordMetric({ name: 'lat', type: 'gauge', labels: {}, value: 10, timestamp: new Date() });
      monitoring.recordMetric({ name: 'lat', type: 'gauge', labels: {}, value: 20, timestamp: new Date() });
      const summary = monitoring.getMetricSummary('lat');
      expect(summary).toBeDefined();
      expect(summary!.count).toBe(2);
      expect(summary!.min).toBe(10);
      expect(summary!.max).toBe(20);
    });
  });
});

import { describe, it, expect, beforeEach } from 'vitest';
import { AutoScaler } from '../src/autoscaler/auto-scaler.js';

describe('AutoScaler', () => {
  let scaler: AutoScaler;

  beforeEach(() => { scaler = new AutoScaler({ defaultCooldown: 0 }); });

  describe('createPolicy', () => {
    it('should create a policy', () => {
      const policy = scaler.createPolicy({ name: 'cpu-scale', serviceId: 'svc-1', minReplicas: 1, maxReplicas: 10, metrics: [{ type: 'cpu', target: 70, operator: 'avg' }], cooldown: 60 });
      expect(policy).toBeDefined();
      expect(policy.name).toBe('cpu-scale');
    });
  });

  describe('ingestMetric', () => {
    it('should accept metrics', () => {
      scaler.ingestMetric({ name: 'cpu', type: 'gauge', labels: {}, value: 80, timestamp: new Date() });
      expect(scaler.getMetricCount()).toBe(1);
    });
  });

  describe('evaluate', () => {
    it('should trigger scale up', async () => {
      scaler.createPolicy({ name: 'up', serviceId: 'svc-1', minReplicas: 1, maxReplicas: 5, metrics: [{ type: 'cpu', target: 70, operator: 'avg' }], cooldown: 0 });
      scaler.ingestMetric({ name: 'cpu', type: 'gauge', labels: {}, value: 85, timestamp: new Date() });
      const action = await scaler.evaluate('svc-1', 2);
      expect(action).toBeDefined();
      expect(action!.direction).toBe('up');
    });

    it('should trigger scale down', async () => {
      scaler.createPolicy({ name: 'down', serviceId: 'svc-1', minReplicas: 1, maxReplicas: 5, metrics: [{ type: 'cpu', target: 70, operator: 'avg' }], cooldown: 0 });
      scaler.ingestMetric({ name: 'cpu', type: 'gauge', labels: {}, value: 20, timestamp: new Date() });
      const action = await scaler.evaluate('svc-1', 3);
      expect(action).toBeDefined();
      expect(action!.direction).toBe('down');
    });

    it('should return undefined without policy', async () => {
      const action = await scaler.evaluate('unknown', 2);
      expect(action).toBeUndefined();
    });
  });

  describe('counts', () => {
    it('should track counts', () => {
      expect(scaler.getPolicyCount()).toBe(0);
      expect(scaler.getMetricCount()).toBe(0);
    });
  });
});

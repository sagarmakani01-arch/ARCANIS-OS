import { describe, it, expect, beforeEach } from 'vitest';
import { LoadBalancer } from '../src/loadbalancer/load-balancer.js';

describe('LoadBalancer', () => {
  let lb: LoadBalancer;

  beforeEach(() => {
    lb = new LoadBalancer({ algorithm: 'round-robin' });
    lb.addBackend('10.0.0.1', 80, 1);
    lb.addBackend('10.0.0.2', 80, 2);
    lb.addBackend('10.0.0.3', 80, 1);
  });

  describe('addBackend', () => {
    it('should add a backend', () => {
      const backends = lb.listBackends();
      expect(backends).toHaveLength(3);
    });

    it('should emit backend:add event', () => {
      let emitted = false;
      lb.on('backend:add', () => { emitted = true; });
      lb.addBackend('10.0.0.4', 80);
      expect(emitted).toBe(true);
    });
  });

  describe('removeBackend', () => {
    it('should remove a backend', () => {
      const backends = lb.listBackends();
      lb.removeBackend(backends[0].id);
      expect(lb.listBackends()).toHaveLength(2);
    });
  });

  describe('selectBackend', () => {
    it('should select a backend with round-robin', async () => {
      const b1 = await lb.selectBackend();
      const b2 = await lb.selectBackend();
      expect(b1).toBeDefined();
      expect(b2).toBeDefined();
    });

    it('should fail with no backends', async () => {
      const emptyLb = new LoadBalancer();
      expect(await emptyLb.selectBackend()).toBeUndefined();
    });
  });

  describe('weighted', () => {
    it('should select based on weights', async () => {
      const weightedLb = new LoadBalancer({ algorithm: 'weighted' });
      weightedLb.addBackend('10.0.0.1', 80, 10);
      weightedLb.addBackend('10.0.0.2', 80, 1);
      const selections = new Map<string, number>();
      for (let i = 0; i < 100; i++) {
        const b = await weightedLb.selectBackend();
        if (b) selections.set(b.id, (selections.get(b.id) || 0) + 1);
        if (b) weightedLb.releaseConnection(b.id);
      }
      expect(selections.size).toBe(2);
    });
  });

  describe('health check', () => {
    it('should run health checks', async () => {
      const result = await lb.runHealthCheck();
      expect(result.healthy.length).toBeGreaterThan(0);
    });
  });

  describe('counts', () => {
    it('should track counts', () => {
      expect(lb.getBackendCount()).toBe(3);
      expect(lb.getHealthyCount()).toBe(3);
      expect(lb.getTotalConnections()).toBe(0);
    });
  });
});

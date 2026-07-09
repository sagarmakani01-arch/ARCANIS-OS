import { describe, it, expect, beforeEach } from 'vitest';
import { ServiceDiscovery } from '../src/discovery/service-discovery.js';

describe('ServiceDiscovery', () => {
  let discovery: ServiceDiscovery;

  beforeEach(() => { discovery = new ServiceDiscovery(); });

  describe('register', () => {
    it('should register a service', async () => {
      const svc = await discovery.register({ name: 'web', address: '10.0.0.1', port: 80 });
      expect(svc).toBeDefined();
      expect(svc.name).toBe('web');
    });

    it('should add endpoint to existing service', async () => {
      await discovery.register({ name: 'web', address: '10.0.0.1', port: 80 });
      const svc2 = await discovery.register({ name: 'web', address: '10.0.0.2', port: 80 });
      const endpoints = await discovery.discover('web');
      expect(endpoints.length).toBe(2);
    });
  });

  describe('deregister', () => {
    it('should deregister a service', async () => {
      const svc = await discovery.register({ name: 'rem', address: '10.0.0.1', port: 80 });
      await discovery.deregister(svc.id);
      expect(discovery.getServiceCount()).toBe(0);
    });
  });

  describe('discover', () => {
    it('should discover healthy endpoints', async () => {
      await discovery.register({ name: 'disc', address: '10.0.0.1', port: 80 });
      const eps = await discovery.discover('disc');
      expect(eps.length).toBe(1);
      expect(eps[0].healthy).toBe(true);
    });
  });

  describe('setEndpointHealth', () => {
    it('should mark endpoint unhealthy', async () => {
      const svc = await discovery.register({ name: 'h', address: '10.0.0.1', port: 80 });
      const eps = await discovery.discover('h');
      await discovery.setEndpointHealth(svc.id, eps[0].nodeId, false);
      const healthy = await discovery.discover('h');
      expect(healthy.length).toBe(0);
    });
  });

  describe('counts', () => {
    it('should track counts', async () => {
      await discovery.register({ name: 'c1', address: '10.0.0.1', port: 80 });
      await discovery.register({ name: 'c2', address: '10.0.0.2', port: 80 });
      expect(discovery.getServiceCount()).toBe(2);
      expect(discovery.getEndpointCount()).toBe(2);
    });
  });
});

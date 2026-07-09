import { describe, it, expect, beforeEach } from 'vitest';
import { ArcanisContainer } from '../src/index.js';

describe('ArcanisContainer Integration', () => {
  let ac: ArcanisContainer;

  beforeEach(() => {
    ac = new ArcanisContainer();
  });

  describe('initialization', () => {
    it('should initialize all subsystems', () => {
      expect(ac.runtime).toBeDefined();
      expect(ac.images).toBeDefined();
      expect(ac.networks).toBeDefined();
      expect(ac.storage).toBeDefined();
      expect(ac.orchestration).toBeDefined();
      expect(ac.security).toBeDefined();
      expect(ac.resources).toBeDefined();
      expect(ac.cli).toBeDefined();
    });
  });

  describe('getSystemInfo', () => {
    it('should return system information', async () => {
      const info = await ac.getSystemInfo();
      expect(info.containers.total).toBe(0);
      expect(info.containers.running).toBe(0);
      expect(info.images.total).toBeGreaterThan(0);
      expect(info.networks).toBeGreaterThan(0);
      expect(info.volumes).toBeGreaterThan(0);
      expect(info.services).toBe(0);
      expect(info.resources.cpu).toBeGreaterThan(0);
      expect(info.resources.memory).toBeGreaterThan(0);
    });
  });

  describe('full container lifecycle', () => {
    it('should create, start, stop, and remove container', async () => {
      const container = await ac.runtime.create({ name: 'lifecycle-test', image: 'alpine:latest' });
      expect(container.state).toBe('created');

      await ac.runtime.start(container.id);
      let details = await ac.runtime.inspect(container.id);
      expect(details.state).toBe('running');

      await ac.runtime.stop(container.id);
      details = await ac.runtime.inspect(container.id);
      expect(details.state).toBe('stopped');

      await ac.runtime.remove(container.id);
      expect(ac.runtime.getContainerCount()).toBe(0);
    });
  });

  describe('image and network integration', () => {
    it('should pull image and connect to network', async () => {
      const image = await ac.images.pull('myapp', 'v1');
      expect(image.status).toBe('ready');

      const ip = await ac.networks.connectContainer('bridge', 'my-container');
      expect(ip).toBeDefined();
    });
  });

  describe('orchestration integration', () => {
    it('should create service and manage tasks', async () => {
      const service = await ac.orchestration.createService({
        name: 'web',
        image: 'nginx:alpine',
        replicas: 2,
      });
      expect(service.replicas).toBe(2);

      const scaled = await ac.orchestration.scaleService(service.id, 4);
      expect(scaled.replicas).toBe(4);
    });
  });

  describe('security integration', () => {
    it('should validate container against policy', () => {
      const result = ac.security.validateContainerSecurity({
        capabilities: { add: ['chown'] },
      }, 'restricted');
      expect(result.allowed).toBe(true);
    });
  });

  describe('resource integration', () => {
    it('should allocate and track resources', async () => {
      const ok = await ac.resources.allocateResources('c1', { cpus: 2, memory: 1024 * 1024 * 1024 });
      expect(ok).toBe(true);

      const usage = await ac.resources.getResourceUsage();
      expect(usage.allocated.cpu).toBe(2);

      await ac.resources.releaseResources('c1');
      const after = await ac.resources.getResourceUsage();
      expect(after.allocated.cpu).toBe(0);
    });
  });

  describe('CLI integration', () => {
    it('should run full CLI workflow', async () => {
      const runResult = await ac.cli.execute(['run', '--name', 'cli-test', 'alpine:latest']);
      expect(runResult.exitCode).toBe(0);

      const psResult = await ac.cli.execute(['ps']);
      expect(psResult.exitCode).toBe(0);

      const sysResult = await ac.cli.execute(['system', 'info']);
      expect(sysResult.exitCode).toBe(0);
    });
  });
});

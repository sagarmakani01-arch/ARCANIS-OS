import { describe, it, expect, beforeEach } from 'vitest';
import { OrchestrationManager } from '../src/orchestration/orchestration-manager.js';
import { ContainerRuntime } from '../src/runtime/container-runtime.js';

describe('OrchestrationManager', () => {
  let runtime: ContainerRuntime;
  let orchestration: OrchestrationManager;

  beforeEach(() => {
    runtime = new ContainerRuntime();
    orchestration = new OrchestrationManager(runtime);
  });

  describe('createService', () => {
    it('should create a service', async () => {
      const service = await orchestration.createService({ name: 'web', image: 'nginx:alpine' });
      expect(service).toBeDefined();
      expect(service.name).toBe('web');
      expect(service.image).toBe('nginx:alpine');
      expect(service.replicas).toBe(1);
      expect(service.tasks).toHaveLength(1);
    });

    it('should create service with multiple replicas', async () => {
      const service = await orchestration.createService({ name: 'api', image: 'node:18', replicas: 3 });
      expect(service.replicas).toBe(3);
      expect(service.tasks).toHaveLength(3);
    });

    it('should emit create event', async () => {
      let emitted = false;
      orchestration.on('service:create', () => { emitted = true; });
      await orchestration.createService({ name: 'ev', image: 'img' });
      expect(emitted).toBe(true);
    });
  });

  describe('scaleService', () => {
    it('should scale up service', async () => {
      const service = await orchestration.createService({ name: 'scalable', image: 'img' });
      const scaled = await orchestration.scaleService(service.id, 5);
      expect(scaled.replicas).toBe(5);
      expect(scaled.tasks.length).toBeGreaterThanOrEqual(5);
    });

    it('should scale down service', async () => {
      const service = await orchestration.createService({ name: 'shrink', image: 'img', replicas: 5 });
      const scaled = await orchestration.scaleService(service.id, 2);
      expect(scaled.replicas).toBe(2);
    });

    it('should reject scaling non-existent service', async () => {
      await expect(orchestration.scaleService('nonexistent', 3)).rejects.toThrow('not found');
    });
  });

  describe('removeService', () => {
    it('should remove a service', async () => {
      const service = await orchestration.createService({ name: 'removable', image: 'img' });
      await orchestration.removeService(service.id, true);
      expect(orchestration.getServiceCount()).toBe(0);
    });
  });

  describe('inspectService', () => {
    it('should return service details', async () => {
      const service = await orchestration.createService({ name: 'inspect-svc', image: 'img' });
      const details = await orchestration.inspectService(service.id);
      expect(details.name).toBe('inspect-svc');
      expect(details.tasks).toBeInstanceOf(Array);
    });

    it('should throw for non-existent service', async () => {
      await expect(orchestration.inspectService('nonexistent')).rejects.toThrow('not found');
    });
  });

  describe('listServices', () => {
    it('should list all services', async () => {
      await orchestration.createService({ name: 'svc1', image: 'img' });
      await orchestration.createService({ name: 'svc2', image: 'img' });
      const list = await orchestration.listServices();
      expect(list.length).toBe(2);
    });

    it('should filter by name', async () => {
      await orchestration.createService({ name: 'web-app', image: 'img' });
      await orchestration.createService({ name: 'db-app', image: 'img' });
      const list = await orchestration.listServices({ name: 'web' });
      expect(list.length).toBe(1);
    });
  });

  describe('getServiceTasks', () => {
    it('should return tasks for a service', async () => {
      const service = await orchestration.createService({ name: 'task-svc', image: 'img', replicas: 3 });
      const tasks = await orchestration.getServiceTasks(service.id);
      expect(tasks).toHaveLength(3);
    });
  });

  describe('getTask', () => {
    it('should find task by ID', async () => {
      const service = await orchestration.createService({ name: 'find-task', image: 'img' });
      const tasks = await orchestration.getServiceTasks(service.id);
      const task = await orchestration.getTask(tasks[0].id);
      expect(task).toBeDefined();
      expect(task!.serviceId).toBe(service.id);
    });
  });

  describe('counts', () => {
    it('should track service count', async () => {
      expect(orchestration.getServiceCount()).toBe(0);
      await orchestration.createService({ name: 'count', image: 'img' });
      expect(orchestration.getServiceCount()).toBe(1);
    });

    it('should track total replicas', async () => {
      await orchestration.createService({ name: 'r1', image: 'img', replicas: 3 });
      await orchestration.createService({ name: 'r2', image: 'img', replicas: 2 });
      expect(orchestration.getTotalReplicas()).toBe(5);
    });
  });
});

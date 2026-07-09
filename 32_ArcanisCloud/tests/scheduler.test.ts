import { describe, it, expect, beforeEach } from 'vitest';
import { Scheduler } from '../src/scheduler/scheduler.js';
import { ClusterManager } from '../src/cluster/cluster-manager.js';
import { NodeResources } from '../src/types.js';

const baseResources: NodeResources = {
  cpuTotal: 8, cpuAvailable: 6, memoryTotal: 16 * 1024 ** 3, memoryAvailable: 12 * 1024 ** 3,
  diskTotal: 500 * 1024 ** 3, diskAvailable: 400 * 1024 ** 3, gpuTotal: 0, gpuAvailable: 0,
};

describe('Scheduler', () => {
  let cluster: ClusterManager;
  let scheduler: Scheduler;

  beforeEach(async () => {
    cluster = new ClusterManager();
    scheduler = new Scheduler(cluster, { strategy: 'spread' });
    await cluster.joinNode({ name: 'w1', address: '10.0.0.1', port: 7946, resources: baseResources });
    await cluster.joinNode({ name: 'w2', address: '10.0.0.2', port: 7946, resources: baseResources });
  });

  describe('scheduleTask', () => {
    it('should schedule a task on a node', async () => {
      const task = await scheduler.scheduleTask('svc-1', {});
      expect(task).toBeDefined();
      expect(task.nodeId).toBeDefined();
      expect(task.state).toBe('assigned');
    });

    it('should fail with no nodes', async () => {
      const emptyCluster = new ClusterManager();
      const emptyScheduler = new Scheduler(emptyCluster);
      await expect(emptyScheduler.scheduleTask('svc-1', {})).rejects.toThrow('No suitable node');
    });

    it('should emit task:scheduled event', async () => {
      let emitted = false;
      scheduler.on('task:scheduled', () => { emitted = true; });
      await scheduler.scheduleTask('svc-1', {});
      expect(emitted).toBe(true);
    });
  });

  describe('findBestNode', () => {
    it('should find a suitable node', async () => {
      const result = scheduler.findBestNode({});
      expect(result).toBeDefined();
      expect(result!.nodeId).toBeDefined();
      expect(result!.score).toBeGreaterThan(0);
    });

    it('should reject nodes without enough resources', async () => {
      const result = scheduler.findBestNode({ resources: { cpuRequest: 100 } });
      expect(result).toBeUndefined();
    });
  });

  describe('listTasks', () => {
    it('should list all tasks', async () => {
      await scheduler.scheduleTask('svc-1', {});
      await scheduler.scheduleTask('svc-1', {});
      expect(scheduler.listTasks()).toHaveLength(2);
    });

    it('should filter by service', async () => {
      await scheduler.scheduleTask('svc-1', {});
      await scheduler.scheduleTask('svc-2', {});
      expect(scheduler.listTasks({ serviceId: 'svc-1' })).toHaveLength(1);
    });
  });

  describe('counts', () => {
    it('should track task counts', async () => {
      expect(scheduler.getTaskCount()).toBe(0);
      await scheduler.scheduleTask('svc-1', {});
      expect(scheduler.getTaskCount()).toBe(1);
    });
  });
});

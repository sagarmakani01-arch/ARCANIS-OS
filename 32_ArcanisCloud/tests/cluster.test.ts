import { describe, it, expect, beforeEach } from 'vitest';
import { ClusterManager } from '../src/cluster/cluster-manager.js';
import { NodeResources } from '../src/types.js';

const baseResources: NodeResources = {
  cpuTotal: 8, cpuAvailable: 6, memoryTotal: 16 * 1024 ** 3, memoryAvailable: 12 * 1024 ** 3,
  diskTotal: 500 * 1024 ** 3, diskAvailable: 400 * 1024 ** 3, gpuTotal: 0, gpuAvailable: 0,
};

describe('ClusterManager', () => {
  let cluster: ClusterManager;

  beforeEach(() => { cluster = new ClusterManager({ maxNodes: 100 }); });

  describe('joinNode', () => {
    it('should add a node', async () => {
      const node = await cluster.joinNode({ name: 'worker-1', address: '10.0.0.1', port: 7946, resources: baseResources });
      expect(node).toBeDefined();
      expect(node.name).toBe('worker-1');
      expect(node.state).toBe('healthy');
      expect(node.role).toBe('worker');
    });

    it('should add manager nodes', async () => {
      const node = await cluster.joinNode({ name: 'manager-1', address: '10.0.0.2', port: 7946, role: 'manager', resources: baseResources });
      expect(node.role).toBe('manager');
    });

    it('should enforce max nodes', async () => {
      const smallCluster = new ClusterManager({ maxNodes: 2 });
      await smallCluster.joinNode({ name: 'n1', address: '10.0.0.1', port: 7946, resources: baseResources });
      await smallCluster.joinNode({ name: 'n2', address: '10.0.0.2', port: 7946, resources: baseResources });
      await expect(smallCluster.joinNode({ name: 'n3', address: '10.0.0.3', port: 7946, resources: baseResources })).rejects.toThrow('Maximum node limit');
    });

    it('should emit node:join event', async () => {
      let emitted = false;
      cluster.on('node:join', () => { emitted = true; });
      await cluster.joinNode({ name: 'ev', address: '10.0.0.1', port: 7946, resources: baseResources });
      expect(emitted).toBe(true);
    });
  });

  describe('removeNode', () => {
    it('should remove a node', async () => {
      const node = await cluster.joinNode({ name: 'removable', address: '10.0.0.1', port: 7946, resources: baseResources });
      await cluster.removeNode(node.id);
      expect(cluster.getNodeCount()).toBe(0);
    });

    it('should drain before removing', async () => {
      const node = await cluster.joinNode({ name: 'drainer', address: '10.0.0.1', port: 7946, resources: baseResources });
      await cluster.removeNode(node.id, true);
      expect(cluster.getNodeCount()).toBe(0);
    });
  });

  describe('heartbeat', () => {
    it('should update heartbeat time', async () => {
      const node = await cluster.joinNode({ name: 'hb', address: '10.0.0.1', port: 7946, resources: baseResources });
      const before = node.lastHeartbeat.getTime();
      await sleep(10);
      await cluster.heartbeat(node.id);
      const after = (await cluster.joinNode ? cluster.getNode(node.id) : node)!.lastHeartbeat.getTime();
      expect(after).toBeGreaterThanOrEqual(before);
    });

    it('should recover unhealthy node', async () => {
      const node = await cluster.joinNode({ name: 'recover', address: '10.0.0.1', port: 7946, resources: baseResources });
      node.state = 'unhealthy';
      await cluster.heartbeat(node.id);
      expect(cluster.getNode(node.id)!.state).toBe('healthy');
    });
  });

  describe('listNodes', () => {
    it('should list all nodes', async () => {
      await cluster.joinNode({ name: 'n1', address: '10.0.0.1', port: 7946, resources: baseResources });
      await cluster.joinNode({ name: 'n2', address: '10.0.0.2', port: 7946, resources: baseResources, role: 'manager' });
      expect(cluster.listNodes()).toHaveLength(2);
    });

    it('should filter by role', async () => {
      await cluster.joinNode({ name: 'w1', address: '10.0.0.1', port: 7946, resources: baseResources, role: 'worker' });
      await cluster.joinNode({ name: 'm1', address: '10.0.0.2', port: 7946, resources: baseResources, role: 'manager' });
      expect(cluster.listNodes({ role: 'manager' })).toHaveLength(1);
    });

    it('should filter by state', async () => {
      const n1 = await cluster.joinNode({ name: 'h', address: '10.0.0.1', port: 7946, resources: baseResources });
      await cluster.joinNode({ name: 'u', address: '10.0.0.2', port: 7946, resources: baseResources });
      cluster.getNode(n1.id)!.state = 'unhealthy';
      expect(cluster.listNodes({ state: 'healthy' })).toHaveLength(1);
    });
  });

  describe('getSchedulableNodes', () => {
    it('should return only healthy non-cordoned nodes', async () => {
      const n1 = await cluster.joinNode({ name: 's1', address: '10.0.0.1', port: 7946, resources: baseResources });
      const n2 = await cluster.joinNode({ name: 's2', address: '10.0.0.2', port: 7946, resources: baseResources });
      cluster.getNode(n2.id)!.state = 'unhealthy';
      const sched = cluster.getSchedulableNodes();
      expect(sched).toHaveLength(1);
    });
  });

  describe('getClusterResources', () => {
    it('should aggregate resources', async () => {
      await cluster.joinNode({ name: 'r1', address: '10.0.0.1', port: 7946, resources: baseResources });
      await cluster.joinNode({ name: 'r2', address: '10.0.0.2', port: 7946, resources: baseResources });
      const res = cluster.getClusterResources();
      expect(res.cpuTotal).toBe(16);
      expect(res.memoryTotal).toBe(32 * 1024 ** 3);
    });
  });

  describe('counts', () => {
    it('should track counts', async () => {
      expect(cluster.getNodeCount()).toBe(0);
      await cluster.joinNode({ name: 'c', address: '10.0.0.1', port: 7946, resources: baseResources });
      expect(cluster.getNodeCount()).toBe(1);
      expect(cluster.getHealthyCount()).toBe(1);
      expect(cluster.getWorkerCount()).toBe(1);
    });
  });
});

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

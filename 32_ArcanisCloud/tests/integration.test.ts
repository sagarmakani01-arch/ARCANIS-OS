import { describe, it, expect, beforeEach } from 'vitest';
import { ArcanisCloud } from '../src/index.js';
import { NodeResources } from '../src/types.js';

const baseResources: NodeResources = {
  cpuTotal: 8, cpuAvailable: 6, memoryTotal: 16 * 1024 ** 3, memoryAvailable: 12 * 1024 ** 3,
  diskTotal: 500 * 1024 ** 3, diskAvailable: 400 * 1024 ** 3, gpuTotal: 0, gpuAvailable: 0,
};

describe('ArcanisCloud Integration', () => {
  let cloud: ArcanisCloud;

  beforeEach(() => {
    cloud = new ArcanisCloud();
  });

  describe('initialization', () => {
    it('should initialize all subsystems', () => {
      expect(cloud.cluster).toBeDefined();
      expect(cloud.scheduler).toBeDefined();
      expect(cloud.loadBalancer).toBeDefined();
      expect(cloud.autoScaler).toBeDefined();
      expect(cloud.discovery).toBeDefined();
      expect(cloud.monitoring).toBeDefined();
      expect(cloud.tenancy).toBeDefined();
      expect(cloud.deployment).toBeDefined();
    });
  });

  describe('getSystemInfo', () => {
    it('should return system info', async () => {
      const info = await cloud.getSystemInfo();
      expect(info.cluster).toBeDefined();
      expect(info.scheduler).toBeDefined();
      expect(info.services).toBeDefined();
      expect(info.monitoring).toBeDefined();
    });
  });

  describe('full lifecycle', () => {
    it('should provision cluster, deploy service, and monitor', async () => {
      const node1 = await cloud.cluster.joinNode({ name: 'w1', address: '10.0.0.1', port: 7946, resources: baseResources });
      const node2 = await cloud.cluster.joinNode({ name: 'w2', address: '10.0.0.2', port: 7946, resources: baseResources });
      expect(cloud.cluster.getNodeCount()).toBe(2);

      const task = await cloud.scheduler.scheduleTask('svc-1', { resources: { cpuRequest: 2, memoryRequest: 1024 ** 3 } });
      expect(task.nodeId).toBeDefined();

      const svc = await cloud.discovery.register({ name: 'web', address: '10.0.0.1', port: 80 });
      const eps = await cloud.discovery.discover('web');
      expect(eps.length).toBe(1);

      cloud.monitoring.recordMetric({ name: 'cpu', type: 'gauge', labels: { host: 'w1' }, value: 45, timestamp: new Date() });
      cloud.monitoring.recordMetric({ name: 'cpu', type: 'gauge', labels: { host: 'w2' }, value: 65, timestamp: new Date() });
      const summary = cloud.monitoring.getMetricSummary('cpu');
      expect(summary).toBeDefined();

      const deployment = await cloud.deployment.createDeployment({ serviceId: svc.id, strategy: 'rolling', image: 'nginx:latest', replicas: 3 });
      await cloud.deployment.executeDeployment(deployment.id);
      expect(cloud.deployment.getDeployment(deployment.id)!.status).toBe('completed');

      const tenant = cloud.tenancy.createTenant({ name: 'prod', tier: 'professional' });
      expect(tenant.quotas.maxNodes).toBe(50);
    });
  });
});

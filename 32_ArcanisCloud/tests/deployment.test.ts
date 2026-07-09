import { describe, it, expect, beforeEach } from 'vitest';
import { DeploymentManager } from '../src/deployment/deployment-manager.js';

describe('DeploymentManager', () => {
  let deployer: DeploymentManager;

  beforeEach(() => { deployer = new DeploymentManager(); });

  describe('createDeployment', () => {
    it('should create a deployment', async () => {
      const d = await deployer.createDeployment({ serviceId: 'svc-1', strategy: 'rolling', image: 'nginx:latest', replicas: 3 });
      expect(d).toBeDefined();
      expect(d.strategy).toBe('rolling');
      expect(d.status).toBe('pending');
    });
  });

  describe('executeDeployment', () => {
    it('should execute rolling deployment', async () => {
      const d = await deployer.createDeployment({ serviceId: 'svc-1', strategy: 'rolling', image: 'nginx:latest', replicas: 3 });
      await deployer.executeDeployment(d.id);
      const result = deployer.getDeployment(d.id)!;
      expect(result.status).toBe('completed');
      expect(result.progress.ready).toBe(3);
    });

    it('should execute blue-green deployment', async () => {
      const d = await deployer.createDeployment({ serviceId: 'svc-1', strategy: 'blue-green', image: 'nginx:latest', replicas: 2 });
      await deployer.executeDeployment(d.id);
      expect(deployer.getDeployment(d.id)!.status).toBe('completed');
    });

    it('should execute canary deployment', async () => {
      const d = await deployer.createDeployment({ serviceId: 'svc-1', strategy: 'canary', image: 'nginx:latest', replicas: 10 });
      await deployer.executeDeployment(d.id);
      expect(deployer.getDeployment(d.id)!.status).toBe('completed');
    });

    it('should execute recreate deployment', async () => {
      const d = await deployer.createDeployment({ serviceId: 'svc-1', strategy: 'recreate', image: 'nginx:latest', replicas: 1 });
      await deployer.executeDeployment(d.id);
      expect(deployer.getDeployment(d.id)!.status).toBe('completed');
    });
  });

  describe('rollbackDeployment', () => {
    it('should rollback a deployment', async () => {
      const d = await deployer.createDeployment({ serviceId: 'svc-1', strategy: 'rolling', image: 'nginx:v1', replicas: 2 });
      await deployer.executeDeployment(d.id);
      const rb = await deployer.rollbackDeployment(d.id);
      expect(rb.status).toBe('completed');
      expect(rb.version).toContain('rollback');
    });
  });

  describe('cancelDeployment', () => {
    it('should cancel an in-progress deployment', async () => {
      const d = await deployer.createDeployment({ serviceId: 'svc-1', strategy: 'rolling', image: 'nginx:latest', replicas: 5 });
      // Manually set to in-progress without executing
      deployer.getDeployment(d.id)!.status = 'in-progress';
      await deployer.cancelDeployment(d.id);
      expect(deployer.getDeployment(d.id)!.status).toBe('failed');
    });
  });

  describe('listDeployments', () => {
    it('should list deployments', async () => {
      await deployer.createDeployment({ serviceId: 'svc-1', strategy: 'rolling', image: 'nginx:v1', replicas: 1 });
      await deployer.createDeployment({ serviceId: 'svc-1', strategy: 'canary', image: 'nginx:v2', replicas: 1 });
      expect(deployer.listDeployments()).toHaveLength(2);
      expect(deployer.listDeployments({ strategy: 'canary' })).toHaveLength(1);
    });
  });

  describe('counts', () => {
    it('should track deployment counts', async () => {
      await deployer.createDeployment({ serviceId: 'svc-1', strategy: 'rolling', image: 'img', replicas: 1 });
      expect(deployer.getDeploymentCount()).toBe(1);
      expect(deployer.getActiveDeploymentCount()).toBe(0);
    });
  });
});

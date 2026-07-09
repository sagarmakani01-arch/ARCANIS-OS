import { describe, it, expect, beforeEach } from 'vitest';
import { ResourceManager } from '../src/resources/resource-manager.js';

describe('ResourceManager', () => {
  let resources: ResourceManager;

  beforeEach(() => {
    resources = new ResourceManager({ totalCpu: 8, totalMemory: 16 * 1024 * 1024 * 1024 });
  });

  describe('createQuota', () => {
    it('should create a quota', () => {
      const quota = resources.createQuota({
        name: 'team-a',
        maxContainers: 10,
        maxCpu: 4,
        maxMemory: 8 * 1024 * 1024 * 1024,
        maxStorage: 100 * 1024 * 1024 * 1024,
        maxNetworks: 5,
        maxVolumes: 20,
      });
      expect(quota).toBeDefined();
      expect(quota.name).toBe('team-a');
      expect(quota.maxCpu).toBe(4);
    });
  });

  describe('allocateResources', () => {
    it('should allocate CPU and memory', async () => {
      const ok = await resources.allocateResources('c1', { cpus: 2, memory: 1024 * 1024 * 1024 });
      expect(ok).toBe(true);
    });

    it('should reject over-allocation of CPU', async () => {
      await resources.allocateResources('c1', { cpus: 7 });
      await expect(resources.allocateResources('c2', { cpus: 2 })).rejects.toThrow('Insufficient CPU');
    });

    it('should reject over-allocation of memory', async () => {
      await resources.allocateResources('c1', { memory: 15 * 1024 * 1024 * 1024 });
      await expect(resources.allocateResources('c2', { memory: 2 * 1024 * 1024 * 1024 })).rejects.toThrow('Insufficient memory');
    });
  });

  describe('releaseResources', () => {
    it('should release allocated resources', async () => {
      await resources.allocateResources('c1', { cpus: 2, memory: 1024 * 1024 * 1024 });
      await resources.releaseResources('c1');
      const usage = await resources.getResourceUsage();
      expect(usage.allocated.cpu).toBe(0);
    });
  });

  describe('updateResources', () => {
    it('should update allocation', async () => {
      await resources.allocateResources('c1', { cpus: 1, memory: 512 * 1024 * 1024 });
      await resources.updateResources('c1', { cpus: 2, memory: 1024 * 1024 * 1024 });
      const usage = await resources.getResourceUsage();
      expect(usage.allocated.cpu).toBe(2);
    });
  });

  describe('getResourceUsage', () => {
    it('should return usage stats', async () => {
      const usage = await resources.getResourceUsage();
      expect(usage.total.cpu).toBe(8);
      expect(usage.allocated.cpu).toBe(0);
      expect(usage.available.cpu).toBe(8);
      expect(usage.utilization.cpu).toBe(0);
    });
  });

  describe('calculateMemoryLimit', () => {
    it('should parse MB', () => {
      expect(resources.calculateMemoryLimit('512m')).toBe(512 * 1024 * 1024);
    });

    it('should parse GB', () => {
      expect(resources.calculateMemoryLimit('2g')).toBe(2 * 1024 * 1024 * 1024);
    });

    it('should parse KB', () => {
      expect(resources.calculateMemoryLimit('1024k')).toBe(1024 * 1024);
    });

    it('should handle plain numbers', () => {
      expect(resources.calculateMemoryLimit(1024)).toBe(1024);
    });
  });

  describe('generateDefaultUlimits', () => {
    it('should generate default ulimits', () => {
      const ulimits = resources.generateDefaultUlimits();
      expect(ulimits.length).toBeGreaterThan(0);
      expect(ulimits.some(u => u.name === 'nofile')).toBe(true);
    });
  });

  describe('validateResourceConfig', () => {
    it('should validate valid config', () => {
      const errors = resources.validateResourceConfig({ cpus: 2, memory: 1024 * 1024 * 1024 });
      expect(errors).toHaveLength(0);
    });

    it('should reject negative CPU', () => {
      const errors = resources.validateResourceConfig({ cpus: -1 });
      expect(errors.length).toBeGreaterThan(0);
    });

    it('should reject excessive CPU', () => {
      const errors = resources.validateResourceConfig({ cpus: 16 });
      expect(errors.length).toBeGreaterThan(0);
    });

    it('should reject memory reservation exceeding memory', () => {
      const errors = resources.validateResourceConfig({ memory: 1024, memoryReservation: 2048 });
      expect(errors.length).toBeGreaterThan(0);
    });
  });
});

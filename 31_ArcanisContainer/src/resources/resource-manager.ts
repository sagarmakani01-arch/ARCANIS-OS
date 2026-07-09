// ArcanisContainer - Resource Manager

import { EventEmitter } from 'events';
import { ResourceConfig, ContainerStats, UlimitConfig } from '../types.js';

export interface ResourceQuota {
  id: string;
  name: string;
  maxContainers: number;
  maxCpu: number;
  maxMemory: number;
  maxStorage: number;
  maxNetworks: number;
  maxVolumes: number;
}

export interface ResourceManagerOptions {
  totalCpu?: number;
  totalMemory?: number;
  totalStorage?: number;
}

export class ResourceManager extends EventEmitter {
  private quotas: Map<string, ResourceQuota> = new Map();
  private allocations: Map<string, ResourceConfig> = new Map();
  private options: Required<ResourceManagerOptions>;

  constructor(options: ResourceManagerOptions = {}) {
    super();
    this.options = {
      totalCpu: options.totalCpu || 8,
      totalMemory: options.totalMemory || 16 * 1024 * 1024 * 1024,
      totalStorage: options.totalStorage || 500 * 1024 * 1024 * 1024,
    };
  }

  createQuota(config: Omit<ResourceQuota, 'id'>): ResourceQuota {
    const id = `quota-${Date.now()}`;
    const quota: ResourceQuota = { id, ...config };
    this.quotas.set(id, quota);
    this.emit('quota:create', quota);
    return quota;
  }

  async removeQuota(quotaId: string): Promise<void> {
    if (!this.quotas.has(quotaId)) throw new Error(`Quota ${quotaId} not found`);
    this.quotas.delete(quotaId);
    this.emit('quota:remove', { id: quotaId });
  }

  async allocateResources(containerId: string, config: ResourceConfig): Promise<boolean> {
    const currentTotal = this.calculateTotalAllocation();

    if (config.cpus && currentTotal.cpus + config.cpus > this.options.totalCpu) {
      throw new Error('Insufficient CPU resources');
    }
    if (config.memory && currentTotal.memory + config.memory > this.options.totalMemory) {
      throw new Error('Insufficient memory resources');
    }

    this.allocations.set(containerId, config);
    this.emit('resources:allocate', { containerId, config });
    return true;
  }

  async releaseResources(containerId: string): Promise<void> {
    this.allocations.delete(containerId);
    this.emit('resources:release', { containerId });
  }

  private calculateTotalAllocation(): { cpus: number; memory: number } {
    let cpus = 0;
    let memory = 0;

    for (const config of this.allocations.values()) {
      cpus += config.cpus || 0;
      memory += config.memory || 0;
    }

    return { cpus, memory };
  }

  async updateResources(containerId: string, config: ResourceConfig): Promise<void> {
    const existing = this.allocations.get(containerId);
    if (!existing) throw new Error(`No allocation found for container ${containerId}`);

    const currentTotal = this.calculateTotalAllocation();
    const oldCpu = existing.cpus || 0;
    const oldMemory = existing.memory || 0;
    const newCpu = config.cpus || 0;
    const newMemory = config.memory || 0;

    if (currentTotal.cpus - oldCpu + newCpu > this.options.totalCpu) {
      throw new Error('Insufficient CPU resources');
    }
    if (currentTotal.memory - oldMemory + newMemory > this.options.totalMemory) {
      throw new Error('Insufficient memory resources');
    }

    this.allocations.set(containerId, config);
    this.emit('resources:update', { containerId, config });
  }

  async getResourceUsage(): Promise<{
    total: { cpu: number; memory: number; storage: number };
    allocated: { cpu: number; memory: number };
    available: { cpu: number; memory: number };
    utilization: { cpu: number; memory: number };
  }> {
    const allocated = this.calculateTotalAllocation();

    return {
      total: {
        cpu: this.options.totalCpu,
        memory: this.options.totalMemory,
        storage: this.options.totalStorage,
      },
      allocated: {
        cpu: allocated.cpus,
        memory: allocated.memory,
      },
      available: {
        cpu: this.options.totalCpu - allocated.cpus,
        memory: this.options.totalMemory - allocated.memory,
      },
      utilization: {
        cpu: (allocated.cpus / this.options.totalCpu) * 100,
        memory: (allocated.memory / this.options.totalMemory) * 100,
      },
    };
  }

  calculateCpuShares(shares: number): number {
    return Math.max(2, Math.min(262144, shares));
  }

  calculateCpuQuota(period: number, quota: number): number {
    return Math.max(0, Math.floor((quota / period) * 100000));
  }

  calculateMemoryLimit(memory: string | number): number {
    if (typeof memory === 'number') return memory;
    const units: Record<string, number> = {
      b: 1, k: 1024, kb: 1024, m: 1024 ** 2, mb: 1024 ** 2,
      g: 1024 ** 3, gb: 1024 ** 3, t: 1024 ** 4, tb: 1024 ** 4,
    };
    const match = memory.match(/^(\d+(?:\.\d+)?)\s*([a-z]+)?$/i);
    if (!match) throw new Error(`Invalid memory size: ${memory}`);
    const value = parseFloat(match[1]);
    const unit = (match[2] || 'b').toLowerCase();
    return Math.floor(value * (units[unit] || 1));
  }

  generateDefaultUlimits(): UlimitConfig[] {
    return [
      { name: 'nofile', soft: 65536, hard: 65536 },
      { name: 'nproc', soft: 4096, hard: 4096 },
      { name: 'memlock', soft: -1, hard: -1 },
      { name: 'stack', soft: 8388608, hard: 8388608 },
      { name: 'core', soft: 0, hard: 0 },
      { name: 'fsize', soft: -1, hard: -1 },
    ];
  }

  validateResourceConfig(config: ResourceConfig): string[] {
    const errors: string[] = [];

    if (config.cpus !== undefined && (config.cpus < 0 || config.cpus > this.options.totalCpu)) {
      errors.push(`CPU must be between 0 and ${this.options.totalCpu}`);
    }
    if (config.memory !== undefined && (config.memory < 0 || config.memory > this.options.totalMemory)) {
      errors.push(`Memory must be between 0 and ${this.options.totalMemory}`);
    }
    if (config.memoryReservation !== undefined && config.memory !== undefined) {
      if (config.memoryReservation > config.memory) {
        errors.push('Memory reservation cannot exceed memory limit');
      }
    }
    if (config.pidsLimit !== undefined && config.pidsLimit < -1) {
      errors.push('PIDs limit must be -1 (unlimited) or positive');
    }
    if (config.cpuShares !== undefined && (config.cpuShares < 2 || config.cpuShares > 262144)) {
      errors.push('CPU shares must be between 2 and 262144');
    }

    return errors;
  }

  getAllocatedResources(): Map<string, ResourceConfig> {
    return new Map(this.allocations);
  }

  getQuota(quotaId: string): ResourceQuota | undefined {
    return this.quotas.get(quotaId);
  }

  listQuotas(): ResourceQuota[] {
    return Array.from(this.quotas.values());
  }
}

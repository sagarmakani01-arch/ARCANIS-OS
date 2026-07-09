// ArcanisCloud - Multi-Tenancy

import { EventEmitter } from 'events';
import { Tenant, TenantTier, TenantQuotas, TenantUsage } from '../types.js';
import { generateTenantId } from '../utils.js';

export interface TenancyOptions {
  maxTenants?: number;
}

export const TIER_QUOTAS: Record<TenantTier, TenantQuotas> = {
  free: { maxNodes: 2, maxServices: 5, maxCpu: 2, maxMemory: 4 * 1024 ** 3, maxStorage: 10 * 1024 ** 3, maxBandwidth: 100 * 1024 ** 2 },
  starter: { maxNodes: 10, maxServices: 25, maxCpu: 16, maxMemory: 32 * 1024 ** 3, maxStorage: 100 * 1024 ** 3, maxBandwidth: 1024 ** 3 },
  professional: { maxNodes: 50, maxServices: 100, maxCpu: 64, maxMemory: 256 * 1024 ** 3, maxStorage: 1024 ** 3, maxBandwidth: 10 * 1024 ** 3 },
  enterprise: { maxNodes: 1000, maxServices: 10000, maxCpu: 10000, maxMemory: 1024 ** 4, maxStorage: 100 * 1024 ** 3, maxBandwidth: 100 * 1024 ** 3 },
};

export class TenancyManager extends EventEmitter {
  private tenants: Map<string, Tenant> = new Map();
  private options: Required<TenancyOptions>;

  constructor(options: TenancyOptions = {}) {
    super();
    this.options = { maxTenants: options.maxTenants || 1000 };
  }

  createTenant(config: { name: string; tier: TenantTier; labels?: Record<string, string> }): Tenant {
    if (this.tenants.size >= this.options.maxTenants) {
      throw new Error(`Maximum tenant limit reached (${this.options.maxTenants})`);
    }

    const id = generateTenantId();
    const tenant: Tenant = {
      id, name: config.name, tier: config.tier,
      quotas: { ...TIER_QUOTAS[config.tier] },
      usage: { nodes: 0, services: 0, cpu: 0, memory: 0, storage: 0, bandwidth: 0 },
      createdAt: new Date(), labels: config.labels,
    };

    this.tenants.set(id, tenant);
    this.emit('tenant:create', tenant);
    return tenant;
  }

  async removeTenant(tenantId: string): Promise<void> {
    if (!this.tenants.has(tenantId)) throw new Error(`Tenant ${tenantId} not found`);
    this.tenants.delete(tenantId);
    this.emit('tenant:remove', { id: tenantId });
  }

  async upgradeTenant(tenantId: string, newTier: TenantTier): Promise<Tenant> {
    const tenant = this.tenants.get(tenantId);
    if (!tenant) throw new Error(`Tenant ${tenantId} not found`);
    tenant.tier = newTier;
    tenant.quotas = { ...TIER_QUOTAS[newTier] };
    this.emit('tenant:upgrade', tenant);
    return tenant;
  }

  async checkQuota(tenantId: string, resource: keyof TenantQuotas, amount: number): Promise<{ allowed: boolean; current: number; limit: number }> {
    const tenant = this.tenants.get(tenantId);
    if (!tenant) throw new Error(`Tenant ${tenantId} not found`);

    const limit = tenant.quotas[resource];
    const current = tenant.usage[resource === 'maxNodes' ? 'nodes' : resource === 'maxServices' ? 'services' : resource === 'maxCpu' ? 'cpu' : resource === 'maxMemory' ? 'memory' : resource === 'maxStorage' ? 'storage' : 'bandwidth'] as number;

    return { allowed: current + amount <= limit, current, limit };
  }

  async updateUsage(tenantId: string, usage: Partial<TenantUsage>): Promise<void> {
    const tenant = this.tenants.get(tenantId);
    if (!tenant) throw new Error(`Tenant ${tenantId} not found`);
    Object.assign(tenant.usage, usage);
    this.emit('tenant:usage', tenant);
  }

  async canDeploy(tenantId: string, cpu: number, memory: number): Promise<boolean> {
    const tenant = this.tenants.get(tenantId);
    if (!tenant) return false;
    return tenant.usage.cpu + cpu <= tenant.quotas.maxCpu && tenant.usage.memory + memory <= tenant.quotas.maxMemory;
  }

  getTenant(tenantId: string): Tenant | undefined { return this.tenants.get(tenantId); }

  listTenants(filters?: { tier?: TenantTier }): Tenant[] {
    let result = Array.from(this.tenants.values());
    if (filters?.tier) result = result.filter(t => t.tier === filters.tier);
    return result;
  }

  getTenantCount(): number { return this.tenants.size; }
  getTenantCountByTier(tier: TenantTier): number { return Array.from(this.tenants.values()).filter(t => t.tier === tier).length; }

  async getUsageReport(tenantId: string): Promise<{
    tenant: string;
    tier: TenantTier;
    usage: TenantUsage;
    quotas: TenantQuotas;
    utilization: Record<string, number>;
  }> {
    const tenant = this.tenants.get(tenantId);
    if (!tenant) throw new Error(`Tenant ${tenantId} not found`);

    return {
      tenant: tenant.name, tier: tenant.tier, usage: tenant.usage, quotas: tenant.quotas,
      utilization: {
        nodes: (tenant.usage.nodes / tenant.quotas.maxNodes) * 100,
        services: (tenant.usage.services / tenant.quotas.maxServices) * 100,
        cpu: (tenant.usage.cpu / tenant.quotas.maxCpu) * 100,
        memory: (tenant.usage.memory / tenant.quotas.maxMemory) * 100,
      },
    };
  }
}

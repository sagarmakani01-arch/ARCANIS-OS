import { describe, it, expect, beforeEach } from 'vitest';
import { TenancyManager, TIER_QUOTAS } from '../src/tenancy/tenancy-manager.js';

describe('TenancyManager', () => {
  let tenancy: TenancyManager;

  beforeEach(() => { tenancy = new TenancyManager({ maxTenants: 100 }); });

  describe('createTenant', () => {
    it('should create a tenant', () => {
      const tenant = tenancy.createTenant({ name: 'team-a', tier: 'free' });
      expect(tenant).toBeDefined();
      expect(tenant.name).toBe('team-a');
      expect(tenant.quotas.maxNodes).toBe(2);
    });

    it('should enforce max tenants', () => {
      const small = new TenancyManager({ maxTenants: 1 });
      small.createTenant({ name: 't1', tier: 'free' });
      expect(() => small.createTenant({ name: 't2', tier: 'free' })).toThrow('Maximum tenant limit');
    });
  });

  describe('upgradeTenant', () => {
    it('should upgrade tenant tier', async () => {
      const tenant = tenancy.createTenant({ name: 'up', tier: 'free' });
      const upgraded = await tenancy.upgradeTenant(tenant.id, 'professional');
      expect(upgraded.tier).toBe('professional');
      expect(upgraded.quotas.maxNodes).toBe(50);
    });
  });

  describe('checkQuota', () => {
    it('should check quota', async () => {
      const tenant = tenancy.createTenant({ name: 'q', tier: 'free' });
      const result = await tenancy.checkQuota(tenant.id, 'maxCpu', 1);
      expect(result.allowed).toBe(true);
    });
  });

  describe('canDeploy', () => {
    it('should allow deploy within quota', async () => {
      const tenant = tenancy.createTenant({ name: 'd', tier: 'free' });
      expect(await tenancy.canDeploy(tenant.id, 1, 1024 ** 3)).toBe(true);
    });

    it('should reject deploy exceeding quota', async () => {
      const tenant = tenancy.createTenant({ name: 'd2', tier: 'free' });
      expect(await tenancy.canDeploy(tenant.id, 100, 1024 ** 4)).toBe(false);
    });
  });

  describe('getUsageReport', () => {
    it('should generate report', async () => {
      const tenant = tenancy.createTenant({ name: 'r', tier: 'starter' });
      const report = await tenancy.getUsageReport(tenant.id);
      expect(report.tier).toBe('starter');
      expect(report.utilization).toBeDefined();
    });
  });

  describe('listTenants', () => {
    it('should list tenants', () => {
      tenancy.createTenant({ name: 'a', tier: 'free' });
      tenancy.createTenant({ name: 'b', tier: 'professional' });
      expect(tenancy.listTenants()).toHaveLength(2);
      expect(tenancy.listTenants({ tier: 'free' })).toHaveLength(1);
    });
  });
});

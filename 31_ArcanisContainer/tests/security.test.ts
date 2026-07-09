import { describe, it, expect, beforeEach } from 'vitest';
import { SecurityManager } from '../src/security/security-manager.js';

describe('SecurityManager', () => {
  let security: SecurityManager;

  beforeEach(() => {
    security = new SecurityManager();
  });

  describe('constructor', () => {
    it('should create default policies', async () => {
      const policies = await security.listPolicies();
      expect(policies.length).toBeGreaterThanOrEqual(3);
    });

    it('should have default, privileged, and restricted policies', async () => {
      const policies = await security.listPolicies();
      const names = policies.map(p => p.name);
      expect(names).toContain('Default Security Policy');
      expect(names).toContain('Privileged Policy');
      expect(names).toContain('Restricted Policy');
    });
  });

  describe('validateContainerSecurity', () => {
    it('should allow valid config with default policy', () => {
      const result = security.validateContainerSecurity({});
      expect(result.allowed).toBe(true);
      expect(result.violations).toHaveLength(0);
    });

    it('should reject privileged mode with default policy', () => {
      const result = security.validateContainerSecurity({ privileged: true });
      expect(result.allowed).toBe(false);
      expect(result.violations.length).toBeGreaterThan(0);
    });

    it('should allow privileged mode with privileged policy', () => {
      const result = security.validateContainerSecurity({ privileged: true }, 'privileged');
      expect(result.allowed).toBe(true);
    });

    it('should reject sys_admin capability with default policy', () => {
      const result = security.validateContainerSecurity({
        capabilities: { add: ['sys_admin'] },
      });
      expect(result.allowed).toBe(false);
    });

    it('should allow chown with restricted policy', () => {
      const result = security.validateContainerSecurity({
        capabilities: { add: ['chown'] },
      }, 'restricted');
      expect(result.allowed).toBe(true);
    });

    it('should warn when noNewPrivileges is disabled', () => {
      const result = security.validateContainerSecurity({ noNewPrivileges: false });
      expect(result.warnings.length).toBeGreaterThan(0);
    });
  });

  describe('createPolicy', () => {
    it('should create a new policy', () => {
      const policy = security.createPolicy({
        name: 'custom',
        description: 'Custom policy',
        rules: [{ type: 'network', action: 'allow', target: 'bridge' }],
        enabled: true,
      });
      expect(policy).toBeDefined();
      expect(policy.name).toBe('custom');
      expect(policy.rules).toHaveLength(1);
    });

    it('should emit create event', () => {
      let emitted = false;
      security.on('policy:create', () => { emitted = true; });
      security.createPolicy({ name: 'ev', description: '', rules: [], enabled: true });
      expect(emitted).toBe(true);
    });
  });

  describe('removePolicy', () => {
    it('should remove a custom policy', async () => {
      const policy = security.createPolicy({ name: 'removable', description: '', rules: [], enabled: true });
      await security.removePolicy(policy.id);
      const policies = await security.listPolicies();
      expect(policies.find(p => p.id === policy.id)).toBeUndefined();
    });

    it('should reject removing built-in policies', async () => {
      await expect(security.removePolicy('default')).rejects.toThrow('built-in');
      await expect(security.removePolicy('privileged')).rejects.toThrow('built-in');
      await expect(security.removePolicy('restricted')).rejects.toThrow('built-in');
    });
  });

  describe('inspectPolicy', () => {
    it('should return policy details', async () => {
      const details = await security.inspectPolicy('default');
      expect(details.name).toBe('Default Security Policy');
      expect(details.rules.length).toBeGreaterThan(0);
    });

    it('should throw for non-existent policy', async () => {
      await expect(security.inspectPolicy('nonexistent')).rejects.toThrow('not found');
    });
  });

  describe('logSecurityEvent', () => {
    it('should log security events', () => {
      security.logSecurityEvent({
        containerId: 'c1',
        type: 'capability_check',
        message: 'Capability check failed',
        severity: 'medium',
      });
      expect(security.getEventCount()).toBe(1);
    });

    it('should emit event', () => {
      let emitted = false;
      security.on('security:event', () => { emitted = true; });
      security.logSecurityEvent({ containerId: 'c1', type: 'capability_check', message: 'test', severity: 'low' });
      expect(emitted).toBe(true);
    });
  });

  describe('getSecurityEvents', () => {
    it('should return events', async () => {
      security.logSecurityEvent({ containerId: 'c1', type: 'capability_check', message: 'test', severity: 'low' });
      security.logSecurityEvent({ containerId: 'c2', type: 'seccomp_violation', message: 'test2', severity: 'high' });
      const events = await security.getSecurityEvents();
      expect(events.length).toBe(2);
    });

    it('should filter by container', async () => {
      security.logSecurityEvent({ containerId: 'c1', type: 'capability_check', message: 'test', severity: 'low' });
      security.logSecurityEvent({ containerId: 'c2', type: 'capability_check', message: 'test2', severity: 'low' });
      const events = await security.getSecurityEvents({ containerId: 'c1' });
      expect(events.length).toBe(1);
    });

    it('should filter by severity', async () => {
      security.logSecurityEvent({ containerId: 'c1', type: 'capability_check', message: 'test', severity: 'low' });
      security.logSecurityEvent({ containerId: 'c1', type: 'capability_check', message: 'test2', severity: 'critical' });
      const events = await security.getSecurityEvents({ severity: 'critical' });
      expect(events.length).toBe(1);
    });
  });

  describe('generateSecurityReport', () => {
    it('should generate report', async () => {
      security.logSecurityEvent({ containerId: 'c1', type: 'capability_check', message: 'test', severity: 'low' });
      security.logSecurityEvent({ containerId: 'c1', type: 'seccomp_violation', message: 'test2', severity: 'high' });
      const report = await security.generateSecurityReport();
      expect(report.totalEvents).toBe(2);
      expect(report.eventsByType).toBeDefined();
      expect(report.eventsBySeverity).toBeDefined();
    });
  });

  describe('counts', () => {
    it('should track policy count', async () => {
      expect(security.getPolicyCount()).toBeGreaterThanOrEqual(3);
    });

    it('should track event count', () => {
      expect(security.getEventCount()).toBe(0);
    });
  });
});

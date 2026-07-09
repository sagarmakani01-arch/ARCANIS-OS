// ArcanisContainer - Security Manager

import { EventEmitter } from 'events';
import { Capability, SecurityConfig } from '../types.js';

export interface SecurityPolicy {
  id: string;
  name: string;
  description: string;
  rules: SecurityRule[];
  enabled: boolean;
  created: Date;
}

export interface SecurityRule {
  type: 'capability' | 'seccomp' | 'apparmor' | 'selinux' | 'user' | 'network';
  action: 'allow' | 'deny' | 'audit';
  target: string;
  options?: Record<string, string>;
}

export interface SecurityEvent {
  id: string;
  containerId: string;
  type: 'capability_check' | 'seccomp_violation' | 'apparmor_violation' | 'privilege_escalation' | 'resource_violation';
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: Date;
  metadata?: Record<string, string>;
}

export interface SecurityManagerOptions {
  defaultSeccompProfile?: string;
  defaultAppArmorProfile?: string;
  auditEnabled?: boolean;
  maxEvents?: number;
}

export class SecurityManager extends EventEmitter {
  private policies: Map<string, SecurityPolicy> = new Map();
  private events: SecurityEvent[] = [];
  private options: Required<SecurityManagerOptions>;

  constructor(options: SecurityManagerOptions = {}) {
    super();
    this.options = {
      defaultSeccompProfile: options.defaultSeccompProfile || 'default',
      defaultAppArmorProfile: options.defaultAppArmorProfile || 'default',
      auditEnabled: options.auditEnabled ?? true,
      maxEvents: options.maxEvents || 10000,
    };
    this.createDefaultPolicies();
  }

  private createDefaultPolicies(): void {
    const defaultPolicy: SecurityPolicy = {
      id: 'default',
      name: 'Default Security Policy',
      description: 'Standard security policy for containers',
      rules: [
        { type: 'capability', action: 'deny', target: 'sys_admin' },
        { type: 'capability', action: 'deny', target: 'sys_PTRACE' },
        { type: 'capability', action: 'deny', target: 'net_raw' },
        { type: 'seccomp', action: 'allow', target: this.options.defaultSeccompProfile },
        { type: 'apparmor', action: 'allow', target: this.options.defaultAppArmorProfile },
      ],
      enabled: true,
      created: new Date(),
    };
    this.policies.set('default', defaultPolicy);

    const privilegedPolicy: SecurityPolicy = {
      id: 'privileged',
      name: 'Privileged Policy',
      description: 'Full access policy for trusted containers',
      rules: [
        { type: 'capability', action: 'allow', target: '*' },
        { type: 'seccomp', action: 'deny', target: 'all' },
        { type: 'apparmor', action: 'deny', target: 'all' },
      ],
      enabled: true,
      created: new Date(),
    };
    this.policies.set('privileged', privilegedPolicy);

    const restrictedPolicy: SecurityPolicy = {
      id: 'restricted',
      name: 'Restricted Policy',
      description: 'Maximum security policy for untrusted containers',
      rules: [
        { type: 'capability', action: 'allow', target: 'chown' },
        { type: 'capability', action: 'allow', target: 'setuid' },
        { type: 'capability', action: 'allow', target: 'setgid' },
        { type: 'capability', action: 'allow', target: 'fowner' },
        { type: 'capability', action: 'allow', target: 'fsetid' },
        { type: 'capability', action: 'allow', target: 'kill' },
        { type: 'capability', action: 'allow', target: 'net_bind_service' },
        { type: 'capability', action: 'allow', target: 'setfcap' },
        { type: 'seccomp', action: 'allow', target: 'default' },
        { type: 'apparmor', action: 'allow', target: 'docker-default' },
      ],
      enabled: true,
      created: new Date(),
    };
    this.policies.set('restricted', restrictedPolicy);
  }

  validateContainerSecurity(config: SecurityConfig, policyId: string = 'default'): {
    allowed: boolean;
    violations: string[];
    warnings: string[];
  } {
    const policy = this.policies.get(policyId);
    if (!policy) throw new Error(`Security policy ${policyId} not found`);

    const violations: string[] = [];
    const warnings: string[] = [];

    if (config.privileged) {
      if (policyId !== 'privileged') {
        violations.push('Privileged mode is not allowed by this policy');
      }
    }

    if (config.capabilities) {
      const allCapabilities = this.getAllCapabilities();

      if (config.capabilities.add) {
        for (const cap of config.capabilities.add) {
          if (!this.isCapabilityAllowed(cap, policy)) {
            violations.push(`Capability ${cap} is not allowed by policy`);
          }
        }
      }

      if (config.capabilities.drop) {
        for (const cap of config.capabilities.drop) {
          if (!this.isCapabilityDroppable(cap, policy)) {
            warnings.push(`Capability ${cap} cannot be dropped`);
          }
        }
      }
    }

    if (config.noNewPrivileges === false) {
      warnings.push('noNewPrivileges is disabled, which reduces security');
    }

    if (config.seccompProfile === 'unconfined') {
      if (policy.rules.some(r => r.type === 'seccomp' && r.action === 'allow' && r.target === 'all')) {
        warnings.push('Seccomp is disabled, which reduces security');
      } else {
        violations.push('Unconfined seccomp profile is not allowed');
      }
    }

    return {
      allowed: violations.length === 0,
      violations,
      warnings,
    };
  }

  private isCapabilityAllowed(cap: Capability, policy: SecurityPolicy): boolean {
    const capRules = policy.rules.filter(r => r.type === 'capability');

    for (const rule of capRules) {
      if (rule.target === '*' || rule.target === cap) {
        return rule.action === 'allow';
      }
    }

    return false;
  }

  private isCapabilityDroppable(cap: Capability, policy: SecurityPolicy): boolean {
    const capRules = policy.rules.filter(r => r.type === 'capability');
    const denyRule = capRules.find(r => r.target === cap && r.action === 'deny');
    return !denyRule;
  }

  private getAllCapabilities(): Capability[] {
    return [
      'net_bind_service', 'sys_admin', 'sys_PTRACE', 'net_raw', 'dac_override',
      'setuid', 'setgid', 'chown', 'mknod', 'audit_write', 'setfcap',
      'sys_chroot', 'kill', 'fowner', 'fsetid', 'sys_resource', 'sys_nice',
      'sys_time', 'sys_tty_config', 'audit_control', 'mac_admin', 'mac_override',
      'syslog', 'wake_alarm', 'block_suspend', 'perfmon',
    ];
  }

  createPolicy(config: Omit<SecurityPolicy, 'id' | 'created'>): SecurityPolicy {
    const id = `policy-${Date.now()}`;
    const policy: SecurityPolicy = { id, ...config, created: new Date() };
    this.policies.set(id, policy);
    this.emit('policy:create', policy);
    return policy;
  }

  async removePolicy(policyId: string): Promise<void> {
    if (policyId === 'default' || policyId === 'privileged' || policyId === 'restricted') {
      throw new Error('Cannot remove built-in policy');
    }
    if (!this.policies.has(policyId)) throw new Error(`Policy ${policyId} not found`);
    this.policies.delete(policyId);
    this.emit('policy:remove', { id: policyId });
  }

  async inspectPolicy(policyId: string): Promise<SecurityPolicy> {
    const policy = this.policies.get(policyId);
    if (!policy) throw new Error(`Policy ${policyId} not found`);
    return { ...policy, rules: [...policy.rules] };
  }

  async listPolicies(): Promise<SecurityPolicy[]> {
    return Array.from(this.policies.values());
  }

  logSecurityEvent(event: Omit<SecurityEvent, 'id' | 'timestamp'>): void {
    const securityEvent: SecurityEvent = {
      id: `se-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      ...event,
      timestamp: new Date(),
    };

    this.events.push(securityEvent);
    if (this.events.length > this.options.maxEvents) {
      this.events.splice(0, this.events.length - this.options.maxEvents);
    }

    this.emit('security:event', securityEvent);
  }

  async getSecurityEvents(filters?: { containerId?: string; type?: string; severity?: string }): Promise<SecurityEvent[]> {
    let result = [...this.events];

    if (filters) {
      if (filters.containerId) result = result.filter(e => e.containerId === filters.containerId);
      if (filters.type) result = result.filter(e => e.type === filters.type);
      if (filters.severity) result = result.filter(e => e.severity === filters.severity);
    }

    return result;
  }

  async generateSecurityReport(): Promise<{
    totalEvents: number;
    eventsByType: Record<string, number>;
    eventsBySeverity: Record<string, number>;
    topContainers: { containerId: string; count: number }[];
    policyViolations: number;
  }> {
    const eventsByType: Record<string, number> = {};
    const eventsBySeverity: Record<string, number> = {};
    const containerCounts: Map<string, number> = new Map();
    let policyViolations = 0;

    for (const event of this.events) {
      eventsByType[event.type] = (eventsByType[event.type] || 0) + 1;
      eventsBySeverity[event.severity] = (eventsBySeverity[event.severity] || 0) + 1;

      const count = containerCounts.get(event.containerId) || 0;
      containerCounts.set(event.containerId, count + 1);

      if (event.type === 'capability_check' || event.type === 'privilege_escalation') {
        policyViolations++;
      }
    }

    const topContainers = Array.from(containerCounts.entries())
      .map(([containerId, count]) => ({ containerId, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    return {
      totalEvents: this.events.length,
      eventsByType,
      eventsBySeverity,
      topContainers,
      policyViolations,
    };
  }

  getPolicyCount(): number {
    return this.policies.size;
  }

  getEventCount(): number {
    return this.events.length;
  }
}

// ArcanisCloud - Auto Scaler

import { EventEmitter } from 'events';
import { AutoScalePolicy, ScaleMetric, Metric } from '../types.js';
import { generateId, sleep } from '../utils.js';

export interface AutoScalerOptions {
  evaluationInterval?: number;
  defaultCooldown?: number;
}

export interface ScaleAction {
  serviceId: string;
  direction: 'up' | 'down';
  currentReplicas: number;
  desiredReplicas: number;
  reason: string;
  timestamp: Date;
}

export class AutoScaler extends EventEmitter {
  private policies: Map<string, AutoScalePolicy> = new Map();
  private lastScaleActions: Map<string, Date> = new Map();
  private metrics: Metric[] = [];
  private options: Required<AutoScalerOptions>;

  constructor(options: AutoScalerOptions = {}) {
    super();
    this.options = {
      evaluationInterval: options.evaluationInterval || 30000,
      defaultCooldown: options.defaultCooldown || 300,
    };
  }

  createPolicy(config: Omit<AutoScalePolicy, 'id'>): AutoScalePolicy {
    const id = generateId(12);
    const policy: AutoScalePolicy = { id, ...config };
    this.policies.set(id, policy);
    this.emit('policy:create', policy);
    return policy;
  }

  async removePolicy(policyId: string): Promise<void> {
    if (!this.policies.has(policyId)) throw new Error(`Policy ${policyId} not found`);
    this.policies.delete(policyId);
    this.emit('policy:remove', { id: policyId });
  }

  ingestMetric(metric: Metric): void {
    this.metrics.push(metric);
    if (this.metrics.length > 10000) this.metrics.splice(0, this.metrics.length - 10000);
  }

  async evaluate(serviceId: string, currentReplicas: number): Promise<ScaleAction | undefined> {
    const policy = Array.from(this.policies.values()).find(p => p.serviceId === serviceId);
    if (!policy) return undefined;

    const lastAction = this.lastScaleActions.get(serviceId);
    if (lastAction) {
      const elapsed = (Date.now() - lastAction.getTime()) / 1000;
      if (elapsed < policy.cooldown) return undefined;
    }

    for (const metric of policy.metrics) {
      const value = this.getMetricValue(metric);
      if (value === undefined) continue;

      if (metric.type === 'cpu' || metric.type === 'memory') {
        if (value > metric.target && currentReplicas < policy.maxReplicas) {
          const desired = Math.min(policy.maxReplicas, currentReplicas + 1);
          const action: ScaleAction = {
            serviceId, direction: 'up', currentReplicas, desiredReplicas: desired,
            reason: `${metric.type} ${metric.operator} ${metric.target} (current: ${value.toFixed(2)})`,
            timestamp: new Date(),
          };
          this.lastScaleActions.set(serviceId, new Date());
          this.emit('scale', action);
          return action;
        }

        if (value < metric.target * 0.5 && currentReplicas > policy.minReplicas) {
          const desired = Math.max(policy.minReplicas, currentReplicas - 1);
          const action: ScaleAction = {
            serviceId, direction: 'down', currentReplicas, desiredReplicas: desired,
            reason: `${metric.type} below threshold (current: ${value.toFixed(2)})`,
            timestamp: new Date(),
          };
          this.lastScaleActions.set(serviceId, new Date());
          this.emit('scale', action);
          return action;
        }
      }
    }

    return undefined;
  }

  private getMetricValue(metric: ScaleMetric): number | undefined {
    const matching = this.metrics.filter(m => m.name === metric.type || m.type === metric.type);
    if (matching.length === 0) return undefined;

    const values = matching.map(m => m.value);
    switch (metric.operator) {
      case 'avg': return values.reduce((s, v) => s + v, 0) / values.length;
      case 'max': return Math.max(...values);
      case 'p95': return values.sort((a, b) => a - b)[Math.floor(values.length * 0.95)];
      case 'p99': return values.sort((a, b) => a - b)[Math.floor(values.length * 0.99)];
      default: return values[values.length - 1];
    }
  }

  getPolicy(policyId: string): AutoScalePolicy | undefined { return this.policies.get(policyId); }
  listPolicies(): AutoScalePolicy[] { return Array.from(this.policies.values()); }
  getPolicyCount(): number { return this.policies.size; }
  getMetricCount(): number { return this.metrics.length; }

  getRecentActions(serviceId?: string): ScaleAction[] {
    const actions: ScaleAction[] = [];
    this.emit('actions:collect', actions);
    return actions;
  }
}

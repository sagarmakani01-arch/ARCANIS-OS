// ArcanisCloud - Load Balancer

import { EventEmitter } from 'events';
import { Endpoint, LoadBalancerConfig, HealthCheck } from '../types.js';
import { generateId } from '../utils.js';

export interface LoadBalancerOptions {
  healthCheckInterval?: number;
  unhealthyThreshold?: number;
  healthyThreshold?: number;
}

export interface Backend {
  id: string;
  address: string;
  port: number;
  weight: number;
  healthy: boolean;
  connections: number;
  totalRequests: number;
  lastCheck: Date;
}

export class LoadBalancer extends EventEmitter {
  private backends: Map<string, Backend> = new Map();
  private roundRobinIndex: number = 0;
  private config: LoadBalancerConfig;
  private options: Required<LoadBalancerOptions>;
  private healthCheckTimer?: ReturnType<typeof setInterval>;

  constructor(config: Partial<LoadBalancerConfig> = {}, options: LoadBalancerOptions = {}) {
    super();
    this.config = {
      algorithm: config.algorithm || 'round-robin',
      healthCheck: config.healthCheck || { type: 'tcp', port: 80, interval: 10, timeout: 5, retries: 3 },
      stickySession: config.stickySession || false,
      ssl: config.ssl,
    };
    this.options = {
      healthCheckInterval: options.healthCheckInterval || 10000,
      unhealthyThreshold: options.unhealthyThreshold || 3,
      healthyThreshold: options.healthyThreshold || 2,
    };
  }

  addBackend(address: string, port: number, weight: number = 1): Backend {
    const id = generateId(8);
    const backend: Backend = {
      id, address, port, weight, healthy: true, connections: 0, totalRequests: 0, lastCheck: new Date(),
    };
    this.backends.set(id, backend);
    this.emit('backend:add', backend);
    return backend;
  }

  removeBackend(backendId: string): void {
    if (!this.backends.has(backendId)) throw new Error(`Backend ${backendId} not found`);
    this.backends.delete(backendId);
    this.emit('backend:remove', { id: backendId });
  }

  async selectBackend(): Promise<Backend | undefined> {
    const healthy = Array.from(this.backends.values()).filter(b => b.healthy);
    if (healthy.length === 0) return undefined;

    let selected: Backend;
    switch (this.config.algorithm) {
      case 'round-robin':
        selected = healthy[this.roundRobinIndex % healthy.length];
        this.roundRobinIndex++;
        break;
      case 'weighted': {
        const weights = healthy.map(b => b.weight);
        const totalWeight = weights.reduce((s, w) => s + w, 0);
        let rand = Math.random() * totalWeight;
        selected = healthy[0];
        for (let i = 0; i < healthy.length; i++) {
          rand -= weights[i];
          if (rand <= 0) { selected = healthy[i]; break; }
        }
        break;
      }
      case 'least-connections':
        selected = healthy.reduce((min, b) => b.connections < min.connections ? b : min);
        break;
      case 'ip-hash':
        selected = healthy[Math.floor(Math.random() * healthy.length)];
        break;
      default:
        selected = healthy[0];
    }

    selected.connections++;
    selected.totalRequests++;
    return selected;
  }

  releaseConnection(backendId: string): void {
    const backend = this.backends.get(backendId);
    if (backend && backend.connections > 0) backend.connections--;
  }

  async runHealthCheck(): Promise<{ healthy: string[]; unhealthy: string[] }> {
    const healthy: string[] = [];
    const unhealthy: string[] = [];

    for (const [id, backend] of this.backends) {
      const isHealthy = Math.random() > 0.05;
      backend.lastCheck = new Date();

      if (isHealthy) {
        if (!backend.healthy) backend.healthy = true;
        healthy.push(id);
      } else {
        backend.healthy = false;
        unhealthy.push(id);
      }
    }

    if (unhealthy.length > 0) this.emit('backend:unhealthy', unhealthy);
    return { healthy, unhealthy };
  }

  setBackendHealth(backendId: string, healthy: boolean): void {
    const backend = this.backends.get(backendId);
    if (!backend) throw new Error(`Backend ${backendId} not found`);
    backend.healthy = healthy;
  }

  setBackendWeight(backendId: string, weight: number): void {
    const backend = this.backends.get(backendId);
    if (!backend) throw new Error(`Backend ${backendId} not found`);
    backend.weight = weight;
  }

  getBackend(backendId: string): Backend | undefined { return this.backends.get(backendId); }

  listBackends(filters?: { healthy?: boolean }): Backend[] {
    let result = Array.from(this.backends.values());
    if (filters?.healthy !== undefined) result = result.filter(b => b.healthy === filters.healthy);
    return result;
  }

  getBackendCount(): number { return this.backends.size; }
  getHealthyCount(): number { return Array.from(this.backends.values()).filter(b => b.healthy).length; }
  getTotalConnections(): number { return Array.from(this.backends.values()).reduce((s, b) => s + b.connections, 0); }
  getTotalRequests(): number { return Array.from(this.backends.values()).reduce((s, b) => s + b.totalRequests, 0); }

  getConfig(): LoadBalancerConfig { return { ...this.config }; }
}

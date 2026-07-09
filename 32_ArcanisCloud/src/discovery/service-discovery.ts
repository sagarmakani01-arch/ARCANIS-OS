// ArcanisCloud - Service Discovery

import { EventEmitter } from 'events';
import { Service, Endpoint, HealthCheck } from '../types.js';
import { generateServiceId, generateId, sleep } from '../utils.js';

export interface ServiceRegistryOptions {
  healthCheckInterval?: number;
  deregistrationTimeout?: number;
  maxServices?: number;
}

export interface ServiceEntry {
  service: Service;
  endpoints: Map<string, Endpoint>;
  lastUpdated: Date;
}

export class ServiceDiscovery extends EventEmitter {
  private registry: Map<string, ServiceEntry> = new Map();
  private options: Required<ServiceRegistryOptions>;

  constructor(options: ServiceRegistryOptions = {}) {
    super();
    this.options = {
      healthCheckInterval: options.healthCheckInterval || 10000,
      deregistrationTimeout: options.deregistrationTimeout || 30000,
      maxServices: options.maxServices || 5000,
    };
  }

  async register(config: {
    name: string;
    namespace?: string;
    address: string;
    port: number;
    tags?: string[];
    meta?: Record<string, string>;
  }): Promise<Service> {
    if (this.registry.size >= this.options.maxServices) {
      throw new Error(`Maximum service limit reached (${this.options.maxServices})`);
    }

    const existing = Array.from(this.registry.values()).find(e => e.service.name === config.name && e.service.namespace === (config.namespace || 'default'));
    if (existing) {
      const endpoint: Endpoint = {
        nodeId: generateId(8),
        address: config.address,
        port: config.port,
        healthy: true,
      };
      existing.endpoints.set(endpoint.nodeId, endpoint);
      existing.lastUpdated = new Date();
      this.emit('service:update', existing.service);
      return existing.service;
    }

    const id = generateServiceId();
    const service: Service = {
      id, name: config.name, namespace: config.namespace || 'default',
      image: '', replicas: 1, runningReplicas: 1, state: 'running',
      config: { labels: config.meta }, endpoints: [],
      createdAt: new Date(), updatedAt: new Date(),
    };

    const endpoint: Endpoint = { nodeId: generateId(8), address: config.address, port: config.port, healthy: true };
    const entry: ServiceEntry = { service, endpoints: new Map([[endpoint.nodeId, endpoint]]), lastUpdated: new Date() };
    this.registry.set(id, entry);

    this.emit('service:register', service);
    return service;
  }

  async deregister(serviceId: string): Promise<void> {
    if (!this.registry.has(serviceId)) throw new Error(`Service ${serviceId} not found`);
    this.registry.delete(serviceId);
    this.emit('service:deregister', { id: serviceId });
  }

  async deregisterEndpoint(serviceId: string, endpointId: string): Promise<void> {
    const entry = this.registry.get(serviceId);
    if (!entry) throw new Error(`Service ${serviceId} not found`);
    if (!entry.endpoints.has(endpointId)) throw new Error(`Endpoint ${endpointId} not found`);
    entry.endpoints.delete(endpointId);
    if (entry.endpoints.size === 0) this.registry.delete(serviceId);
    this.emit('endpoint:deregister', { serviceId, endpointId });
  }

  async discover(serviceName: string, namespace?: string): Promise<Endpoint[]> {
    const entries = Array.from(this.registry.values()).filter(e =>
      e.service.name === serviceName && (namespace ? e.service.namespace === namespace : true)
    );
    const endpoints: Endpoint[] = [];
    for (const entry of entries) {
      for (const ep of entry.endpoints.values()) {
        if (ep.healthy) endpoints.push(ep);
      }
    }
    return endpoints;
  }

  async discoverService(serviceId: string): Promise<Service | undefined> {
    const entry = this.registry.get(serviceId);
    return entry ? entry.service : undefined;
  }

  async getHealthyEndpoints(serviceId: string): Promise<Endpoint[]> {
    const entry = this.registry.get(serviceId);
    if (!entry) return [];
    return Array.from(entry.endpoints.values()).filter(e => e.healthy);
  }

  async setEndpointHealth(serviceId: string, endpointId: string, healthy: boolean): Promise<void> {
    const entry = this.registry.get(serviceId);
    if (!entry) throw new Error(`Service ${serviceId} not found`);
    const endpoint = entry.endpoints.get(endpointId);
    if (!endpoint) throw new Error(`Endpoint ${endpointId} not found`);
    endpoint.healthy = healthy;
    this.emit('endpoint:health', { serviceId, endpointId, healthy });
  }

  listServices(namespace?: string): Service[] {
    return Array.from(this.registry.values())
      .filter(e => !namespace || e.service.namespace === namespace)
      .map(e => e.service);
  }

  getServiceCount(): number { return this.registry.size; }

  getEndpointCount(): number {
    return Array.from(this.registry.values()).reduce((sum, e) => sum + e.endpoints.size, 0);
  }

  async getServicesByTag(tag: string): Promise<Service[]> {
    return Array.from(this.registry.values())
      .filter(e => e.service.config.labels && e.service.config.labels[tag])
      .map(e => e.service);
  }
}

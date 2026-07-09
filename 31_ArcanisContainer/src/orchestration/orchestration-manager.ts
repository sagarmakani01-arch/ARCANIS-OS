// ArcanisContainer - Orchestration Manager

import { EventEmitter } from 'events';
import { Service, Task, ServiceConfig, ServiceState, UpdateConfig, ContainerConfig } from '../types.js';
import { generateServiceId, generateTaskId, sleep } from '../utils.js';
import { ContainerRuntime } from '../runtime/container-runtime.js';

export interface OrchestrationOptions {
  maxServices?: number;
  maxReplicas?: number;
  defaultUpdateDelay?: number;
}

export class OrchestrationManager extends EventEmitter {
  private services: Map<string, Service> = new Map();
  private runtime: ContainerRuntime;
  private options: Required<OrchestrationOptions>;

  constructor(runtime: ContainerRuntime, options: OrchestrationOptions = {}) {
    super();
    this.runtime = runtime;
    this.options = {
      maxServices: options.maxServices || 128,
      maxReplicas: options.maxReplicas || 1000,
      defaultUpdateDelay: options.defaultUpdateDelay || 5000,
    };
  }

  async createService(config: {
    name: string;
    image: string;
    replicas?: number;
    serviceConfig?: ServiceConfig;
  }): Promise<Service> {
    if (this.services.size >= this.options.maxServices) {
      throw new Error(`Maximum service limit reached (${this.options.maxServices})`);
    }

    const replicas = config.replicas || 1;
    if (replicas > this.options.maxReplicas) {
      throw new Error(`Maximum replica limit reached (${this.options.maxReplicas})`);
    }

    const id = generateServiceId();
    const now = new Date();

    const tasks: Task[] = Array.from({ length: replicas }, (_, i) => ({
      id: generateTaskId(),
      serviceId: id,
      slot: i + 1,
      state: 'pending' as ServiceState,
      desiredState: 'running' as ServiceState,
      created: now,
      updated: now,
    }));

    const service: Service = {
      id,
      name: config.name,
      image: config.image,
      replicas,
      runningReplicas: 0,
      state: 'pending',
      config: config.serviceConfig || {},
      tasks,
      created: now,
      updated: now,
    };

    this.services.set(id, service);
    this.emit('service:create', service);
    return service;
  }

  async removeService(serviceId: string, force: boolean = false): Promise<void> {
    const service = this.services.get(serviceId);
    if (!service) throw new Error(`Service ${serviceId} not found`);

    if (service.runningReplicas > 0 && !force) {
      throw new Error('Service has running tasks. Use force to remove.');
    }

    for (const task of service.tasks) {
      if (task.containerId) {
        try { await this.runtime.remove(task.containerId, true); } catch { }
      }
    }

    this.services.delete(serviceId);
    this.emit('service:remove', service);
  }

  async scaleService(serviceId: string, replicas: number): Promise<Service> {
    const service = this.services.get(serviceId);
    if (!service) throw new Error(`Service ${serviceId} not found`);
    if (replicas > this.options.maxReplicas) {
      throw new Error(`Maximum replica limit reached (${this.options.maxReplicas})`);
    }

    const oldReplicas = service.replicas;
    service.replicas = replicas;

    if (replicas > oldReplicas) {
      for (let i = oldReplicas; i < replicas; i++) {
        const task: Task = {
          id: generateTaskId(),
          serviceId: service.id,
          slot: i + 1,
          state: 'pending',
          desiredState: 'running',
          created: new Date(),
          updated: new Date(),
        };
        service.tasks.push(task);
        await this.deployTask(service, task);
      }
    } else if (replicas < oldReplicas) {
      const tasksToRemove = service.tasks.splice(replicas);
      for (const task of tasksToRemove) {
        if (task.containerId) {
          try { await this.runtime.stop(task.containerId, 5); } catch { }
          try { await this.runtime.remove(task.containerId, true); } catch { }
        }
        service.runningReplicas--;
      }
    }

    service.updated = new Date();
    this.emit('service:scale', service);
    return service;
  }

  async updateService(serviceId: string, config: { image?: string; replicas?: number; updateConfig?: UpdateConfig }): Promise<Service> {
    const service = this.services.get(serviceId);
    if (!service) throw new Error(`Service ${serviceId} not found`);

    service.state = 'updating';
    service.updated = new Date();

    if (config.image) {
      service.image = config.image;
    }

    if (config.replicas !== undefined) {
      await this.scaleService(serviceId, config.replicas);
    }

    const updateConfig = config.updateConfig || service.config.updateConfig;
    const parallelism = updateConfig?.parallelism || 1;

    let updated = 0;
    for (const task of service.tasks) {
      if (task.state === 'running' && config.image) {
        if (task.containerId) {
          try { await this.runtime.stop(task.containerId, 5); } catch { }
          try { await this.runtime.remove(task.containerId, true); } catch { }
        }
        await this.deployTask(service, task);
        updated++;

        if (updated % parallelism === 0 && updateConfig?.delay) {
          await sleep(updateConfig.delay);
        }
      }
    }

    service.state = 'running';
    service.runningReplicas = service.tasks.filter(t => t.state === 'running').length;
    service.updated = new Date();

    this.emit('service:update', service);
    return service;
  }

  async rollbackService(serviceId: string): Promise<Service> {
    const service = this.services.get(serviceId);
    if (!service) throw new Error(`Service ${serviceId} not found`);

    this.emit('service:rollback:start', service);

    for (const task of service.tasks) {
      if (task.containerId) {
        try { await this.runtime.stop(task.containerId, 5); } catch { }
        try { await this.runtime.remove(task.containerId, true); } catch { }
        await this.deployTask(service, task);
      }
    }

    service.runningReplicas = service.tasks.filter(t => t.state === 'running').length;
    service.updated = new Date();

    this.emit('service:rollback:complete', service);
    return service;
  }

  private async deployTask(service: Service, task: Task): Promise<void> {
    try {
      const containerConfig: ContainerConfig = {
        name: `${service.name}-task-${task.slot}`,
        image: service.image,
        command: service.config.command,
        env: service.config.env,
        ports: service.config.ports,
        resources: service.config.resources,
        restartPolicy: service.config.restartPolicy,
        labels: {
          ...service.config.labels,
          'com.arcanis.service.id': service.id,
          'com.arcanis.task.id': task.id,
          'com.arcanis.task.slot': String(task.slot),
        },
      };

      const container = await this.runtime.create(containerConfig);
      task.containerId = container.id;
      await this.runtime.start(container.id);

      task.state = 'running';
      task.updated = new Date();
      service.runningReplicas++;
    } catch (error) {
      task.state = 'failed';
      task.updated = new Date();
      service.state = 'failed';
    }
  }

  async inspectService(serviceId: string): Promise<Service> {
    const service = this.services.get(serviceId);
    if (!service) throw new Error(`Service ${serviceId} not found`);
    return { ...service, tasks: [...service.tasks] };
  }

  async listServices(filters?: { name?: string; state?: ServiceState }): Promise<Service[]> {
    let result = Array.from(this.services.values());

    if (filters) {
      if (filters.name) {
        result = result.filter(s => s.name.includes(filters.name!));
      }
      if (filters.state) {
        result = result.filter(s => s.state === filters.state);
      }
    }

    return result;
  }

  async getServiceTasks(serviceId: string): Promise<Task[]> {
    const service = this.services.get(serviceId);
    if (!service) throw new Error(`Service ${serviceId} not found`);
    return [...service.tasks];
  }

  async getTask(taskId: string): Promise<Task | undefined> {
    for (const service of this.services.values()) {
      const task = service.tasks.find(t => t.id === taskId);
      if (task) return task;
    }
    return undefined;
  }

  async startAll(): Promise<void> {
    for (const service of this.services.values()) {
      if (service.state === 'pending') {
        for (const task of service.tasks) {
          if (task.state === 'pending') {
            await this.deployTask(service, task);
          }
        }
        service.state = 'running';
        service.runningReplicas = service.tasks.filter(t => t.state === 'running').length;
      }
    }
  }

  async stopAll(): Promise<void> {
    for (const service of this.services.values()) {
      for (const task of service.tasks) {
        if (task.containerId && task.state === 'running') {
          try { await this.runtime.stop(task.containerId, 5); } catch { }
          task.state = 'stopped';
          task.updated = new Date();
        }
      }
      service.runningReplicas = 0;
      service.state = 'stopped';
      service.updated = new Date();
    }
  }

  getServiceCount(): number {
    return this.services.size;
  }

  getTotalReplicas(): number {
    return Array.from(this.services.values()).reduce((sum, s) => sum + s.replicas, 0);
  }
}

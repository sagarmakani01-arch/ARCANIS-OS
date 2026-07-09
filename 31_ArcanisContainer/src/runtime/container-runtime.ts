// ArcanisContainer - Container Runtime

import { EventEmitter } from 'events';
import {
  Container, ContainerConfig, ContainerState, LogEntry, ContainerStats
} from '../types.js';
import { generateContainerId, sleep } from '../utils.js';

export interface RuntimeOptions {
  rootDir?: string;
  maxContainers?: number;
  defaultStopTimeout?: number;
  logMaxSize?: number;
}

export class ContainerRuntime extends EventEmitter {
  private containers: Map<string, Container> = new Map();
  private options: Required<RuntimeOptions>;
  private containerLogs: Map<string, LogEntry[]> = new Map();

  constructor(options: RuntimeOptions = {}) {
    super();
    this.options = {
      rootDir: options.rootDir || '/var/lib/arcanis/containers',
      maxContainers: options.maxContainers || 256,
      defaultStopTimeout: options.defaultStopTimeout || 10,
      logMaxSize: options.logMaxSize || 10000,
    };
  }

  async create(config: ContainerConfig): Promise<Container> {
    if (this.containers.size >= this.options.maxContainers) {
      throw new Error(`Maximum container limit reached (${this.options.maxContainers})`);
    }

    const id = config.id || generateContainerId();
    if (this.containers.has(id)) {
      throw new Error(`Container ${id} already exists`);
    }

    const container: Container = {
      id,
      name: config.name,
      image: config.image,
      state: 'created',
      config: { ...config, id },
      created: new Date(),
      logs: [],
      mounts: [],
    };

    this.containers.set(id, container);
    this.containerLogs.set(id, []);

    this.addLog(id, 'stdout', `Container ${id} created`);
    this.emit('container:create', container);

    return container;
  }

  async start(containerId: string): Promise<void> {
    const container = this.containers.get(containerId);
    if (!container) throw new Error(`Container ${containerId} not found`);
    if (container.state !== 'created' && container.state !== 'stopped') {
      throw new Error(`Cannot start container in state: ${container.state}`);
    }

    container.state = 'running';
    container.started = new Date();
    container.pid = Math.floor(Math.random() * 32768) + 1000;

    this.addLog(containerId, 'stdout', `Container ${containerId} started (PID: ${container.pid})`);
    this.emit('container:start', container);
  }

  async stop(containerId: string, timeout?: number): Promise<void> {
    const container = this.containers.get(containerId);
    if (!container) throw new Error(`Container ${containerId} not found`);
    if (container.state !== 'running' && container.state !== 'paused') {
      throw new Error(`Cannot stop container in state: ${container.state}`);
    }

    const stopTimeout = timeout ?? container.config.stopTimeout ?? this.options.defaultStopTimeout;

    this.addLog(containerId, 'stdout', `Sending SIGTERM to container ${containerId}`);
    await sleep(Math.min(stopTimeout * 100, 500));

    container.state = 'stopped';
    container.stopped = new Date();
    container.exitCode = 0;
    container.pid = undefined;

    this.addLog(containerId, 'stdout', `Container ${containerId} stopped`);
    this.emit('container:stop', container);
  }

  async restart(containerId: string, timeout?: number): Promise<void> {
    await this.stop(containerId, timeout);
    await this.start(containerId);
  }

  async pause(containerId: string): Promise<void> {
    const container = this.containers.get(containerId);
    if (!container) throw new Error(`Container ${containerId} not found`);
    if (container.state !== 'running') {
      throw new Error(`Cannot pause container in state: ${container.state}`);
    }

    container.state = 'paused';
    this.addLog(containerId, 'stdout', `Container ${containerId} paused`);
    this.emit('container:pause', container);
  }

  async unpause(containerId: string): Promise<void> {
    const container = this.containers.get(containerId);
    if (!container) throw new Error(`Container ${containerId} not found`);
    if (container.state !== 'paused') {
      throw new Error(`Cannot unpause container in state: ${container.state}`);
    }

    container.state = 'running';
    this.addLog(containerId, 'stdout', `Container ${containerId} unpaused`);
    this.emit('container:unpause', container);
  }

  async remove(containerId: string, force: boolean = false): Promise<void> {
    const container = this.containers.get(containerId);
    if (!container) throw new Error(`Container ${containerId} not found`);

    if (container.state === 'running' && !force) {
      throw new Error('Container is running. Use force to remove.');
    }

    if (container.state === 'running') {
      await this.stop(containerId, 0);
    }

    container.state = 'deleted';
    this.containers.delete(containerId);
    this.containerLogs.delete(containerId);

    this.emit('container:remove', container);
  }

  async inspect(containerId: string): Promise<Container> {
    const container = this.containers.get(containerId);
    if (!container) throw new Error(`Container ${containerId} not found`);
    return { ...container };
  }

  async list(filters?: { name?: string; state?: ContainerState; image?: string }): Promise<Container[]> {
    let result = Array.from(this.containers.values());

    if (filters) {
      if (filters.name) {
        result = result.filter(c => c.name.includes(filters.name!));
      }
      if (filters.state) {
        result = result.filter(c => c.state === filters.state);
      }
      if (filters.image) {
        result = result.filter(c => c.image === filters.image);
      }
    }

    return result;
  }

  async logs(containerId: string, options?: { follow?: boolean; tail?: number; since?: Date }): Promise<LogEntry[]> {
    const container = this.containers.get(containerId);
    if (!container) throw new Error(`Container ${containerId} not found`);

    let logs = this.containerLogs.get(containerId) || [];

    if (options?.since) {
      logs = logs.filter(l => l.timestamp >= options.since!);
    }
    if (options?.tail) {
      logs = logs.slice(-options.tail);
    }

    return [...logs];
  }

  async exec(containerId: string, command: string[], options?: { user?: string; workingDir?: string; env?: Record<string, string> }): Promise<{ exitCode: number; output: string }> {
    const container = this.containers.get(containerId);
    if (!container) throw new Error(`Container ${containerId} not found`);
    if (container.state !== 'running') {
      throw new Error('Container is not running');
    }

    this.addLog(containerId, 'stdout', `[exec] ${command.join(' ')}`);

    return {
      exitCode: 0,
      output: `Executed: ${command.join(' ')}`,
    };
  }

  async stats(containerId: string): Promise<ContainerStats> {
    const container = this.containers.get(containerId);
    if (!container) throw new Error(`Container ${containerId} not found`);
    if (container.state !== 'running') {
      throw new Error('Container is not running');
    }

    return {
      cpuStats: {
        cpuUsage: Math.random() * 50,
        systemCpuUsage: Math.random() * 80,
        onlineCpus: 4,
        throttlingData: { periods: 0, throttledPeriods: 0, throttledTime: 0 },
      },
      memoryStats: {
        usage: Math.floor(Math.random() * 1024 * 1024 * 100),
        limit: container.config.resources?.memory || 512 * 1024 * 1024,
        maxUsage: Math.floor(Math.random() * 1024 * 1024 * 200),
        rss: Math.floor(Math.random() * 1024 * 1024 * 80),
        cache: Math.floor(Math.random() * 1024 * 1024 * 20),
        swap: 0,
      },
      networkStats: {
        rxBytes: Math.floor(Math.random() * 1024 * 1024),
        txBytes: Math.floor(Math.random() * 1024 * 1024),
        rxPackets: Math.floor(Math.random() * 10000),
        txPackets: Math.floor(Math.random() * 10000),
        rxErrors: 0,
        txErrors: 0,
        rxDropped: 0,
        txDropped: 0,
      },
      ioStats: {
        readBytes: Math.floor(Math.random() * 1024 * 1024 * 10),
        writeBytes: Math.floor(Math.random() * 1024 * 1024 * 5),
        readOps: Math.floor(Math.random() * 1000),
        writeOps: Math.floor(Math.random() * 500),
      },
      timestamp: new Date(),
    };
  }

  async update(containerId: string, config: Partial<ContainerConfig>): Promise<void> {
    const container = this.containers.get(containerId);
    if (!container) throw new Error(`Container ${containerId} not found`);
    if (container.state === 'running') {
      throw new Error('Cannot update running container');
    }

    if (config.resources) container.config.resources = config.resources;
    if (config.labels) container.config.labels = { ...container.config.labels, ...config.labels };
    if (config.env) container.config.env = { ...container.config.env, ...config.env };
    if (config.restartPolicy) container.config.restartPolicy = config.restartPolicy;

    this.emit('container:update', container);
  }

  async copyToContainer(containerId: string, path: string, data: Buffer): Promise<void> {
    const container = this.containers.get(containerId);
    if (!container) throw new Error(`Container ${containerId} not found`);
    this.addLog(containerId, 'stdout', `[copy] ${data.length} bytes to ${path}`);
  }

  async copyFromContainer(containerId: string, path: string): Promise<Buffer> {
    const container = this.containers.get(containerId);
    if (!container) throw new Error(`Container ${containerId} not found`);
    this.addLog(containerId, 'stdout', `[copy] from ${path}`);
    return Buffer.from(`content of ${path}`);
  }

  private addLog(containerId: string, stream: 'stdout' | 'stderr', message: string): void {
    const logs = this.containerLogs.get(containerId) || [];
    const entry: LogEntry = { timestamp: new Date(), stream, message };
    logs.push(entry);
    if (logs.length > this.options.logMaxSize) {
      logs.splice(0, logs.length - this.options.logMaxSize);
    }
    this.containerLogs.set(containerId, logs);
    this.emit('log', { containerId, ...entry });
  }

  getContainerCount(): number {
    return this.containers.size;
  }

  getRunningCount(): number {
    return Array.from(this.containers.values()).filter(c => c.state === 'running').length;
  }
}

// ArcanisCloud - Scheduler

import { EventEmitter } from 'events';
import { Node, Task, ServiceConfig, ScheduleResult, Constraint, ResourceRequirements } from '../types.js';
import { generateTaskId, calculateAffinity } from '../utils.js';
import { ClusterManager } from '../cluster/cluster-manager.js';

export interface SchedulerOptions {
  strategy?: 'spread' | 'binpack' | 'random';
  maxRetries?: number;
}

export class Scheduler extends EventEmitter {
  private cluster: ClusterManager;
  private scheduledTasks: Map<string, Task> = new Map();
  private options: Required<SchedulerOptions>;

  constructor(cluster: ClusterManager, options: SchedulerOptions = {}) {
    super();
    this.cluster = cluster;
    this.options = {
      strategy: options.strategy || 'spread',
      maxRetries: options.maxRetries || 3,
    };
  }

  async scheduleTask(serviceId: string, config: ServiceConfig): Promise<Task> {
    const result = this.findBestNode(config);
    if (!result) throw new Error('No suitable node found for task');

    const task: Task = {
      id: generateTaskId(),
      serviceId,
      nodeId: result.nodeId,
      slot: this.scheduledTasks.size + 1,
      state: 'assigned',
      desiredState: 'running',
      status: `Scheduled on node ${result.nodeId} (score: ${result.score})`,
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    this.scheduledTasks.set(task.id, task);
    this.emit('task:scheduled', { task, result });
    return task;
  }

  findBestNode(config: ServiceConfig): ScheduleResult | undefined {
    const candidates = this.cluster.getSchedulableNodes();
    if (candidates.length === 0) return undefined;

    const scored: ScheduleResult[] = [];

    for (const node of candidates) {
      const score = this.scoreNode(node, config);
      if (score > 0) {
        scored.push({ nodeId: node.id, score, reasons: this.getScoreReasons(node, config) });
      }
    }

    if (scored.length === 0) return undefined;
    scored.sort((a, b) => b.score - a.score);

    switch (this.options.strategy) {
      case 'spread': return scored[0];
      case 'binpack': return scored[scored.length - 1];
      case 'random': return scored[Math.floor(Math.random() * scored.length)];
      default: return scored[0];
    }
  }

  private scoreNode(node: Node, config: ServiceConfig): number {
    const resources = config.resources;
    if (resources) {
      if (resources.cpuRequest && node.resources.cpuAvailable < resources.cpuRequest) return 0;
      if (resources.memoryRequest && node.resources.memoryAvailable < resources.memoryRequest) return 0;
      if (resources.gpuRequest && node.resources.gpuAvailable < resources.gpuRequest) return 0;
    }

    let score = 50;
    if (config.constraints) {
      score = calculateAffinity(node.labels, config.constraints);
    }

    const cpuUtil = 1 - (node.resources.cpuAvailable / node.resources.cpuTotal);
    const memUtil = 1 - (node.resources.memoryAvailable / node.resources.memoryTotal);

    if (this.options.strategy === 'binpack') {
      score += (cpuUtil + memUtil) * 25;
    } else if (this.options.strategy === 'spread') {
      score += (1 - cpuUtil) * 25 + (1 - memUtil) * 25;
    }

    if (node.services.length < 10) score += 5;

    return Math.max(0, Math.min(100, score));
  }

  private getScoreReasons(node: Node, config: ServiceConfig): string[] {
    const reasons: string[] = [];
    if (config.constraints) {
      for (const c of config.constraints) {
        const val = node.labels[c.key];
        reasons.push(`${c.key}=${val || 'unset'} (${c.operator} ${c.value || '*'})`);
      }
    }
    reasons.push(`CPU available: ${node.resources.cpuAvailable.toFixed(1)}`);
    reasons.push(`Memory available: ${(node.resources.memoryAvailable / 1024 / 1024 / 1024).toFixed(1)}Gi`);
    return reasons;
  }

  async updateTask(taskId: string, state: Task['state']): Promise<void> {
    const task = this.scheduledTasks.get(taskId);
    if (!task) throw new Error(`Task ${taskId} not found`);
    task.state = state;
    task.updatedAt = new Date();
    this.emit('task:update', task);
  }

  async removeTask(taskId: string): Promise<void> {
    const task = this.scheduledTasks.get(taskId);
    if (!task) throw new Error(`Task ${taskId} not found`);
    this.scheduledTasks.delete(taskId);
    this.emit('task:remove', task);
  }

  getTask(taskId: string): Task | undefined { return this.scheduledTasks.get(taskId); }

  listTasks(filters?: { serviceId?: string; nodeId?: string; state?: Task['state'] }): Task[] {
    let result = Array.from(this.scheduledTasks.values());
    if (filters?.serviceId) result = result.filter(t => t.serviceId === filters.serviceId);
    if (filters?.nodeId) result = result.filter(t => t.nodeId === filters.nodeId);
    if (filters?.state) result = result.filter(t => t.state === filters.state);
    return result;
  }

  getTaskCount(): number { return this.scheduledTasks.size; }
  getRunningTaskCount(): number { return Array.from(this.scheduledTasks.values()).filter(t => t.state === 'running').length; }

  async reschedule(taskId: string): Promise<Task | undefined> {
    const task = this.scheduledTasks.get(taskId);
    if (!task) return undefined;

    const node = this.cluster.getNode(task.nodeId || '');
    if (!node || node.state !== 'healthy') {
      this.scheduledTasks.delete(taskId);
      return this.scheduleTask(task.serviceId, {});
    }
    return task;
  }
}

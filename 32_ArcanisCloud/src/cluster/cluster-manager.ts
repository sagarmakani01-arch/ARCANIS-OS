// ArcanisCloud - Cluster Manager

import { EventEmitter } from 'events';
import { Node, NodeResources, ClusterEvent } from '../types.js';
import { generateNodeId, generateEventId, sleep } from '../utils.js';

export interface ClusterManagerOptions {
  heartbeatInterval?: number;
  unhealthyThreshold?: number;
  drainingTimeout?: number;
  maxNodes?: number;
}

export class ClusterManager extends EventEmitter {
  private nodes: Map<string, Node> = new Map();
  private events: ClusterEvent[] = [];
  private options: Required<ClusterManagerOptions>;
  private heartbeatTimer?: ReturnType<typeof setInterval>;

  constructor(options: ClusterManagerOptions = {}) {
    super();
    this.options = {
      heartbeatInterval: options.heartbeatInterval || 30000,
      unhealthyThreshold: options.unhealthyThreshold || 3,
      drainingTimeout: options.drainingTimeout || 60000,
      maxNodes: options.maxNodes || 1000,
    };
  }

  async joinNode(config: { name: string; address: string; port: number; role?: 'manager' | 'worker'; resources: NodeResources; labels?: Record<string, string> }): Promise<Node> {
    if (this.nodes.size >= this.options.maxNodes) {
      throw new Error(`Maximum node limit reached (${this.options.maxNodes})`);
    }

    const id = generateNodeId();
    const node: Node = {
      id,
      name: config.name,
      address: config.address,
      port: config.port,
      state: 'healthy',
      role: config.role || 'worker',
      resources: { ...config.resources },
      labels: config.labels || {},
      services: [],
      lastHeartbeat: new Date(),
      joinedAt: new Date(),
    };

    this.nodes.set(id, node);
    this.addEvent('node-join', id, `Node ${config.name} joined the cluster`);
    this.emit('node:join', node);
    return node;
  }

  async removeNode(nodeId: string, graceful: boolean = true): Promise<void> {
    const node = this.nodes.get(nodeId);
    if (!node) throw new Error(`Node ${nodeId} not found`);

    if (graceful) {
      node.state = 'draining';
      this.emit('node:draining', node);
      await sleep(100);
    }

    node.state = 'left';
    this.nodes.delete(nodeId);
    this.addEvent('node-leave', nodeId, `Node ${node.name} left the cluster`);
    this.emit('node:leave', node);
  }

  async heartbeat(nodeId: string, resources?: NodeResources): Promise<void> {
    const node = this.nodes.get(nodeId);
    if (!node) throw new Error(`Node ${nodeId} not found`);

    node.lastHeartbeat = new Date();
    if (resources) node.resources = { ...resources };
    if (node.state === 'unhealthy') {
      node.state = 'healthy';
      this.addEvent('node-join', nodeId, `Node ${node.name} recovered`);
      this.emit('node:recover', node);
    }
  }

  async checkHealth(): Promise<{ healthy: string[]; unhealthy: string[] }> {
    const healthy: string[] = [];
    const unhealthy: string[] = [];
    const now = Date.now();

    for (const [id, node] of this.nodes) {
      const elapsed = now - node.lastHeartbeat.getTime();
      if (elapsed > this.options.heartbeatInterval * this.options.unhealthyThreshold) {
        if (node.state === 'healthy') {
          node.state = 'unhealthy';
          this.addEvent('node-unhealthy', id, `Node ${node.name} is unhealthy`);
          this.emit('node:unhealthy', node);
        }
        unhealthy.push(id);
      } else {
        healthy.push(id);
      }
    }

    return { healthy, unhealthy };
  }

  async cordonNode(nodeId: string): Promise<void> {
    const node = this.nodes.get(nodeId);
    if (!node) throw new Error(`Node ${nodeId} not found`);
    node.labels['node.kubernetes.io/unschedulable'] = 'true';
    this.emit('node:cordon', node);
  }

  async uncordonNode(nodeId: string): Promise<void> {
    const node = this.nodes.get(nodeId);
    if (!node) throw new Error(`Node ${nodeId} not found`);
    delete node.labels['node.kubernetes.io/unschedulable'];
    this.emit('node:uncordon', node);
  }

  getNode(nodeId: string): Node | undefined {
    return this.nodes.get(nodeId);
  }

  listNodes(filters?: { role?: string; state?: NodeState; labels?: Record<string, string> }): Node[] {
    let result = Array.from(this.nodes.values());

    if (filters) {
      if (filters.role) result = result.filter(n => n.role === filters.role);
      if (filters.state) result = result.filter(n => n.state === filters.state);
      if (filters.labels) {
        for (const [key, value] of Object.entries(filters.labels)) {
          result = result.filter(n => n.labels[key] === value);
        }
      }
    }

    return result;
  }

  getSchedulableNodes(): Node[] {
    return Array.from(this.nodes.values()).filter(
      n => n.state === 'healthy' && n.labels['node.kubernetes.io/unschedulable'] !== 'true'
    );
  }

  getClusterResources(): NodeResources {
    const nodes = this.getSchedulableNodes();
    return {
      cpuTotal: nodes.reduce((s, n) => s + n.resources.cpuTotal, 0),
      cpuAvailable: nodes.reduce((s, n) => s + n.resources.cpuAvailable, 0),
      memoryTotal: nodes.reduce((s, n) => s + n.resources.memoryTotal, 0),
      memoryAvailable: nodes.reduce((s, n) => s + n.resources.memoryAvailable, 0),
      diskTotal: nodes.reduce((s, n) => s + n.resources.diskTotal, 0),
      diskAvailable: nodes.reduce((s, n) => s + n.resources.diskAvailable, 0),
      gpuTotal: nodes.reduce((s, n) => s + n.resources.gpuTotal, 0),
      gpuAvailable: nodes.reduce((s, n) => s + n.resources.gpuAvailable, 0),
    };
  }

  getNodeCount(): number { return this.nodes.size; }
  getHealthyCount(): number { return Array.from(this.nodes.values()).filter(n => n.state === 'healthy').length; }
  getWorkerCount(): number { return Array.from(this.nodes.values()).filter(n => n.role === 'worker').length; }
  getManagerCount(): number { return Array.from(this.nodes.values()).filter(n => n.role === 'manager').length; }

  getEvents(filters?: { type?: string; source?: string }): ClusterEvent[] {
    let result = [...this.events];
    if (filters?.type) result = result.filter(e => e.type === filters.type);
    if (filters?.source) result = result.filter(e => e.source === filters.source);
    return result;
  }

  private addEvent(type: ClusterEvent['type'], source: string, message: string): void {
    const event: ClusterEvent = {
      id: generateEventId(),
      type,
      source,
      message,
      timestamp: new Date(),
    };
    this.events.push(event);
    if (this.events.length > 10000) this.events.splice(0, this.events.length - 10000);
    this.emit('event', event);
  }
}

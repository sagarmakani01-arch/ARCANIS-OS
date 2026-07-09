// ArcanisContainer - Network Manager

import { EventEmitter } from 'events';
import { Network, NetworkMode } from '../types.js';
import { generateNetworkId } from '../utils.js';

export interface NetworkManagerOptions {
  defaultSubnet?: string;
  defaultGateway?: string;
  dnsServers?: string[];
}

export class NetworkManager extends EventEmitter {
  private networks: Map<string, Network> = new Map();
  private options: Required<NetworkManagerOptions>;

  constructor(options: NetworkManagerOptions = {}) {
    super();
    this.options = {
      defaultSubnet: options.defaultSubnet || '172.17.0.0/16',
      defaultGateway: options.defaultGateway || '172.17.0.1',
      dnsServers: options.dnsServers || ['8.8.8.8', '8.8.4.4'],
    };
    this.createDefaultNetworks();
  }

  private createDefaultNetworks(): void {
    this.createNetwork({
      name: 'bridge',
      driver: 'bridge',
      subnet: '172.17.0.0/16',
      gateway: '172.17.0.1',
    });

    this.createNetwork({
      name: 'host',
      driver: 'host',
      subnet: '0.0.0.0/0',
      gateway: '0.0.0.0',
    });

    this.createNetwork({
      name: 'none',
      driver: 'none',
      subnet: '0.0.0.0/0',
      gateway: '0.0.0.0',
    });
  }

  createNetwork(config: { name: string; driver: NetworkMode; subnet: string; gateway: string; ipRange?: string; options?: Record<string, string> }): Network {
    const existing = Array.from(this.networks.values()).find(n => n.name === config.name);
    if (existing) throw new Error(`Network ${config.name} already exists`);

    const network: Network = {
      id: generateNetworkId(),
      name: config.name,
      driver: config.driver,
      subnet: config.subnet,
      gateway: config.gateway,
      ipRange: config.ipRange,
      containers: new Map(),
      options: config.options,
      created: new Date(),
    };

    this.networks.set(network.id, network);
    this.emit('network:create', network);
    return network;
  }

  async removeNetwork(networkId: string): Promise<void> {
    const network = this.networks.get(networkId);
    if (!network) throw new Error(`Network ${networkId} not found`);

    if (network.name === 'bridge' || network.name === 'host' || network.name === 'none') {
      throw new Error(`Cannot remove built-in network: ${network.name}`);
    }

    if (network.containers.size > 0) {
      throw new Error('Network has active containers');
    }

    this.networks.delete(networkId);
    this.emit('network:remove', network);
  }

  async connectContainer(networkId: string, containerId: string, options?: { ipAddress?: string; aliases?: string[] }): Promise<string> {
    const network = this.networks.get(networkId);
    if (!network) throw new Error(`Network ${networkId} not found`);

    if (network.driver === 'none') {
      throw new Error('Cannot connect to none network');
    }

    const ipAddress = options?.ipAddress || this.allocateIP(network);
    network.containers.set(containerId, ipAddress);

    this.emit('network:connect', { networkId, containerId, ipAddress });
    return ipAddress;
  }

  async disconnectContainer(networkId: string, containerId: string): Promise<void> {
    const network = this.networks.get(networkId);
    if (!network) throw new Error(`Network ${networkId} not found`);

    if (!network.containers.has(containerId)) {
      throw new Error(`Container ${containerId} not connected to network ${networkId}`);
    }

    network.containers.delete(containerId);
    this.emit('network:disconnect', { networkId, containerId });
  }

  private allocateIP(network: Network): string {
    const subnetParts = network.subnet.split('/')[0].split('.').map(Number);
    const usedIPs = new Set(Array.from(network.containers.values()));

    for (let i = 2; i < 254; i++) {
      const ip = `${subnetParts[0]}.${subnetParts[1]}.${subnetParts[2]}.${i}`;
      if (!usedIPs.has(ip)) return ip;
    }

    throw new Error('No available IP addresses in subnet');
  }

  async inspect(networkId: string): Promise<Network> {
    const network = this.networks.get(networkId);
    if (!network) throw new Error(`Network ${networkId} not found`);
    return { ...network, containers: new Map(network.containers) };
  }

  async list(filters?: { name?: string; driver?: NetworkMode }): Promise<Network[]> {
    let result = Array.from(this.networks.values());

    if (filters) {
      if (filters.name) {
        result = result.filter(n => n.name.includes(filters.name!));
      }
      if (filters.driver) {
        result = result.filter(n => n.driver === filters.driver);
      }
    }

    return result;
  }

  async resolve(name: string): Promise<Network> {
    const network = Array.from(this.networks.values()).find(n => n.name === name);
    if (!network) throw new Error(`Network ${name} not found`);
    return network;
  }

  async getContainerIP(networkId: string, containerId: string): Promise<string> {
    const network = this.networks.get(networkId);
    if (!network) throw new Error(`Network ${networkId} not found`);

    const ip = network.containers.get(containerId);
    if (!ip) throw new Error(`Container ${containerId} not connected to network ${networkId}`);

    return ip;
  }

  async getConnectedContainers(networkId: string): Promise<Map<string, string>> {
    const network = this.networks.get(networkId);
    if (!network) throw new Error(`Network ${networkId} not found`);
    return new Map(network.containers);
  }

  async createOverlay(name: string, subnet: string, gateway: string): Promise<Network> {
    return this.createNetwork({ name, driver: 'overlay', subnet, gateway });
  }

  getNetworkCount(): number {
    return this.networks.size;
  }

  getDnsServers(): string[] {
    return [...this.options.dnsServers];
  }
}

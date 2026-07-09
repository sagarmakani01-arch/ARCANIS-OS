import { EventEmitter } from "events";
import {
  NetworkInterface,
  NetworkInterfaceType,
  MacAddress,
  IPv4Address,
  NetworkConfig,
  DEFAULT_NETWORK_CONFIG,
  NetworkStats,
  NetworkPacket,
  Protocol,
  PacketDirection,
  NetworkEvent,
  NetworkEventHandler,
} from "../types";
import { v4 as uuidv4 } from "uuid";

export class NetworkStack extends EventEmitter {
  private interfaces: Map<string, NetworkInterface> = new Map();
  private config: NetworkConfig;
  private stats: NetworkStats;
  private packetHandlers: Map<Protocol, (packet: NetworkPacket) => void> = new Map();
  private eventHandlers: Set<NetworkEventHandler> = new Set();
  private running: boolean = false;

  constructor(config: Partial<NetworkConfig> = {}) {
    super();
    this.config = { ...DEFAULT_NETWORK_CONFIG, ...config };
    this.stats = this.createEmptyStats();
    this.initializeLoopback();
  }

  private createEmptyStats(): NetworkStats {
    return {
      totalPacketsSent: 0,
      totalPacketsReceived: 0,
      totalBytesSent: 0,
      totalBytesReceived: 0,
      activeConnections: 0,
      totalConnections: 0,
      errors: 0,
      droppedPackets: 0,
      averageLatency: 0,
      bandwidth: 0,
    };
  }

  private initializeLoopback(): void {
    const loopback: NetworkInterface = {
      id: "lo",
      name: "lo",
      type: NetworkInterfaceType.Loopback,
      mac: { octets: [0, 0, 0, 0, 0, 0] },
      ipv4: { octets: [127, 0, 0, 1] },
      subnet: "255.0.0.0",
      gateway: "127.0.0.1",
      dns: ["127.0.0.1"],
      mtu: 65535,
      speed: 10000000000,
      status: "up",
    };
    this.interfaces.set(loopback.id, loopback);
  }

  async initialize(): Promise<void> {
    if (this.running) return;
    this.running = true;
    this.emitEvent("network:initialized", "stack", { interfaces: this.interfaces.size });
  }

  async shutdown(): Promise<void> {
    this.running = false;
    this.packetHandlers.clear();
    this.eventHandlers.clear();
    this.emitEvent("network:shutdown", "stack", {});
  }

  createInterface(
    name: string,
    type: NetworkInterfaceType,
    config: Partial<{
      mac: MacAddress;
      ipv4: IPv4Address;
      subnet: string;
      gateway: string;
      dns: string[];
      mtu: number;
      speed: number;
    }> = {}
  ): NetworkInterface {
    const id = uuidv4();
    const networkInterface: NetworkInterface = {
      id,
      name,
      type,
      mac: config.mac || this.generateMac(),
      ipv4: config.ipv4 || { octets: [192, 168, 1, 100] },
      subnet: config.subnet || "255.255.255.0",
      gateway: config.gateway || "192.168.1.1",
      dns: config.dns || ["8.8.8.8", "8.8.4.4"],
      mtu: config.mtu || 1500,
      speed: config.speed || 1000000000,
      status: "up",
    };
    this.interfaces.set(id, networkInterface);
    this.emitEvent("interface:created", "stack", { interface: networkInterface });
    return networkInterface;
  }

  removeInterface(id: string): boolean {
    const networkInterface = this.interfaces.get(id);
    if (!networkInterface || networkInterface.type === NetworkInterfaceType.Loopback) {
      return false;
    }
    this.interfaces.delete(id);
    this.emitEvent("interface:removed", "stack", { id });
    return true;
  }

  getInterface(id: string): NetworkInterface | undefined {
    return this.interfaces.get(id);
  }

  getInterfaceByName(name: string): NetworkInterface | undefined {
    for (const iface of this.interfaces.values()) {
      if (iface.name === name) return iface;
    }
    return undefined;
  }

  listInterfaces(): NetworkInterface[] {
    return Array.from(this.interfaces.values());
  }

  getActiveInterfaces(): NetworkInterface[] {
    return this.listInterfaces().filter((i) => i.status === "up");
  }

  registerPacketHandler(protocol: Protocol, handler: (packet: NetworkPacket) => void): void {
    this.packetHandlers.set(protocol, handler);
  }

  unregisterPacketHandler(protocol: Protocol): void {
    this.packetHandlers.delete(protocol);
  }

  async sendPacket(packet: NetworkPacket): Promise<boolean> {
    if (!this.running) return false;
    const handler = this.packetHandlers.get(packet.protocol);
    if (handler) {
      try {
        handler(packet);
        this.stats.totalPacketsSent++;
        this.stats.totalBytesSent += packet.size;
        this.emitEvent("packet:sent", "stack", { packet });
        return true;
      } catch {
        this.stats.errors++;
        return false;
      }
    }
    this.stats.droppedPackets++;
    return false;
  }

  receivePacket(packet: NetworkPacket): void {
    if (!this.running) return;
    const handler = this.packetHandlers.get(packet.protocol);
    if (handler) {
      try {
        handler(packet);
        this.stats.totalPacketsReceived++;
        this.stats.totalBytesReceived += packet.size;
        this.emitEvent("packet:received", "stack", { packet });
      } catch {
        this.stats.errors++;
      }
    } else {
      this.stats.droppedPackets++;
    }
  }

  onNetworkEvent(handler: NetworkEventHandler): void {
    this.eventHandlers.add(handler);
  }

  offNetworkEvent(handler: NetworkEventHandler): void {
    this.eventHandlers.delete(handler);
  }

  private emitEvent(type: string, source: string, data: unknown): void {
    const event: NetworkEvent = {
      id: uuidv4(),
      type,
      source,
      data,
      timestamp: Date.now(),
    };
    this.emit(type, event);
    for (const handler of this.eventHandlers) {
      try {
        handler(event);
      } catch {}
    }
  }

  getStats(): NetworkStats {
    return { ...this.stats };
  }

  getConfig(): NetworkConfig {
    return { ...this.config };
  }

  private generateMac(): MacAddress {
    return {
      octets: [
        Math.floor(Math.random() * 256),
        Math.floor(Math.random() * 256),
        Math.floor(Math.random() * 256),
        Math.floor(Math.random() * 256),
        Math.floor(Math.random() * 256),
        Math.floor(Math.random() * 256),
      ],
    };
  }

  static ipToString(ip: IPv4Address): string {
    return ip.octets.join(".");
  }

  static stringToIp(ip: string): IPv4Address {
    const parts = ip.split(".").map(Number);
    return {
      octets: [parts[0] || 0, parts[1] || 0, parts[2] || 0, parts[3] || 0],
    };
  }

  static macToString(mac: MacAddress): string {
    return mac.octets.map((o) => o.toString(16).padStart(2, "0")).join(":");
  }
}

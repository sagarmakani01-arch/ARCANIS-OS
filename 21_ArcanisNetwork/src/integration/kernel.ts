import { EventEmitter } from "events";
import { NetworkConfig, DEFAULT_NETWORK_CONFIG, NetworkStats } from "../types";

export interface KernelNetworkInterface {
  name: string;
  mac: string;
  ip: string;
  subnet: string;
  gateway: string;
  status: "up" | "down";
}

export interface KernelPacket {
  data: Buffer;
  source: string;
  destination: string;
  protocol: string;
  size: number;
}

export class ArcanisKernelIntegration extends EventEmitter {
  private kernelRef: unknown = null;
  private interfaces: Map<string, KernelNetworkInterface> = new Map();
  private packetHandlers: Map<string, (packet: KernelPacket) => void> = new Map();

  constructor() {
    super();
    this.registerDefaultInterface();
  }

  private registerDefaultInterface(): void {
    this.interfaces.set("eth0", {
      name: "eth0",
      mac: "00:00:00:00:00:00",
      ip: "192.168.1.100",
      subnet: "255.255.255.0",
      gateway: "192.168.1.1",
      status: "up",
    });
  }

  setKernelReference(kernel: unknown): void {
    this.kernelRef = kernel;
    this.emit("kernel:connected");
  }

  getKernelReference(): unknown {
    return this.kernelRef;
  }

  getInterfaces(): KernelNetworkInterface[] {
    return Array.from(this.interfaces.values());
  }

  addInterface(iface: KernelNetworkInterface): void {
    this.interfaces.set(iface.name, iface);
    this.emit("interface:added", iface);
  }

  removeInterface(name: string): boolean {
    const iface = this.interfaces.get(name);
    if (!iface) return false;
    this.interfaces.delete(name);
    this.emit("interface:removed", iface);
    return true;
  }

  registerPacketHandler(protocol: string, handler: (packet: KernelPacket) => void): void {
    this.packetHandlers.set(protocol, handler);
  }

  sendPacket(packet: KernelPacket): boolean {
    const handler = this.packetHandlers.get(packet.protocol);
    if (handler) {
      handler(packet);
      this.emit("packet:sent", packet);
      return true;
    }
    this.emit("packet:dropped", packet);
    return false;
  }

  receivePacket(packet: KernelPacket): void {
    this.emit("packet:received", packet);
  }

  getStats(): {
    interfaces: number;
    activeInterfaces: number;
    registeredHandlers: number;
  } {
    const ifaces = this.getInterfaces();
    return {
      interfaces: ifaces.length,
      activeInterfaces: ifaces.filter((i) => i.status === "up").length,
      registeredHandlers: this.packetHandlers.size,
    };
  }
}

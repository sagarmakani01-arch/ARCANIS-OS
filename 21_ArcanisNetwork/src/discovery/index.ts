import { EventEmitter } from "events";
import {
  NetworkInterface,
  NetworkAddress,
  NetworkConfig,
  DEFAULT_NETWORK_CONFIG,
} from "../types";
import { v4 as uuidv4 } from "uuid";

export interface DiscoveredDevice {
  id: string;
  name: string;
  type: string;
  address: NetworkAddress;
  mac: string;
  manufacturer: string;
  model: string;
  services: string[];
  lastSeen: number;
  isOnline: boolean;
  metadata: Record<string, unknown>;
}

export interface MdnsService {
  name: string;
  type: string;
  domain: string;
  port: number;
  TXT: Record<string, string>;
}

export class MDNSDiscovery extends EventEmitter {
  private services: Map<string, MdnsService> = new Map();
  private discoveredDevices: Map<string, DiscoveredDevice> = new Map();
  private multicastAddress: string = "224.0.0.251";
  private port: number = 5353;

  constructor() {
    super();
  }

  registerService(service: MdnsService): void {
    const id = uuidv4();
    this.services.set(id, { ...service, id } as MdnsService & { id: string });
    this.emit("service:registered", service);
  }

  unregisterService(name: string): boolean {
    for (const [id, service] of this.services.entries()) {
      if (service.name === name) {
        this.services.delete(id);
        this.emit("service:unregistered", service);
        return true;
      }
    }
    return false;
  }

  async discover(): Promise<DiscoveredDevice[]> {
    const devices = Array.from(this.discoveredDevices.values());
    return devices.filter((d) => d.isOnline);
  }

  addDevice(device: Omit<DiscoveredDevice, "id" | "lastSeen" | "isOnline">): DiscoveredDevice {
    const existing = this.findDeviceByMac(device.mac);
    if (existing) {
      existing.lastSeen = Date.now();
      existing.isOnline = true;
      return existing;
    }
    const newDevice: DiscoveredDevice = {
      ...device,
      id: uuidv4(),
      lastSeen: Date.now(),
      isOnline: true,
    };
    this.discoveredDevices.set(newDevice.id, newDevice);
    this.emit("device:found", newDevice);
    return newDevice;
  }

  removeDevice(id: string): boolean {
    const device = this.discoveredDevices.get(id);
    if (!device) return false;
    device.isOnline = false;
    this.emit("device:lost", device);
    return true;
  }

  findDeviceByMac(mac: string): DiscoveredDevice | undefined {
    for (const device of this.discoveredDevices.values()) {
      if (device.mac === mac) return device;
    }
    return undefined;
  }

  findDeviceByIp(ip: string): DiscoveredDevice | undefined {
    for (const device of this.discoveredDevices.values()) {
      if (device.address.ip === ip) return device;
    }
    return undefined;
  }

  getDevices(): DiscoveredDevice[] {
    return Array.from(this.discoveredDevices.values());
  }

  getOnlineDevices(): DiscoveredDevice[] {
    return this.getDevices().filter((d) => d.isOnline);
  }

  getServices(): MdnsService[] {
    return Array.from(this.services.values());
  }

  markDeviceOffline(id: string): void {
    const device = this.discoveredDevices.get(id);
    if (device) {
      device.isOnline = false;
      this.emit("device:offline", device);
    }
  }

  cleanup(maxAge: number = 300000): void {
    const now = Date.now();
    for (const [id, device] of this.discoveredDevices.entries()) {
      if (now - device.lastSeen >= maxAge) {
        device.isOnline = false;
        this.discoveredDevices.delete(id);
      }
    }
  }

  getStats(): {
    totalDevices: number;
    onlineDevices: number;
    registeredServices: number;
  } {
    const devices = this.getDevices();
    return {
      totalDevices: devices.length,
      onlineDevices: devices.filter((d) => d.isOnline).length,
      registeredServices: this.services.size,
    };
  }
}

export interface UpnpDevice {
  id: string;
  name: string;
  type: string;
  location: string;
  manufacturer: string;
  modelName: string;
  services: UpnpService[];
  lastSeen: number;
}

export interface UpnpService {
  type: string;
  controlUrl: string;
  eventSubUrl: string;
  scpdUrl: string;
}

export class UPnPDiscovery extends EventEmitter {
  private devices: Map<string, UpnpDevice> = new Map();
  private searchTimeout: number = 5000;

  constructor() {
    super();
  }

  async discover(): Promise<UpnpDevice[]> {
    return Array.from(this.devices.values());
  }

  addDevice(device: Omit<UpnpDevice, "id" | "lastSeen">): UpnpDevice {
    const newDevice: UpnpDevice = {
      ...device,
      id: uuidv4(),
      lastSeen: Date.now(),
    };
    this.devices.set(newDevice.id, newDevice);
    this.emit("device:found", newDevice);
    return newDevice;
  }

  removeDevice(id: string): boolean {
    return this.devices.delete(id);
  }

  getDevices(): UpnpDevice[] {
    return Array.from(this.devices.values());
  }

  getDeviceByType(type: string): UpnpDevice | undefined {
    return Array.from(this.devices.values()).find((d) => d.type === type);
  }

  getStats(): {
    totalDevices: number;
    totalServices: number;
  } {
    const devices = this.getDevices();
    return {
      totalDevices: devices.length,
      totalServices: devices.reduce((sum, d) => sum + d.services.length, 0),
    };
  }
}

export class DeviceManager extends EventEmitter {
  public readonly mdns: MDNSDiscovery;
  public readonly upnp: UPnPDiscovery;
  private devices: Map<string, DiscoveredDevice> = new Map();

  constructor() {
    super();
    this.mdns = new MDNSDiscovery();
    this.upnp = new UPnPDiscovery();
    this.setupEventForwarding();
  }

  private setupEventForwarding(): void {
    this.mdns.on("device:found", (device) => {
      this.devices.set(device.id, device);
      this.emit("device:found", device);
    });
    this.mdns.on("device:lost", (device) => {
      this.emit("device:lost", device);
    });
    this.upnp.on("device:found", (device) => {
      this.emit("device:found", device);
    });
  }

  async discoverAll(): Promise<DiscoveredDevice[]> {
    const mdnsDevices = await this.mdns.discover();
    return mdnsDevices;
  }

  getDevice(id: string): DiscoveredDevice | undefined {
    return this.devices.get(id);
  }

  getDevices(): DiscoveredDevice[] {
    return Array.from(this.devices.values());
  }

  getDeviceByType(type: string): DiscoveredDevice[] {
    return this.getDevices().filter((d) => d.type === type);
  }

  getDeviceByService(service: string): DiscoveredDevice[] {
    return this.getDevices().filter((d) => d.services.includes(service));
  }

  getStats(): {
    mdns: ReturnType<MDNSDiscovery["getStats"]>;
    upnp: ReturnType<UPnPDiscovery["getStats"]>;
    totalManaged: number;
  } {
    return {
      mdns: this.mdns.getStats(),
      upnp: this.upnp.getStats(),
      totalManaged: this.devices.size,
    };
  }
}

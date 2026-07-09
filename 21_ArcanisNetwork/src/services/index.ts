import { EventEmitter } from "events";
import {
  NetworkConfig,
  DEFAULT_NETWORK_CONFIG,
  NetworkAddress,
} from "../types";
import { v4 as uuidv4 } from "uuid";

export interface DnsRecord {
  id: string;
  name: string;
  type: "A" | "AAAA" | "CNAME" | "MX" | "TXT" | "NS" | "SOA";
  value: string;
  ttl: number;
  createdAt: number;
}

export interface DnsCacheEntry {
  name: string;
  records: DnsRecord[];
  cachedAt: number;
  ttl: number;
}

export class DnsResolver extends EventEmitter {
  private records: Map<string, DnsRecord[]> = new Map();
  private cache: Map<string, DnsCacheEntry> = new Map();
  private upstreamServers: string[] = ["8.8.8.8", "8.8.4.4", "1.1.1.1"];

  constructor() {
    super();
    this.addLocalRecords();
  }

  private addLocalRecords(): void {
    this.addRecord({
      name: "localhost",
      type: "A",
      value: "127.0.0.1",
      ttl: 3600,
    });
    this.addRecord({
      name: "arcanis.local",
      type: "A",
      value: "192.168.1.100",
      ttl: 3600,
    });
  }

  addRecord(record: Omit<DnsRecord, "id" | "createdAt">): DnsRecord {
    const fullRecord: DnsRecord = {
      ...record,
      id: uuidv4(),
      createdAt: Date.now(),
    };
    const existing = this.records.get(record.name) || [];
    existing.push(fullRecord);
    this.records.set(record.name, existing);
    this.emit("record:added", fullRecord);
    return fullRecord;
  }

  removeRecord(name: string, type?: string): boolean {
    if (type) {
      const records = this.records.get(name);
      if (!records) return false;
      const filtered = records.filter((r) => r.type !== type);
      if (filtered.length === records.length) return false;
      this.records.set(name, filtered);
    } else {
      this.records.delete(name);
    }
    this.emit("record:removed", { name, type });
    return true;
  }

  resolve(name: string, type: string = "A"): DnsRecord[] {
    const cached = this.cache.get(name);
    if (cached && Date.now() - cached.cachedAt < cached.ttl * 1000) {
      return cached.records.filter((r) => r.type === type);
    }
    const records = this.records.get(name) || [];
    const filtered = records.filter((r) => r.type === type);
    if (filtered.length > 0) {
      this.cache.set(name, {
        name,
        records,
        cachedAt: Date.now(),
        ttl: Math.max(...records.map((r) => r.ttl)),
      });
    }
    return filtered;
  }

  resolveIp(name: string): string | null {
    const records = this.resolve(name, "A");
    return records.length > 0 ? records[0].value : null;
  }

  getRecords(name: string): DnsRecord[] {
    return this.records.get(name) || [];
  }

  getAllRecords(): DnsRecord[] {
    const all: DnsRecord[] = [];
    for (const records of this.records.values()) {
      all.push(...records);
    }
    return all;
  }

  clearCache(): void {
    this.cache.clear();
  }

  getStats(): {
    totalRecords: number;
    cachedEntries: number;
    upstreamServers: number;
  } {
    return {
      totalRecords: this.getAllRecords().length,
      cachedEntries: this.cache.size,
      upstreamServers: this.upstreamServers.length,
    };
  }
}

export interface DhcpLease {
  id: string;
  mac: string;
  ip: string;
  hostname: string;
  leaseStart: number;
  leaseEnd: number;
  isPermanent: boolean;
}

export class DhcpServer extends EventEmitter {
  private leases: Map<string, DhcpLease> = new Map();
  private poolStart: string = "192.168.1.100";
  private poolEnd: string = "192.168.1.200";
  private subnet: string = "255.255.255.0";
  private gateway: string = "192.168.1.1";
  private dns: string[] = ["8.8.8.8", "8.8.4.4"];
  private leaseTime: number = 86400000;

  constructor() {
    super();
  }

  configure(options: {
    poolStart?: string;
    poolEnd?: string;
    subnet?: string;
    gateway?: string;
    dns?: string[];
    leaseTime?: number;
  }): void {
    if (options.poolStart) this.poolStart = options.poolStart;
    if (options.poolEnd) this.poolEnd = options.poolEnd;
    if (options.subnet) this.subnet = options.subnet;
    if (options.gateway) this.gateway = options.gateway;
    if (options.dns) this.dns = options.dns;
    if (options.leaseTime) this.leaseTime = options.leaseTime;
  }

  assignIp(mac: string, hostname: string = ""): DhcpLease | null {
    const existing = this.findLeaseByMac(mac);
    if (existing) {
      existing.leaseEnd = Date.now() + this.leaseTime;
      return existing;
    }
    const ip = this.findAvailableIp();
    if (!ip) return null;
    const lease: DhcpLease = {
      id: uuidv4(),
      mac,
      ip,
      hostname,
      leaseStart: Date.now(),
      leaseEnd: Date.now() + this.leaseTime,
      isPermanent: false,
    };
    this.leases.set(lease.id, lease);
    this.emit("lease:assigned", lease);
    return lease;
  }

  releaseIp(leaseId: string): boolean {
    const lease = this.leases.get(leaseId);
    if (!lease) return false;
    this.leases.delete(leaseId);
    this.emit("lease:released", lease);
    return true;
  }

  findLeaseByMac(mac: string): DhcpLease | undefined {
    for (const lease of this.leases.values()) {
      if (lease.mac === mac) return lease;
    }
    return undefined;
  }

  findLeaseByIp(ip: string): DhcpLease | undefined {
    for (const lease of this.leases.values()) {
      if (lease.ip === ip) return lease;
    }
    return undefined;
  }

  private findAvailableIp(): string | null {
    const startParts = this.poolStart.split(".").map(Number);
    const endParts = this.poolEnd.split(".").map(Number);
    const usedIps = new Set(Array.from(this.leases.values()).map((l) => l.ip));
    for (let i = startParts[3]; i <= endParts[3]; i++) {
      const ip = `${startParts[0]}.${startParts[1]}.${startParts[2]}.${i}`;
      if (!usedIps.has(ip)) return ip;
    }
    return null;
  }

  cleanup(): void {
    const now = Date.now();
    for (const [id, lease] of this.leases.entries()) {
      if (!lease.isPermanent && now > lease.leaseEnd) {
        this.leases.delete(id);
        this.emit("lease:expired", lease);
      }
    }
  }

  getLeases(): DhcpLease[] {
    return Array.from(this.leases.values());
  }

  getStats(): {
    totalLeases: number;
    activeLeases: number;
    poolSize: number;
  } {
    const leases = this.getLeases();
    const startParts = this.poolStart.split(".").map(Number);
    const endParts = this.poolEnd.split(".").map(Number);
    return {
      totalLeases: leases.length,
      activeLeases: leases.filter((l) => l.leaseEnd > Date.now()).length,
      poolSize: endParts[3] - startParts[3] + 1,
    };
  }
}

export class LocalNetworkServices extends EventEmitter {
  public readonly dns: DnsResolver;
  public readonly dhcp: DhcpServer;

  constructor() {
    super();
    this.dns = new DnsResolver();
    this.dhcp = new DhcpServer();
  }

  initialize(): void {
    this.dhcp.configure({
      poolStart: "192.168.1.100",
      poolEnd: "192.168.1.200",
      gateway: "192.168.1.1",
    });
    this.emit("services:initialized");
  }

  getStats(): {
    dns: ReturnType<DnsResolver["getStats"]>;
    dhcp: ReturnType<DhcpServer["getStats"]>;
  } {
    return {
      dns: this.dns.getStats(),
      dhcp: this.dhcp.getStats(),
    };
  }
}

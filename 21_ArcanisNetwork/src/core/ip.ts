import { IPv4Address, NetworkAddress } from "../types";
import { NetworkStack } from "./stack";

export interface IpRoute {
  destination: string;
  gateway: string;
  interface: string;
  metric: number;
}

export interface ArpEntry {
  ip: string;
  mac: string;
  interface: string;
  timestamp: number;
}

export class IpLayer {
  private routes: IpRoute[] = [];
  private arpTable: Map<string, ArpEntry> = new Map();
  private stack: NetworkStack;

  constructor(stack: NetworkStack) {
    this.stack = stack;
    this.addDefaultRoute();
  }

  private addDefaultRoute(): void {
    this.routes.push({
      destination: "0.0.0.0",
      gateway: "192.168.1.1",
      interface: "eth0",
      metric: 1,
    });
  }

  addRoute(route: IpRoute): void {
    this.routes.push(route);
  }

  removeRoute(destination: string, gateway: string): boolean {
    const index = this.routes.findIndex(
      (r) => r.destination === destination && r.gateway === gateway
    );
    if (index === -1) return false;
    this.routes.splice(index, 1);
    return true;
  }

  getRoutes(): IpRoute[] {
    return [...this.routes];
  }

  routePacket(destinationIp: string): IpRoute | null {
    let bestRoute: IpRoute | null = null;
    let bestMetric = Infinity;
    for (const route of this.routes) {
      if (this.matchesRoute(destinationIp, route.destination)) {
        if (route.metric < bestMetric) {
          bestMetric = route.metric;
          bestRoute = route;
        }
      }
    }
    return bestRoute;
  }

  private matchesRoute(ip: string, destination: string): boolean {
    if (destination === "0.0.0.0") return true;
    const destParts = destination.split(".").map(Number);
    const ipParts = ip.split(".").map(Number);
    for (let i = 0; i < 4; i++) {
      if (destParts[i] !== 0 && destParts[i] !== ipParts[i]) {
        return false;
      }
    }
    return true;
  }

  addArpEntry(ip: string, mac: string, networkInterface: string): void {
    this.arpTable.set(ip, {
      ip,
      mac,
      interface: networkInterface,
      timestamp: Date.now(),
    });
  }

  removeArpEntry(ip: string): boolean {
    return this.arpTable.delete(ip);
  }

  getArpEntry(ip: string): ArpEntry | undefined {
    return this.arpTable.get(ip);
  }

  getArpTable(): ArpEntry[] {
    return Array.from(this.arpTable.values());
  }

  resolveMac(ip: string): string | null {
    const entry = this.arpTable.get(ip);
    return entry ? entry.mac : null;
  }

  isLocalNetwork(ip: string): boolean {
    const parts = ip.split(".").map(Number);
    if (parts[0] === 10) return true;
    if (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) return true;
    if (parts[0] === 192 && parts[1] === 168) return true;
    if (parts[0] === 127) return true;
    return false;
  }

  calculateSubnet(ip: string, subnetMask: string): string {
    const ipParts = ip.split(".").map(Number);
    const maskParts = subnetMask.split(".").map(Number);
    const networkParts = ipParts.map((part, i) => part & (maskParts[i] || 0));
    return networkParts.join(".");
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
}

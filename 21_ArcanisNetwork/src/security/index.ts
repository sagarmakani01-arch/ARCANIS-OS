import { TlsManager, Firewall, NetworkEncryption } from "./tls";
export { TlsManager, Firewall, NetworkEncryption } from "./tls";
import {
  NetworkConfig,
  DEFAULT_NETWORK_CONFIG,
  SecurityEvent,
  NetworkAddress,
} from "../types";
import { EventEmitter } from "events";
import { v4 as uuidv4 } from "uuid";

export interface SecurityConfig {
  enableTls: boolean;
  enableFirewall: boolean;
  enableEncryption: boolean;
  encryptionKey: string;
  maxSecurityEvents: number;
}

export const DEFAULT_SECURITY_CONFIG: SecurityConfig = {
  enableTls: true,
  enableFirewall: true,
  enableEncryption: true,
  encryptionKey: "arcanis-network-default-key",
  maxSecurityEvents: 10000,
};

export class NetworkSecurity extends EventEmitter {
  public readonly tls: TlsManager;
  public readonly firewall: Firewall;
  public readonly encryption: NetworkEncryption;
  private config: SecurityConfig;
  private securityEvents: SecurityEvent[] = [];

  constructor(config: Partial<SecurityConfig> = {}) {
    super();
    this.config = { ...DEFAULT_SECURITY_CONFIG, ...config };
    this.tls = new TlsManager();
    this.firewall = new Firewall();
    this.encryption = new NetworkEncryption(
      Buffer.from(this.config.encryptionKey.padEnd(32, "\0"))
    );
    this.setupFirewallDefaults();
  }

  private setupFirewallDefaults(): void {
    this.firewall.addRule({
      id: "allow-outbound",
      name: "Allow Outbound Traffic",
      action: "allow",
      direction: "outbound",
      priority: 100,
      enabled: true,
    });
    this.firewall.addRule({
      id: "block-malicious-ports",
      name: "Block Known Malicious Ports",
      action: "deny",
      destinationPort: 4444,
      direction: "inbound",
      priority: 1,
      enabled: true,
    });
    this.firewall.addRule({
      id: "block-malicious-ports-2",
      name: "Block Known Malicious Ports 2",
      action: "deny",
      destinationPort: 5555,
      direction: "inbound",
      priority: 1,
      enabled: true,
    });
  }

  checkPermission(
    sourceIp: string,
    destinationIp: string,
    protocol: string,
    sourcePort: number,
    destinationPort: number,
    direction: "inbound" | "outbound"
  ): boolean {
    const result = this.firewall.evaluatePacket(
      sourceIp,
      destinationIp,
      protocol,
      sourcePort,
      destinationPort,
      direction
    );
    if (!result.allowed) {
      this.logSecurityEvent({
        type: "firewall:block",
        severity: "medium",
        source: sourceIp,
        destination: destinationIp,
        description: `Packet blocked by rule ${result.ruleId || "unknown"}`,
        metadata: { protocol, sourcePort, destinationPort, direction },
      });
    }
    return result.allowed;
  }

  logSecurityEvent(event: Omit<SecurityEvent, "id" | "timestamp">): void {
    const fullEvent: SecurityEvent = {
      id: uuidv4(),
      timestamp: Date.now(),
      ...event,
    };
    this.securityEvents.push(fullEvent);
    if (this.securityEvents.length > this.config.maxSecurityEvents) {
      this.securityEvents.shift();
    }
    this.emit("security:event", fullEvent);
    if (event.severity === "critical" || event.severity === "high") {
      this.emit("security:alert", fullEvent);
    }
  }

  getSecurityEvents(type?: string): SecurityEvent[] {
    if (type) {
      return this.securityEvents.filter((e) => e.type === type);
    }
    return [...this.securityEvents];
  }

  clearSecurityEvents(): void {
    this.securityEvents = [];
  }

  encryptData(data: Buffer): { iv: string; encrypted: string; tag: string } {
    return this.encryption.encrypt(data);
  }

  decryptData(iv: string, encrypted: string, tag: string): Buffer {
    return this.encryption.decrypt(iv, encrypted, tag);
  }

  getStats(): {
    tlsSessions: number;
    firewallRules: number;
    blockedIps: number;
    securityEvents: number;
  } {
    return {
      tlsSessions: 0,
      firewallRules: this.firewall.getRules().length,
      blockedIps: 0,
      securityEvents: this.securityEvents.length,
    };
  }
}

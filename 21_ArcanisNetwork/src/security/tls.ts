import { createCipheriv, createDecipheriv, randomBytes, createHash, createHmac } from "crypto";
import { EventEmitter } from "events";
import {
  SecurityEvent,
  NetworkConfig,
  DEFAULT_NETWORK_CONFIG,
  NetworkAddress,
} from "../types";
import { v4 as uuidv4 } from "uuid";

export interface TlsConfig {
  version: string;
  cipherSuite: string;
  certificate: string | null;
  privateKey: string | null;
  caCertificate: string | null;
  verifyPeer: boolean;
  rejectUnauthorized: boolean;
}

export const DEFAULT_TLS_CONFIG: TlsConfig = {
  version: "TLSv1.3",
  cipherSuite: "AES_256_GCM_SHA384",
  certificate: null,
  privateKey: null,
  caCertificate: null,
  verifyPeer: true,
  rejectUnauthorized: true,
};

export class TlsManager extends EventEmitter {
  private config: TlsConfig;
  private sessionKeys: Map<string, Buffer> = new Map();

  constructor(config: Partial<TlsConfig> = {}) {
    super();
    this.config = { ...DEFAULT_TLS_CONFIG, ...config };
  }

  async generateSessionKey(sessionId: string): Promise<Buffer> {
    const key = randomBytes(32);
    this.sessionKeys.set(sessionId, key);
    return key;
  }

  getSessionKey(sessionId: string): Buffer | undefined {
    return this.sessionKeys.get(sessionId);
  }

  removeSessionKey(sessionId: string): boolean {
    return this.sessionKeys.delete(sessionId);
  }

  encrypt(data: Buffer, key: Buffer): { iv: string; encrypted: string; tag: string } {
    const iv = randomBytes(16);
    const cipher = createCipheriv("aes-256-gcm", key, iv);
    let encrypted = cipher.update(data);
    encrypted = Buffer.concat([encrypted, cipher.final()]);
    const tag = cipher.getAuthTag();
    return {
      iv: iv.toString("hex"),
      encrypted: encrypted.toString("hex"),
      tag: tag.toString("hex"),
    };
  }

  decrypt(iv: string, encrypted: string, tag: string, key: Buffer): Buffer {
    const decipher = createDecipheriv(
      "aes-256-gcm",
      key,
      Buffer.from(iv, "hex")
    );
    decipher.setAuthTag(Buffer.from(tag, "hex"));
    let decrypted = decipher.update(Buffer.from(encrypted, "hex"));
    decrypted = Buffer.concat([decrypted, decipher.final()]);
    return decrypted;
  }

  sign(data: Buffer, key: Buffer): string {
    return createHmac("sha256", key).update(data).digest("hex");
  }

  verify(data: Buffer, signature: string, key: Buffer): boolean {
    const expected = this.sign(data, key);
    return expected === signature;
  }
}

export interface FirewallRule {
  id: string;
  name: string;
  action: "allow" | "deny" | "log";
  protocol?: string;
  sourceIp?: string;
  destinationIp?: string;
  sourcePort?: number;
  destinationPort?: number;
  direction: "inbound" | "outbound" | "both";
  priority: number;
  enabled: boolean;
}

export class Firewall extends EventEmitter {
  private rules: FirewallRule[] = [];
  private blockedIps: Set<string> = new Set();
  private rateLimits: Map<string, { count: number; resetTime: number }> = new Map();

  addRule(rule: FirewallRule): void {
    this.rules.push(rule);
    this.rules.sort((a, b) => a.priority - b.priority);
    this.emit("rule:added", rule);
  }

  removeRule(id: string): boolean {
    const index = this.rules.findIndex((r) => r.id === id);
    if (index === -1) return false;
    const rule = this.rules.splice(index, 1)[0];
    this.emit("rule:removed", rule);
    return true;
  }

  updateRule(id: string, updates: Partial<FirewallRule>): boolean {
    const rule = this.rules.find((r) => r.id === id);
    if (!rule) return false;
    Object.assign(rule, updates);
    this.emit("rule:updated", rule);
    return true;
  }

  getRules(): FirewallRule[] {
    return [...this.rules];
  }

  blockIp(ip: string): void {
    this.blockedIps.add(ip);
    this.emit("ip:blocked", { ip });
  }

  unblockIp(ip: string): void {
    this.blockedIps.delete(ip);
    this.emit("ip:unblocked", { ip });
  }

  isBlocked(ip: string): boolean {
    return this.blockedIps.has(ip);
  }

  checkRateLimit(ip: string, limit: number = 100, windowMs: number = 60000): boolean {
    const now = Date.now();
    const record = this.rateLimits.get(ip);
    if (!record || now > record.resetTime) {
      this.rateLimits.set(ip, { count: 1, resetTime: now + windowMs });
      return true;
    }
    record.count++;
    return record.count <= limit;
  }

  evaluatePacket(
    sourceIp: string,
    destinationIp: string,
    protocol: string,
    sourcePort: number,
    destinationPort: number,
    direction: "inbound" | "outbound"
  ): { allowed: boolean; ruleId?: string; action: string } {
    if (this.blockedIps.has(sourceIp) || this.blockedIps.has(destinationIp)) {
      return { allowed: false, action: "deny" };
    }
    for (const rule of this.rules) {
      if (!rule.enabled) continue;
      if (rule.direction !== "both" && rule.direction !== direction) continue;
      if (rule.protocol && rule.protocol !== protocol) continue;
      if (rule.sourceIp && rule.sourceIp !== sourceIp) continue;
      if (rule.destinationIp && rule.destinationIp !== destinationIp) continue;
      if (rule.sourcePort && rule.sourcePort !== sourcePort) continue;
      if (rule.destinationPort && rule.destinationPort !== destinationPort) continue;
      return {
        allowed: rule.action === "allow",
        ruleId: rule.id,
        action: rule.action,
      };
    }
    return { allowed: true, action: "allow" };
  }

  clearRules(): void {
    this.rules = [];
    this.emit("rules:cleared");
  }
}

export interface EncryptionConfig {
  algorithm: string;
  keySize: number;
  ivSize: number;
  tagSize: number;
}

export const DEFAULT_ENCRYPTION_CONFIG: EncryptionConfig = {
  algorithm: "aes-256-gcm",
  keySize: 32,
  ivSize: 16,
  tagSize: 16,
};

export class NetworkEncryption {
  private config: EncryptionConfig;
  private key: Buffer;

  constructor(key: Buffer, config: Partial<EncryptionConfig> = {}) {
    this.config = { ...DEFAULT_ENCRYPTION_CONFIG, ...config };
    this.key = key;
  }

  encrypt(data: Buffer): { iv: string; encrypted: string; tag: string } {
    const iv = randomBytes(this.config.ivSize);
    const cipher = createCipheriv(this.config.algorithm, this.key, iv);
    let encrypted = cipher.update(data);
    encrypted = Buffer.concat([encrypted, cipher.final()]);
    const tag = cipher.getAuthTag();
    return {
      iv: iv.toString("hex"),
      encrypted: encrypted.toString("hex"),
      tag: tag.toString("hex"),
    };
  }

  decrypt(iv: string, encrypted: string, tag: string): Buffer {
    const decipher = createDecipheriv(
      this.config.algorithm,
      this.key,
      Buffer.from(iv, "hex")
    );
    decipher.setAuthTag(Buffer.from(tag, "hex"));
    let decrypted = decipher.update(Buffer.from(encrypted, "hex"));
    decrypted = Buffer.concat([decrypted, decipher.final()]);
    return decrypted;
  }

  hash(data: Buffer): string {
    return createHash("sha256").update(data).digest("hex");
  }

  static generateKey(size: number = 32): Buffer {
    return randomBytes(size);
  }
}

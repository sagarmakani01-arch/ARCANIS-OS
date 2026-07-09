import { EventEmitter } from "events";
import { SecurityEvent, NetworkAddress } from "../types";

export interface SecurityPermission {
  id: string;
  name: string;
  resource: string;
  actions: string[];
  granted: boolean;
}

export interface SecurityPolicy {
  id: string;
  name: string;
  permissions: string[];
  restrictions: string[];
  networkAccess: boolean;
  encryptionRequired: boolean;
}

export class ArcanisSecurityIntegration extends EventEmitter {
  private securityRef: unknown = null;
  private policies: Map<string, SecurityPolicy> = new Map();
  private permissions: Map<string, SecurityPermission> = new Map();

  constructor() {
    super();
    this.registerDefaultPolicies();
  }

  private registerDefaultPolicies(): void {
    this.policies.set("system", {
      id: "system",
      name: "System Policy",
      permissions: ["read", "write", "execute", "admin", "network"],
      restrictions: [],
      networkAccess: true,
      encryptionRequired: false,
    });
    this.policies.set("user", {
      id: "user",
      name: "User Policy",
      permissions: ["read", "write", "execute"],
      restrictions: ["admin", "network"],
      networkAccess: false,
      encryptionRequired: true,
    });
    this.policies.set("guest", {
      id: "guest",
      name: "Guest Policy",
      permissions: ["read"],
      restrictions: ["admin", "network", "filesystem", "process"],
      networkAccess: false,
      encryptionRequired: true,
    });
  }

  setSecurityReference(security: unknown): void {
    this.securityRef = security;
    this.emit("security:connected");
  }

  getSecurityReference(): unknown {
    return this.securityRef;
  }

  checkNetworkPermission(policyId: string): boolean {
    const policy = this.policies.get(policyId);
    return policy ? policy.networkAccess : false;
  }

  checkEncryptionRequired(policyId: string): boolean {
    const policy = this.policies.get(policyId);
    return policy ? policy.encryptionRequired : true;
  }

  addPolicy(policy: SecurityPolicy): void {
    this.policies.set(policy.id, policy);
    this.emit("policy:added", policy);
  }

  removePolicy(id: string): boolean {
    const policy = this.policies.get(id);
    if (!policy) return false;
    this.policies.delete(id);
    this.emit("policy:removed", policy);
    return true;
  }

  getPolicy(id: string): SecurityPolicy | undefined {
    return this.policies.get(id);
  }

  getPolicies(): SecurityPolicy[] {
    return Array.from(this.policies.values());
  }

  addPermission(permission: SecurityPermission): void {
    this.permissions.set(permission.id, permission);
    this.emit("permission:added", permission);
  }

  removePermission(id: string): boolean {
    return this.permissions.delete(id);
  }

  checkPermission(resource: string, action: string): boolean {
    for (const perm of this.permissions.values()) {
      if (perm.resource === resource && perm.actions.includes(action)) {
        return perm.granted;
      }
    }
    return false;
  }

  validateNetworkSecurity(
    source: NetworkAddress,
    destination: NetworkAddress,
    policyId: string = "user"
  ): { allowed: boolean; reason: string } {
    if (!this.checkNetworkPermission(policyId)) {
      return { allowed: false, reason: "Network access not permitted by policy" };
    }
    if (this.checkEncryptionRequired(policyId)) {
      return { allowed: true, reason: "Encryption required" };
    }
    return { allowed: true, reason: "Passed security checks" };
  }

  logSecurityEvent(event: Omit<SecurityEvent, "id" | "timestamp">): void {
    const fullEvent: SecurityEvent = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2),
      timestamp: Date.now(),
      ...event,
    };
    this.emit("security:event", fullEvent);
  }

  getStats(): {
    policies: number;
    permissions: number;
    networkPolicies: number;
  } {
    const policies = this.getPolicies();
    return {
      policies: policies.length,
      permissions: this.permissions.size,
      networkPolicies: policies.filter((p) => p.networkAccess).length,
    };
  }
}

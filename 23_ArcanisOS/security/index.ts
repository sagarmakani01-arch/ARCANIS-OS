import { createCipheriv, createDecipheriv, randomBytes, createHash } from "crypto";

export enum Permission {
  Read = "read",
  Write = "write",
  Execute = "execute",
  Admin = "admin",
  Network = "network",
  FileSystem = "filesystem",
  Process = "process",
  AIAccess = "ai_access",
}

export interface SecurityPolicy {
  id: string;
  name: string;
  permissions: Permission[];
  restrictions: string[];
}

export class SecurityManager {
  private policies: Map<string, SecurityPolicy> = new Map();
  private encryptionKey: Buffer;

  constructor() {
    this.encryptionKey = createHash("sha256").update("arcanis-os-secure-key").digest();
    this.registerDefaultPolicies();
  }

  private registerDefaultPolicies(): void {
    this.registerPolicy({
      id: "system",
      name: "System Policy",
      permissions: Object.values(Permission),
      restrictions: [],
    });
    this.registerPolicy({
      id: "user",
      name: "User Policy",
      permissions: [Permission.Read, Permission.Write, Permission.Execute],
      restrictions: ["admin", "network"],
    });
    this.registerPolicy({
      id: "guest",
      name: "Guest Policy",
      permissions: [Permission.Read],
      restrictions: ["admin", "network", "filesystem", "process", "ai_access"],
    });
  }

  registerPolicy(policy: SecurityPolicy): void {
    this.policies.set(policy.id, policy);
  }

  getPolicy(id: string): SecurityPolicy | undefined {
    return this.policies.get(id);
  }

  checkPermission(policyId: string, permission: Permission): boolean {
    const policy = this.policies.get(policyId);
    return policy ? policy.permissions.includes(permission) : false;
  }

  encrypt(data: string): { iv: string; encrypted: string; tag: string } {
    const iv = randomBytes(16);
    const cipher = createCipheriv("aes-256-gcm", this.encryptionKey, iv);
    let encrypted = cipher.update(data, "utf-8", "hex");
    encrypted += cipher.final("hex");
    const tag = cipher.getAuthTag().toString("hex");
    return { iv: iv.toString("hex"), encrypted, tag };
  }

  decrypt(iv: string, encrypted: string, tag: string): string {
    const decipher = createDecipheriv("aes-256-gcm", this.encryptionKey, Buffer.from(iv, "hex"));
    decipher.setAuthTag(Buffer.from(tag, "hex"));
    let decrypted = decipher.update(encrypted, "hex", "utf-8");
    decrypted += decipher.final("utf-8");
    return decrypted;
  }
}

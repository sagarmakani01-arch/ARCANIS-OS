import { describe, it, expect, beforeEach } from "vitest";
import { NetworkSecurity, TlsManager, Firewall, NetworkEncryption } from "../src/security";
import { v4 as uuidv4 } from "uuid";

describe("NetworkSecurity", () => {
  let security: NetworkSecurity;

  beforeEach(() => {
    security = new NetworkSecurity();
  });

  it("should initialize with default rules", () => {
    const rules = security.firewall.getRules();
    expect(rules.length).toBeGreaterThan(0);
  });

  it("should check permission", () => {
    const allowed = security.checkPermission(
      "192.168.1.1",
      "192.168.1.2",
      "tcp",
      1234,
      80,
      "outbound"
    );
    expect(allowed).toBe(true);
  });

  it("should log security event", () => {
    security.logSecurityEvent({
      type: "test",
      severity: "low",
      source: "192.168.1.1",
      destination: "192.168.1.2",
      description: "Test event",
      metadata: {},
    });
    const events = security.getSecurityEvents();
    expect(events.length).toBe(1);
  });

  it("should encrypt and decrypt data", () => {
    const data = Buffer.from("Hello, ArcanisNetwork!");
    const encrypted = security.encryptData(data);
    expect(encrypted.encrypted).toBeDefined();
    expect(encrypted.iv).toBeDefined();
    expect(encrypted.tag).toBeDefined();
    const decrypted = security.decryptData(encrypted.iv, encrypted.encrypted, encrypted.tag);
    expect(decrypted.toString()).toBe("Hello, ArcanisNetwork!");
  });
});

describe("TlsManager", () => {
  let tls: TlsManager;

  beforeEach(() => {
    tls = new TlsManager();
  });

  it("should generate session key", async () => {
    const key = await tls.generateSessionKey("test-session");
    expect(key).toBeDefined();
    expect(key.length).toBe(32);
  });

  it("should encrypt and decrypt with session key", async () => {
    const key = await tls.generateSessionKey("test-session");
    const data = Buffer.from("Test data");
    const encrypted = tls.encrypt(data, key);
    const decrypted = tls.decrypt(encrypted.iv, encrypted.encrypted, encrypted.tag, key);
    expect(decrypted.toString()).toBe("Test data");
  });

  it("should sign and verify", async () => {
    const key = await tls.generateSessionKey("test-session");
    const data = Buffer.from("Test data");
    const signature = tls.sign(data, key);
    expect(tls.verify(data, signature, key)).toBe(true);
    expect(tls.verify(Buffer.from("tampered"), signature, key)).toBe(false);
  });
});

describe("Firewall", () => {
  let firewall: Firewall;

  beforeEach(() => {
    firewall = new Firewall();
  });

  it("should add rule", () => {
    firewall.addRule({
      id: "test-rule",
      name: "Test Rule",
      action: "allow",
      direction: "outbound",
      priority: 100,
      enabled: true,
    });
    const rules = firewall.getRules();
    expect(rules.length).toBe(1);
  });

  it("should block IP", () => {
    firewall.blockIp("192.168.1.100");
    expect(firewall.isBlocked("192.168.1.100")).toBe(true);
    expect(firewall.isBlocked("192.168.1.1")).toBe(false);
  });

  it("should evaluate packet", () => {
    const result = firewall.evaluatePacket(
      "192.168.1.1",
      "192.168.1.2",
      "tcp",
      1234,
      80,
      "outbound"
    );
    expect(result.allowed).toBe(true);
  });

  it("should deny blocked IP", () => {
    firewall.blockIp("192.168.1.100");
    const result = firewall.evaluatePacket(
      "192.168.1.100",
      "192.168.1.2",
      "tcp",
      1234,
      80,
      "outbound"
    );
    expect(result.allowed).toBe(false);
  });

  it("should check rate limit", () => {
    for (let i = 0; i < 100; i++) {
      firewall.checkRateLimit("192.168.1.1");
    }
    expect(firewall.checkRateLimit("192.168.1.1")).toBe(false);
  });
});

describe("NetworkEncryption", () => {
  let encryption: NetworkEncryption;

  beforeEach(() => {
    encryption = new NetworkEncryption(Buffer.from("test-key-32-chars-padding-here!!"));
  });

  it("should encrypt and decrypt", () => {
    const data = Buffer.from("Hello, World!");
    const encrypted = encryption.encrypt(data);
    const decrypted = encryption.decrypt(encrypted.iv, encrypted.encrypted, encrypted.tag);
    expect(decrypted.toString()).toBe("Hello, World!");
  });

  it("should hash data", () => {
    const data = Buffer.from("test data");
    const hash = encryption.hash(data);
    expect(hash).toBeDefined();
    expect(hash.length).toBe(64);
  });

  it("should generate key", () => {
    const key = NetworkEncryption.generateKey();
    expect(key.length).toBe(32);
  });
});

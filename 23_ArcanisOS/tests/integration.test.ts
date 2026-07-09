import { describe, it, expect, beforeEach } from "vitest";
import { ArcanisOS } from "../index";
import { EventBus } from "../integration/bus";
import { ApiGateway } from "../integration/api";
import { SecurityManager, Permission } from "../security";

describe("ArcanisOS Integration", () => {
  let os: ArcanisOS;

  beforeEach(async () => {
    os = new ArcanisOS();
    await os.boot();
  });

  afterEach(async () => {
    await os.shutdown();
  });

  it("should boot all components", () => {
    expect(os.status).toBe("running");
    expect(os.kernel.isRunning()).toBe(true);
  });

  it("should process commands via AI", async () => {
    const result = await os.executeCommand("echo hello from arcanis");
    expect(result).toBeTruthy();
  });

  it("should have API endpoints registered", () => {
    const endpoints = os.api.list();
    expect(endpoints.length).toBeGreaterThan(0);
  });

  it("should emit events", (done) => {
    os.eventBus.on("test:event", (event) => {
      expect(event.type).toBe("test:event");
      expect(event.data).toBe("test-data");
      done();
    });
    os.eventBus.emit("test:event", "test", "test-data");
  });

  it("should have correct version", () => {
    expect(os.version).toBe("1.0.0-alpha");
  });
});

describe("EventBus", () => {
  let bus: EventBus;

  beforeEach(() => {
    bus = new EventBus();
  });

  it("should emit and receive events", (done) => {
    bus.on("test", (event) => {
      expect(event.data).toBe(42);
      done();
    });
    bus.emit("test", "source", 42);
  });

  it("should support once handlers", () => {
    let count = 0;
    bus.once("once", () => { count++; });
    bus.emit("once", "s", 1);
    bus.emit("once", "s", 2);
    expect(count).toBe(1);
  });

  it("should track history", () => {
    bus.emit("a", "s", 1);
    bus.emit("b", "s", 2);
    expect(bus.getHistory()).toHaveLength(2);
    expect(bus.getHistory("a")).toHaveLength(1);
  });
});

describe("ApiGateway", () => {
  let api: ApiGateway;

  beforeEach(() => {
    api = new ApiGateway();
  });

  it("should register and call endpoints", async () => {
    api.register({
      method: "GET", path: "/ping",
      handler: async () => ({ status: 200, data: "pong" }),
    });
    const response = await api.call("GET", "/ping");
    expect(response.status).toBe(200);
    expect(response.data).toBe("pong");
  });

  it("should return 404 for unknown routes", async () => {
    const response = await api.call("GET", "/unknown");
    expect(response.status).toBe(404);
  });
});

describe("SecurityManager", () => {
  let security: SecurityManager;

  beforeEach(() => {
    security = new SecurityManager();
  });

  it("should have default policies", () => {
    expect(security.getPolicy("system")).toBeDefined();
    expect(security.getPolicy("user")).toBeDefined();
    expect(security.getPolicy("guest")).toBeDefined();
  });

  it("should check permissions", () => {
    expect(security.checkPermission("system", Permission.Admin)).toBe(true);
    expect(security.checkPermission("guest", Permission.Admin)).toBe(false);
  });

  it("should encrypt and decrypt", () => {
    const { iv, encrypted, tag } = security.encrypt("secret-data");
    const decrypted = security.decrypt(iv, encrypted, tag);
    expect(decrypted).toBe("secret-data");
  });
});

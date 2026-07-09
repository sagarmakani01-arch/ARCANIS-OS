import { describe, it, expect, beforeEach } from "vitest";
import { ArcanisNetwork } from "../src/index";
import { Protocol, DEFAULT_NETWORK_CONFIG } from "../src/types";

describe("ArcanisNetwork Integration", () => {
  let network: ArcanisNetwork;

  beforeEach(() => {
    network = new ArcanisNetwork();
  });

  it("should initialize successfully", async () => {
    await network.initialize();
    expect(network.isInitialized()).toBe(true);
  });

  it("should shutdown successfully", async () => {
    await network.initialize();
    await network.shutdown();
    expect(network.isInitialized()).toBe(false);
  });

  it("should have all components", () => {
    expect(network.core).toBeDefined();
    expect(network.transfer).toBeDefined();
    expect(network.streams).toBeDefined();
    expect(network.security).toBeDefined();
    expect(network.discovery).toBeDefined();
    expect(network.services).toBeDefined();
    expect(network.cloud).toBeDefined();
    expect(network.optimizer).toBeDefined();
    expect(network.connectionMonitor).toBeDefined();
    expect(network.securityAnalyzer).toBeDefined();
    expect(network.integration).toBeDefined();
    expect(network.metrics).toBeDefined();
    expect(network.logger).toBeDefined();
    expect(network.tracer).toBeDefined();
  });

  it("should return network stats", async () => {
    await network.initialize();
    const stats = network.getNetworkStats();
    expect(stats).toBeDefined();
    expect(stats.core).toBeDefined();
    expect(stats.transfer).toBeDefined();
    expect(stats.security).toBeDefined();
    expect(stats.optimizer).toBeDefined();
  });

  it("should return config", () => {
    const config = network.getConfig();
    expect(config).toBeDefined();
    expect(config.maxConnections).toBe(DEFAULT_NETWORK_CONFIG.maxConnections);
  });

  it("should connect to remote", async () => {
    await network.initialize();
    const connection = await network.connect(
      { ip: "192.168.1.1", port: 80 },
      Protocol.TCP
    );
    expect(connection).toBeDefined();
  });

  it("should create TCP server", async () => {
    await network.initialize();
    const server = network.core.createTcpServer(8080);
    expect(server).toBeDefined();
  });

  it("should create UDP socket", async () => {
    await network.initialize();
    const socket = await network.core.createUdpSocket(9999);
    expect(socket).toBeDefined();
  });
});

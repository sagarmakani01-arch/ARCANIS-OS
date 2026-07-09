import { describe, it, expect, beforeEach } from "vitest";
import { NetworkOptimizer, ConnectionMonitor, SecurityAnalyzer } from "../src/ai";
import { NetworkStats, SecurityEvent } from "../src/types";

describe("NetworkOptimizer", () => {
  let optimizer: NetworkOptimizer;

  beforeEach(() => {
    optimizer = new NetworkOptimizer();
  });

  it("should have default rules", () => {
    const rules = optimizer.getRules();
    expect(rules.length).toBeGreaterThan(0);
  });

  it("should add rule", () => {
    optimizer.addRule({
      id: "test-rule",
      name: "Test Rule",
      condition: "test > 100",
      action: "alert",
      priority: 1,
      enabled: true,
      triggerCount: 0,
    });
    const rules = optimizer.getRules();
    expect(rules.length).toBe(5);
  });

  it("should analyze stats and generate recommendations", () => {
    const stats: NetworkStats = {
      totalPacketsSent: 1000,
      totalPacketsReceived: 950,
      totalBytesSent: 1000000,
      totalBytesReceived: 950000,
      activeConnections: 500,
      totalConnections: 600,
      errors: 10,
      droppedPackets: 50,
      averageLatency: 150,
      bandwidth: 500000,
    };
    const recommendations = optimizer.analyzeStats(stats);
    expect(recommendations.length).toBeGreaterThan(0);
  });

  it("should add pattern", () => {
    const pattern = optimizer.addPattern({
      name: "HTTP Traffic",
      protocol: "tcp",
      portRange: [80, 443],
      bandwidth: 100000,
      frequency: 100,
      peakHours: [9, 17],
    });
    expect(pattern).toBeDefined();
    expect(pattern.isAnomalous).toBe(false);
  });

  it("should return stats", () => {
    const stats = optimizer.getStats();
    expect(stats.rules).toBe(4);
    expect(stats.patterns).toBe(0);
  });
});

describe("ConnectionMonitor", () => {
  let monitor: ConnectionMonitor;

  beforeEach(() => {
    monitor = new ConnectionMonitor();
  });

  it("should track connection", () => {
    monitor.trackConnection({
      id: "test-conn",
      localAddress: { ip: "127.0.0.1", port: 1234 },
      remoteAddress: { ip: "192.168.1.1", port: 80 },
      protocol: "tcp",
      state: "connected",
      createdAt: Date.now(),
      lastActivity: Date.now(),
      bytesSent: 100,
      bytesReceived: 200,
      latency: 50,
      isActive: true,
    });
    const history = monitor.getConnectionHistory("test-conn");
    expect(history.length).toBe(1);
  });

  it("should detect high latency", () => {
    const issues = monitor.detectConnectionIssues({
      id: "test-conn",
      localAddress: { ip: "127.0.0.1", port: 1234 },
      remoteAddress: { ip: "192.168.1.1", port: 80 },
      protocol: "tcp",
      state: "connected",
      createdAt: Date.now(),
      lastActivity: Date.now(),
      bytesSent: 100,
      bytesReceived: 200,
      latency: 300,
      isActive: true,
    });
    expect(issues.length).toBeGreaterThan(0);
    expect(issues[0]).toContain("latency");
  });

  it("should return stats", () => {
    const stats = monitor.getStats();
    expect(stats.trackedConnections).toBe(0);
  });
});

describe("SecurityAnalyzer", () => {
  let analyzer: SecurityAnalyzer;

  beforeEach(() => {
    analyzer = new SecurityAnalyzer();
  });

  it("should analyze critical event", () => {
    const event: SecurityEvent = {
      id: "test-event",
      type: "intrusion",
      severity: "critical",
      source: "192.168.1.100",
      destination: "192.168.1.1",
      timestamp: Date.now(),
      description: "Test intrusion attempt",
      metadata: {},
    };
    analyzer.analyzeEvent(event);
    const threats = analyzer.getThreats();
    expect(threats.length).toBe(1);
  });

  it("should track blocked attempts", () => {
    for (let i = 0; i < 15; i++) {
      analyzer.analyzeEvent({
        id: `event-${i}`,
        type: "brute_force",
        severity: "high",
        source: "192.168.1.100",
        destination: "192.168.1.1",
        timestamp: Date.now(),
        description: "Brute force attempt",
        metadata: {},
      });
    }
    const attempts = analyzer.getBlockedAttempts();
    expect(attempts.length).toBe(1);
    expect(attempts[0].count).toBe(15);
  });

  it("should return stats", () => {
    const stats = analyzer.getStats();
    expect(stats.totalThreats).toBe(0);
  });
});

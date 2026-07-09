import { EventEmitter } from "events";
import {
  NetworkStats,
  ConnectionInfo,
  NetworkConfig,
  DEFAULT_NETWORK_CONFIG,
  SecurityEvent,
} from "../types";
import { v4 as uuidv4 } from "uuid";

export interface OptimizationRule {
  id: string;
  name: string;
  condition: string;
  action: string;
  priority: number;
  enabled: boolean;
  lastTriggered?: number;
  triggerCount: number;
}

export interface TrafficPattern {
  id: string;
  name: string;
  protocol: string;
  portRange: [number, number];
  bandwidth: number;
  frequency: number;
  peakHours: [number, number];
  isAnomalous: boolean;
}

export interface OptimizationRecommendation {
  id: string;
  type: "bandwidth" | "latency" | "security" | "reliability";
  severity: "low" | "medium" | "high";
  title: string;
  description: string;
  impact: string;
  implementation: string;
  estimatedImprovement: number;
  createdAt: number;
}

export class NetworkOptimizer extends EventEmitter {
  private rules: OptimizationRule[] = [];
  private patterns: TrafficPattern[] = [];
  private recommendations: OptimizationRecommendation[] = [];
  private historicalStats: NetworkStats[] = [];
  private maxHistory: number = 1000;

  constructor() {
    super();
    this.setupDefaultRules();
  }

  private setupDefaultRules(): void {
    this.addRule({
      name: "High Bandwidth Alert",
      condition: "bandwidth > 80%",
      action: "suggest_optimization",
      priority: 1,
      enabled: true,
      triggerCount: 0,
    });
    this.addRule({
      name: "High Latency Alert",
      condition: "latency > 100ms",
      action: "suggest_optimization",
      priority: 2,
      enabled: true,
      triggerCount: 0,
    });
    this.addRule({
      name: "Connection Limit Warning",
      condition: "connections > 90%",
      action: "suggest_scale_up",
      priority: 3,
      enabled: true,
      triggerCount: 0,
    });
    this.addRule({
      name: "Packet Loss Alert",
      condition: "packet_loss > 5%",
      action: "suggest_optimization",
      priority: 4,
      enabled: true,
      triggerCount: 0,
    });
  }

  addRule(rule: OptimizationRule): void {
    this.rules.push(rule);
    this.rules.sort((a, b) => a.priority - b.priority);
    this.emit("rule:added", rule);
  }

  removeRule(id: string): boolean {
    const index = this.rules.findIndex((r) => r.id === id);
    if (index === -1) return false;
    this.rules.splice(index, 1);
    this.emit("rule:removed", { id });
    return true;
  }

  getRules(): OptimizationRule[] {
    return [...this.rules];
  }

  analyzeStats(stats: NetworkStats): OptimizationRecommendation[] {
    this.historicalStats.push(stats);
    if (this.historicalStats.length > this.maxHistory) {
      this.historicalStats.shift();
    }
    const recommendations: OptimizationRecommendation[] = [];
    if (stats.averageLatency > 100) {
      recommendations.push(this.createRecommendation(
        "latency",
        "high",
        "High Latency Detected",
        `Average latency is ${stats.averageLatency}ms, exceeding 100ms threshold`,
        "May cause connection timeouts and poor user experience",
        "Consider optimizing route selection or reducing packet size",
        30
      ));
    }
    if (stats.droppedPackets > stats.totalPacketsSent * 0.05) {
      recommendations.push(this.createRecommendation(
        "reliability",
        "high",
        "High Packet Loss",
        `Packet loss rate is ${((stats.droppedPackets / stats.totalPacketsSent) * 100).toFixed(2)}%`,
        "May cause data corruption and retransmissions",
        "Check network interface health and buffer sizes",
        25
      ));
    }
    if (stats.activeConnections > 900) {
      recommendations.push(this.createRecommendation(
        "bandwidth",
        "medium",
        "High Connection Count",
        `${stats.activeConnections} active connections approaching limit`,
        "May cause connection refused errors",
        "Consider scaling up connection limits or implementing connection pooling",
        20
      ));
    }
    return recommendations;
  }

  private createRecommendation(
    type: OptimizationRecommendation["type"],
    severity: OptimizationRecommendation["severity"],
    title: string,
    description: string,
    impact: string,
    implementation: string,
    estimatedImprovement: number
  ): OptimizationRecommendation {
    const recommendation: OptimizationRecommendation = {
      id: uuidv4(),
      type,
      severity,
      title,
      description,
      impact,
      implementation,
      estimatedImprovement,
      createdAt: Date.now(),
    };
    this.recommendations.push(recommendation);
    this.emit("recommendation:created", recommendation);
    return recommendation;
  }

  getRecommendations(type?: string): OptimizationRecommendation[] {
    if (type) {
      return this.recommendations.filter((r) => r.type === type);
    }
    return [...this.recommendations];
  }

  addPattern(pattern: Omit<TrafficPattern, "id" | "isAnomalous">): TrafficPattern {
    const fullPattern: TrafficPattern = {
      ...pattern,
      id: uuidv4(),
      isAnomalous: false,
    };
    this.patterns.push(fullPattern);
    return fullPattern;
  }

  detectAnomalies(currentStats: NetworkStats): TrafficPattern[] {
    const anomalies: TrafficPattern[] = [];
    if (this.historicalStats.length < 10) return anomalies;
    const avgBandwidth = this.historicalStats.reduce((sum, s) => sum + s.bandwidth, 0) / this.historicalStats.length;
    if (currentStats.bandwidth > avgBandwidth * 2) {
      const anomaly: TrafficPattern = {
        id: uuidv4(),
        name: "Bandwidth Spike",
        protocol: "unknown",
        portRange: [0, 65535],
        bandwidth: currentStats.bandwidth,
        frequency: 1,
        peakHours: [new Date().getHours(), new Date().getHours() + 1],
        isAnomalous: true,
      };
      anomalies.push(anomaly);
      this.emit("anomaly:detected", anomaly);
    }
    return anomalies;
  }

  getStats(): {
    rules: number;
    patterns: number;
    recommendations: number;
    historicalDataPoints: number;
  } {
    return {
      rules: this.rules.length,
      patterns: this.patterns.length,
      recommendations: this.recommendations.length,
      historicalDataPoints: this.historicalStats.length,
    };
  }
}

export class ConnectionMonitor extends EventEmitter {
  private connectionHistory: Map<string, ConnectionInfo[]> = new Map();
  private alerts: Map<string, { message: string; timestamp: number; severity: string }> = new Map();

  constructor() {
    super();
  }

  trackConnection(connection: ConnectionInfo): void {
    const history = this.connectionHistory.get(connection.id) || [];
    history.push({ ...connection });
    if (history.length > 100) {
      history.shift();
    }
    this.connectionHistory.set(connection.id, history);
  }

  getConnectionHistory(id: string): ConnectionInfo[] {
    return this.connectionHistory.get(id) || [];
  }

  detectConnectionIssues(connection: ConnectionInfo): string[] {
    const issues: string[] = [];
    if (connection.latency > 200) {
      issues.push("High latency detected");
    }
    if (connection.bytesSent === 0 && connection.bytesReceived === 0) {
      issues.push("No data transfer activity");
    }
    const history = this.connectionHistory.get(connection.id) || [];
    if (history.length > 5) {
      const recentErrors = history.slice(-5).filter((h) => h.state === "error");
      if (recentErrors.length >= 3) {
        issues.push("Multiple recent errors");
      }
    }
    return issues;
  }

  addAlert(id: string, message: string, severity: string): void {
    this.alerts.set(id, { message, timestamp: Date.now(), severity });
    this.emit("alert", { id, message, severity });
  }

  getAlerts(): Array<{ id: string; message: string; timestamp: number; severity: string }> {
    return Array.from(this.alerts.entries()).map(([id, alert]) => ({ id, ...alert }));
  }

  getStats(): {
    trackedConnections: number;
    totalAlerts: number;
  } {
    return {
      trackedConnections: this.connectionHistory.size,
      totalAlerts: this.alerts.size,
    };
  }
}

export class SecurityAnalyzer extends EventEmitter {
  private threats: Map<string, { type: string; severity: string; timestamp: number; details: string }> = new Map();
  private blockedAttempts: Map<string, { count: number; lastAttempt: number }> = new Map();

  constructor() {
    super();
  }

  analyzeEvent(event: SecurityEvent): void {
    if (event.severity === "critical" || event.severity === "high") {
      this.threats.set(event.id, {
        type: event.type,
        severity: event.severity,
        timestamp: event.timestamp,
        details: event.description,
      });
      this.emit("threat:detected", event);
    }
    const ip = event.source;
    const record = this.blockedAttempts.get(ip) || { count: 0, lastAttempt: 0 };
    record.count++;
    record.lastAttempt = Date.now();
    this.blockedAttempts.set(ip, record);
    if (record.count >= 10) {
      this.emit("ip:flagged", { ip, attempts: record.count });
    }
  }

  getThreats(): Array<{ type: string; severity: string; timestamp: number; details: string }> {
    return Array.from(this.threats.values());
  }

  getBlockedAttempts(): Array<{ ip: string; count: number; lastAttempt: number }> {
    return Array.from(this.blockedAttempts.entries()).map(([ip, record]) => ({
      ip,
      ...record,
    }));
  }

  getStats(): {
    totalThreats: number;
    criticalThreats: number;
    flaggedIps: number;
  } {
    const threats = this.getThreats();
    return {
      totalThreats: threats.length,
      criticalThreats: threats.filter((t) => t.severity === "critical").length,
      flaggedIps: this.blockedAttempts.size,
    };
  }
}

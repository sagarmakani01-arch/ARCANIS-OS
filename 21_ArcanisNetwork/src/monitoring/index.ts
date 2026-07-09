import { EventEmitter } from "events";
import {
  NetworkConfig,
  DEFAULT_NETWORK_CONFIG,
  NetworkStats,
  NetworkEvent,
  NetworkEventHandler,
} from "../types";
import { v4 as uuidv4 } from "uuid";

export interface NetworkMetrics {
  timestamp: number;
  cpu: number;
  memory: number;
  bandwidth: number;
  latency: number;
  packetLoss: number;
  connections: number;
  errors: number;
}

export interface MetricThreshold {
  metric: string;
  warning: number;
  critical: number;
  unit: string;
}

export class NetworkMetricsCollector extends EventEmitter {
  private metrics: NetworkMetrics[] = [];
  private thresholds: MetricThreshold[] = [];
  private collectionInterval: NodeJS.Timeout | null = null;
  private maxMetrics: number = 1000;

  constructor() {
    super();
    this.setupDefaultThresholds();
  }

  private setupDefaultThresholds(): void {
    this.thresholds.push(
      { metric: "cpu", warning: 70, critical: 90, unit: "%" },
      { metric: "memory", warning: 70, critical: 90, unit: "%" },
      { metric: "latency", warning: 100, critical: 500, unit: "ms" },
      { metric: "packetLoss", warning: 5, critical: 10, unit: "%" },
      { metric: "errors", warning: 100, critical: 1000, unit: "count" }
    );
  }

  addThreshold(threshold: MetricThreshold): void {
    this.thresholds.push(threshold);
  }

  collectMetrics(): NetworkMetrics {
    const metrics: NetworkMetrics = {
      timestamp: Date.now(),
      cpu: Math.random() * 100,
      memory: Math.random() * 100,
      bandwidth: Math.random() * 1000000,
      latency: Math.random() * 200,
      packetLoss: Math.random() * 10,
      connections: Math.floor(Math.random() * 1000),
      errors: Math.floor(Math.random() * 100),
    };
    this.metrics.push(metrics);
    if (this.metrics.length > this.maxMetrics) {
      this.metrics.shift();
    }
    this.checkThresholds(metrics);
    this.emit("metrics:collected", metrics);
    return metrics;
  }

  private checkThresholds(metrics: NetworkMetrics): void {
    for (const threshold of this.thresholds) {
      const value = (metrics as Record<string, number>)[threshold.metric];
      if (value !== undefined) {
        if (value >= threshold.critical) {
          this.emit("threshold:critical", { metric: threshold.metric, value, threshold });
        } else if (value >= threshold.warning) {
          this.emit("threshold:warning", { metric: threshold.metric, value, threshold });
        }
      }
    }
  }

  startCollection(intervalMs: number = 5000): void {
    this.stopCollection();
    this.collectionInterval = setInterval(() => {
      this.collectMetrics();
    }, intervalMs);
    this.emit("collection:started", { interval: intervalMs });
  }

  stopCollection(): void {
    if (this.collectionInterval) {
      clearInterval(this.collectionInterval);
      this.collectionInterval = null;
      this.emit("collection:stopped");
    }
  }

  getMetrics(count?: number): NetworkMetrics[] {
    if (count) {
      return this.metrics.slice(-count);
    }
    return [...this.metrics];
  }

  getAverageMetrics(count: number = 10): Partial<NetworkMetrics> {
    const recent = this.metrics.slice(-count);
    if (recent.length === 0) return {};
    return {
      cpu: recent.reduce((sum, m) => sum + m.cpu, 0) / recent.length,
      memory: recent.reduce((sum, m) => sum + m.memory, 0) / recent.length,
      bandwidth: recent.reduce((sum, m) => sum + m.bandwidth, 0) / recent.length,
      latency: recent.reduce((sum, m) => sum + m.latency, 0) / recent.length,
      packetLoss: recent.reduce((sum, m) => sum + m.packetLoss, 0) / recent.length,
      connections: recent.reduce((sum, m) => sum + m.connections, 0) / recent.length,
      errors: recent.reduce((sum, m) => sum + m.errors, 0) / recent.length,
    };
  }

  getThresholds(): MetricThreshold[] {
    return [...this.thresholds];
  }

  clearMetrics(): void {
    this.metrics = [];
  }

  getStats(): {
    totalMetrics: number;
    avgCpu: number;
    avgMemory: number;
    avgLatency: number;
    avgPacketLoss: number;
  } {
    const avg = this.getAverageMetrics(100);
    return {
      totalMetrics: this.metrics.length,
      avgCpu: (avg.cpu as number) || 0,
      avgMemory: (avg.memory as number) || 0,
      avgLatency: (avg.latency as number) || 0,
      avgPacketLoss: (avg.packetLoss as number) || 0,
    };
  }
}

export interface NetworkLogEntry {
  id: string;
  timestamp: number;
  level: "debug" | "info" | "warn" | "error" | "fatal";
  category: string;
  message: string;
  metadata: Record<string, unknown>;
}

export class NetworkLogger extends EventEmitter {
  private logs: NetworkLogEntry[] = [];
  private maxLogs: number = 10000;
  private minLevel: NetworkLogEntry["level"] = "info";

  constructor() {
    super();
  }

  setMinLevel(level: NetworkLogEntry["level"]): void {
    this.minLevel = level;
  }

  private shouldLog(level: NetworkLogEntry["level"]): boolean {
    const levels: NetworkLogEntry["level"][] = ["debug", "info", "warn", "error", "fatal"];
    return levels.indexOf(level) >= levels.indexOf(this.minLevel);
  }

  log(
    level: NetworkLogEntry["level"],
    category: string,
    message: string,
    metadata: Record<string, unknown> = {}
  ): void {
    if (!this.shouldLog(level)) return;
    const entry: NetworkLogEntry = {
      id: uuidv4(),
      timestamp: Date.now(),
      level,
      category,
      message,
      metadata,
    };
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }
    this.emit("log", entry);
    if (level === "error" || level === "fatal") {
      this.emit("error:log", entry);
    }
  }

  debug(category: string, message: string, metadata?: Record<string, unknown>): void {
    this.log("debug", category, message, metadata);
  }

  info(category: string, message: string, metadata?: Record<string, unknown>): void {
    this.log("info", category, message, metadata);
  }

  warn(category: string, message: string, metadata?: Record<string, unknown>): void {
    this.log("warn", category, message, metadata);
  }

  error(category: string, message: string, metadata?: Record<string, unknown>): void {
    this.log("error", category, message, metadata);
  }

  fatal(category: string, message: string, metadata?: Record<string, unknown>): void {
    this.log("fatal", category, message, metadata);
  }

  getLogs(options: {
    level?: NetworkLogEntry["level"];
    category?: string;
    count?: number;
    since?: number;
  } = {}): NetworkLogEntry[] {
    let filtered = [...this.logs];
    if (options.level) {
      filtered = filtered.filter((l) => l.level === options.level);
    }
    if (options.category) {
      filtered = filtered.filter((l) => l.category === options.category);
    }
    if (options.since) {
      filtered = filtered.filter((l) => l.timestamp >= options.since);
    }
    if (options.count) {
      filtered = filtered.slice(-options.count);
    }
    return filtered;
  }

  clearLogs(): void {
    this.logs = [];
  }

  getStats(): {
    totalLogs: number;
    byLevel: Record<string, number>;
    byCategory: Record<string, number>;
  } {
    const byLevel: Record<string, number> = {};
    const byCategory: Record<string, number> = {};
    for (const log of this.logs) {
      byLevel[log.level] = (byLevel[log.level] || 0) + 1;
      byCategory[log.category] = (byCategory[log.category] || 0) + 1;
    }
    return {
      totalLogs: this.logs.length,
      byLevel,
      byCategory,
    };
  }
}

export interface PacketTrace {
  id: string;
  timestamp: number;
  source: string;
  destination: string;
  protocol: string;
  size: number;
  hops: Array<{
    node: string;
    timestamp: number;
    latency: number;
  }>;
  totalLatency: number;
  status: "success" | "timeout" | "error";
}

export class PacketTracer extends EventEmitter {
  private traces: PacketTrace[] = [];
  private maxTraces: number = 100;

  constructor() {
    super();
  }

  startTrace(
    source: string,
    destination: string,
    protocol: string,
    size: number
  ): PacketTrace {
    const trace: PacketTrace = {
      id: uuidv4(),
      timestamp: Date.now(),
      source,
      destination,
      protocol,
      size,
      hops: [],
      totalLatency: 0,
      status: "success",
    };
    this.traces.push(trace);
    if (this.traces.length > this.maxTraces) {
      this.traces.shift();
    }
    this.emit("trace:started", trace);
    return trace;
  }

  addHop(traceId: string, node: string, latency: number): boolean {
    const trace = this.traces.find((t) => t.id === traceId);
    if (!trace) return false;
    trace.hops.push({
      node,
      timestamp: Date.now(),
      latency,
    });
    trace.totalLatency += latency;
    this.emit("hop:added", { traceId, node, latency });
    return true;
  }

  completeTrace(traceId: string, status: PacketTrace["status"]): boolean {
    const trace = this.traces.find((t) => t.id === traceId);
    if (!trace) return false;
    trace.status = status;
    this.emit("trace:completed", trace);
    return true;
  }

  getTrace(id: string): PacketTrace | undefined {
    return this.traces.find((t) => t.id === id);
  }

  getTraces(count?: number): PacketTrace[] {
    if (count) {
      return this.traces.slice(-count);
    }
    return [...this.traces];
  }

  getStats(): {
    totalTraces: number;
    averageLatency: number;
    averageHops: number;
    successRate: number;
  } {
    const traces = this.traces;
    if (traces.length === 0) {
      return { totalTraces: 0, averageLatency: 0, averageHops: 0, successRate: 0 };
    }
    return {
      totalTraces: traces.length,
      averageLatency: traces.reduce((sum, t) => sum + t.totalLatency, 0) / traces.length,
      averageHops: traces.reduce((sum, t) => sum + t.hops.length, 0) / traces.length,
      successRate: (traces.filter((t) => t.status === "success").length / traces.length) * 100,
    };
  }
}

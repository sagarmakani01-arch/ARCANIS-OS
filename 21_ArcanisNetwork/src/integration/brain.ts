import { EventEmitter } from "events";
import { NetworkStats, SecurityEvent, NetworkEvent } from "../types";

export interface BrainInsight {
  id: string;
  type: "optimization" | "security" | "prediction" | "anomaly";
  confidence: number;
  data: Record<string, unknown>;
  recommendation: string;
  timestamp: number;
}

export interface BrainPrediction {
  id: string;
  metric: string;
  predictedValue: number;
  confidence: number;
  timeframe: number;
  timestamp: number;
}

export class ArcanisBrainIntegration extends EventEmitter {
  private brainRef: unknown = null;
  private insights: BrainInsight[] = [];
  private predictions: BrainPrediction[] = [];
  private learningData: Map<string, unknown[]> = new Map();

  constructor() {
    super();
  }

  setBrainReference(brain: unknown): void {
    this.brainRef = brain;
    this.emit("brain:connected");
  }

  getBrainReference(): unknown {
    return this.brainRef;
  }

  analyzeNetworkStats(stats: NetworkStats): BrainInsight[] {
    const insights: BrainInsight[] = [];
    if (stats.averageLatency > 100) {
      insights.push(this.createInsight(
        "optimization",
        0.85,
        { metric: "latency", value: stats.averageLatency, threshold: 100 },
        "Consider optimizing route selection to reduce latency"
      ));
    }
    if (stats.droppedPackets > stats.totalPacketsSent * 0.05) {
      insights.push(this.createInsight(
        "security",
        0.9,
        { metric: "packetLoss", value: stats.droppedPackets, total: stats.totalPacketsSent },
        "High packet loss may indicate network interference or attack"
      ));
    }
    if (stats.activeConnections > 900) {
      insights.push(this.createInsight(
        "prediction",
        0.75,
        { metric: "connections", value: stats.activeConnections, limit: 1024 },
        "Connection limit approaching, consider scaling up"
      ));
    }
    return insights;
  }

  private createInsight(
    type: BrainInsight["type"],
    confidence: number,
    data: Record<string, unknown>,
    recommendation: string
  ): BrainInsight {
    const insight: BrainInsight = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2),
      type,
      confidence,
      data,
      recommendation,
      timestamp: Date.now(),
    };
    this.insights.push(insight);
    this.emit("insight:created", insight);
    return insight;
  }

  predictMetric(
    metric: string,
    currentValue: number,
    timeframe: number
  ): BrainPrediction {
    const history = this.learningData.get(metric) || [];
    let predictedValue = currentValue;
    if (history.length > 0) {
      const avgChange = history.reduce((sum, val) => sum + (val as number), 0) / history.length;
      predictedValue = currentValue + avgChange * (timeframe / 60000);
    }
    const prediction: BrainPrediction = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2),
      metric,
      predictedValue,
      confidence: Math.min(0.95, 0.5 + history.length * 0.05),
      timeframe,
      timestamp: Date.now(),
    };
    this.predictions.push(prediction);
    this.emit("prediction:created", prediction);
    return prediction;
  }

  learn(metric: string, value: unknown): void {
    const data = this.learningData.get(metric) || [];
    data.push(value);
    if (data.length > 1000) {
      data.shift();
    }
    this.learningData.set(metric, data);
  }

  getInsights(type?: string): BrainInsight[] {
    if (type) {
      return this.insights.filter((i) => i.type === type);
    }
    return [...this.insights];
  }

  getPredictions(metric?: string): BrainPrediction[] {
    if (metric) {
      return this.predictions.filter((p) => p.metric === metric);
    }
    return [...this.predictions];
  }

  processNetworkEvent(event: NetworkEvent): void {
    this.learn("events", event);
    if (event.type.includes("error") || event.type.includes("security")) {
      this.createInsight(
        "anomaly",
        0.7,
        { event: event.type, source: event.source },
        `Anomalous network event detected: ${event.type}`
      );
    }
  }

  processSecurityEvent(event: SecurityEvent): void {
    this.learn("security", event);
    if (event.severity === "critical" || event.severity === "high") {
      this.createInsight(
        "security",
        0.95,
        { event: event.type, severity: event.severity, source: event.source },
        `Critical security event: ${event.description}`
      );
    }
  }

  getStats(): {
    totalInsights: number;
    totalPredictions: number;
    learningMetrics: number;
    totalDataPoints: number;
  } {
    return {
      totalInsights: this.insights.length,
      totalPredictions: this.predictions.length,
      learningMetrics: this.learningData.size,
      totalDataPoints: Array.from(this.learningData.values()).reduce(
        (sum, data) => sum + data.length,
        0
      ),
    };
  }
}

import { EventEmitter } from 'events';
import { randomBytes } from 'crypto';

function generateId(len = 12): string { return randomBytes(len / 2).toString('hex'); }

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';
export interface LogEntry { id: string; timestamp: Date; level: LogLevel; message: string; source: string; context?: Record<string, unknown>; traceId?: string; }
export interface LogQuery { level?: LogLevel; source?: string; startDate?: Date; endDate?: Date; pattern?: string; limit?: number; offset?: number; }
export interface LogTransport { id: string; name: string; type: 'console' | 'file' | 'http' | 'stream' | 'elasticsearch'; minLevel: LogLevel; options: Record<string, unknown>; }
export interface LogAlert { id: string; level: LogLevel; pattern: string; callback: string; threshold: number; windowMs: number; triggerCount: number; lastTriggered?: Date; }
export interface LogMetric { source: string; level: LogLevel; count: number; lastSeen: Date; }
export interface LogRetention { source: string; maxAgeMs: number; maxCount: number; }

export class LogManager extends EventEmitter {
  private entries: LogEntry[] = [];
  private transports: Map<string, LogTransport> = new Map();
  private alerts: Map<string, LogAlert> = new Map();
  private metrics: Map<string, LogMetric> = new Map();
  private retentions: Map<string, LogRetention> = new Map();
  private maxEntries: number;
  private minLevel: LogLevel;

  constructor(options: { maxEntries?: number; minLevel?: LogLevel } = {}) {
    super();
    this.maxEntries = options.maxEntries || 10000;
    this.minLevel = options.minLevel || 'debug';
  }

  private levelOrder(level: LogLevel): number {
    const order: Record<LogLevel, number> = { debug: 0, info: 1, warn: 2, error: 3, fatal: 4 };
    return order[level];
  }

  private shouldLog(level: LogLevel): boolean { return this.levelOrder(level) >= this.levelOrder(this.minLevel); }

  log(config: { level: LogLevel; message: string; source: string; context?: Record<string, unknown>; traceId?: string }): LogEntry {
    if (!this.shouldLog(config.level)) return null as any;
    const entry: LogEntry = { id: generateId(8), timestamp: new Date(), level: config.level, message: config.message, source: config.source, context: config.context, traceId: config.traceId };
    this.entries.push(entry);
    if (this.entries.length > this.maxEntries) this.entries.shift();
    this.updateMetrics(config.source, config.level);
    this.checkAlerts(config.level, config.message);
    this.emit('log', entry);
    return entry;
  }

  debug(message: string, source: string, context?: Record<string, unknown>): LogEntry { return this.log({ level: 'debug', message, source, context }); }
  info(message: string, source: string, context?: Record<string, unknown>): LogEntry { return this.log({ level: 'info', message, source, context }); }
  warn(message: string, source: string, context?: Record<string, unknown>): LogEntry { return this.log({ level: 'warn', message, source, context }); }
  error(message: string, source: string, context?: Record<string, unknown>): LogEntry { return this.log({ level: 'error', message, source, context }); }
  fatal(message: string, source: string, context?: Record<string, unknown>): LogEntry { return this.log({ level: 'fatal', message, source, context }); }

  query(filters: LogQuery): LogEntry[] {
    let result = [...this.entries];
    if (filters.level) result = result.filter(e => e.level === filters.level);
    if (filters.source) result = result.filter(e => e.source === filters.source);
    if (filters.startDate) result = result.filter(e => e.timestamp >= filters.startDate!);
    if (filters.endDate) result = result.filter(e => e.timestamp <= filters.endDate!);
    if (filters.pattern) result = result.filter(e => e.message.includes(filters.pattern!));
    const offset = filters.offset || 0;
    const limit = filters.limit || result.length;
    return result.slice(offset, offset + limit);
  }

  addTransport(config: { name: string; type: LogTransport['type']; minLevel?: LogLevel; options?: Record<string, unknown> }): LogTransport {
    const t: LogTransport = { id: generateId(8), name: config.name, type: config.type, minLevel: config.minLevel || 'info', options: config.options || {} };
    this.transports.set(t.id, t);
    return t;
  }

  removeTransport(id: string): void { this.transports.delete(id); }
  getTransports(): LogTransport[] { return Array.from(this.transports.values()); }

  addAlert(config: { level: LogLevel; pattern: string; callback: string; threshold: number; windowMs: number }): LogAlert {
    const a: LogAlert = { id: generateId(8), level: config.level, pattern: config.pattern, callback: config.callback, threshold: config.threshold, windowMs: config.windowMs, triggerCount: 0 };
    this.alerts.set(a.id, a);
    return a;
  }

  private checkAlerts(level: LogLevel, message: string): void {
    for (const alert of this.alerts.values()) {
      if (alert.level === level && message.includes(alert.pattern)) {
        alert.triggerCount++;
        if (alert.triggerCount >= alert.threshold) {
          alert.lastTriggered = new Date();
          this.emit('alert:trigger', alert);
        }
      }
    }
  }

  private updateMetrics(source: string, level: LogLevel): void {
    const key = `${source}:${level}`;
    const existing = this.metrics.get(key);
    if (existing) { existing.count++; existing.lastSeen = new Date(); }
    else this.metrics.set(key, { source, level, count: 1, lastSeen: new Date() });
  }

  getMetrics(): LogMetric[] { return Array.from(this.metrics.values()); }
  getMetricsBySource(source: string): LogMetric[] { return Array.from(this.metrics.values()).filter(m => m.source === source); }
  getAlerts(): LogAlert[] { return Array.from(this.alerts.values()); }

  getEntryCount(): number { return this.entries.length; }

  setRetention(source: string, config: { maxAgeMs: number; maxCount: number }): void {
    this.retentions.set(source, { source, ...config });
  }

  applyRetentions(): number {
    let removed = 0;
    for (const [source, retention] of this.retentions) {
      const sourceEntries = this.entries.filter(e => e.source === source);
      const now = Date.now();
      for (const entry of sourceEntries) {
        if (now - entry.timestamp.getTime() > retention.maxAgeMs) {
          this.entries = this.entries.filter(e => e.id !== entry.id);
          removed++;
        }
      }
      const remaining = this.entries.filter(e => e.source === source);
      if (remaining.length > retention.maxCount) {
        const toRemove = remaining.slice(0, remaining.length - retention.maxCount);
        for (const entry of toRemove) this.entries = this.entries.filter(e => e.id !== entry.id);
        removed += toRemove.length;
      }
    }
    return removed;
  }

  clear(): void { this.entries = []; this.emit('logs:clear'); }
  clearSource(source: string): void { this.entries = this.entries.filter(e => e.source !== source); }
}

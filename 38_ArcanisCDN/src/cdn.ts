import { EventEmitter } from 'events';
import { createHash, randomBytes } from 'crypto';

function generateId(len = 12): string { return randomBytes(len / 2).toString('hex'); }
function sha256(d: string): string { return createHash('sha256').update(d).digest('hex'); }

export type CacheStatus = 'hit' | 'miss' | 'stale' | 'revalidated';
export type EdgeStatus = 'healthy' | 'degraded' | 'down';
export interface CdnOrigin { id: string; url: string; weight: number; healthCheck: string; status: EdgeStatus; failovers: string[]; }
export interface CdnCache { key: string; url: string; content: string; contentType: string; size: number; hash: string; headers: Record<string, string>; cachedAt: Date; expiresAt: Date; ttl: number; }
export interface CdnEdge { id: string; name: string; region: string; url: string; status: EdgeStatus; cacheHitRate: number; requestCount: number; bandwidth: number; }
export interface CdnRule { id: string; pattern: string; ttl: number; bypassCache: boolean; purgeOnUpdate: boolean; compress: boolean; securityHeaders: boolean; corsOrigin?: string; }
export interface CdnPurgeJob { id: string; type: 'url' | 'tag' | 'all'; targets: string[]; status: 'pending' | 'running' | 'completed'; createdAt: Date; completedAt?: Date; }
export interface CdnMetrics { totalRequests: number; cacheHits: number; cacheMisses: number; bandwidth: number; avgLatency: number; errorRate: number; }
export interface CdnAnalytics { requestsByRegion: Record<string, number>; hitsByRegion: Record<string, number>; topUrls: { url: string; count: number }[]; bandwidthByEdge: Record<string, number>; }

export class CdnManager extends EventEmitter {
  private origins: Map<string, CdnOrigin> = new Map();
  private cache: Map<string, CdnCache> = new Map();
  private edges: Map<string, CdnEdge> = new Map();
  private rules: Map<string, CdnRule> = new Map();
  private purgeJobs: Map<string, CdnPurgeJob> = new Map();
  private metrics: CdnMetrics = { totalRequests: 0, cacheHits: 0, cacheMisses: 0, bandwidth: 0, avgLatency: 0, errorRate: 0 };
  private requestLogs: { url: string; region: string; hit: boolean; size: number; timestamp: Date }[] = [];
  private maxCacheSize: number;

  constructor(options: { maxCacheSize?: number } = {}) {
    super();
    this.maxCacheSize = options.maxCacheSize || 10000;
  }

  addOrigin(config: { url: string; weight?: number; healthCheck?: string; failovers?: string[] }): CdnOrigin {
    const origin: CdnOrigin = { id: generateId(8), url: config.url, weight: config.weight || 100, healthCheck: config.healthCheck || '/health', status: 'healthy', failovers: config.failovers || [] };
    this.origins.set(origin.id, origin);
    return origin;
  }

  removeOrigin(id: string): void { this.origins.delete(id); }
  getOrigins(): CdnOrigin[] { return Array.from(this.origins.values()); }

  selectOrigin(): CdnOrigin | undefined {
    const healthy = Array.from(this.origins.values()).filter(o => o.status === 'healthy');
    if (healthy.length === 0) return undefined;
    const totalWeight = healthy.reduce((a, o) => a + o.weight, 0);
    let random = Math.random() * totalWeight;
    for (const origin of healthy) { random -= origin.weight; if (random <= 0) return origin; }
    return healthy[0];
  }

  addEdge(config: { name: string; region: string; url: string }): CdnEdge {
    const edge: CdnEdge = { id: generateId(8), name: config.name, region: config.region, url: config.url, status: 'healthy', cacheHitRate: 0, requestCount: 0, bandwidth: 0 };
    this.edges.set(edge.id, edge);
    return edge;
  }

  removeEdge(id: string): void { this.edges.delete(id); }
  getEdges(): CdnEdge[] { return Array.from(this.edges.values()); }
  getEdgeByRegion(region: string): CdnEdge | undefined { return Array.from(this.edges.values()).find(e => e.region === region && e.status === 'healthy'); }

  addRule(config: { pattern: string; ttl: number; bypassCache?: boolean; purgeOnUpdate?: boolean; compress?: boolean; securityHeaders?: boolean; corsOrigin?: string }): CdnRule {
    const rule: CdnRule = { id: generateId(8), pattern: config.pattern, ttl: config.ttl, bypassCache: config.bypassCache || false, purgeOnUpdate: config.purgeOnUpdate || false, compress: config.compress ?? true, securityHeaders: config.securityHeaders ?? true, corsOrigin: config.corsOrigin };
    this.rules.set(rule.id, rule);
    return rule;
  }

  removeRule(id: string): void { this.rules.delete(id); }
  getRules(): CdnRule[] { return Array.from(this.rules.values()); }

  findRule(url: string): CdnRule | undefined {
    return Array.from(this.rules.values()).find(r => {
      const regex = new RegExp(r.pattern.replace(/\*/g, '.*'));
      return regex.test(url);
    });
  }

  async fetch(url: string, options?: { region?: string; headers?: Record<string, string> }): Promise<{ content: string; status: CacheStatus; size: number; ttl: number }> {
    const rule = this.findRule(url);
    if (rule?.bypassCache) {
      this.metrics.totalRequests++;
      this.metrics.cacheMisses++;
      this.recordRequest(url, options?.region || 'default', false, 0);
      return { content: '', status: 'miss', size: 0, ttl: rule.ttl };
    }

    const cached = this.cache.get(url);
    if (cached && cached.expiresAt > new Date()) {
      this.metrics.totalRequests++;
      this.metrics.cacheHits++;
      this.recordRequest(url, options?.region || 'default', true, cached.size);
      return { content: cached.content, status: 'hit', size: cached.size, ttl: Math.floor((cached.expiresAt.getTime() - Date.now()) / 1000) };
    }

    if (cached) {
      this.metrics.totalRequests++;
      this.recordRequest(url, options?.region || 'default', false, 0);
      return { content: '', status: 'stale', size: 0, ttl: 0 };
    }

    this.metrics.totalRequests++;
    this.metrics.cacheMisses++;
    this.recordRequest(url, options?.region || 'default', false, 0);
    return { content: '', status: 'miss', size: 0, ttl: 0 };
  }

  store(url: string, content: string, contentType: string, ttl: number, headers?: Record<string, string>): CdnCache {
    const entry: CdnCache = { key: generateId(8), url, content, contentType, size: content.length, hash: sha256(content), headers: headers || {}, cachedAt: new Date(), expiresAt: new Date(Date.now() + ttl * 1000), ttl };
    this.cache.set(url, entry);
    this.purgeOnUpdate(url);
    return entry;
  }

  private purgeOnUpdate(url: string): void {
    const rule = this.findRule(url);
    if (rule?.purgeOnUpdate) this.purgeUrl(url);
  }

  purgeUrl(url: string): CdnPurgeJob {
    const job: CdnPurgeJob = { id: generateId(8), type: 'url', targets: [url], status: 'completed', createdAt: new Date(), completedAt: new Date() };
    this.purgeJobs.set(job.id, job);
    this.cache.delete(url);
    return job;
  }

  purgeAll(): CdnPurgeJob {
    const job: CdnPurgeJob = { id: generateId(8), type: 'all', targets: [], status: 'completed', createdAt: new Date(), completedAt: new Date() };
    this.purgeJobs.set(job.id, job);
    this.cache.clear();
    return job;
  }

  private recordRequest(url: string, region: string, hit: boolean, size: number): void {
    this.requestLogs.push({ url, region, hit, size, timestamp: new Date() });
    this.metrics.bandwidth += size;
  }

  getAnalytics(): CdnAnalytics {
    const requestsByRegion: Record<string, number> = {};
    const hitsByRegion: Record<string, number> = {};
    const urlCounts: Record<string, number> = {};
    const bandwidthByEdge: Record<string, number> = {};
    for (const log of this.requestLogs) {
      requestsByRegion[log.region] = (requestsByRegion[log.region] || 0) + 1;
      if (log.hit) hitsByRegion[log.region] = (hitsByRegion[log.region] || 0) + 1;
      urlCounts[log.url] = (urlCounts[log.url] || 0) + 1;
    }
    const topUrls = Object.entries(urlCounts).map(([url, count]) => ({ url, count })).sort((a, b) => b.count - a.count).slice(0, 10);
    return { requestsByRegion, hitsByRegion, topUrls, bandwidthByEdge };
  }

  getMetrics(): CdnMetrics { return { ...this.metrics, avgLatency: this.metrics.totalRequests > 0 ? 50 : 0 }; }
  getCache(): CdnCache[] { return Array.from(this.cache.values()); }
  getPurgeJobs(): CdnPurgeJob[] { return Array.from(this.purgeJobs.values()); }
  clearCache(): void { this.cache.clear(); }
}

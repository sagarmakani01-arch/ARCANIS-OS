import { EventEmitter } from 'events';
import { HttpMethod, Route, ApiRequest, ApiResponse, Middleware, RateLimitRule, ApiKey, CircuitBreaker, Transformer } from './types.js';
import { generateId } from './utils.js';

export interface ApiGatewayOptions { maxRoutes?: number; defaultTimeout?: number; }

export class ApiGateway extends EventEmitter {
  private routes: Map<string, Route> = new Map();
  private middlewares: Map<string, Middleware> = new Map();
  private rateLimits: Map<string, RateLimitRule> = new Map();
  private apiKeys: Map<string, ApiKey> = new Map();
  private circuitBreakers: Map<string, CircuitBreaker> = new Map();
  private transformers: Map<string, Transformer> = new Map();
  private requestCounts: Map<string, { count: number; windowStart: number }> = new Map();
  private options: Required<ApiGatewayOptions>;

  constructor(options: ApiGatewayOptions = {}) {
    super();
    this.options = { maxRoutes: options.maxRoutes || 1000, defaultTimeout: options.defaultTimeout || 30000 };
  }

  registerRoute(config: { method: HttpMethod; path: string; handler: string; middleware?: string[]; auth?: boolean; rateLimit?: number; version?: string }): Route {
    if (this.routes.size >= this.options.maxRoutes) throw new Error(`Maximum route limit reached (${this.options.maxRoutes})`);
    const id = generateId(8);
    const route: Route = { id, method: config.method, path: config.path, handler: config.handler, middleware: config.middleware || [], auth: config.auth, rateLimit: config.rateLimit, version: config.version };
    this.routes.set(id, route);
    this.emit('route:register', route);
    return route;
  }

  removeRoute(routeId: string): void {
    if (!this.routes.has(routeId)) throw new Error(`Route ${routeId} not found`);
    this.routes.delete(routeId);
    this.emit('route:remove', { id: routeId });
  }

  matchRoute(method: HttpMethod, path: string): Route | undefined {
    return Array.from(this.routes.values()).find(r => r.method === method && this.pathMatches(r.path, path));
  }

  private pathMatches(pattern: string, path: string): boolean {
    const patternParts = pattern.split('/').filter(Boolean);
    const pathParts = path.split('/').filter(Boolean);
    if (patternParts.length !== pathParts.length) return false;
    for (let i = 0; i < patternParts.length; i++) {
      if (patternParts[i].startsWith(':')) continue;
      if (patternParts[i] !== pathParts[i]) return false;
    }
    return true;
  }

  extractParams(pattern: string, path: string): Record<string, string> {
    const params: Record<string, string> = {};
    const patternParts = pattern.split('/').filter(Boolean);
    const pathParts = path.split('/').filter(Boolean);
    for (let i = 0; i < patternParts.length; i++) {
      if (patternParts[i].startsWith(':')) params[patternParts[i].slice(1)] = pathParts[i];
    }
    return params;
  }

  async handleRequest(request: ApiRequest): Promise<ApiResponse> {
    const start = Date.now();
    const route = this.matchRoute(request.method, request.path);
    if (!route) return { status: 404, headers: {}, body: { error: 'Not Found' }, duration: Date.now() - start };

    if (route.auth && !request.userId) return { status: 401, headers: {}, body: { error: 'Unauthorized' }, duration: Date.now() - start };

    if (route.rateLimit) {
      const allowed = this.checkRateLimit(request.path, route.rateLimit);
      if (!allowed) return { status: 429, headers: { 'Retry-After': '60' }, body: { error: 'Rate limit exceeded' }, duration: Date.now() - start };
    }

    this.emit('request', { request, route });
    return { status: 200, headers: { 'Content-Type': 'application/json' }, body: { success: true, path: request.path }, duration: Date.now() - start };
  }

  private checkRateLimit(path: string, limit: number): boolean {
    const now = Date.now();
    const entry = this.requestCounts.get(path);
    if (!entry || now - entry.windowStart > 60000) {
      this.requestCounts.set(path, { count: 1, windowStart: now });
      return true;
    }
    entry.count++;
    return entry.count <= limit;
  }

  addMiddleware(config: { name: string; order: number; handler: string }): Middleware {
    const id = generateId(8);
    const mw: Middleware = { id, name: config.name, order: config.order, handler: config.handler };
    this.middlewares.set(id, mw);
    this.emit('middleware:add', mw);
    return mw;
  }

  removeMiddleware(mwId: string): void { this.middlewares.delete(mwId); }

  createApiKey(config: { name: string; scopes: string[]; rateLimit: number; expiresAt?: Date }): ApiKey {
    const id = generateId(8);
    const key = generateId(32);
    const apiKey: ApiKey = { id, key, name: config.name, scopes: config.scopes, rateLimit: config.rateLimit, createdAt: new Date(), expiresAt: config.expiresAt };
    this.apiKeys.set(id, apiKey);
    return apiKey;
  }

  validateApiKey(key: string): ApiKey | undefined {
    return Array.from(this.apiKeys.values()).find(k => k.key === key && (!k.expiresAt || k.expiresAt > new Date()));
  }

  addCircuitBreaker(config: { serviceId: string; threshold: number; timeout: number }): CircuitBreaker {
    const id = generateId(8);
    const cb: CircuitBreaker = { id, serviceId: config.serviceId, state: 'closed', failureCount: 0, threshold: config.threshold, timeout: config.timeout };
    this.circuitBreakers.set(id, cb);
    return cb;
  }

  recordFailure(serviceId: string): void {
    const cb = Array.from(this.circuitBreakers.values()).find(c => c.serviceId === serviceId);
    if (!cb) return;
    cb.failureCount++;
    cb.lastFailure = new Date();
    if (cb.failureCount >= cb.threshold) { cb.state = 'open'; this.emit('circuit:open', cb); }
  }

  getRouteCount(): number { return this.routes.size; }
  getMiddlewareCount(): number { return this.middlewares.size; }
  getApiKeyCount(): number { return this.apiKeys.size; }
  getCircuitBreakerCount(): number { return this.circuitBreakers.size; }
}

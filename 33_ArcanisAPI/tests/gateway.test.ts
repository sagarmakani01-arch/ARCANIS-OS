import { describe, it, expect, beforeEach } from 'vitest';
import { ApiGateway } from '../src/gateway.js';

describe('ApiGateway', () => {
  let gw: ApiGateway;
  beforeEach(() => { gw = new ApiGateway(); });

  describe('registerRoute', () => {
    it('should register a route', () => {
      const r = gw.registerRoute({ method: 'GET', path: '/api/users', handler: 'getUsers' });
      expect(r).toBeDefined();
      expect(r.method).toBe('GET');
    });
    it('should emit route:register', () => {
      let emitted = false;
      gw.on('route:register', () => { emitted = true; });
      gw.registerRoute({ method: 'POST', path: '/api/users', handler: 'createUser' });
      expect(emitted).toBe(true);
    });
  });

  describe('matchRoute', () => {
    it('should match exact routes', () => {
      gw.registerRoute({ method: 'GET', path: '/api/users', handler: 'list' });
      const match = gw.matchRoute('GET', '/api/users');
      expect(match).toBeDefined();
    });
    it('should match parameterized routes', () => {
      gw.registerRoute({ method: 'GET', path: '/api/users/:id', handler: 'get' });
      const match = gw.matchRoute('GET', '/api/users/123');
      expect(match).toBeDefined();
    });
    it('should return undefined for no match', () => {
      expect(gw.matchRoute('GET', '/nonexistent')).toBeUndefined();
    });
  });

  describe('handleRequest', () => {
    it('should return 404 for unknown route', async () => {
      const res = await gw.handleRequest({ id: '1', method: 'GET', path: '/unknown', headers: {}, query: {}, timestamp: new Date() });
      expect(res.status).toBe(404);
    });
    it('should return 401 when auth required', async () => {
      gw.registerRoute({ method: 'GET', path: '/secure', handler: 'secure', auth: true });
      const res = await gw.handleRequest({ id: '1', method: 'GET', path: '/secure', headers: {}, query: {}, timestamp: new Date() });
      expect(res.status).toBe(401);
    });
    it('should return 200 for valid request', async () => {
      gw.registerRoute({ method: 'GET', path: '/api/health', handler: 'health' });
      const res = await gw.handleRequest({ id: '1', method: 'GET', path: '/api/health', headers: {}, query: {}, timestamp: new Date() });
      expect(res.status).toBe(200);
    });
  });

  describe('middleware', () => {
    it('should add middleware', () => {
      const mw = gw.addMiddleware({ name: 'auth', order: 1, handler: 'authHandler' });
      expect(mw).toBeDefined();
      expect(gw.getMiddlewareCount()).toBe(1);
    });
  });

  describe('apiKeys', () => {
    it('should create and validate api key', () => {
      const k = gw.createApiKey({ name: 'test', scopes: ['read'], rateLimit: 100 });
      expect(gw.validateApiKey(k.key)).toBeDefined();
      expect(gw.validateApiKey('invalid')).toBeUndefined();
    });
  });

  describe('circuitBreaker', () => {
    it('should trip circuit breaker', () => {
      gw.addCircuitBreaker({ serviceId: 'svc-1', threshold: 3, timeout: 5000 });
      for (let i = 0; i < 3; i++) gw.recordFailure('svc-1');
      expect(gw.getCircuitBreakerCount()).toBe(1);
    });
  });
});

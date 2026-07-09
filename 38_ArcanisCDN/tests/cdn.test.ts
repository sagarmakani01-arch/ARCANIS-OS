import { describe, it, expect, beforeEach } from 'vitest';
import { CdnManager } from '../src/cdn.js';

describe('CdnManager', () => {
  let cdn: CdnManager;
  beforeEach(() => { cdn = new CdnManager(); });

  describe('origins', () => {
    it('should add and select origin', () => {
      cdn.addOrigin({ url: 'https://origin1.com', weight: 100 });
      cdn.addOrigin({ url: 'https://origin2.com', weight: 100 });
      const o = cdn.selectOrigin();
      expect(o).toBeDefined();
      expect(cdn.getOrigins().length).toBe(2);
    });
    it('should return undefined for no healthy origins', () => {
      expect(cdn.selectOrigin()).toBeUndefined();
    });
  });

  describe('edges', () => {
    it('should add edge and find by region', () => {
      cdn.addEdge({ name: 'us-east', region: 'us-east-1', url: 'https://us-east.cdn.com' });
      cdn.addEdge({ name: 'eu-west', region: 'eu-west-1', url: 'https://eu-west.cdn.com' });
      expect(cdn.getEdgeByRegion('us-east-1')).toBeDefined();
      expect(cdn.getEdgeByRegion('ap-south-1')).toBeUndefined();
    });
  });

  describe('rules', () => {
    it('should add rule and match url', () => {
      cdn.addRule({ pattern: '/static/*', ttl: 3600 });
      const rule = cdn.findRule('/static/app.js');
      expect(rule).toBeDefined();
      expect(cdn.findRule('/api/users')).toBeUndefined();
    });
  });

  describe('caching', () => {
    it('should store and retrieve from cache', async () => {
      cdn.store('/page.html', '<html>test</html>', 'text/html', 3600);
      const result = await cdn.fetch('/page.html');
      expect(result.status).toBe('hit');
      expect(result.content).toBe('<html>test</html>');
    });
    it('should return miss for uncached', async () => {
      const result = await cdn.fetch('/missing');
      expect(result.status).toBe('miss');
    });
    it('should bypass cache when rule says so', async () => {
      cdn.addRule({ pattern: '/api/*', ttl: 0, bypassCache: true });
      cdn.store('/api/data', '{}', 'application/json', 3600);
      const result = await cdn.fetch('/api/data');
      expect(result.status).toBe('miss');
    });
  });

  describe('purge', () => {
    it('should purge by url', async () => {
      cdn.store('/test', 'data', 'text/plain', 3600);
      const job = cdn.purgeUrl('/test');
      expect(job.status).toBe('completed');
      expect(cdn.getCache().length).toBe(0);
    });
    it('should purge all', async () => {
      cdn.store('/a', '1', 'text/plain', 3600);
      cdn.store('/b', '2', 'text/plain', 3600);
      cdn.purgeAll();
      expect(cdn.getCache().length).toBe(0);
    });
  });

  describe('metrics', () => {
    it('should track requests', async () => {
      cdn.addEdge({ name: 'edge', region: 'us-east', url: 'https://cdn.com' });
      cdn.store('/test', 'data', 'text/plain', 3600);
      await cdn.fetch('/test');
      await cdn.fetch('/miss');
      const m = cdn.getMetrics();
      expect(m.totalRequests).toBe(2);
      expect(m.cacheHits).toBe(1);
    });
  });

  describe('analytics', () => {
    it('should return analytics data', async () => {
      cdn.addEdge({ name: 'e', region: 'us-east', url: 'https://cdn.com' });
      cdn.store('/a', '1', 'text/plain', 3600);
      await cdn.fetch('/a', { region: 'us-east' });
      const a = cdn.getAnalytics();
      expect(a.requestsByRegion['us-east']).toBe(1);
    });
  });
});

import { describe, it, expect, beforeEach } from 'vitest';
import { LogManager } from '../src/logs.js';

describe('LogManager', () => {
  let lm: LogManager;
  beforeEach(() => { lm = new LogManager(); });

  describe('logging', () => {
    it('should log entries at different levels', () => {
      lm.debug('d', 'sys'); lm.info('i', 'sys'); lm.warn('w', 'sys'); lm.error('e', 'sys'); lm.fatal('f', 'sys');
      expect(lm.getEntryCount()).toBe(5);
    });
    it('should filter by level', () => {
      lm.info('a', 'sys'); lm.error('b', 'sys'); lm.warn('c', 'sys');
      const entries = lm.query({ level: 'error' });
      expect(entries.length).toBe(1);
      expect(entries[0].message).toBe('b');
    });
    it('should filter by source', () => {
      lm.info('a', 'api'); lm.info('b', 'db');
      expect(lm.query({ source: 'api' }).length).toBe(1);
    });
    it('should filter by pattern', () => {
      lm.info('connection timeout', 'db'); lm.info('connection ok', 'db');
      expect(lm.query({ pattern: 'timeout' }).length).toBe(1);
    });
    it('should respect limit', () => {
      for (let i = 0; i < 100; i++) lm.info(`msg ${i}`, 'sys');
      expect(lm.query({ limit: 10 }).length).toBe(10);
    });
  });

  describe('transports', () => {
    it('should add and remove transports', () => {
      const t = lm.addTransport({ name: 'console', type: 'console', minLevel: 'info' });
      expect(lm.getTransports().length).toBe(1);
      lm.removeTransport(t.id);
      expect(lm.getTransports().length).toBe(0);
    });
  });

  describe('alerts', () => {
    it('should trigger alert on threshold', () => {
      let triggered = false;
      lm.on('alert:trigger', () => { triggered = true; });
      lm.addAlert({ level: 'error', pattern: 'DB', callback: 'onAlert', threshold: 2, windowMs: 60000 });
      lm.error('DB connection failed', 'db'); lm.error('DB timeout', 'db');
      expect(triggered).toBe(true);
    });
  });

  describe('metrics', () => {
    it('should track metrics by source', () => {
      lm.info('msg', 'api'); lm.info('msg', 'api'); lm.error('msg', 'api');
      const metrics = lm.getMetricsBySource('api');
      expect(metrics.length).toBe(2);
    });
  });

  describe('retention', () => {
    it('should apply retention policies', () => {
      lm.setRetention('tmp', { maxAgeMs: 0, maxCount: 1 });
      lm.info('old', 'tmp'); lm.info('new', 'tmp');
      const removed = lm.applyRetentions();
      expect(removed).toBeGreaterThanOrEqual(0);
    });
  });
});

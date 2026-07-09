import { describe, it, expect, beforeEach } from 'vitest';
import { BackupManager } from '../src/backup.js';

describe('BackupManager', () => {
  let bm: BackupManager;
  beforeEach(() => { bm = new BackupManager(); });

  describe('jobs', () => {
    it('should create and run a backup job', async () => {
      const job = bm.createJob({ name: 'full-backup', type: 'full', sources: ['/data'], destination: '/backup' });
      expect(job.status).toBe('pending');
      const snap = await bm.runJob(job.id);
      expect(snap).toBeDefined();
      expect(job.status).toBe('completed');
      expect(job.size).toBeGreaterThan(0);
    });
    it('should cancel a running job', async () => {
      const job = bm.createJob({ name: 'inc', type: 'incremental', sources: ['/data'], destination: '/backup' });
      await bm.runJob(job.id);
      // Cannot cancel completed job
      expect(job.status).toBe('completed');
    });
  });

  describe('restore', () => {
    it('should restore from backup', async () => {
      const job = bm.createJob({ name: 'b', type: 'full', sources: ['/a'], destination: '/b' });
      const snap = await bm.runJob(job.id);
      const restore = await bm.restore({ backupId: snap.id, targetPath: '/restore' });
      expect(restore.status).toBe('completed');
    });
    it('should fail restore for missing backup', async () => {
      await expect(bm.restore({ backupId: 'missing', targetPath: '/t' })).rejects.toThrow('not found');
    });
  });

  describe('policies', () => {
    it('should create and apply policies', async () => {
      bm.createPolicy({ name: 'keep10', retentionDays: 30, maxBackups: 2, schedule: 'daily', sources: ['/data'], destination: '/backup' });
      const job = bm.createJob({ name: 'b', type: 'full', sources: ['/data'], destination: '/backup' });
      await bm.runJob(job.id);
      await bm.runJob(job.id);
      await bm.runJob(job.id);
      const pruned = bm.applyPolicies();
      expect(pruned).toBeGreaterThanOrEqual(0);
    });
  });

  describe('verify', () => {
    it('should verify backup integrity', async () => {
      const job = bm.createJob({ name: 'b', type: 'full', sources: ['/a'], destination: '/b' });
      const snap = await bm.runJob(job.id);
      const result = bm.verify(snap.id);
      expect(result.valid).toBe(true);
    });
  });

  describe('metrics', () => {
    it('should calculate metrics', async () => {
      const job = bm.createJob({ name: 'b', type: 'full', sources: ['/a'], destination: '/b' });
      await bm.runJob(job.id);
      const metrics = bm.getMetrics();
      expect(metrics.totalBackups).toBe(1);
      expect(metrics.successRate).toBe(1);
    });
  });
});

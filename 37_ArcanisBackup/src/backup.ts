import { EventEmitter } from 'events';
import { randomBytes, createHash } from 'crypto';

function generateId(len = 12): string { return randomBytes(len / 2).toString('hex'); }
function sha256(d: string): string { return createHash('sha256').update(d).digest('hex'); }

export type BackupType = 'full' | 'incremental' | 'differential';
export type BackupStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
export type RestoreStatus = 'pending' | 'running' | 'completed' | 'failed';
export interface BackupJob { id: string; name: string; type: BackupType; status: BackupStatus; sources: string[]; destination: string; compression: 'none' | 'gzip' | 'lz4' | 'zstd'; encryption: 'none' | 'aes256'; encryptionKey?: string; createdAt: Date; startedAt?: Date; completedAt?: Date; size?: number; compressedSize?: number; error?: string; schedule?: string; }
export interface BackupSnapshot { id: string; jobId: string; type: BackupType; timestamp: Date; files: BackupFile[]; size: number; hash: string; parentId?: string; }
export interface BackupFile { path: string; size: number; hash: string; modifiedAt: Date; included: boolean; }
export interface RestoreJob { id: string; backupId: string; targetPath: string; status: RestoreStatus; files: string[]; createdAt: Date; completedAt?: Date; error?: string; }
export interface BackupPolicy { id: string; name: string; retentionDays: number; maxBackups: number; schedule: string; sources: string[]; destination: string; }
export interface BackupMetrics { totalBackups: number; totalSize: number; successRate: number; avgDuration: number; lastBackup?: Date; }

export class BackupManager extends EventEmitter {
  private jobs: Map<string, BackupJob> = new Map();
  private snapshots: Map<string, BackupSnapshot> = new Map();
  private restoreJobs: Map<string, RestoreJob> = new Map();
  private policies: Map<string, BackupPolicy> = new Map();

  createJob(config: { name: string; type: BackupType; sources: string[]; destination: string; compression?: BackupJob['compression']; encryption?: BackupJob['encryption']; schedule?: string }): BackupJob {
    const job: BackupJob = { id: generateId(8), name: config.name, type: config.type, status: 'pending', sources: config.sources, destination: config.destination, compression: config.compression || 'gzip', encryption: config.encryption || 'none', createdAt: new Date(), schedule: config.schedule };
    this.jobs.set(job.id, job);
    this.emit('job:create', job);
    return job;
  }

  async runJob(jobId: string): Promise<BackupSnapshot> {
    const job = this.jobs.get(jobId);
    if (!job) throw new Error('Job not found');
    job.status = 'running';
    job.startedAt = new Date();
    this.emit('job:start', job);

    const files = job.sources.map(s => ({ path: s, size: Math.floor(Math.random() * 10000), hash: sha256(s), modifiedAt: new Date(), included: true }));
    const totalSize = files.reduce((a, f) => a + f.size, 0);
    const parentId = job.type !== 'full' ? this.findLatestSnapshot(jobId)?.id : undefined;
    const snapshot: BackupSnapshot = { id: generateId(8), jobId, type: job.type, timestamp: new Date(), files, size: totalSize, hash: sha256(JSON.stringify(files)), parentId };
    this.snapshots.set(snapshot.id, snapshot);

    job.status = 'completed';
    job.completedAt = new Date();
    job.size = totalSize;
    job.compressedSize = totalSize * (job.compression === 'none' ? 1 : 0.6);
    this.emit('job:complete', { job, snapshot });
    return snapshot;
  }

  cancelJob(jobId: string): void {
    const job = this.jobs.get(jobId);
    if (!job) throw new Error('Job not found');
    if (job.status !== 'running') throw new Error('Job is not running');
    job.status = 'cancelled';
    this.emit('job:cancel', job);
  }

  private findLatestSnapshot(jobId: string): BackupSnapshot | undefined {
    return Array.from(this.snapshots.values()).filter(s => s.jobId === jobId).sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())[0];
  }

  async restore(config: { backupId: string; targetPath: string; files?: string[] }): Promise<RestoreJob> {
    const snapshot = this.snapshots.get(config.backupId);
    if (!snapshot) throw new Error('Backup snapshot not found');
    const restoreJob: RestoreJob = { id: generateId(8), backupId: config.backupId, targetPath: config.targetPath, status: 'running', files: config.files || snapshot.files.map(f => f.path), createdAt: new Date() };
    this.restoreJobs.set(restoreJob.id, restoreJob);
    this.emit('restore:start', restoreJob);
    restoreJob.status = 'completed';
    restoreJob.completedAt = new Date();
    this.emit('restore:complete', restoreJob);
    return restoreJob;
  }

  createPolicy(config: { name: string; retentionDays: number; maxBackups: number; schedule: string; sources: string[]; destination: string }): BackupPolicy {
    const policy: BackupPolicy = { id: generateId(8), ...config };
    this.policies.set(policy.id, policy);
    return policy;
  }

  applyPolicies(): number {
    let pruned = 0;
    for (const policy of this.policies.values()) {
      const jobSnapshots = Array.from(this.snapshots.values()).filter(s => {
        const job = this.jobs.get(s.jobId);
        return job && policy.sources.some(src => job.sources.includes(src));
      }).sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

      for (let i = policy.maxBackups; i < jobSnapshots.length; i++) {
        this.snapshots.delete(jobSnapshots[i].id);
        pruned++;
      }
      const cutoff = new Date(Date.now() - policy.retentionDays * 86400000);
      for (const snap of jobSnapshots) {
        if (snap.timestamp < cutoff) { this.snapshots.delete(snap.id); pruned++; }
      }
    }
    return pruned;
  }

  verify(backupId: string): { valid: boolean; errors: string[] } {
    const snapshot = this.snapshots.get(backupId);
    if (!snapshot) return { valid: false, errors: ['Snapshot not found'] };
    const errors: string[] = [];
    const expectedHash = sha256(JSON.stringify(snapshot.files));
    if (expectedHash !== snapshot.hash) errors.push('Hash mismatch');
    for (const file of snapshot.files) { if (!file.path) errors.push('Missing file path'); }
    return { valid: errors.length === 0, errors };
  }

  getMetrics(): BackupMetrics {
    const allJobs = Array.from(this.jobs.values());
    const completed = allJobs.filter(j => j.status === 'completed');
    const totalSize = completed.reduce((a, j) => a + (j.size || 0), 0);
    const durations = completed.filter(j => j.startedAt && j.completedAt).map(j => j.completedAt!.getTime() - j.startedAt!.getTime());
    return {
      totalBackups: completed.length,
      totalSize,
      successRate: allJobs.length > 0 ? completed.length / allJobs.length : 0,
      avgDuration: durations.length > 0 ? durations.reduce((a, b) => a + b, 0) / durations.length : 0,
      lastBackup: completed.length > 0 ? completed.sort((a, b) => (b.completedAt?.getTime() || 0) - (a.completedAt?.getTime() || 0))[0].completedAt : undefined
    };
  }

  listJobs(): BackupJob[] { return Array.from(this.jobs.values()); }
  listSnapshots(): BackupSnapshot[] { return Array.from(this.snapshots.values()); }
  listRestoreJobs(): RestoreJob[] { return Array.from(this.restoreJobs.values()); }
  listPolicies(): BackupPolicy[] { return Array.from(this.policies.values()); }
  deleteJob(jobId: string): void { this.jobs.delete(jobId); }
  deleteSnapshot(snapshotId: string): void { this.snapshots.delete(snapshotId); }
}

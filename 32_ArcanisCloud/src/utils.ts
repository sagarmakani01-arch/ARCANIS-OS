// ArcanisCloud - Utility Functions

import { randomBytes, createHash } from 'crypto';

export function generateId(length: number = 12): string {
  return randomBytes(length / 2).toString('hex');
}

export function generateNodeId(): string { return 'node-' + generateId(12); }
export function generateServiceId(): string { return 'svc-' + generateId(12); }
export function generateTaskId(): string { return 'task-' + generateId(12); }
export function generateDeploymentId(): string { return 'deploy-' + generateId(12); }
export function generateAlertId(): string { return 'alert-' + generateId(12); }
export function generateEventId(): string { return 'evt-' + generateId(12); }
export function generateTenantId(): string { return 'tenant-' + generateId(12); }
export function generateMetricId(): string { return 'metric-' + generateId(8); }

export function sha256(data: string): string {
  return createHash('sha256').update(data).digest('hex');
}

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function formatCpu(cpu: number): string {
  if (cpu < 1) return `${Math.round(cpu * 1000)}m`;
  return `${cpu.toFixed(1)}`;
}

export function formatMemory(bytes: number): string {
  if (bytes < 1024 ** 2) return `${bytes} B`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(0)} Mi`;
  return `${(bytes / 1024 ** 3).toFixed(1)} Gi`;
}

export function matchesConstraint(value: string, constraint: { operator: string; value?: string }): boolean {
  switch (constraint.operator) {
    case 'eq': return value === constraint.value;
    case 'neq': return value !== constraint.value;
    case 'in': return constraint.value?.split(',').includes(value) ?? false;
    case 'notin': return !(constraint.value?.split(',').includes(value) ?? false);
    case 'exists': return !!value;
    default: return true;
  }
}

export function calculateAffinity(labels: Record<string, string>, constraints: { key: string; operator: string; value?: string }[]): number {
  let score = 100;
  for (const c of constraints) {
    const val = labels[c.key];
    if (matchesConstraint(val || '', c)) {
      score += 10;
    } else {
      score -= 20;
    }
  }
  return Math.max(0, Math.min(100, score));
}

export function weightedRandom<T>(items: T[], weights: number[]): T {
  const totalWeight = weights.reduce((sum, w) => sum + w, 0);
  let random = Math.random() * totalWeight;
  for (let i = 0; i < items.length; i++) {
    random -= weights[i];
    if (random <= 0) return items[i];
  }
  return items[items.length - 1];
}

// ArcanisContainer - Utility Functions

import { randomBytes, createHash } from 'crypto';

export function generateId(length: number = 12): string {
  return randomBytes(length / 2).toString('hex');
}

export function generateContainerId(): string {
  return generateId(64);
}

export function generateImageId(): string {
  return 'sha256:' + generateId(64);
}

export function generateNetworkId(): string {
  return generateId(12);
}

export function generateVolumeId(): string {
  return generateId(12);
}

export function generateServiceId(): string {
  return generateId(12);
}

export function generateTaskId(): string {
  return generateId(12);
}

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

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  return `${h}h ${m}m`;
}

export function validateContainerName(name: string): boolean {
  return /^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,62}$/.test(name);
}

export function validateImageName(name: string): boolean {
  return /^[a-zA-Z0-9][a-zA-Z0-9._/-]{0,127}$/.test(name);
}

export function parsePortMapping(mapping: string): { hostPort: number; containerPort: number; protocol: 'tcp' | 'udp' } {
  const parts = mapping.split(':');
  if (parts.length < 2) throw new Error(`Invalid port mapping: ${mapping}`);
  
  const containerPart = parts[parts.length - 1];
  const hostPort = parseInt(parts[0], 10);
  let containerPort: number;
  let protocol: 'tcp' | 'udp' = 'tcp';

  if (containerPart.includes('/')) {
    const [port, proto] = containerPart.split('/');
    containerPort = parseInt(port, 10);
    protocol = proto as 'tcp' | 'udp';
  } else {
    containerPort = parseInt(containerPart, 10);
  }

  if (isNaN(hostPort) || isNaN(containerPort)) {
    throw new Error(`Invalid port mapping: ${mapping}`);
  }

  return { hostPort, containerPort, protocol };
}

export function parseMemorySize(size: string): number {
  const match = size.match(/^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB|TB)?$/i);
  if (!match) throw new Error(`Invalid memory size: ${size}`);
  
  const value = parseFloat(match[1]);
  const unit = (match[2] || 'B').toUpperCase();
  
  const multipliers: Record<string, number> = {
    'B': 1,
    'KB': 1024,
    'MB': 1024 ** 2,
    'GB': 1024 ** 3,
    'TB': 1024 ** 4,
  };
  
  return Math.floor(value * multipliers[unit]);
}

export function parseCpuCpus(cpus: string): { start: number; end: number }[] {
  const ranges: { start: number; end: number }[] = [];
  const parts = cpus.split(',');
  
  for (const part of parts) {
    if (part.includes('-')) {
      const [start, end] = part.split('-').map(Number);
      ranges.push({ start, end });
    } else {
      const num = parseInt(part, 10);
      ranges.push({ start: num, end: num });
    }
  }
  
  return ranges;
}

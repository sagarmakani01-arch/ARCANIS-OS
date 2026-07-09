export enum ProcessState {
  Created = "created",
  Running = "running",
  Suspended = "suspended",
  Terminated = "terminated",
  Blocked = "blocked",
}

export enum Priority {
  High = 0,
  Normal = 1,
  Low = 2,
  Idle = 3,
}

export interface ProcessInfo {
  pid: string;
  name: string;
  state: ProcessState;
  priority: Priority;
  parentPid: string | null;
  createdAt: number;
  cpuUsage: number;
  memoryUsage: number;
  metadata: Record<string, unknown>;
}

export interface KernelConfig {
  version: string;
  maxProcesses: number;
  defaultPriority: Priority;
  schedulerTickMs: number;
  securityLevel: SecurityLevel;
  features: KernelFeatures;
}

export interface KernelFeatures {
  aiAcceleration: boolean;
  voiceControl: boolean;
  memoryManagement: boolean;
  processIsolation: boolean;
}

export enum SecurityLevel {
  Maximum = "maximum",
  High = "high",
  Standard = "standard",
  Low = "low",
}

export interface SystemCall {
  pid: string;
  type: string;
  args: unknown[];
  timestamp: number;
}

export interface SystemStats {
  uptime: number;
  totalProcesses: number;
  activeProcesses: number;
  cpuLoad: number;
  memoryUsed: number;
  memoryTotal: number;
}

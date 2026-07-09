// ArcanisContainer - Type Definitions

export type ContainerState = 'created' | 'running' | 'paused' | 'stopped' | 'deleted';
export type NetworkMode = 'bridge' | 'host' | 'none' | 'overlay';
export type MountType = 'volume' | 'bind' | 'tmpfs';
export type ImageStatus = 'pulling' | 'ready' | 'building' | 'error';
export type ServiceState = 'pending' | 'running' | 'updating' | 'failed' | 'stopped';
export type RestartPolicy = 'no' | 'always' | 'on-failure' | 'unless-stopped';
export type Capability = 'net_bind_service' | 'sys_admin' | 'sys_PTRACE' | 'net_raw' | 'dac_override' | 'setuid' | 'setgid' | 'chown' | 'mknod' | 'audit_write' | 'setfcap' | 'sys_chroot' | 'kill' | 'fowner' | 'fsetid' | 'sys_resource' | 'sys_nice' | 'sys_time' | 'sys_tty_config' | 'audit_control' | 'mac_admin' | 'mac_override' | 'syslog' | 'wake_alarm' | 'block_suspend' | 'perfmon';

export interface ContainerConfig {
  id?: string;
  name: string;
  image: string;
  command?: string[];
  entrypoint?: string[];
  env?: Record<string, string>;
  labels?: Record<string, string>;
  ports?: PortMapping[];
  volumes?: MountConfig[];
  network?: NetworkConfig;
  resources?: ResourceConfig;
  security?: SecurityConfig;
  restartPolicy?: RestartPolicy;
  hostname?: string;
  workingDir?: string;
  user?: string;
  readonlyRootfs?: boolean;
  stopTimeout?: number;
}

export interface PortMapping {
  hostPort: number;
  containerPort: number;
  protocol: 'tcp' | 'udp';
  hostIp?: string;
}

export interface MountConfig {
  source: string;
  target: string;
  type: MountType;
  readonly?: boolean;
  tmpfsSizeBytes?: number;
}

export interface NetworkConfig {
  mode: NetworkMode;
  networks?: string[];
  ipAddress?: string;
  dns?: string[];
  hostname?: string;
  extraHosts?: Record<string, string>;
}

export interface ResourceConfig {
  cpuShares?: number;
  cpuPeriod?: number;
  cpuQuota?: number;
  cpus?: number;
  memory?: number;
  memorySwap?: number;
  memoryReservation?: number;
  blkioWeight?: number;
  blkioDeviceWeight?: { path: string; weight: number }[];
  pidsLimit?: number;
  ulimits?: UlimitConfig[];
  oomKillDisable?: boolean;
  cpusetCpus?: string;
  cpusetMems?: string;
}

export interface UlimitConfig {
  name: string;
  soft: number;
  hard: number;
}

export interface SecurityConfig {
  privileged?: boolean;
  capabilities?: {
    add?: Capability[];
    drop?: Capability[];
  };
  seccompProfile?: string;
  appArmorProfile?: string;
  noNewPrivileges?: boolean;
  readOnlyPaths?: string[];
  maskPaths?: string[];
  procOpts?: string[];
}

export interface Container {
  id: string;
  name: string;
  image: string;
  state: ContainerState;
  pid?: number;
  exitCode?: number;
  config: ContainerConfig;
  created: Date;
  started?: Date;
  stopped?: Date;
  filesystem?: string;
  networkSettings?: NetworkSettings;
  mounts?: MountInfo[];
  logs?: LogEntry[];
}

export interface NetworkSettings {
  mode: NetworkMode;
  ipAddress?: string;
  gateway?: string;
  bridge?: string;
  ports?: PortMapping[];
  networks?: Record<string, NetworkInfo>;
}

export interface NetworkInfo {
  name: string;
  ipAddress: string;
  gateway: string;
  macAddress: string;
}

export interface MountInfo {
  source: string;
  target: string;
  type: MountType;
  readonly: boolean;
}

export interface LogEntry {
  timestamp: Date;
  stream: 'stdout' | 'stderr';
  message: string;
}

export interface Image {
  id: string;
  name: string;
  tag: string;
  size: number;
  created: Date;
  status: ImageStatus;
  layers: ImageLayer[];
  config: ImageConfig;
  labels?: Record<string, string>;
}

export interface ImageLayer {
  id: string;
  size: number;
  command?: string;
  created: Date;
}

export interface ImageConfig {
  cmd?: string[];
  entrypoint?: string[];
  env?: string[];
  workingDir?: string;
  user?: string;
  labels?: Record<string, string>;
  exposedPorts?: string[];
  volumes?: string[];
}

export interface DockerfileInstruction {
  command: string;
  args: string[];
  flags: Record<string, string>;
}

export interface Network {
  id: string;
  name: string;
  driver: NetworkMode;
  subnet: string;
  gateway: string;
  ipRange?: string;
  containers: Map<string, string>;
  options?: Record<string, string>;
  created: Date;
}

export interface Volume {
  name: string;
  driver: string;
  mountpoint: string;
  labels?: Record<string, string>;
  options?: Record<string, string>;
  scope: 'local' | 'global';
  created: Date;
}

export interface Service {
  id: string;
  name: string;
  image: string;
  replicas: number;
  runningReplicas: number;
  state: ServiceState;
  config: ServiceConfig;
  tasks: Task[];
  created: Date;
  updated: Date;
}

export interface ServiceConfig {
  command?: string[];
  env?: Record<string, string>;
  ports?: PortMapping[];
  resources?: ResourceConfig;
  updateConfig?: UpdateConfig;
  restartPolicy?: RestartPolicy;
  labels?: Record<string, string>;
}

export interface UpdateConfig {
  parallelism?: number;
  delay?: number;
  failureAction?: 'continue' | 'pause' | 'rollback';
  order?: 'stop-first' | 'start-first';
  maxFailureRatio?: number;
}

export interface Task {
  id: string;
  serviceId: string;
  containerId?: string;
  slot: number;
  state: ServiceState;
  desiredState: ServiceState;
  created: Date;
  updated: Date;
}

export interface ContainerStats {
  cpuStats: CpuStats;
  memoryStats: MemoryStats;
  networkStats: NetworkStats;
  ioStats: IoStats;
  timestamp: Date;
}

export interface CpuStats {
  cpuUsage: number;
  systemCpuUsage: number;
  onlineCpus: number;
  throttlingData: {
    periods: number;
    throttledPeriods: number;
    throttledTime: number;
  };
}

export interface MemoryStats {
  usage: number;
  limit: number;
  maxUsage: number;
  rss: number;
  cache: number;
  swap: number;
}

export interface NetworkStats {
  rxBytes: number;
  txBytes: number;
  rxPackets: number;
  txPackets: number;
  rxErrors: number;
  txErrors: number;
  rxDropped: number;
  txDropped: number;
}

export interface IoStats {
  readBytes: number;
  writeBytes: number;
  readOps: number;
  writeOps: number;
}

// ArcanisCloud - Type Definitions

export type NodeState = 'joining' | 'healthy' | 'unhealthy' | 'draining' | 'left';
export type ServiceState = 'pending' | 'running' | 'updating' | 'failed' | 'stopped';
export type TaskState = 'pending' | 'assigned' | 'running' | 'failed' | 'completed';
export type DeploymentStrategy = 'rolling' | 'blue-green' | 'canary' | 'recreate';
export type AlertSeverity = 'info' | 'warning' | 'critical';
export type AlertState = 'firing' | 'resolved' | 'silenced';
export type MetricType = 'counter' | 'gauge' | 'histogram' | 'summary';
export type TenantTier = 'free' | 'starter' | 'professional' | 'enterprise';

export interface Node {
  id: string;
  name: string;
  address: string;
  port: number;
  state: NodeState;
  role: 'manager' | 'worker';
  resources: NodeResources;
  labels: Record<string, string>;
  services: string[];
  lastHeartbeat: Date;
  joinedAt: Date;
}

export interface NodeResources {
  cpuTotal: number;
  cpuAvailable: number;
  memoryTotal: number;
  memoryAvailable: number;
  diskTotal: number;
  diskAvailable: number;
  gpuTotal: number;
  gpuAvailable: number;
}

export interface Service {
  id: string;
  name: string;
  namespace: string;
  image: string;
  replicas: number;
  runningReplicas: number;
  state: ServiceState;
  config: ServiceConfig;
  endpoints: Endpoint[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ServiceConfig {
  command?: string[];
  env?: Record<string, string>;
  ports?: PortConfig[];
  resources?: ResourceRequirements;
  constraints?: Constraint[];
  healthCheck?: HealthCheck;
  labels?: Record<string, string>;
  updateConfig?: UpdateConfig;
}

export interface PortConfig {
  name: string;
  port: number;
  targetPort: number;
  protocol: 'tcp' | 'udp';
}

export interface ResourceRequirements {
  cpuRequest?: number;
  cpuLimit?: number;
  memoryRequest?: number;
  memoryLimit?: number;
  gpuRequest?: number;
  gpuLimit?: number;
}

export interface Constraint {
  key: string;
  operator: 'eq' | 'neq' | 'in' | 'notin' | 'exists';
  value?: string;
}

export interface HealthCheck {
  type: 'http' | 'tcp' | 'exec';
  path?: string;
  port?: number;
  command?: string[];
  interval: number;
  timeout: number;
  retries: number;
}

export interface UpdateConfig {
  parallelism?: number;
  delay?: number;
  failureAction?: 'continue' | 'pause' | 'rollback';
  order?: 'stop-first' | 'start-first';
  maxFailureRatio?: number;
}

export interface Endpoint {
  nodeId: string;
  address: string;
  port: number;
  healthy: boolean;
}

export interface Task {
  id: string;
  serviceId: string;
  nodeId?: string;
  slot: number;
  state: TaskState;
  desiredState: TaskState;
  status: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Deployment {
  id: string;
  serviceId: string;
  strategy: DeploymentStrategy;
  version: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed' | 'rolled-back';
  progress: DeploymentProgress;
  config: DeploymentConfig;
  createdAt: Date;
  completedAt?: Date;
}

export interface DeploymentProgress {
  total: number;
  ready: number;
  updated: number;
  failed: number;
}

export interface DeploymentConfig {
  image: string;
  replicas: number;
  resources?: ResourceRequirements;
  strategy: DeploymentStrategy;
  rollbackVersion?: string;
}

export interface ClusterEvent {
  id: string;
  type: 'node-join' | 'node-leave' | 'node-unhealthy' | 'service-create' | 'service-update' | 'service-delete' | 'task-fail' | 'deployment-start' | 'deployment-complete' | 'alert-fire' | 'alert-resolve';
  source: string;
  message: string;
  metadata?: Record<string, string>;
  timestamp: Date;
}

export interface Metric {
  name: string;
  type: MetricType;
  labels: Record<string, string>;
  value: number;
  timestamp: Date;
}

export interface Alert {
  id: string;
  name: string;
  severity: AlertSeverity;
  state: AlertState;
  condition: AlertCondition;
  currentValue: number;
  firedAt: Date;
  resolvedAt?: Date;
  labels?: Record<string, string>;
}

export interface AlertCondition {
  metric: string;
  operator: 'gt' | 'lt' | 'gte' | 'lte' | 'eq';
  threshold: number;
  duration: number;
}

export interface Tenant {
  id: string;
  name: string;
  tier: TenantTier;
  quotas: TenantQuotas;
  usage: TenantUsage;
  createdAt: Date;
  labels?: Record<string, string>;
}

export interface TenantQuotas {
  maxNodes: number;
  maxServices: number;
  maxCpu: number;
  maxMemory: number;
  maxStorage: number;
  maxBandwidth: number;
}

export interface TenantUsage {
  nodes: number;
  services: number;
  cpu: number;
  memory: number;
  storage: number;
  bandwidth: number;
}

export interface LoadBalancerConfig {
  algorithm: 'round-robin' | 'weighted' | 'least-connections' | 'ip-hash';
  healthCheck: HealthCheck;
  stickySession?: boolean;
  ssl?: SslConfig;
}

export interface SslConfig {
  certPath: string;
  keyPath: string;
  caPath?: string;
}

export interface ScheduleResult {
  nodeId: string;
  score: number;
  reasons: string[];
}

export interface AutoScalePolicy {
  id: string;
  name: string;
  serviceId: string;
  minReplicas: number;
  maxReplicas: number;
  metrics: ScaleMetric[];
  cooldown: number;
}

export interface ScaleMetric {
  type: 'cpu' | 'memory' | 'custom';
  name?: string;
  target: number;
  operator: 'avg' | 'max' | 'p95' | 'p99';
}

// ArcanisCloud - Main Exports

export * from './types.js';
export * from './utils.js';
export * from './cluster/cluster-manager.js';
export * from './scheduler/scheduler.js';
export * from './loadbalancer/load-balancer.js';
export * from './autoscaler/auto-scaler.js';
export * from './discovery/service-discovery.js';
export * from './monitoring/monitoring-manager.js';
export * from './tenancy/tenancy-manager.js';
export * from './deployment/deployment-manager.js';

import { ClusterManager, ClusterManagerOptions } from './cluster/cluster-manager.js';
import { Scheduler, SchedulerOptions } from './scheduler/scheduler.js';
import { LoadBalancer, LoadBalancerConfig, LoadBalancerOptions } from './loadbalancer/load-balancer.js';
import { AutoScaler, AutoScalerOptions } from './autoscaler/auto-scaler.js';
import { ServiceDiscovery, ServiceRegistryOptions } from './discovery/service-discovery.js';
import { MonitoringManager, MonitoringOptions } from './monitoring/monitoring-manager.js';
import { TenancyManager, TenancyOptions } from './tenancy/tenancy-manager.js';
import { DeploymentManager, DeploymentManagerOptions } from './deployment/deployment-manager.js';

export interface ArcanisCloudOptions {
  cluster?: ClusterManagerOptions;
  scheduler?: SchedulerOptions;
  loadBalancer?: LoadBalancerConfig & LoadBalancerOptions;
  autoScaler?: AutoScalerOptions;
  serviceDiscovery?: ServiceRegistryOptions;
  monitoring?: MonitoringOptions;
  tenancy?: TenancyOptions;
  deployment?: DeploymentManagerOptions;
}

export class ArcanisCloud {
  readonly cluster: ClusterManager;
  readonly scheduler: Scheduler;
  readonly loadBalancer: LoadBalancer;
  readonly autoScaler: AutoScaler;
  readonly discovery: ServiceDiscovery;
  readonly monitoring: MonitoringManager;
  readonly tenancy: TenancyManager;
  readonly deployment: DeploymentManager;

  constructor(options: ArcanisCloudOptions = {}) {
    this.cluster = new ClusterManager(options.cluster);
    this.scheduler = new Scheduler(this.cluster, options.scheduler);
    this.loadBalancer = new LoadBalancer(options.loadBalancer, options.loadBalancer);
    this.autoScaler = new AutoScaler(options.autoScaler);
    this.discovery = new ServiceDiscovery(options.serviceDiscovery);
    this.monitoring = new MonitoringManager(options.monitoring);
    this.tenancy = new TenancyManager(options.tenancy);
    this.deployment = new DeploymentManager(options.deployment);
  }

  async getSystemInfo(): Promise<{
    cluster: { nodes: number; healthy: number; managers: number; workers: number };
    scheduler: { tasks: number; running: number };
    loadBalancer: { backends: number; healthy: number; connections: number };
    services: { registered: number; endpoints: number };
    monitoring: { metrics: number; alerts: number; firing: number };
    tenancy: { tenants: number };
    deployment: { active: number; total: number };
  }> {
    return {
      cluster: {
        nodes: this.cluster.getNodeCount(),
        healthy: this.cluster.getHealthyCount(),
        managers: this.cluster.getManagerCount(),
        workers: this.cluster.getWorkerCount(),
      },
      scheduler: {
        tasks: this.scheduler.getTaskCount(),
        running: this.scheduler.getRunningTaskCount(),
      },
      loadBalancer: {
        backends: this.loadBalancer.getBackendCount(),
        healthy: this.loadBalancer.getHealthyCount(),
        connections: this.loadBalancer.getTotalConnections(),
      },
      services: {
        registered: this.discovery.getServiceCount(),
        endpoints: this.discovery.getEndpointCount(),
      },
      monitoring: {
        metrics: this.monitoring.getMetricCount(),
        alerts: this.monitoring.getAlertCount(),
        firing: this.monitoring.getFiringAlertCount(),
      },
      tenancy: { tenants: this.tenancy.getTenantCount() },
      deployment: {
        active: this.deployment.getActiveDeploymentCount(),
        total: this.deployment.getDeploymentCount(),
      },
    };
  }
}

// ArcanisContainer - Main Exports

export * from './types.js';
export * from './utils.js';
export * from './runtime/container-runtime.js';
export * from './images/image-manager.js';
export * from './networking/network-manager.js';
export * from './storage/storage-manager.js';
export * from './orchestration/orchestration-manager.js';
export * from './security/security-manager.js';
export * from './resources/resource-manager.js';
export * from './cli/cli.js';

import { ContainerRuntime, RuntimeOptions } from './runtime/container-runtime.js';
import { ImageManager, ImageManagerOptions } from './images/image-manager.js';
import { NetworkManager, NetworkManagerOptions } from './networking/network-manager.js';
import { StorageManager, StorageManagerOptions } from './storage/storage-manager.js';
import { OrchestrationManager, OrchestrationOptions } from './orchestration/orchestration-manager.js';
import { SecurityManager, SecurityManagerOptions } from './security/security-manager.js';
import { ResourceManager, ResourceManagerOptions } from './resources/resource-manager.js';
import { ArcanisContainerCLI } from './cli/cli.js';

export interface ArcanisContainerOptions {
  runtime?: RuntimeOptions;
  images?: ImageManagerOptions;
  networks?: NetworkManagerOptions;
  storage?: StorageManagerOptions;
  orchestration?: OrchestrationOptions;
  security?: SecurityManagerOptions;
  resources?: ResourceManagerOptions;
}

export class ArcanisContainer {
  readonly runtime: ContainerRuntime;
  readonly images: ImageManager;
  readonly networks: NetworkManager;
  readonly storage: StorageManager;
  readonly orchestration: OrchestrationManager;
  readonly security: SecurityManager;
  readonly resources: ResourceManager;
  readonly cli: ArcanisContainerCLI;

  constructor(options: ArcanisContainerOptions = {}) {
    this.runtime = new ContainerRuntime(options.runtime);
    this.images = new ImageManager(options.images);
    this.networks = new NetworkManager(options.networks);
    this.storage = new StorageManager(options.storage);
    this.resources = new ResourceManager(options.resources);
    this.security = new SecurityManager(options.security);
    this.orchestration = new OrchestrationManager(this.runtime, options.orchestration);

    this.cli = new ArcanisContainerCLI({
      runtime: this.runtime,
      images: this.images,
      networks: this.networks,
      storage: this.storage,
      orchestration: this.orchestration,
      security: this.security,
      resources: this.resources,
    });
  }

  async getSystemInfo(): Promise<{
    containers: { total: number; running: number };
    images: { total: number; totalSize: number };
    networks: number;
    volumes: number;
    services: number;
    resources: { cpu: number; memory: number; cpuUtilization: number; memoryUtilization: number };
  }> {
    const usage = await this.resources.getResourceUsage();
    return {
      containers: { total: this.runtime.getContainerCount(), running: this.runtime.getRunningCount() },
      images: { total: this.images.getImageCount(), totalSize: this.images.getTotalSize() },
      networks: this.networks.getNetworkCount(),
      volumes: this.storage.getVolumeCount(),
      services: this.orchestration.getServiceCount(),
      resources: {
        cpu: usage.total.cpu,
        memory: usage.total.memory,
        cpuUtilization: usage.utilization.cpu,
        memoryUtilization: usage.utilization.memory,
      },
    };
  }
}

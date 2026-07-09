// ArcanisContainer - CLI

import { ContainerRuntime } from '../runtime/container-runtime.js';
import { ImageManager } from '../images/image-manager.js';
import { NetworkManager } from '../networking/network-manager.js';
import { StorageManager } from '../storage/storage-manager.js';
import { OrchestrationManager } from '../orchestration/orchestration-manager.js';
import { SecurityManager } from '../security/security-manager.js';
import { ResourceManager } from '../resources/resource-manager.js';
import { formatBytes, formatDuration, parsePortMapping, parseMemorySize } from '../utils.js';
import { ContainerConfig, NetworkMode, MountType, Capability } from '../types.js';

export interface CliOptions {
  runtime: ContainerRuntime;
  images: ImageManager;
  networks: NetworkManager;
  storage: StorageManager;
  orchestration: OrchestrationManager;
  security: SecurityManager;
  resources: ResourceManager;
}

export class ArcanisContainerCLI {
  private runtime: ContainerRuntime;
  private images: ImageManager;
  private networks: NetworkManager;
  private storage: StorageManager;
  private orchestration: OrchestrationManager;
  private security: SecurityManager;
  private resources: ResourceManager;

  constructor(options: CliOptions) {
    this.runtime = options.runtime;
    this.images = options.images;
    this.networks = options.networks;
    this.storage = options.storage;
    this.orchestration = options.orchestration;
    this.security = options.security;
    this.resources = options.resources;
  }

  async execute(args: string[]): Promise<{ exitCode: number; output: string }> {
    if (args.length === 0) {
      return this.showHelp();
    }

    const command = args[0];
    const subArgs = args.slice(1);

    try {
      switch (command) {
        case 'run': return this.runCommand(subArgs);
        case 'create': return this.createCommand(subArgs);
        case 'start': return this.startCommand(subArgs);
        case 'stop': return this.stopCommand(subArgs);
        case 'restart': return this.restartCommand(subArgs);
        case 'rm': case 'remove': return this.removeCommand(subArgs);
        case 'ps': case 'list': return this.listCommand(subArgs);
        case 'inspect': return this.inspectCommand(subArgs);
        case 'logs': return this.logsCommand(subArgs);
        case 'exec': return this.execCommand(subArgs);
        case 'stats': return this.statsCommand(subArgs);
        case 'images': return this.imagesCommand(subArgs);
        case 'pull': return this.pullCommand(subArgs);
        case 'build': return this.buildCommand(subArgs);
        case 'network': return this.networkCommand(subArgs);
        case 'volume': return this.volumeCommand(subArgs);
        case 'service': return this.serviceCommand(subArgs);
        case 'security': return this.securityCommand(subArgs);
        case 'system': return this.systemCommand(subArgs);
        case 'help': return this.showHelp();
        case 'version': return this.versionCommand();
        default:
          return { exitCode: 1, output: `Unknown command: ${command}. Run 'arcanis-container help' for usage.` };
      }
    } catch (error) {
      return { exitCode: 1, output: `Error: ${error instanceof Error ? error.message : String(error)}` };
    }
  }

  private async runCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    if (args.length < 1) return { exitCode: 1, output: 'Usage: arcanis-container run [OPTIONS] IMAGE [COMMAND]' };

    const config: ContainerConfig = {
      name: `container-${Date.now()}`,
      image: args.find(a => !a.startsWith('-')) || 'arcanis/base:latest',
    };

    const portIdx = args.indexOf('-p');
    if (portIdx !== -1 && args[portIdx + 1]) {
      const mapping = parsePortMapping(args[portIdx + 1]);
      config.ports = [{ hostPort: mapping.hostPort, containerPort: mapping.containerPort, protocol: mapping.protocol }];
    }

    const nameIdx = args.indexOf('--name');
    if (nameIdx !== -1 && args[nameIdx + 1]) config.name = args[nameIdx + 1];

    const memIdx = args.indexOf('-m');
    if (memIdx !== -1 && args[memIdx + 1]) {
      config.resources = { memory: parseMemorySize(args[memIdx + 1]) };
    }

    const container = await this.runtime.create(config);
    await this.runtime.start(container.id);

    return { exitCode: 0, output: container.id };
  }

  private async createCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    if (args.length < 1) return { exitCode: 1, output: 'Usage: arcanis-container create [OPTIONS] IMAGE' };

    const config: ContainerConfig = {
      name: `container-${Date.now()}`,
      image: args.find(a => !a.startsWith('-')) || 'arcanis/base:latest',
    };

    const nameIdx = args.indexOf('--name');
    if (nameIdx !== -1 && args[nameIdx + 1]) config.name = args[nameIdx + 1];

    const container = await this.runtime.create(config);
    return { exitCode: 0, output: container.id };
  }

  private async startCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    if (args.length === 0) return { exitCode: 1, output: 'Usage: arcanis-container start CONTAINER' };
    await this.runtime.start(args[0]);
    return { exitCode: 0, output: '' };
  }

  private async stopCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    if (args.length === 0) return { exitCode: 1, output: 'Usage: arcanis-container stop CONTAINER' };
    const timeout = args.includes('-t') ? parseInt(args[args.indexOf('-t') + 1]) : undefined;
    await this.runtime.stop(args[0], timeout);
    return { exitCode: 0, output: '' };
  }

  private async restartCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    if (args.length === 0) return { exitCode: 1, output: 'Usage: arcanis-container restart CONTAINER' };
    await this.runtime.restart(args[0]);
    return { exitCode: 0, output: '' };
  }

  private async removeCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    if (args.length === 0) return { exitCode: 1, output: 'Usage: arcanis-container rm [OPTIONS] CONTAINER' };
    const force = args.includes('-f');
    await this.runtime.remove(args[0], force);
    return { exitCode: 0, output: '' };
  }

  private async listCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    const containers = await this.runtime.list();
    const lines = ['CONTAINER ID\tNAME\tIMAGE\tSTATUS'];
    for (const c of containers) {
      lines.push(`${c.id.slice(0, 12)}\t${c.name}\t${c.image}\t${c.state}`);
    }
    return { exitCode: 0, output: lines.join('\n') };
  }

  private async inspectCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    if (args.length === 0) return { exitCode: 1, output: 'Usage: arcanis-container inspect CONTAINER' };
    const container = await this.runtime.inspect(args[0]);
    return { exitCode: 0, output: JSON.stringify(container, null, 2) };
  }

  private async logsCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    if (args.length === 0) return { exitCode: 1, output: 'Usage: arcanis-container logs CONTAINER' };
    const logs = await this.runtime.logs(args[0], { tail: 100 });
    const output = logs.map(l => `${l.timestamp.toISOString()} ${l.stream}: ${l.message}`).join('\n');
    return { exitCode: 0, output };
  }

  private async execCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    if (args.length < 2) return { exitCode: 1, output: 'Usage: arcanis-container exec CONTAINER COMMAND' };
    const result = await this.runtime.exec(args[0], args.slice(1));
    return { exitCode: result.exitCode, output: result.output };
  }

  private async statsCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    if (args.length === 0) return { exitCode: 1, output: 'Usage: arcanis-container stats CONTAINER' };
    const stats = await this.runtime.stats(args[0]);
    const output = [
      `CPU: ${stats.cpuStats.cpuUsage.toFixed(1)}%`,
      `Memory: ${formatBytes(stats.memoryStats.usage)} / ${formatBytes(stats.memoryStats.limit)}`,
      `Network I/O: ${formatBytes(stats.networkStats.rxBytes)} / ${formatBytes(stats.networkStats.txBytes)}`,
      `Block I/O: ${formatBytes(stats.ioStats.readBytes)} / ${formatBytes(stats.ioStats.writeBytes)}`,
    ].join('\n');
    return { exitCode: 0, output };
  }

  private async imagesCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    const images = await this.images.list();
    const lines = ['REPOSITORY\tTAG\tIMAGE ID\tSIZE'];
    for (const img of images) {
      lines.push(`${img.name}\t${img.tag}\t${img.id.slice(0, 12)}\t${formatBytes(img.size)}`);
    }
    return { exitCode: 0, output: lines.join('\n') };
  }

  private async pullCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    if (args.length === 0) return { exitCode: 1, output: 'Usage: arcanis-container pull IMAGE[:TAG]' };
    const [name, tag] = args[0].includes(':') ? args[0].split(':') : [args[0], 'latest'];
    await this.images.pull(name, tag);
    return { exitCode: 0, output: `Pull complete: ${args[0]}` };
  }

  private async buildCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    if (args.length < 1) return { exitCode: 1, output: 'Usage: arcanis-container build -t NAME:TAG DOCKERFILE_PATH' };
    const tagIdx = args.indexOf('-t');
    const nameTag = tagIdx !== -1 && args[tagIdx + 1] ? args[tagIdx + 1] : 'app:latest';
    const [name, tag] = nameTag.includes(':') ? nameTag.split(':') : [nameTag, 'latest'];
    const dockerfile = 'FROM arcanis/base:latest\nRUN echo hello\nCMD ["/bin/sh"]';
    await this.images.build(dockerfile, name, tag);
    return { exitCode: 0, output: `Build complete: ${nameTag}` };
  }

  private async networkCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    const sub = args[0];
    if (sub === 'ls' || sub === 'list' || !sub) {
      const networks = await this.networks.list();
      const lines = ['NETWORK ID\tNAME\tDRIVER'];
      for (const n of networks) {
        lines.push(`${n.id}\t${n.name}\t${n.driver}`);
      }
      return { exitCode: 0, output: lines.join('\n') };
    }
    if (sub === 'create') {
      const name = args[1];
      if (!name) return { exitCode: 1, output: 'Usage: arcanis-container network create NAME' };
      this.networks.createNetwork({ name, driver: 'bridge', subnet: `172.${Math.floor(Math.random() * 255)}.0.0/16`, gateway: `172.${Math.floor(Math.random() * 255)}.0.1` });
      return { exitCode: 0, output: name };
    }
    if (sub === 'rm' || sub === 'remove') {
      const name = args[1];
      if (!name) return { exitCode: 1, output: 'Usage: arcanis-container network rm NAME' };
      const network = await this.networks.resolve(name);
      await this.networks.removeNetwork(network.id);
      return { exitCode: 0, output: '' };
    }
    return { exitCode: 1, output: `Unknown network subcommand: ${sub}` };
  }

  private async volumeCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    const sub = args[0];
    if (sub === 'ls' || sub === 'list' || !sub) {
      const volumes = await this.storage.listVolumes();
      const lines = ['DRIVER\tVOLUME NAME'];
      for (const v of volumes) {
        lines.push(`${v.driver}\t${v.name}`);
      }
      return { exitCode: 0, output: lines.join('\n') };
    }
    if (sub === 'create') {
      const name = args[1];
      if (!name) return { exitCode: 1, output: 'Usage: arcanis-container volume create NAME' };
      this.storage.createVolume(name);
      return { exitCode: 0, output: name };
    }
    if (sub === 'rm' || sub === 'remove') {
      const name = args[1];
      if (!name) return { exitCode: 1, output: 'Usage: arcanis-container volume rm NAME' };
      await this.storage.removeVolume(name, true);
      return { exitCode: 0, output: '' };
    }
    return { exitCode: 1, output: `Unknown volume subcommand: ${sub}` };
  }

  private async serviceCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    const sub = args[0];
    if (sub === 'ls' || sub === 'list' || !sub) {
      const services = await this.orchestration.listServices();
      const lines = ['SERVICE ID\tNAME\tREPLICAS\tIMAGE'];
      for (const s of services) {
        lines.push(`${s.id.slice(0, 12)}\t${s.name}\t${s.runningReplicas}/${s.replicas}\t${s.image}`);
      }
      return { exitCode: 0, output: lines.join('\n') };
    }
    if (sub === 'create') {
      const nameIdx = args.indexOf('--name');
      const imageIdx = args.indexOf('--image');
      const name = nameIdx !== -1 ? args[nameIdx + 1] : `service-${Date.now()}`;
      const image = imageIdx !== -1 ? args[imageIdx + 1] : 'arcanis/base:latest';
      const replicaIdx = args.indexOf('--replicas');
      const replicas = replicaIdx !== -1 ? parseInt(args[replicaIdx + 1]) : 1;
      const service = await this.orchestration.createService({ name, image, replicas });
      return { exitCode: 0, output: service.id };
    }
    if (sub === 'rm' || sub === 'remove') {
      const id = args[1];
      if (!id) return { exitCode: 1, output: 'Usage: arcanis-container service rm SERVICE' };
      await this.orchestration.removeService(id, true);
      return { exitCode: 0, output: '' };
    }
    return { exitCode: 1, output: `Unknown service subcommand: ${sub}` };
  }

  private async securityCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    const sub = args[0];
    if (sub === 'report') {
      const report = await this.security.generateSecurityReport();
      const output = [
        `Total Events: ${report.totalEvents}`,
        `Policy Violations: ${report.policyViolations}`,
        `Events by Type: ${JSON.stringify(report.eventsByType)}`,
        `Events by Severity: ${JSON.stringify(report.eventsBySeverity)}`,
      ].join('\n');
      return { exitCode: 0, output };
    }
    if (sub === 'policies') {
      const policies = await this.security.listPolicies();
      const lines = ['ID\tNAME\tENABLED'];
      for (const p of policies) {
        lines.push(`${p.id}\t${p.name}\t${p.enabled}`);
      }
      return { exitCode: 0, output: lines.join('\n') };
    }
    return { exitCode: 1, output: `Unknown security subcommand: ${sub}` };
  }

  private async systemCommand(args: string[]): Promise<{ exitCode: number; output: string }> {
    const sub = args[0];
    if (sub === 'info' || !sub) {
      const usage = await this.resources.getResourceUsage();
      const output = [
        'ArcanisContainer System Info',
        '===========================',
        `Containers: ${this.runtime.getContainerCount()} (${this.runtime.getRunningCount()} running)`,
        `Images: ${this.images.getImageCount()}`,
        `Networks: ${this.networks.getNetworkCount()}`,
        `Volumes: ${this.storage.getVolumeCount()}`,
        `Services: ${this.orchestration.getServiceCount()}`,
        '',
        'Resource Usage:',
        `  CPU: ${usage.allocated.cpu.toFixed(1)} / ${usage.total.cpu} cores (${usage.utilization.cpu.toFixed(1)}%)`,
        `  Memory: ${formatBytes(usage.allocated.memory)} / ${formatBytes(usage.total.memory)} (${usage.utilization.memory.toFixed(1)}%)`,
      ].join('\n');
      return { exitCode: 0, output };
    }
    if (sub === 'df') {
      const usage = await this.resources.getResourceUsage();
      return { exitCode: 0, output: `Total: ${formatBytes(usage.total.storage)}\nUsed: ${formatBytes(usage.total.storage - usage.available.memory)}\nAvailable: ${formatBytes(usage.available.memory)}` };
    }
    if (sub === 'prune') {
      const volResult = await this.storage.pruneVolumes();
      return { exitCode: 0, output: `Pruned ${volResult.count} volumes (${formatBytes(volResult.reclaimedBytes)} reclaimed)` };
    }
    return { exitCode: 1, output: `Unknown system subcommand: ${sub}` };
  }

  private showHelp(): { exitCode: number; output: string } {
    return {
      exitCode: 0,
      output: `ArcanisContainer - AI-Native Container Runtime

Usage: arcanis-container [OPTIONS] COMMAND [ARGS...]

Commands:
  run         Run a container
  create      Create a container
  start       Start a container
  stop        Stop a container
  restart     Restart a container
  rm          Remove a container
  ps          List containers
  inspect     Inspect a container
  logs        Fetch container logs
  exec        Run command in container
  stats       Display container statistics

  images      List images
  pull        Pull an image
  build       Build an image from Dockerfile

  network     Manage networks
  volume      Manage volumes
  service     Manage services

  security    Security management
  system      System information

  help        Show this help
  version     Show version`,
    };
  }

  private versionCommand(): { exitCode: number; output: string } {
    return { exitCode: 0, output: 'ArcanisContainer v0.1.0' };
  }
}

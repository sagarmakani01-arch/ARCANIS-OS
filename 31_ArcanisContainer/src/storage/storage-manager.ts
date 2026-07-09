// ArcanisContainer - Storage Manager

import { EventEmitter } from 'events';
import { Volume, MountConfig, MountInfo } from '../types.js';
import { generateVolumeId } from '../utils.js';

export interface StorageManagerOptions {
  defaultDriver?: string;
  dataRoot?: string;
}

export class StorageManager extends EventEmitter {
  private volumes: Map<string, Volume> = new Map();
  private bindMounts: Map<string, string> = new Map();
  private tmpfsMounts: Map<string, { sizeBytes: number }> = new Map();
  private options: Required<StorageManagerOptions>;

  constructor(options: StorageManagerOptions = {}) {
    super();
    this.options = {
      defaultDriver: options.defaultDriver || 'local',
      dataRoot: options.dataRoot || '/var/lib/arcanis/volumes',
    };
    this.seedDefaultVolumes();
  }

  private seedDefaultVolumes(): void {
    const defaults = [
      { name: 'arcanis-data', path: '/var/lib/arcanis/data' },
      { name: 'arcanis-logs', path: '/var/lib/arcanis/logs' },
      { name: 'arcanis-config', path: '/var/lib/arcanis/config' },
    ];

    for (const vol of defaults) {
      this.volumes.set(vol.name, {
        name: vol.name,
        driver: this.options.defaultDriver,
        mountpoint: vol.path,
        scope: 'local',
        created: new Date(),
      });
    }
  }

  createVolume(name: string, options?: { driver?: string; labels?: Record<string, string>; opts?: Record<string, string> }): Volume {
    if (this.volumes.has(name)) {
      throw new Error(`Volume ${name} already exists`);
    }

    const volume: Volume = {
      name,
      driver: options?.driver || this.options.defaultDriver,
      mountpoint: `${this.options.dataRoot}/${name}`,
      labels: options?.labels,
      options: options?.opts,
      scope: 'local',
      created: new Date(),
    };

    this.volumes.set(name, volume);
    this.emit('volume:create', volume);
    return volume;
  }

  async removeVolume(name: string, force: boolean = false): Promise<void> {
    const volume = this.volumes.get(name);
    if (!volume) throw new Error(`Volume ${name} not found`);

    if (!force && this.isVolumeInUse(name)) {
      throw new Error(`Volume ${name} is in use`);
    }

    this.volumes.delete(name);
    this.emit('volume:remove', volume);
  }

  private isVolumeInUse(name: string): boolean {
    return this.bindMounts.has(name);
  }

  async mountVolume(config: MountConfig): Promise<MountInfo> {
    const mountInfo: MountInfo = {
      source: config.source,
      target: config.target,
      type: config.type,
      readonly: config.readonly || false,
    };

    if (config.type === 'volume') {
      const volume = this.volumes.get(config.source);
      if (!volume) throw new Error(`Volume ${config.source} not found`);
      this.bindMounts.set(config.source, config.target);
    } else if (config.type === 'bind') {
      this.bindMounts.set(config.source, config.target);
    } else if (config.type === 'tmpfs') {
      this.tmpfsMounts.set(config.target, {
        sizeBytes: config.tmpfsSizeBytes || 100 * 1024 * 1024,
      });
    }

    this.emit('mount', mountInfo);
    return mountInfo;
  }

  async unmountVolume(source: string, target: string): Promise<void> {
    this.bindMounts.delete(source);
    this.tmpfsMounts.delete(target);
    this.emit('unmount', { source, target });
  }

  async inspectVolume(name: string): Promise<Volume> {
    const volume = this.volumes.get(name);
    if (!volume) throw new Error(`Volume ${name} not found`);
    return { ...volume };
  }

  async listVolumes(filters?: { name?: string; driver?: string }): Promise<Volume[]> {
    let result = Array.from(this.volumes.values());

    if (filters) {
      if (filters.name) {
        result = result.filter(v => v.name.includes(filters.name!));
      }
      if (filters.driver) {
        result = result.filter(v => v.driver === filters.driver);
      }
    }

    return result;
  }

  async volumeExists(name: string): Promise<boolean> {
    return this.volumes.has(name);
  }

  async getVolumeMountpoint(name: string): Promise<string> {
    const volume = this.volumes.get(name);
    if (!volume) throw new Error(`Volume ${name} not found`);
    return volume.mountpoint;
  }

  async copyVolume(source: string, destination: string): Promise<Volume> {
    const srcVolume = this.volumes.get(source);
    if (!srcVolume) throw new Error(`Source volume ${source} not found`);

    const newVolume = this.createVolume(destination, {
      driver: srcVolume.driver,
      labels: srcVolume.labels ? { ...srcVolume.labels } : undefined,
    });

    this.emit('volume:copy', { source, destination });
    return newVolume;
  }

  async pruneVolumes(): Promise<{ count: number; reclaimedBytes: number }> {
    let count = 0;
    let reclaimedBytes = 0;

    for (const [name, volume] of this.volumes) {
      if (!this.isVolumeInUse(name)) {
        reclaimedBytes += 1024 * 1024;
        this.volumes.delete(name);
        count++;
      }
    }

    this.emit('volume:prune', { count, reclaimedBytes });
    return { count, reclaimedBytes };
  }

  getVolumeCount(): number {
    return this.volumes.size;
  }

  getActiveMounts(): Map<string, string> {
    return new Map(this.bindMounts);
  }

  getTmpfsMounts(): Map<string, { sizeBytes: number }> {
    return new Map(this.tmpfsMounts);
  }
}

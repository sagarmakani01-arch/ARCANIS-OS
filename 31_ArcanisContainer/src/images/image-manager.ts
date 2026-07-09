// ArcanisContainer - Image Manager

import { EventEmitter } from 'events';
import { Image, ImageLayer, ImageConfig, ImageStatus, DockerfileInstruction } from '../types.js';
import { generateImageId, sha256 } from '../utils.js';

export interface ImageManagerOptions {
  registryUrl?: string;
  cacheDir?: string;
  maxImageSize?: number;
}

export class ImageManager extends EventEmitter {
  private images: Map<string, Image> = new Map();
  private tagIndex: Map<string, string> = new Map();
  private options: Required<ImageManagerOptions>;

  constructor(options: ImageManagerOptions = {}) {
    super();
    this.options = {
      registryUrl: options.registryUrl || 'https://registry.arcanis.dev',
      cacheDir: options.cacheDir || '/var/lib/arcanis/images',
      maxImageSize: options.maxImageSize || 10 * 1024 * 1024 * 1024,
    };
    this.seedBaseImages();
  }

  private seedBaseImages(): void {
    const baseImages: { name: string; tag: string; size: number; layers: number }[] = [
      { name: 'arcanis/base', tag: 'latest', size: 50 * 1024 * 1024, layers: 3 },
      { name: 'arcanis/base', tag: 'alpine', size: 5 * 1024 * 1024, layers: 2 },
      { name: 'arcanis/node', tag: '18', size: 200 * 1024 * 1024, layers: 5 },
      { name: 'arcanis/python', tag: '3.11', size: 180 * 1024 * 1024, layers: 4 },
      { name: 'arcanis/java', tag: '21', size: 300 * 1024 * 1024, layers: 6 },
      { name: 'arcanis/go', tag: '1.21', size: 150 * 1024 * 1024, layers: 4 },
      { name: 'arcanis/rust', tag: 'latest', size: 400 * 1024 * 1024, layers: 7 },
      { name: 'nginx', tag: 'alpine', size: 25 * 1024 * 1024, layers: 3 },
      { name: 'redis', tag: '7', size: 30 * 1024 * 1024, layers: 2 },
      { name: 'postgres', tag: '16', size: 120 * 1024 * 1024, layers: 4 },
    ];

    for (const base of baseImages) {
      const id = generateImageId();
      const layers: ImageLayer[] = Array.from({ length: base.layers }, (_, i) => ({
        id: sha256(`${id}-layer-${i}`),
        size: Math.floor(base.size / base.layers),
        command: i === base.layers - 1 ? '/bin/sh' : undefined,
        created: new Date(),
      }));

      const image: Image = {
        id,
        name: base.name,
        tag: base.tag,
        size: base.size,
        created: new Date(),
        status: 'ready',
        layers,
        config: {
          cmd: ['/bin/sh'],
          env: ['PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'],
          workingDir: '/',
        },
      };

      this.images.set(id, image);
      this.tagIndex.set(`${base.name}:${base.tag}`, id);
    }
  }

  async pull(imageName: string, tag: string = 'latest'): Promise<Image> {
    const fullName = `${imageName}:${tag}`;
    const existingId = this.tagIndex.get(fullName);
    if (existingId) {
      const existing = this.images.get(existingId);
      if (existing && existing.status === 'ready') return existing;
    }

    const id = generateImageId();
    const layers: ImageLayer[] = [];

    const image: Image = {
      id,
      name: imageName,
      tag,
      size: 0,
      created: new Date(),
      status: 'pulling',
      layers,
      config: {
        cmd: ['/bin/sh'],
        env: ['PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'],
        workingDir: '/',
      },
    };

    this.images.set(id, image);
    this.emit('image:pull:start', image);

    for (let i = 0; i < 3; i++) {
      const layerId = sha256(`${id}-layer-${i}`);
      const layerSize = Math.floor(50 * 1024 * 1024 / 3);
      layers.push({
        id: layerId,
        size: layerSize,
        command: i === 2 ? '/bin/sh' : undefined,
        created: new Date(),
      });
      image.size += layerSize;
      this.emit('image:layer', { imageId: id, layerIndex: i, total: 3 });
    }

    image.status = 'ready';
    this.tagIndex.set(fullName, id);
    this.emit('image:pull:complete', image);

    return image;
  }

  async build(dockerfile: string, name: string, tag: string = 'latest'): Promise<Image> {
    const instructions = this.parseDockerfile(dockerfile);
    const id = generateImageId();
    const layers: ImageLayer[] = [];

    const image: Image = {
      id,
      name,
      tag,
      size: 0,
      created: new Date(),
      status: 'building',
      layers,
      config: {},
    };

    this.images.set(id, image);
    this.emit('image:build:start', image);

    let currentEnv: string[] = [];
    let currentCmd: string[] | undefined;
    let currentEntrypoint: string[] | undefined;
    let currentWorkDir = '/';
    let currentLabels: Record<string, string> = {};

    for (let i = 0; i < instructions.length; i++) {
      const inst = instructions[i];

      switch (inst.command.toUpperCase()) {
        case 'FROM':
          break;
        case 'ENV':
          if (inst.args.length >= 2) {
            const key = inst.args[0];
            const value = inst.args.slice(1).join(' ');
            currentEnv.push(`${key}=${value}`);
          }
          break;
        case 'RUN':
          layers.push({
            id: sha256(`${id}-run-${i}`),
            size: Math.floor(Math.random() * 10 * 1024 * 1024) + 1024 * 1024,
            command: inst.args.join(' '),
            created: new Date(),
          });
          break;
        case 'CMD':
          currentCmd = inst.args;
          break;
        case 'ENTRYPOINT':
          currentEntrypoint = inst.args;
          break;
        case 'WORKDIR':
          currentWorkDir = inst.args[0] || '/';
          break;
        case 'LABEL':
          for (let j = 0; j < inst.args.length; j += 2) {
            if (j + 1 < inst.args.length) {
              currentLabels[inst.args[j]] = inst.args[j + 1];
            }
          }
          break;
        case 'EXPOSE':
          break;
        case 'VOLUME':
          break;
        case 'COPY':
        case 'ADD':
          layers.push({
            id: sha256(`${id}-copy-${i}`),
            size: Math.floor(Math.random() * 5 * 1024 * 1024) + 512 * 1024,
            created: new Date(),
          });
          break;
      }

      this.emit('image:build:step', { imageId: id, step: i + 1, total: instructions.length });
    }

    image.size = layers.reduce((sum, l) => sum + l.size, 0);
    image.config = {
      env: currentEnv.length > 0 ? currentEnv : undefined,
      cmd: currentCmd,
      entrypoint: currentEntrypoint,
      workingDir: currentWorkDir,
      labels: Object.keys(currentLabels).length > 0 ? currentLabels : undefined,
    };
    image.status = 'ready';
    this.tagIndex.set(`${name}:${tag}`, id);

    this.emit('image:build:complete', image);
    return image;
  }

  private parseDockerfile(dockerfile: string): DockerfileInstruction[] {
    const instructions: DockerfileInstruction[] = [];
    const lines = dockerfile.split('\n').filter(l => l.trim() && !l.trim().startsWith('#'));

    for (const line of lines) {
      const parts = line.trim().split(/\s+/);
      const command = parts[0];
      const args = parts.slice(1);
      instructions.push({ command, args, flags: {} });
    }

    return instructions;
  }

  async inspect(imageId: string): Promise<Image> {
    const image = this.images.get(imageId);
    if (!image) throw new Error(`Image ${imageId} not found`);
    return { ...image };
  }

  async list(filters?: { name?: string; tag?: string }): Promise<Image[]> {
    let result = Array.from(this.images.values());

    if (filters) {
      if (filters.name) {
        result = result.filter(i => i.name.includes(filters.name!));
      }
      if (filters.tag) {
        result = result.filter(i => i.tag === filters.tag);
      }
    }

    return result;
  }

  async remove(imageId: string, force: boolean = false): Promise<void> {
    const image = this.images.get(imageId);
    if (!image) throw new Error(`Image ${imageId} not found`);

    if (!force) {
      const fullName = `${image.name}:${image.tag}`;
      this.tagIndex.delete(fullName);
    }

    this.images.delete(imageId);
    this.emit('image:remove', image);
  }

  async tag(imageId: string, name: string, tag: string): Promise<void> {
    const image = this.images.get(imageId);
    if (!image) throw new Error(`Image ${imageId} not found`);

    const fullName = `${name}:${tag}`;
    this.tagIndex.set(fullName, imageId);
    this.emit('image:tag', { imageId, name, tag });
  }

  async exists(imageName: string, tag: string = 'latest'): Promise<boolean> {
    return this.tagIndex.has(`${imageName}:${tag}`);
  }

  async resolve(imageRef: string): Promise<Image> {
    const [name, tag] = imageRef.includes(':') ? imageRef.split(':') : [imageRef, 'latest'];
    const id = this.tagIndex.get(`${name}:${tag}`);
    if (!id) throw new Error(`Image ${imageRef} not found`);
    return this.inspect(id);
  }

  getImageCount(): number {
    return this.images.size;
  }

  getTotalSize(): number {
    return Array.from(this.images.values()).reduce((sum, img) => sum + img.size, 0);
  }
}

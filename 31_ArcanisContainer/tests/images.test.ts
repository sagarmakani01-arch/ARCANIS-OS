import { describe, it, expect, beforeEach } from 'vitest';
import { ImageManager } from '../src/images/image-manager.js';

describe('ImageManager', () => {
  let images: ImageManager;

  beforeEach(() => {
    images = new ImageManager();
  });

  describe('constructor', () => {
    it('should seed base images', async () => {
      const list = await images.list();
      expect(list.length).toBeGreaterThan(0);
    });

    it('should have arcanis/base image', async () => {
      const exists = await images.exists('arcanis/base', 'latest');
      expect(exists).toBe(true);
    });
  });

  describe('pull', () => {
    it('should pull a new image', async () => {
      const image = await images.pull('custom/app', 'v1');
      expect(image).toBeDefined();
      expect(image.name).toBe('custom/app');
      expect(image.tag).toBe('v1');
      expect(image.status).toBe('ready');
      expect(image.layers.length).toBeGreaterThan(0);
    });

    it('should return existing image if already pulled', async () => {
      const first = await images.pull('cached/img', 'latest');
      const second = await images.pull('cached/img', 'latest');
      expect(first.id).toBe(second.id);
    });

    it('should generate layers with sizes', async () => {
      const image = await images.pull('test/img', 'latest');
      expect(image.layers.length).toBe(3);
      expect(image.size).toBeGreaterThan(0);
    });

    it('should emit pull events', async () => {
      const events: string[] = [];
      images.on('image:pull:start', () => events.push('start'));
      images.on('image:pull:complete', () => events.push('complete'));
      await images.pull('events/img', 'latest');
      expect(events).toContain('start');
      expect(events).toContain('complete');
    });
  });

  describe('build', () => {
    it('should build image from dockerfile', async () => {
      const dockerfile = `
FROM arcanis/base:latest
ENV NODE_ENV=production
RUN npm install
RUN npm run build
CMD ["node", "server.js"]
WORKDIR /app
LABEL version=1.0
`;
      const image = await images.build(dockerfile, 'myapp', 'latest');
      expect(image).toBeDefined();
      expect(image.name).toBe('myapp');
      expect(image.status).toBe('ready');
      expect(image.config.cmd).toEqual(['node', 'server.js']);
      expect(image.config.workingDir).toBe('/app');
    });

    it('should parse ENV instructions', async () => {
      const dockerfile = `
FROM base:latest
ENV KEY1=value1
ENV KEY2=value2
`;
      const image = await images.build(dockerfile, 'env-test', 'latest');
      expect(image.config.env).toBeDefined();
      expect(image.config.env!.length).toBe(2);
    });

    it('should parse LABEL instructions', async () => {
      const dockerfile = `
FROM base:latest
LABEL maintainer=test
LABEL version=1.0
`;
      const image = await images.build(dockerfile, 'label-test', 'latest');
      expect(image.config.labels).toBeDefined();
      expect(image.config.labels!['maintainer']).toBe('test');
    });

    it('should emit build events', async () => {
      const events: string[] = [];
      images.on('image:build:start', () => events.push('start'));
      images.on('image:build:step', () => events.push('step'));
      images.on('image:build:complete', () => events.push('complete'));
      const dockerfile = 'FROM base:latest\nRUN echo hi';
      await images.build(dockerfile, 'event-img', 'latest');
      expect(events).toContain('start');
      expect(events.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('inspect', () => {
    it('should return image details', async () => {
      const image = await images.pull('inspect/img', 'latest');
      const details = await images.inspect(image.id);
      expect(details.id).toBe(image.id);
      expect(details.name).toBe('inspect/img');
    });

    it('should throw for non-existent image', async () => {
      await expect(images.inspect('nonexistent')).rejects.toThrow('not found');
    });
  });

  describe('list', () => {
    it('should list all images', async () => {
      await images.pull('list/img1', 'latest');
      await images.pull('list/img2', 'latest');
      const list = await images.list();
      expect(list.length).toBeGreaterThanOrEqual(12);
    });

    it('should filter by name', async () => {
      await images.pull('filter/myapp', 'v1');
      await images.pull('filter/other', 'v1');
      const list = await images.list({ name: 'filter/myapp' });
      expect(list.length).toBe(1);
    });

    it('should filter by tag', async () => {
      await images.pull('tag/img', 'v1');
      await images.pull('tag/img', 'v2');
      const v1 = await images.list({ tag: 'v1' });
      const v2 = await images.list({ tag: 'v2' });
      expect(v1.some(i => i.name === 'tag/img')).toBe(true);
      expect(v2.some(i => i.name === 'tag/img')).toBe(true);
    });
  });

  describe('remove', () => {
    it('should remove an image', async () => {
      const image = await images.pull('remove/img', 'latest');
      await images.remove(image.id);
      const list = await images.list();
      expect(list.find(i => i.id === image.id)).toBeUndefined();
    });
  });

  describe('tag', () => {
    it('should tag an image with new name/tag', async () => {
      const image = await images.pull('tag/img', 'latest');
      await images.tag(image.id, 'tag/img', 'v2');
      const exists = await images.exists('tag/img', 'v2');
      expect(exists).toBe(true);
    });
  });

  describe('resolve', () => {
    it('should resolve image reference', async () => {
      const image = await images.pull('resolve/img', 'latest');
      const resolved = await images.resolve('resolve/img:latest');
      expect(resolved.id).toBe(image.id);
    });

    it('should default to latest tag', async () => {
      const image = await images.pull('resolve/img2', 'latest');
      const resolved = await images.resolve('resolve/img2');
      expect(resolved.id).toBe(image.id);
    });

    it('should throw for unknown image', async () => {
      await expect(images.resolve('unknown/img:latest')).rejects.toThrow('not found');
    });
  });

  describe('counts', () => {
    it('should track image count and total size', async () => {
      const count = images.getImageCount();
      expect(count).toBeGreaterThan(0);
      const size = images.getTotalSize();
      expect(size).toBeGreaterThan(0);
    });
  });
});

import { describe, it, expect, beforeEach } from 'vitest';
import { ContainerRuntime } from '../src/runtime/container-runtime.js';

describe('ContainerRuntime', () => {
  let runtime: ContainerRuntime;

  beforeEach(() => {
    runtime = new ContainerRuntime({ maxContainers: 10 });
  });

  describe('create', () => {
    it('should create a container', async () => {
      const container = await runtime.create({ name: 'test', image: 'alpine:latest' });
      expect(container).toBeDefined();
      expect(container.id).toBeDefined();
      expect(container.name).toBe('test');
      expect(container.image).toBe('alpine:latest');
      expect(container.state).toBe('created');
    });

    it('should generate unique IDs', async () => {
      const c1 = await runtime.create({ name: 'c1', image: 'img' });
      const c2 = await runtime.create({ name: 'c2', image: 'img' });
      expect(c1.id).not.toBe(c2.id);
    });

    it('should reject duplicate IDs', async () => {
      await runtime.create({ id: 'dup-123', name: 'c1', image: 'img' });
      await expect(runtime.create({ id: 'dup-123', name: 'c2', image: 'img' })).rejects.toThrow('already exists');
    });

    it('should enforce max container limit', async () => {
      for (let i = 0; i < 10; i++) {
        await runtime.create({ name: `c${i}`, image: 'img' });
      }
      await expect(runtime.create({ name: 'c10', image: 'img' })).rejects.toThrow('Maximum container limit');
    });

    it('should store container config', async () => {
      const container = await runtime.create({
        name: 'configured',
        image: 'node:18',
        env: { NODE_ENV: 'production' },
        ports: [{ hostPort: 8080, containerPort: 80, protocol: 'tcp' }],
      });
      expect(container.config.env).toEqual({ NODE_ENV: 'production' });
      expect(container.config.ports).toHaveLength(1);
    });

    it('should emit container:create event', async () => {
      let emitted = false;
      runtime.on('container:create', () => { emitted = true; });
      await runtime.create({ name: 'ev', image: 'img' });
      expect(emitted).toBe(true);
    });
  });

  describe('start', () => {
    it('should start a created container', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.start(container.id);
      const updated = await runtime.inspect(container.id);
      expect(updated.state).toBe('running');
      expect(updated.started).toBeDefined();
      expect(updated.pid).toBeGreaterThan(0);
    });

    it('should reject starting non-existent container', async () => {
      await expect(runtime.start('nonexistent')).rejects.toThrow('not found');
    });

    it('should reject starting running container', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.start(container.id);
      await expect(runtime.start(container.id)).rejects.toThrow('Cannot start');
    });

    it('should emit container:start event', async () => {
      let emitted = false;
      runtime.on('container:start', () => { emitted = true; });
      const container = await runtime.create({ name: 'ev', image: 'img' });
      await runtime.start(container.id);
      expect(emitted).toBe(true);
    });
  });

  describe('stop', () => {
    it('should stop a running container', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.start(container.id);
      await runtime.stop(container.id);
      const updated = await runtime.inspect(container.id);
      expect(updated.state).toBe('stopped');
      expect(updated.stopped).toBeDefined();
      expect(updated.exitCode).toBe(0);
    });

    it('should reject stopping non-existent container', async () => {
      await expect(runtime.stop('nonexistent')).rejects.toThrow('not found');
    });

    it('should reject stopping created container', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await expect(runtime.stop(container.id)).rejects.toThrow('Cannot stop');
    });

    it('should accept custom timeout', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.start(container.id);
      await runtime.stop(container.id, 1);
      const updated = await runtime.inspect(container.id);
      expect(updated.state).toBe('stopped');
    });
  });

  describe('restart', () => {
    it('should restart a running container', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.start(container.id);
      await runtime.restart(container.id);
      const updated = await runtime.inspect(container.id);
      expect(updated.state).toBe('running');
    });
  });

  describe('pause/unpause', () => {
    it('should pause a running container', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.start(container.id);
      await runtime.pause(container.id);
      const updated = await runtime.inspect(container.id);
      expect(updated.state).toBe('paused');
    });

    it('should unpause a paused container', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.start(container.id);
      await runtime.pause(container.id);
      await runtime.unpause(container.id);
      const updated = await runtime.inspect(container.id);
      expect(updated.state).toBe('running');
    });

    it('should reject pausing non-running container', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await expect(runtime.pause(container.id)).rejects.toThrow('Cannot pause');
    });
  });

  describe('remove', () => {
    it('should remove a stopped container', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.remove(container.id);
      expect(runtime.getContainerCount()).toBe(0);
    });

    it('should force remove running container', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.start(container.id);
      await runtime.remove(container.id, true);
      expect(runtime.getContainerCount()).toBe(0);
    });

    it('should reject removing running container without force', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.start(container.id);
      await expect(runtime.remove(container.id)).rejects.toThrow('running');
    });
  });

  describe('inspect', () => {
    it('should return container details', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      const details = await runtime.inspect(container.id);
      expect(details.id).toBe(container.id);
      expect(details.name).toBe('test');
      expect(details.created).toBeInstanceOf(Date);
    });

    it('should reject non-existent container', async () => {
      await expect(runtime.inspect('nonexistent')).rejects.toThrow('not found');
    });
  });

  describe('list', () => {
    it('should list all containers', async () => {
      await runtime.create({ name: 'c1', image: 'img1' });
      await runtime.create({ name: 'c2', image: 'img2' });
      const list = await runtime.list();
      expect(list).toHaveLength(2);
    });

    it('should filter by name', async () => {
      await runtime.create({ name: 'web-server', image: 'nginx' });
      await runtime.create({ name: 'db-server', image: 'postgres' });
      const list = await runtime.list({ name: 'web' });
      expect(list).toHaveLength(1);
      expect(list[0].name).toBe('web-server');
    });

    it('should filter by state', async () => {
      const c1 = await runtime.create({ name: 'c1', image: 'img' });
      await runtime.start(c1.id);
      await runtime.create({ name: 'c2', image: 'img' });
      const running = await runtime.list({ state: 'running' });
      expect(running).toHaveLength(1);
      const created = await runtime.list({ state: 'created' });
      expect(created).toHaveLength(1);
    });
  });

  describe('logs', () => {
    it('should return container logs', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.start(container.id);
      await runtime.stop(container.id);
      const logs = await runtime.logs(container.id);
      expect(logs.length).toBeGreaterThan(0);
    });

    it('should support tail option', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.start(container.id);
      const logs = await runtime.logs(container.id, { tail: 1 });
      expect(logs).toHaveLength(1);
    });
  });

  describe('exec', () => {
    it('should execute command in running container', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.start(container.id);
      const result = await runtime.exec(container.id, ['ls', '-la']);
      expect(result.exitCode).toBe(0);
      expect(result.output).toContain('Executed');
    });

    it('should reject exec on non-running container', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await expect(runtime.exec(container.id, ['ls'])).rejects.toThrow('not running');
    });
  });

  describe('stats', () => {
    it('should return container stats', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.start(container.id);
      const stats = await runtime.stats(container.id);
      expect(stats.cpuStats).toBeDefined();
      expect(stats.memoryStats).toBeDefined();
      expect(stats.networkStats).toBeDefined();
      expect(stats.ioStats).toBeDefined();
      expect(stats.timestamp).toBeInstanceOf(Date);
    });
  });

  describe('update', () => {
    it('should update stopped container config', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.update(container.id, { env: { NEW_VAR: 'value' } });
      const updated = await runtime.inspect(container.id);
      expect(updated.config.env?.NEW_VAR).toBe('value');
    });

    it('should reject updating running container', async () => {
      const container = await runtime.create({ name: 'test', image: 'img' });
      await runtime.start(container.id);
      await expect(runtime.update(container.id, { env: {} })).rejects.toThrow('running');
    });
  });

  describe('counts', () => {
    it('should track container counts', async () => {
      expect(runtime.getContainerCount()).toBe(0);
      expect(runtime.getRunningCount()).toBe(0);
      const c = await runtime.create({ name: 'test', image: 'img' });
      expect(runtime.getContainerCount()).toBe(1);
      await runtime.start(c.id);
      expect(runtime.getRunningCount()).toBe(1);
    });
  });
});

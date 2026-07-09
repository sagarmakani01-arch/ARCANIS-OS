import { describe, it, expect, beforeEach } from 'vitest';
import { ArcanisContainerCLI } from '../src/cli/cli.js';
import { ContainerRuntime } from '../src/runtime/container-runtime.js';
import { ImageManager } from '../src/images/image-manager.js';
import { NetworkManager } from '../src/networking/network-manager.js';
import { StorageManager } from '../src/storage/storage-manager.js';
import { OrchestrationManager } from '../src/orchestration/orchestration-manager.js';
import { SecurityManager } from '../src/security/security-manager.js';
import { ResourceManager } from '../src/resources/resource-manager.js';

describe('ArcanisContainerCLI', () => {
  let cli: ArcanisContainerCLI;
  let runtime: ContainerRuntime;

  beforeEach(() => {
    runtime = new ContainerRuntime();
    cli = new ArcanisContainerCLI({
      runtime,
      images: new ImageManager(),
      networks: new NetworkManager(),
      storage: new StorageManager(),
      orchestration: new OrchestrationManager(runtime),
      security: new SecurityManager(),
      resources: new ResourceManager(),
    });
  });

  describe('help', () => {
    it('should show help', async () => {
      const result = await cli.execute(['help']);
      expect(result.exitCode).toBe(0);
      expect(result.output).toContain('ArcanisContainer');
      expect(result.output).toContain('run');
      expect(result.output).toContain('images');
      expect(result.output).toContain('network');
    });
  });

  describe('version', () => {
    it('should show version', async () => {
      const result = await cli.execute(['version']);
      expect(result.exitCode).toBe(0);
      expect(result.output).toContain('v0.1.0');
    });
  });

  describe('run', () => {
    it('should run a container', async () => {
      const result = await cli.execute(['run', '--name', 'test', 'alpine:latest']);
      expect(result.exitCode).toBe(0);
      expect(result.output).toBeDefined();
    });

    it('should show usage without args', async () => {
      const result = await cli.execute(['run']);
      expect(result.exitCode).toBe(1);
      expect(result.output).toContain('Usage');
    });
  });

  describe('create', () => {
    it('should create a container', async () => {
      const result = await cli.execute(['create', '--name', 'test', 'alpine:latest']);
      expect(result.exitCode).toBe(0);
    });
  });

  describe('start/stop', () => {
    it('should start and stop a container', async () => {
      const createResult = await cli.execute(['create', '--name', 'test', 'alpine:latest']);
      const containerId = createResult.output;

      const startResult = await cli.execute(['start', containerId]);
      expect(startResult.exitCode).toBe(0);

      const stopResult = await cli.execute(['stop', containerId]);
      expect(stopResult.exitCode).toBe(0);
    });
  });

  describe('ps', () => {
    it('should list containers', async () => {
      await cli.execute(['create', '--name', 'c1', 'img']);
      const result = await cli.execute(['ps']);
      expect(result.exitCode).toBe(0);
      expect(result.output).toContain('CONTAINER ID');
    });
  });

  describe('inspect', () => {
    it('should inspect a container', async () => {
      const createResult = await cli.execute(['create', '--name', 'test', 'img']);
      const result = await cli.execute(['inspect', createResult.output]);
      expect(result.exitCode).toBe(0);
      expect(result.output).toContain('test');
    });
  });

  describe('logs', () => {
    it('should fetch logs', async () => {
      const createResult = await cli.execute(['create', '--name', 'test', 'img']);
      await cli.execute(['start', createResult.output]);
      const result = await cli.execute(['logs', createResult.output]);
      expect(result.exitCode).toBe(0);
    });
  });

  describe('exec', () => {
    it('should exec command in container', async () => {
      const createResult = await cli.execute(['create', '--name', 'test', 'img']);
      await cli.execute(['start', createResult.output]);
      const result = await cli.execute(['exec', createResult.output, 'ls']);
      expect(result.exitCode).toBe(0);
    });
  });

  describe('stats', () => {
    it('should show stats', async () => {
      const createResult = await cli.execute(['create', '--name', 'test', 'img']);
      await cli.execute(['start', createResult.output]);
      const result = await cli.execute(['stats', createResult.output]);
      expect(result.exitCode).toBe(0);
      expect(result.output).toContain('CPU');
    });
  });

  describe('images', () => {
    it('should list images', async () => {
      const result = await cli.execute(['images']);
      expect(result.exitCode).toBe(0);
      expect(result.output).toContain('REPOSITORY');
    });
  });

  describe('pull', () => {
    it('should pull an image', async () => {
      const result = await cli.execute(['pull', 'custom/app:v1']);
      expect(result.exitCode).toBe(0);
      expect(result.output).toContain('Pull complete');
    });
  });

  describe('network', () => {
    it('should list networks', async () => {
      const result = await cli.execute(['network', 'ls']);
      expect(result.exitCode).toBe(0);
      expect(result.output).toContain('NETWORK ID');
    });

    it('should create network', async () => {
      const result = await cli.execute(['network', 'create', 'test-net']);
      expect(result.exitCode).toBe(0);
    });
  });

  describe('volume', () => {
    it('should list volumes', async () => {
      const result = await cli.execute(['volume', 'ls']);
      expect(result.exitCode).toBe(0);
      expect(result.output).toContain('DRIVER');
    });

    it('should create volume', async () => {
      const result = await cli.execute(['volume', 'create', 'test-vol']);
      expect(result.exitCode).toBe(0);
    });
  });

  describe('service', () => {
    it('should list services', async () => {
      const result = await cli.execute(['service', 'ls']);
      expect(result.exitCode).toBe(0);
      expect(result.output).toContain('SERVICE ID');
    });
  });

  describe('security', () => {
    it('should show security report', async () => {
      const result = await cli.execute(['security', 'report']);
      expect(result.exitCode).toBe(0);
      expect(result.output).toContain('Total Events');
    });

    it('should list policies', async () => {
      const result = await cli.execute(['security', 'policies']);
      expect(result.exitCode).toBe(0);
      expect(result.output).toContain('default');
    });
  });

  describe('system', () => {
    it('should show system info', async () => {
      const result = await cli.execute(['system', 'info']);
      expect(result.exitCode).toBe(0);
      expect(result.output).toContain('ArcanisContainer System Info');
    });
  });

  describe('unknown command', () => {
    it('should return error for unknown command', async () => {
      const result = await cli.execute(['nonexistent']);
      expect(result.exitCode).toBe(1);
      expect(result.output).toContain('Unknown command');
    });
  });
});

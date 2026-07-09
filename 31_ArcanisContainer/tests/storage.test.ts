import { describe, it, expect, beforeEach } from 'vitest';
import { StorageManager } from '../src/storage/storage-manager.js';

describe('StorageManager', () => {
  let storage: StorageManager;

  beforeEach(() => {
    storage = new StorageManager();
  });

  describe('constructor', () => {
    it('should create default volumes', async () => {
      const list = await storage.listVolumes();
      expect(list.length).toBeGreaterThanOrEqual(3);
    });

    it('should have arcanis-data volume', async () => {
      const exists = await storage.volumeExists('arcanis-data');
      expect(exists).toBe(true);
    });
  });

  describe('createVolume', () => {
    it('should create a new volume', () => {
      const vol = storage.createVolume('my-vol');
      expect(vol).toBeDefined();
      expect(vol.name).toBe('my-vol');
      expect(vol.driver).toBe('local');
      expect(vol.scope).toBe('local');
    });

    it('should reject duplicate volume names', () => {
      storage.createVolume('dup-vol');
      expect(() => storage.createVolume('dup-vol')).toThrow('already exists');
    });

    it('should store labels and options', () => {
      const vol = storage.createVolume('labeled', { labels: { env: 'prod' }, opts: { type: 'nfs' } });
      expect(vol.labels).toEqual({ env: 'prod' });
      expect(vol.options).toEqual({ type: 'nfs' });
    });
  });

  describe('removeVolume', () => {
    it('should remove a volume', async () => {
      storage.createVolume('removable');
      await storage.removeVolume('removable');
      const exists = await storage.volumeExists('removable');
      expect(exists).toBe(false);
    });

    it('should reject removing non-existent volume', async () => {
      await expect(storage.removeVolume('nonexistent')).rejects.toThrow('not found');
    });
  });

  describe('mountVolume', () => {
    it('should mount a volume', async () => {
      const mount = await storage.mountVolume({
        source: 'arcanis-data',
        target: '/data',
        type: 'volume',
      });
      expect(mount.source).toBe('arcanis-data');
      expect(mount.target).toBe('/data');
      expect(mount.type).toBe('volume');
    });

    it('should mount bind mount', async () => {
      const mount = await storage.mountVolume({
        source: '/host/path',
        target: '/container/path',
        type: 'bind',
      });
      expect(mount.type).toBe('bind');
    });

    it('should mount tmpfs', async () => {
      const mount = await storage.mountVolume({
        source: 'tmpfs',
        target: '/tmp',
        type: 'tmpfs',
        tmpfsSizeBytes: 100 * 1024 * 1024,
      });
      expect(mount.type).toBe('tmpfs');
      const tmpfs = storage.getTmpfsMounts();
      expect(tmpfs.has('/tmp')).toBe(true);
    });

    it('should reject mounting non-existent volume', async () => {
      await expect(storage.mountVolume({ source: 'nonexistent', target: '/x', type: 'volume' })).rejects.toThrow('not found');
    });
  });

  describe('inspectVolume', () => {
    it('should return volume details', async () => {
      const vol = await storage.inspectVolume('arcanis-data');
      expect(vol.name).toBe('arcanis-data');
    });

    it('should throw for non-existent volume', async () => {
      await expect(storage.inspectVolume('nonexistent')).rejects.toThrow('not found');
    });
  });

  describe('listVolumes', () => {
    it('should list all volumes', async () => {
      const list = await storage.listVolumes();
      expect(list.length).toBeGreaterThanOrEqual(3);
    });

    it('should filter by name', async () => {
      const list = await storage.listVolumes({ name: 'arcanis' });
      expect(list.length).toBeGreaterThan(0);
    });

    it('should filter by driver', async () => {
      const list = await storage.listVolumes({ driver: 'local' });
      expect(list.length).toBeGreaterThan(0);
    });
  });

  describe('copyVolume', () => {
    it('should copy a volume', async () => {
      const copy = await storage.copyVolume('arcanis-data', 'copy-data');
      expect(copy.name).toBe('copy-data');
      expect(copy.driver).toBe('local');
    });
  });

  describe('pruneVolumes', () => {
    it('should prune unused volumes', async () => {
      storage.createVolume('prune-1');
      storage.createVolume('prune-2');
      const result = await storage.pruneVolumes();
      expect(result.count).toBeGreaterThanOrEqual(0);
    });
  });

  describe('counts', () => {
    it('should track volume count', () => {
      expect(storage.getVolumeCount()).toBeGreaterThanOrEqual(3);
    });

    it('should return active mounts', () => {
      const mounts = storage.getActiveMounts();
      expect(mounts).toBeInstanceOf(Map);
    });
  });
});

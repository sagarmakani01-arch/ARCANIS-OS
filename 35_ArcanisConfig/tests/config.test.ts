import { describe, it, expect, beforeEach } from 'vitest';
import { ConfigManager } from '../src/config.js';

describe('ConfigManager', () => {
  let cm: ConfigManager;
  beforeEach(() => { cm = new ConfigManager(); });

  describe('set/get', () => {
    it('should set and get a value', () => {
      cm.set('db.host', 'localhost');
      expect(cm.get('db.host')).toBe('localhost');
    });
    it('should return default for missing key', () => {
      expect(cm.get('missing', 'default')).toBe('default');
    });
    it('should delete a key', () => {
      cm.set('temp', 1);
      cm.delete('temp');
      expect(cm.get('temp')).toBeUndefined();
    });
    it('should throw on delete missing', () => {
      expect(() => cm.delete('missing')).toThrow('not found');
    });
  });

  describe('bulk operations', () => {
    it('should set and get many', () => {
      cm.setMany({ a: 1, b: 2, c: 3 });
      expect(cm.getMany(['a', 'b', 'c'])).toEqual({ a: 1, b: 2, c: 3 });
    });
    it('should return all keys', () => {
      cm.setMany({ x: 1, y: 2 });
      expect(cm.listKeys().length).toBe(2);
    });
  });

  describe('snapshots', () => {
    it('should create and restore snapshot', () => {
      cm.set('key1', 'val1');
      const snap = cm.snapshot();
      cm.set('key1', 'val2');
      expect(cm.get('key1')).toBe('val2');
      cm.restoreSnapshot(snap.id);
      expect(cm.get('key1')).toBe('val1');
    });
    it('should diff snapshots', () => {
      cm.set('a', 1);
      const s1 = cm.snapshot();
      cm.set('b', 2);
      cm.set('a', 10);
      const s2 = cm.snapshot();
      const diffs = cm.diff(s1.id, s2.id);
      expect(diffs.length).toBe(2);
    });
  });

  describe('versions', () => {
    it('should track versions', () => {
      cm.set('v', 'first');
      expect(cm.getVersion('v')).toBe(1);
      cm.set('v', 'second');
      expect(cm.getVersion('v')).toBe(2);
    });
  });

  describe('import/export', () => {
    it('should export and import', () => {
      cm.set('e1', 'val1');
      const json = cm.export();
      const cm2 = new ConfigManager();
      cm2.import(json);
      expect(cm2.get('e1')).toBe('val1');
    });
  });

  describe('watches', () => {
    it('should create and remove watch', () => {
      const w = cm.watch('db.*', 'onChange');
      expect(w.id).toBeDefined();
      cm.unwatch(w.id);
      expect(cm.get('db.*')).toBeUndefined();
    });
  });
});

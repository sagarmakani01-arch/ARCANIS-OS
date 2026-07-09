import { describe, it, expect } from 'vitest';
import {
  generateId, sha256, formatBytes, formatDuration,
  validateContainerName, validateImageName,
  parsePortMapping, parseMemorySize, parseCpuCpus,
} from '../src/utils.js';

describe('Utilities', () => {
  describe('generateId', () => {
    it('should generate ID of specified length', () => {
      const id = generateId(12);
      expect(id).toHaveLength(12);
    });

    it('should generate unique IDs', () => {
      const ids = new Set(Array.from({ length: 100 }, () => generateId(8)));
      expect(ids.size).toBe(100);
    });

    it('should generate hex strings', () => {
      const id = generateId(16);
      expect(/^[0-9a-f]+$/.test(id)).toBe(true);
    });
  });

  describe('sha256', () => {
    it('should compute sha256 hash', () => {
      const hash = sha256('hello');
      expect(hash).toHaveLength(64);
      expect(/^[0-9a-f]+$/.test(hash)).toBe(true);
    });

    it('should be deterministic', () => {
      expect(sha256('test')).toBe(sha256('test'));
    });

    it('should differ for different inputs', () => {
      expect(sha256('a')).not.toBe(sha256('b'));
    });
  });

  describe('formatBytes', () => {
    it('should format bytes', () => {
      expect(formatBytes(0)).toBe('0 B');
      expect(formatBytes(1024)).toBe('1 KB');
      expect(formatBytes(1024 * 1024)).toBe('1 MB');
      expect(formatBytes(1024 * 1024 * 1024)).toBe('1 GB');
    });
  });

  describe('formatDuration', () => {
    it('should format milliseconds', () => {
      expect(formatDuration(500)).toBe('500ms');
    });

    it('should format seconds', () => {
      expect(formatDuration(5000)).toBe('5.0s');
    });

    it('should format minutes', () => {
      expect(formatDuration(90000)).toBe('1m 30s');
    });
  });

  describe('validateContainerName', () => {
    it('should accept valid names', () => {
      expect(validateContainerName('my-container')).toBe(true);
      expect(validateContainerName('web_1.0')).toBe(true);
      expect(validateContainerName('test123')).toBe(true);
    });

    it('should reject invalid names', () => {
      expect(validateContainerName('')).toBe(false);
      expect(validateContainerName('-invalid')).toBe(false);
      expect(validateContainerName('has spaces')).toBe(false);
    });
  });

  describe('validateImageName', () => {
    it('should accept valid names', () => {
      expect(validateImageName('nginx')).toBe(true);
      expect(validateImageName('arcanis/base')).toBe(true);
      expect(validateImageName('registry.io/image:tag')).toBe(true);
    });

    it('should reject invalid names', () => {
      expect(validateImageName('')).toBe(false);
      expect(validateImageName('-invalid')).toBe(false);
    });
  });

  describe('parsePortMapping', () => {
    it('should parse host:container', () => {
      const result = parsePortMapping('8080:80');
      expect(result.hostPort).toBe(8080);
      expect(result.containerPort).toBe(80);
      expect(result.protocol).toBe('tcp');
    });

    it('should parse protocol', () => {
      const result = parsePortMapping('53:53/udp');
      expect(result.protocol).toBe('udp');
    });

    it('should reject invalid format', () => {
      expect(() => parsePortMapping('invalid')).toThrow('Invalid port mapping');
    });
  });

  describe('parseMemorySize', () => {
    it('should parse MB', () => {
      expect(parseMemorySize('512MB')).toBe(512 * 1024 * 1024);
    });

    it('should parse GB', () => {
      expect(parseMemorySize('2GB')).toBe(2 * 1024 * 1024 * 1024);
    });

    it('should parse KB', () => {
      expect(parseMemorySize('1024KB')).toBe(1024 * 1024);
    });

    it('should parse B', () => {
      expect(parseMemorySize('100B')).toBe(100);
    });

    it('should reject invalid format', () => {
      expect(() => parseMemorySize('invalid')).toThrow('Invalid memory size');
    });
  });

  describe('parseCpuCpus', () => {
    it('should parse single CPU', () => {
      const result = parseCpuCpus('0');
      expect(result).toEqual([{ start: 0, end: 0 }]);
    });

    it('should parse range', () => {
      const result = parseCpuCpus('0-3');
      expect(result).toEqual([{ start: 0, end: 3 }]);
    });

    it('should parse comma-separated', () => {
      const result = parseCpuCpus('0,2,4');
      expect(result).toHaveLength(3);
    });
  });
});

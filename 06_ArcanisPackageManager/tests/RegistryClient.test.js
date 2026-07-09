const { RegistryClient, RegistryError } = require('../src/core/RegistryClient');

describe('RegistryClient', () => {
  let client;

  beforeEach(() => {
    client = new RegistryClient({ timeout: 5000 });
  });

  describe('buildUrl', () => {
    test('builds URL from endpoint', () => {
      const url = client.buildUrl('packages/foo');
      expect(url).toBe('https://registry.arcanis.dev/v1/packages/foo');
    });

    test('strips leading slash from endpoint', () => {
      const url = client.buildUrl('/packages/foo');
      expect(url).toBe('https://registry.arcanis.dev/v1/packages/foo');
    });

    test('strips trailing slashes from base', () => {
      const url = client.buildUrl('test', 'https://example.com/v1///');
      expect(url).toBe('https://example.com/v1/test');
    });

    test('uses custom registry URL', () => {
      const url = client.buildUrl('test', 'https://custom.reg/v2');
      expect(url).toBe('https://custom.reg/v2/test');
    });
  });

  describe('satisfies', () => {
    test('wildcard matches all', () => {
      expect(client.satisfies('1.0.0', '*')).toBe(true);
    });

    test('exact match', () => {
      expect(client.satisfies('1.2.3', '1.2.3')).toBe(true);
      expect(client.satisfies('1.2.3', '1.2.4')).toBe(false);
    });

    test('tilde constraint', () => {
      expect(client.satisfies('1.2.5', '~1.2.3')).toBe(true);
      expect(client.satisfies('1.3.0', '~1.2.3')).toBe(false);
    });

    test('caret constraint', () => {
      expect(client.satisfies('1.5.0', '^1.2.3')).toBe(true);
      expect(client.satisfies('2.0.0', '^1.2.3')).toBe(false);
    });

    test('gte constraint', () => {
      expect(client.satisfies('1.3.0', '>=1.2.3')).toBe(true);
      expect(client.satisfies('1.2.0', '>=1.2.3')).toBe(false);
    });

    test('lte constraint', () => {
      expect(client.satisfies('1.2.0', '<=1.2.3')).toBe(true);
      expect(client.satisfies('1.3.0', '<=1.2.3')).toBe(false);
    });
  });

  describe('compare', () => {
    test('returns 1 for greater', () => {
      expect(client.compare('2.0.0', '1.0.0')).toBe(1);
    });

    test('returns -1 for lesser', () => {
      expect(client.compare('1.0.0', '2.0.0')).toBe(-1);
    });

    test('returns 0 for equal', () => {
      expect(client.compare('1.2.3', '1.2.3')).toBe(0);
    });
  });

  describe('cache', () => {
    test('caches package info', async () => {
      // Mock the fetch method
      client.fetch = jest.fn().mockResolvedValue({ name: 'test', versions: {} });
      await client.fetchPackageInfo('test');
      await client.fetchPackageInfo('test');
      expect(client.fetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('fetchPackageVersion', () => {
    test('returns exact version match', async () => {
      client.fetch = jest.fn().mockResolvedValue({
        name: 'test',
        versions: {
          '1.0.0': { name: 'test', version: '1.0.0' },
          '1.1.0': { name: 'test', version: '1.1.0' }
        },
        'dist-tags': { latest: '1.1.0' }
      });

      const result = await client.fetchPackageVersion('test', '1.0.0');
      expect(result.version).toBe('1.0.0');
    });

    test('resolves via dist-tags', async () => {
      client.fetch = jest.fn().mockResolvedValue({
        name: 'test',
        versions: {
          '1.0.0': { name: 'test', version: '1.0.0' },
          '1.1.0': { name: 'test', version: '1.1.0' }
        },
        'dist-tags': { latest: '1.1.0' }
      });

      const result = await client.fetchPackageVersion('test', 'latest');
      expect(result.version).toBe('1.1.0');
    });

    test('returns null when no version exists', async () => {
      client.fetch = jest.fn().mockResolvedValue({
        name: 'test',
        versions: {},
        'dist-tags': {}
      });

      const result = await client.fetchPackageVersion('test', '1.0.0');
      expect(result).toBeNull();
    });
  });
});

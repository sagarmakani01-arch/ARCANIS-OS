const { DependencyResolver, ResolverError } = require('../src/core/DependencyResolver');

describe('DependencyResolver', () => {
  let resolver;
  let mockRegistry;

  beforeEach(() => {
    mockRegistry = {
      fetchPackageInfo: jest.fn(),
      fetchPackageVersion: jest.fn()
    };
    resolver = new DependencyResolver(mockRegistry);
  });

  describe('parseConstraint', () => {
    test('parses wildcard', () => {
      expect(resolver.parseConstraint('*')).toEqual({ type: 'any', value: '*' });
    });

    test('parses exact version', () => {
      expect(resolver.parseConstraint('1.2.3')).toEqual({ type: 'exact', value: '1.2.3' });
    });

    test('parses tilde constraint', () => {
      expect(resolver.parseConstraint('~1.2.3')).toEqual({ type: '~', value: '1.2.3' });
    });

    test('parses caret constraint', () => {
      expect(resolver.parseConstraint('^1.2.3')).toEqual({ type: '^', value: '1.2.3' });
    });

    test('parses gte constraint', () => {
      expect(resolver.parseConstraint('>=1.2.3')).toEqual({ type: '>=', value: '1.2.3' });
    });

    test('throws on invalid constraint', () => {
      expect(() => resolver.parseConstraint('abc')).toThrow(ResolverError);
    });
  });

  describe('satisfies', () => {
    test('wildcard matches anything', () => {
      expect(resolver.satisfies('1.0.0', '*')).toBe(true);
    });

    test('exact match', () => {
      expect(resolver.satisfies('1.2.3', '1.2.3')).toBe(true);
      expect(resolver.satisfies('1.2.3', '1.2.4')).toBe(false);
    });

    test('tilde matches same major.minor', () => {
      expect(resolver.satisfies('1.2.5', '~1.2.3')).toBe(true);
      expect(resolver.satisfies('1.3.0', '~1.2.3')).toBe(false);
    });

    test('caret matches same major', () => {
      expect(resolver.satisfies('1.5.0', '^1.2.3')).toBe(true);
      expect(resolver.satisfies('2.0.0', '^1.2.3')).toBe(false);
    });

    test('gte comparison', () => {
      expect(resolver.satisfies('1.3.0', '>=1.2.3')).toBe(true);
      expect(resolver.satisfies('1.2.0', '>=1.2.3')).toBe(false);
    });

    test('lte comparison', () => {
      expect(resolver.satisfies('1.2.0', '<=1.2.3')).toBe(true);
      expect(resolver.satisfies('1.3.0', '<=1.2.3')).toBe(false);
    });

    test('gt comparison', () => {
      expect(resolver.satisfies('1.3.0', '>1.2.3')).toBe(true);
      expect(resolver.satisfies('1.2.3', '>1.2.3')).toBe(false);
    });

    test('lt comparison', () => {
      expect(resolver.satisfies('1.2.0', '<1.2.3')).toBe(true);
      expect(resolver.satisfies('1.2.3', '<1.2.3')).toBe(false);
    });
  });

  describe('compareVersions', () => {
    test('returns 1 when a > b', () => {
      expect(resolver.compareVersions('2.0.0', '1.0.0')).toBe(1);
    });

    test('returns -1 when a < b', () => {
      expect(resolver.compareVersions('1.0.0', '2.0.0')).toBe(-1);
    });

    test('returns 0 when equal', () => {
      expect(resolver.compareVersions('1.2.3', '1.2.3')).toBe(0);
    });
  });

  describe('resolve', () => {
    test('resolves a package with no dependencies', async () => {
      mockRegistry.fetchPackageVersion.mockResolvedValue({
        name: 'foo',
        version: '1.0.0',
        dependencies: {}
      });

      const result = await resolver.resolve('foo', '1.0.0');
      expect(result.name).toBe('foo');
      expect(result.version).toBe('1.0.0');
      expect(result.resolved).toBe(true);
      expect(result.dependencies).toEqual({});
    });

    test('resolves wildcard by fetching latest', async () => {
      mockRegistry.fetchPackageInfo.mockResolvedValue({
        'dist-tags': { latest: '2.0.0' }
      });
      mockRegistry.fetchPackageVersion.mockResolvedValue({
        name: 'bar',
        version: '2.0.0',
        dependencies: {}
      });

      const result = await resolver.resolve('bar', '*');
      expect(result.version).toBe('2.0.0');
    });

    test('throws on missing package', async () => {
      mockRegistry.fetchPackageInfo.mockResolvedValue(null);
      await expect(resolver.resolve('missing', '*')).rejects.toThrow('not found');
    });

    test('throws on no matching version', async () => {
      mockRegistry.fetchPackageVersion.mockResolvedValue(null);
      await expect(resolver.resolve('foo', '99.99.99')).rejects.toThrow('No version');
    });

    test('resolves transitive dependencies', async () => {
      mockRegistry.fetchPackageVersion
        .mockResolvedValueOnce({
          name: 'parent',
          version: '1.0.0',
          dependencies: { child: '^1.0.0' }
        })
        .mockResolvedValueOnce({
          name: 'child',
          version: '1.2.0',
          dependencies: {}
        });

      const result = await resolver.resolve('parent', '1.0.0');
      expect(result.dependencies.child.name).toBe('child');
      expect(result.dependencies.child.version).toBe('1.2.0');
    });

    test('detects circular dependencies', async () => {
      mockRegistry.fetchPackageVersion
        .mockResolvedValueOnce({
          name: 'a',
          version: '1.0.0',
          dependencies: { b: '1.0.0' }
        })
        .mockResolvedValueOnce({
          name: 'b',
          version: '1.0.0',
          dependencies: { a: '1.0.0' }
        });

      const result = await resolver.resolve('a', '1.0.0');
      expect(result.dependencies.b.dependencies.a.circular).toBe(true);
    });

    test('caches resolved packages', async () => {
      mockRegistry.fetchPackageVersion.mockResolvedValue({
        name: 'cached',
        version: '1.0.0',
        dependencies: {}
      });

      await resolver.resolve('cached', '1.0.0');
      await resolver.resolve('cached', '1.0.0');
      expect(mockRegistry.fetchPackageVersion).toHaveBeenCalledTimes(1);
    });
  });

  describe('flatten', () => {
    test('flattens a dependency tree', () => {
      const tree = {
        name: 'root',
        version: '1.0.0',
        dependencies: {
          a: { name: 'a', version: '1.0.0', dependencies: {} }
        }
      };
      const flat = resolver.flatten(tree);
      expect(flat).toHaveLength(2);
      expect(flat[0].name).toBe('root');
      expect(flat[1].name).toBe('a');
    });

    test('deduplicates packages', () => {
      const shared = { name: 'shared', version: '1.0.0', dependencies: {} };
      const tree = {
        name: 'root',
        version: '1.0.0',
        dependencies: {
          a: { name: 'a', version: '1.0.0', dependencies: { shared } },
          b: { name: 'b', version: '1.0.0', dependencies: { shared } }
        }
      };
      const flat = resolver.flatten(tree);
      expect(flat.filter(p => p.name === 'shared')).toHaveLength(1);
    });
  });

  describe('detectConflicts', () => {
    test('detects version conflicts', () => {
      const flat = [
        { name: 'dep', version: '1.0.0' },
        { name: 'dep', version: '2.0.0' }
      ];
      const conflicts = resolver.detectConflicts(flat);
      expect(conflicts).toHaveLength(1);
      expect(conflicts[0].package).toBe('dep');
    });

    test('returns empty when no conflicts', () => {
      const flat = [
        { name: 'a', version: '1.0.0' },
        { name: 'b', version: '1.0.0' }
      ];
      expect(resolver.detectConflicts(flat)).toHaveLength(0);
    });
  });
});

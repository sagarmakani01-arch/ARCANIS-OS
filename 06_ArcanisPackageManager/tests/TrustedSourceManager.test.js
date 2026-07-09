const { TrustedSourceManager } = require('../src/security/TrustedSourceManager');

describe('TrustedSourceManager', () => {
  let tsm;

  beforeEach(() => {
    tsm = new TrustedSourceManager();
  });

  describe('isTrusted', () => {
    test('trusts built-in sources', async () => {
      expect(await tsm.isTrusted('https://registry.arcanis.dev')).toBe(true);
      expect(await tsm.isTrusted('https://packages.arcanis.org')).toBe(true);
    });

    test('does not trust unknown sources', async () => {
      expect(await tsm.isTrusted('https://unknown-registry.com')).toBe(false);
    });

    test('trusts user-added sources', async () => {
      tsm.addSource('https://my-registry.com');
      expect(await tsm.isTrusted('https://my-registry.com')).toBe(true);
    });

    test('trusts sub-paths of trusted sources', async () => {
      tsm.addSource('https://my-registry.com');
      expect(await tsm.isTrusted('https://my-registry.com/packages')).toBe(true);
    });

    test('normalizes trailing slashes', async () => {
      expect(await tsm.isTrusted('https://registry.arcanis.dev/')).toBe(true);
    });

    test('returns false for null', async () => {
      expect(await tsm.isTrusted(null)).toBe(false);
    });
  });

  describe('addSource', () => {
    test('adds a source', () => {
      const result = tsm.addSource('https://new-registry.com');
      expect(result.added).toBe(true);
      expect(tsm.trustedSources.has('https://new-registry.com')).toBe(true);
    });

    test('normalizes trailing slashes', () => {
      tsm.addSource('https://new-registry.com/');
      expect(tsm.trustedSources.has('https://new-registry.com')).toBe(true);
    });
  });

  describe('removeSource', () => {
    test('removes a user source', () => {
      tsm.addSource('https://my-registry.com');
      const result = tsm.removeSource('https://my-registry.com');
      expect(result.removed).toBe(true);
      expect(tsm.trustedSources.has('https://my-registry.com')).toBe(false);
    });

    test('cannot remove built-in source', () => {
      const result = tsm.removeSource('https://registry.arcanis.dev');
      expect(result.removed).toBe(false);
      expect(result.error).toBe('Cannot remove built-in source');
    });

    test('returns removed: false for non-existent source', () => {
      const result = tsm.removeSource('https://never-added.com');
      expect(result.removed).toBe(false);
    });
  });

  describe('listSources', () => {
    test('lists built-in and user sources', () => {
      tsm.addSource('https://custom.com');
      const list = tsm.listSources();
      expect(list.builtin).toContain('https://registry.arcanis.dev');
      expect(list.user).toContain('https://custom.com');
      expect(list.all).toContain('https://registry.arcanis.dev');
      expect(list.all).toContain('https://custom.com');
    });
  });
});

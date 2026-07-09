const { PermissionManager } = require('../src/security/PermissionManager');

describe('PermissionManager', () => {
  let pm;

  beforeEach(() => {
    pm = new PermissionManager({ defaultPolicy: 'ask' });
  });

  describe('requestPermission', () => {
    test('allows with allow policy', async () => {
      const result = await pm.requestPermission('install', 'test-pkg', { policy: 'allow' });
      expect(result).toBe(true);
    });

    test('denies with deny policy', async () => {
      const result = await pm.requestPermission('install', 'test-pkg', { policy: 'deny' });
      expect(result).toBe(false);
    });

    test('caches granted permissions', async () => {
      await pm.requestPermission('install', 'pkg-a', { policy: 'allow' });
      const result = await pm.requestPermission('install', 'pkg-a');
      expect(result).toBe(true);
    });

    test('caches denied permissions', async () => {
      await pm.requestPermission('install', 'pkg-b', { policy: 'deny' });
      const result = await pm.requestPermission('install', 'pkg-b');
      expect(result).toBe(false);
    });
  });

  describe('grantPermission', () => {
    test('grants a permission', () => {
      pm.grantPermission('install', 'test');
      expect(pm.grantedPermissions.get('install:test')).toBe(true);
    });

    test('request returns true for granted permission', async () => {
      pm.grantPermission('install', 'test');
      const result = await pm.requestPermission('install', 'test');
      expect(result).toBe(true);
    });
  });

  describe('revokePermission', () => {
    test('revokes a permission', () => {
      pm.grantPermission('install', 'test');
      pm.revokePermission('install', 'test');
      expect(pm.grantedPermissions.has('install:test')).toBe(false);
    });
  });

  describe('checkScope', () => {
    test('allows all when no scopes configured', () => {
      expect(pm.checkScope('any-package')).toBe(true);
    });

    test('checks scope matching', () => {
      pm.allowedScopes = ['@arcanis/'];
      expect(pm.checkScope('@arcanis/core')).toBe(true);
      expect(pm.checkScope('other-package')).toBe(false);
    });
  });

  describe('listPermissions', () => {
    test('lists granted permissions', () => {
      pm.grantPermission('install', 'pkg-a');
      pm.grantPermission('network', 'api-call');
      const list = pm.listPermissions();
      expect(list).toHaveLength(2);
      expect(list.map(p => p.action)).toContain('install');
      expect(list.map(p => p.action)).toContain('network');
    });
  });

  describe('setDefaultPolicy', () => {
    test('sets valid policy', () => {
      pm.setDefaultPolicy('allow');
      expect(pm.defaultPolicy).toBe('allow');
    });

    test('throws on invalid policy', () => {
      expect(() => pm.setDefaultPolicy('invalid')).toThrow('Invalid policy');
    });
  });
});

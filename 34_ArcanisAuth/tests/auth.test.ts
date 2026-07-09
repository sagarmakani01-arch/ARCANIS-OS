import { describe, it, expect, beforeEach } from 'vitest';
import { AuthManager } from '../src/auth.js';

describe('AuthManager', () => {
  let auth: AuthManager;
  beforeEach(() => { auth = new AuthManager({ passwordPolicy: { minLength: 4, requireUppercase: true, requireLowercase: true, requireNumbers: true, requireSpecial: false, maxAge: 90 * 86400000 } }); });

  describe('register', () => {
    it('should register a user', async () => {
      const u = await auth.register({ username: 'alice', email: 'a@test.com', password: 'Pass1234' });
      expect(u.username).toBe('alice');
      expect(u.id).toBeDefined();
    });
    it('should reject duplicate username', async () => {
      await auth.register({ username: 'alice', email: 'a@test.com', password: 'Pass1234' });
      await expect(auth.register({ username: 'alice', email: 'b@test.com', password: 'Pass1234' })).rejects.toThrow('Username already exists');
    });
    it('should reject weak password', async () => {
      await expect(auth.register({ username: 'bob', email: 'b@test.com', password: 'low' })).rejects.toThrow('Password policy');
    });
  });

  describe('login', () => {
    it('should login and return tokens', async () => {
      await auth.register({ username: 'alice', email: 'a@test.com', password: 'Pass1234' });
      const tokens = await auth.login({ username: 'alice', password: 'Pass1234', ip: '127.0.0.1', userAgent: 'test' });
      expect(tokens.accessToken).toBeDefined();
      expect(tokens.expiresIn).toBe(3600);
    });
    it('should reject wrong password', async () => {
      await auth.register({ username: 'alice', email: 'a@test.com', password: 'Pass1234' });
      await expect(auth.login({ username: 'alice', password: 'wrong', ip: '127.0.0.1', userAgent: 'test' })).rejects.toThrow('Invalid credentials');
    });
    it('should reject login for locked user', async () => {
      const u = await auth.register({ username: 'alice', email: 'a@test.com', password: 'Pass1234' });
      await auth.lockUser(u.id);
      await expect(auth.login({ username: 'alice', password: 'Pass1234', ip: '127.0.0.1', userAgent: 'test' })).rejects.toThrow('Account locked');
    });
  });

  describe('validateToken', () => {
    it('should validate token', async () => {
      const u = await auth.register({ username: 'alice', email: 'a@test.com', password: 'Pass1234' });
      const tokens = await auth.login({ username: 'alice', password: 'Pass1234', ip: '127.0.0.1', userAgent: 'test' });
      const valid = await auth.validateToken(tokens.accessToken);
      expect(valid?.id).toBe(u.id);
    });
    it('should reject invalid token', async () => {
      expect(await auth.validateToken('invalid')).toBeUndefined();
    });
  });

  describe('changePassword', () => {
    it('should change password', async () => {
      const u = await auth.register({ username: 'alice', email: 'a@test.com', password: 'Pass1234' });
      await auth.changePassword(u.id, 'Pass1234', 'NewPass5678');
      const tokens = await auth.login({ username: 'alice', password: 'NewPass5678', ip: '127.0.0.1', userAgent: 'test' });
      expect(tokens.accessToken).toBeDefined();
    });
    it('should reject old password if wrong', async () => {
      const u = await auth.register({ username: 'alice', email: 'a@test.com', password: 'Pass1234' });
      await expect(auth.changePassword(u.id, 'wrong', 'NewPass5678')).rejects.toThrow('Invalid current password');
    });
  });

  describe('permissions', () => {
    it('should check permissions by role', async () => {
      const u = await auth.register({ username: 'alice', email: 'a@test.com', password: 'Pass1234' });
      const role = auth.createRole({ name: 'custom', permissions: ['read', 'write'], description: 'custom' });
      u.roles.push(role.id);
      expect(auth.hasPermission(u.id, 'read')).toBe(true);
      expect(auth.hasPermission(u.id, 'admin')).toBe(false);
    });
  });

  describe('audit', () => {
    it('should record login events', async () => {
      await auth.register({ username: 'alice', email: 'a@test.com', password: 'Pass1234' });
      try { await auth.login({ username: 'alice', password: 'wrong', ip: '127.0.0.1', userAgent: 'test' }); } catch {}
      expect(auth.getAuditLog().length).toBeGreaterThan(0);
    });
  });
});

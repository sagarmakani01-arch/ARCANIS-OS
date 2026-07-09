import { EventEmitter } from 'events';
import { createHash, randomBytes } from 'crypto';

function generateId(len = 12): string { return randomBytes(len / 2).toString('hex'); }
function sha256(d: string): string { return createHash('sha256').update(d).digest('hex'); }

export type AuthMethod = 'password' | 'token' | 'oauth2' | 'saml' | 'api-key';
export type Permission = 'read' | 'write' | 'delete' | 'admin' | 'execute' | 'deploy' | 'manage-users' | 'view-audit';
export interface User { id: string; username: string; email: string; passwordHash: string; salt: string; roles: string[]; mfaEnabled: boolean; mfaSecret?: string; createdAt: Date; lastLogin?: Date; locked: boolean; }
export interface Role { id: string; name: string; permissions: Permission[]; description: string; }
export interface Session { id: string; userId: string; token: string; expiresAt: Date; ip: string; userAgent: string; createdAt: Date; }
export interface TokenPair { accessToken: string; refreshToken: string; expiresIn: number; }
export interface AuditEntry { id: string; userId: string; action: string; resource: string; ip: string; timestamp: Date; success: boolean; details?: string; }
export interface PasswordPolicy { minLength: number; requireUppercase: boolean; requireLowercase: boolean; requireNumbers: boolean; requireSpecial: boolean; maxAge: number; }

export class AuthManager extends EventEmitter {
  private users: Map<string, User> = new Map();
  private roles: Map<string, Role> = new Map();
  private sessions: Map<string, Session> = new Map();
  private auditLog: AuditEntry[] = [];
  private passwordPolicy: PasswordPolicy;
  private maxSessions: number;

  constructor(options: { maxSessions?: number; passwordPolicy?: Partial<PasswordPolicy> } = {}) {
    super();
    this.maxSessions = options.maxSessions || 100;
    this.passwordPolicy = { minLength: 8, requireUppercase: true, requireLowercase: true, requireNumbers: true, requireSpecial: false, maxAge: 90 * 86400000, ...options.passwordPolicy };
    this.seedRoles();
  }

  private seedRoles(): void {
    this.roles.set('admin', { id: 'admin', name: 'admin', permissions: ['read', 'write', 'delete', 'admin', 'execute', 'deploy', 'manage-users', 'view-audit'], description: 'Full access' });
    this.roles.set('developer', { id: 'developer', name: 'developer', permissions: ['read', 'write', 'execute', 'deploy'], description: 'Development access' });
    this.roles.set('viewer', { id: 'viewer', name: 'viewer', permissions: ['read'], description: 'Read-only access' });
  }

  async register(config: { username: string; email: string; password: string; roles?: string[] }): Promise<User> {
    if (Array.from(this.users.values()).find(u => u.username === config.username)) throw new Error('Username already exists');
    if (Array.from(this.users.values()).find(u => u.email === config.email)) throw new Error('Email already exists');
    this.validatePassword(config.password);
    const salt = generateId(16);
    const passwordHash = sha256(config.password + salt);
    const user: User = { id: generateId(16), username: config.username, email: config.email, passwordHash, salt, roles: config.roles || ['viewer'], mfaEnabled: false, createdAt: new Date(), locked: false };
    this.users.set(user.id, user);
    this.emit('user:create', user);
    return { ...user };
  }

  async login(config: { username: string; password: string; ip: string; userAgent: string }): Promise<TokenPair> {
    const user = Array.from(this.users.values()).find(u => u.username === config.username);
    if (!user) { this.addAudit('login', 'unknown', config.ip, false, 'User not found'); throw new Error('Invalid credentials'); }
    if (user.locked) { this.addAudit('login', user.id, config.ip, false, 'Account locked'); throw new Error('Account locked'); }
    if (user.passwordHash !== sha256(config.password + user.salt)) { this.addAudit('login', user.id, config.ip, false, 'Invalid password'); throw new Error('Invalid credentials'); }
    user.lastLogin = new Date();
    const token = generateId(32);
    const session: Session = { id: generateId(12), userId: user.id, token, expiresAt: new Date(Date.now() + 3600000), ip: config.ip, userAgent: config.userAgent, createdAt: new Date() };
    this.sessions.set(session.id, session);
    this.addAudit('login', user.id, config.ip, true);
    this.emit('user:login', user);
    return { accessToken: token, refreshToken: generateId(32), expiresIn: 3600 };
  }

  async logout(sessionId: string): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (!session) throw new Error('Session not found');
    this.sessions.delete(sessionId);
    this.emit('user:logout', { userId: session.userId });
  }

  async validateToken(token: string): Promise<User | undefined> {
    const session = Array.from(this.sessions.values()).find(s => s.token === token && s.expiresAt > new Date());
    if (!session) return undefined;
    return this.users.get(session.userId);
  }

  async changePassword(userId: string, oldPassword: string, newPassword: string): Promise<void> {
    const user = this.users.get(userId);
    if (!user) throw new Error('User not found');
    if (user.passwordHash !== sha256(oldPassword + user.salt)) throw new Error('Invalid current password');
    this.validatePassword(newPassword);
    user.salt = generateId(16);
    user.passwordHash = sha256(newPassword + user.salt);
    this.emit('password:change', { userId });
  }

  validatePassword(password: string): void {
    const errors: string[] = [];
    if (password.length < this.passwordPolicy.minLength) errors.push(`Min length ${this.passwordPolicy.minLength}`);
    if (this.passwordPolicy.requireUppercase && !/[A-Z]/.test(password)) errors.push('Requires uppercase');
    if (this.passwordPolicy.requireLowercase && !/[a-z]/.test(password)) errors.push('Requires lowercase');
    if (this.passwordPolicy.requireNumbers && !/[0-9]/.test(password)) errors.push('Requires number');
    if (this.passwordPolicy.requireSpecial && !/[!@#$%^&*]/.test(password)) errors.push('Requires special char');
    if (errors.length > 0) throw new Error(`Password policy: ${errors.join(', ')}`);
  }

  hasPermission(userId: string, permission: Permission): boolean {
    const user = this.users.get(userId);
    if (!user) return false;
    for (const roleName of user.roles) {
      const role = this.roles.get(roleName);
      if (role && role.permissions.includes(permission)) return true;
    }
    return false;
  }

  createRole(config: { name: string; permissions: Permission[]; description: string }): Role {
    const role: Role = { id: generateId(8), ...config };
    this.roles.set(role.id, role);
    return role;
  }

  async lockUser(userId: string): Promise<void> {
    const user = this.users.get(userId);
    if (!user) throw new Error('User not found');
    user.locked = true;
    this.emit('user:lock', user);
  }

  async unlockUser(userId: string): Promise<void> {
    const user = this.users.get(userId);
    if (!user) throw new Error('User not found');
    user.locked = false;
  }

  getUser(userId: string): User | undefined { return this.users.get(userId); }
  getUserByUsername(username: string): User | undefined { return Array.from(this.users.values()).find(u => u.username === username); }
  listUsers(): User[] { return Array.from(this.users.values()); }
  getRole(roleId: string): Role | undefined { return this.roles.get(roleId); }
  listRoles(): Role[] { return Array.from(this.roles.values()); }
  getActiveSessions(): Session[] { return Array.from(this.sessions.values()).filter(s => s.expiresAt > new Date()); }
  getAuditLog(filters?: { userId?: string; action?: string }): AuditEntry[] {
    let result = [...this.auditLog];
    if (filters?.userId) result = result.filter(e => e.userId === filters.userId);
    if (filters?.action) result = result.filter(e => e.action === filters.action);
    return result;
  }
  private addAudit(action: string, userId: string, ip: string, success: boolean, details?: string): void {
    this.auditLog.push({ id: generateId(8), userId, action, resource: '', ip, timestamp: new Date(), success, details });
  }
}

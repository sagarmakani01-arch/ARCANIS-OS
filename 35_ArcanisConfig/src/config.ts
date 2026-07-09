import { EventEmitter } from 'events';
import { createHash, randomBytes } from 'crypto';

function generateId(len = 12): string { return randomBytes(len / 2).toString('hex'); }

export interface ConfigValue { key: string; value: unknown; type: 'string' | 'number' | 'boolean' | 'json' | 'encrypted' | 'secret'; version: number; updatedAt: Date; updatedBy?: string; schema?: ConfigSchema; }
export interface ConfigSchema { type: string; required?: boolean; default?: unknown; min?: number; max?: number; pattern?: string; enum?: unknown[]; description?: string; }
export interface ConfigSnapshot { id: string; timestamp: Date; data: Record<string, unknown>; version: number; }
export interface ConfigWatch { id: string; pattern: string; callback: string; }
export interface ConfigDiff { key: string; oldValue: unknown; newValue: unknown; action: 'add' | 'change' | 'remove'; }

export class ConfigManager extends EventEmitter {
  private store: Map<string, ConfigValue> = new Map();
  private snapshots: ConfigSnapshot[] = [];
  private watches: ConfigWatch[] = [];
  private schemas: Map<string, ConfigSchema> = new Map();
  private maxSnapshots: number;

  constructor(options: { maxSnapshots?: number } = {}) {
    super();
    this.maxSnapshots = options.maxSnapshots || 50;
  }

  set(key: string, value: unknown, options?: { type?: ConfigValue['type']; updatedBy?: string }): ConfigValue {
    const existing = this.store.get(key);
    const type = options?.type || this.inferType(value);
    const version = existing ? existing.version + 1 : 1;
    const cv: ConfigValue = { key, value, type, version, updatedAt: new Date(), updatedBy: options?.updatedBy };
    this.store.set(key, cv);
    this.emit('config:set', { key, version });
    return cv;
  }

  get<T = unknown>(key: string, defaultValue?: T): T | undefined {
    const cv = this.store.get(key);
    return cv ? cv.value as T : defaultValue;
  }

  has(key: string): boolean { return this.store.has(key); }

  delete(key: string): void {
    if (!this.store.has(key)) throw new Error(`Key ${key} not found`);
    this.store.delete(key);
    this.emit('config:delete', { key });
  }

  getMany(keys: string[]): Record<string, unknown> {
    const result: Record<string, unknown> = {};
    for (const key of keys) { const cv = this.store.get(key); result[key] = cv?.value; }
    return result;
  }

  setMany(entries: Record<string, unknown>, updatedBy?: string): void {
    for (const [key, value] of Object.entries(entries)) this.set(key, value, { updatedBy });
  }

  getAll(): Record<string, unknown> {
    const result: Record<string, unknown> = {};
    for (const [k, cv] of this.store) result[k] = cv.value;
    return result;
  }

  listKeys(pattern?: string): string[] {
    const keys = Array.from(this.store.keys());
    if (!pattern) return keys;
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    return keys.filter(k => regex.test(k));
  }

  getVersion(key: string): number { return this.store.get(key)?.version || 0; }

  snapshot(): ConfigSnapshot {
    const snap: ConfigSnapshot = { id: generateId(8), timestamp: new Date(), data: this.getAll(), version: this.snapshots.length + 1 };
    this.snapshots.push(snap);
    if (this.snapshots.length > this.maxSnapshots) this.snapshots.shift();
    return snap;
  }

  restoreSnapshot(snapshotId: string): void {
    const snap = this.snapshots.find(s => s.id === snapshotId);
    if (!snap) throw new Error('Snapshot not found');
    this.store.clear();
    for (const [key, value] of Object.entries(snap.data)) this.set(key, value);
    this.emit('config:restore', { snapshotId });
  }

  getSnapshots(): ConfigSnapshot[] { return [...this.snapshots]; }

  watch(pattern: string, callback: string): ConfigWatch {
    const w: ConfigWatch = { id: generateId(8), pattern, callback };
    this.watches.push(w);
    return w;
  }

  unwatch(watchId: string): void { this.watches = this.watches.filter(w => w.id !== watchId); }

  diff(oldSnapshotId: string, newSnapshotId: string): ConfigDiff[] {
    const oldSnap = this.snapshots.find(s => s.id === oldSnapshotId);
    const newSnap = this.snapshots.find(s => s.id === newSnapshotId);
    if (!oldSnap || !newSnap) throw new Error('Snapshot not found');
    const diffs: ConfigDiff[] = [];
    const allKeys = new Set([...Object.keys(oldSnap.data), ...Object.keys(newSnap.data)]);
    for (const key of allKeys) {
      if (!(key in oldSnap.data)) diffs.push({ key, oldValue: undefined, newValue: newSnap.data[key], action: 'add' });
      else if (!(key in newSnap.data)) diffs.push({ key, oldValue: oldSnap.data[key], newValue: undefined, action: 'remove' });
      else if (JSON.stringify(oldSnap.data[key]) !== JSON.stringify(newSnap.data[key])) diffs.push({ key, oldValue: oldSnap.data[key], newValue: newSnap.data[key], action: 'change' });
    }
    return diffs;
  }

  validate(key: string, value: unknown): void {
    const schema = this.schemas.get(key);
    if (!schema) return;
    if (schema.required && (value === undefined || value === null)) throw new Error(`${key} is required`);
    if (schema.enum && !schema.enum.includes(value)) throw new Error(`${key} must be one of: ${schema.enum.join(', ')}`);
    if (schema.min !== undefined && typeof value === 'number' && value < schema.min) throw new Error(`${key} must be >= ${schema.min}`);
    if (schema.max !== undefined && typeof value === 'number' && value > schema.max) throw new Error(`${key} must be <= ${schema.max}`);
  }

  private inferType(value: unknown): ConfigValue['type'] {
    if (typeof value === 'number') return 'number';
    if (typeof value === 'boolean') return 'boolean';
    if (typeof value === 'string' && (value.startsWith('{') || value.startsWith('['))) return 'json';
    return 'string';
  }

  export(): string { return JSON.stringify(Object.fromEntries(this.store)); }
  import(json: string): void { const data = JSON.parse(json); for (const [k, v] of Object.entries(data)) this.set(k, (v as ConfigValue).value); }
  count(): number { return this.store.size; }
}

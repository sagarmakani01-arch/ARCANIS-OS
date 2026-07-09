import { v4 as uuid } from "uuid";
import { MemoryEntry, MemoryType } from "./types";

export class ArcanisMemory {
  private entries: Map<string, MemoryEntry> = new Map();
  private index: Map<string, Set<string>> = new Map();
  private maxEntries: number;

  constructor(maxEntries: number = 10000) {
    this.maxEntries = maxEntries;
    this.startEvictionLoop();
  }

  store(key: string, value: unknown, type: MemoryType = MemoryType.Semantic, ttl: number | null = null, metadata: Record<string, unknown> = {}): MemoryEntry {
    this.evictIfNeeded();
    const entry: MemoryEntry = {
      id: uuid(),
      key,
      value,
      type,
      timestamp: Date.now(),
      ttl,
      metadata,
    };
    this.entries.set(entry.id, entry);
    const keys = key.toLowerCase().split(/\s+/);
    for (const k of keys) {
      if (!this.index.has(k)) {
        this.index.set(k, new Set());
      }
      this.index.get(k)!.add(entry.id);
    }
    return entry;
  }

  recall(key: string): MemoryEntry[] {
    const query = key.toLowerCase();
    const results: MemoryEntry[] = [];
    for (const [, entry] of this.entries) {
      const searchKeys = entry.key.toLowerCase().split(/\s+/);
      if (searchKeys.some(k => k.includes(query) || query.includes(k))) {
        if (entry.ttl === null || Date.now() - entry.timestamp < entry.ttl) {
          results.push(entry);
        }
      }
    }
    return results.sort((a, b) => b.timestamp - a.timestamp);
  }

  forget(id: string): boolean {
    const entry = this.entries.get(id);
    if (!entry) return false;
    this.entries.delete(id);
    const keys = entry.key.toLowerCase().split(/\s+/);
    for (const k of keys) {
      const ids = this.index.get(k);
      if (ids) {
        ids.delete(id);
        if (ids.size === 0) this.index.delete(k);
      }
    }
    return true;
  }

  clear(type?: MemoryType): void {
    if (!type) {
      this.entries.clear();
      this.index.clear();
      return;
    }
    for (const [id, entry] of this.entries) {
      if (entry.type === type) {
        this.forget(id);
      }
    }
  }

  stats(): { total: number; byType: Record<string, number> } {
    const byType: Record<string, number> = {};
    for (const [, entry] of this.entries) {
      byType[entry.type] = (byType[entry.type] || 0) + 1;
    }
    return { total: this.entries.size, byType };
  }

  private evictIfNeeded(): void {
    if (this.entries.size < this.maxEntries) return;
    const sorted = Array.from(this.entries.values())
      .filter(e => e.ttl !== null)
      .sort((a, b) => a.timestamp - b.timestamp);
    const toEvict = this.entries.size - this.maxEntries + 100;
    for (let i = 0; i < Math.min(toEvict, sorted.length); i++) {
      this.forget(sorted[i].id);
    }
  }

  private startEvictionLoop(): void {
    setInterval(() => {
      const now = Date.now();
      for (const [id, entry] of this.entries) {
        if (entry.ttl !== null && now - entry.timestamp > entry.ttl) {
          this.forget(id);
        }
      }
    }, 60000);
  }
}

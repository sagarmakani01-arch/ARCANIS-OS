import * as crypto from 'crypto';
import * as fs from 'fs';

export interface BuildCache {
  version: string;
  entries: Map<string, CacheEntry>;
}

export interface CacheEntry {
  hash: string;
  dependencies: string[];
  outputHash: string;
  stage: string;
  timestamp: number;
}

export class IncrementalCompiler {
  private cache: BuildCache;
  private cachePath: string;

  constructor(cachePath?: string) {
    this.cache = {
      version: '0.1.0',
      entries: new Map(),
    };
    this.cachePath = cachePath || '.arcanis-cache.json';
    this.load();
  }

  private hashContent(content: string): string {
    return crypto.createHash('sha256').update(content).digest('hex');
  }

  isCached(sourceId: string, content: string, stage?: string): boolean {
    const hash = this.hashContent(content);
    const entry = this.cache.entries.get(sourceId);
    if (!entry) return false;
    if (entry.hash !== hash) return false;
    if (stage && entry.stage !== stage) return false;
    return true;
  }

  updateCache(
    sourceId: string,
    content: string,
    dependencies: string[],
    stage: string,
  ): void {
    const hash = this.hashContent(content);
    const outputHash = this.hashContent(hash + dependencies.join(','));
    this.cache.entries.set(sourceId, {
      hash,
      dependencies,
      outputHash,
      stage,
      timestamp: Date.now(),
    });
    this.save();
  }

  invalidate(sourceId: string): void {
    this.cache.entries.delete(sourceId);
    for (const [key, entry] of this.cache.entries) {
      if (entry.dependencies.includes(sourceId)) {
        this.cache.entries.delete(key);
      }
    }
    this.save();
  }

  getCachedOutput(sourceId: string): string | null {
    const cacheDir = '.arcanis-cache';
    const cacheFile = `${cacheDir}/${sourceId.replace(/[^a-zA-Z0-9_-]/g, '_')}.out`;
    try {
      return fs.readFileSync(cacheFile, 'utf-8');
    } catch {
      return null;
    }
  }

  private load(): void {
    try {
      const raw = fs.readFileSync(this.cachePath, 'utf-8');
      const parsed = JSON.parse(raw);
      this.cache.version = parsed.version;
      this.cache.entries = new Map(Object.entries(parsed.entries));
    } catch {
      this.cache.entries = new Map();
    }
  }

  private save(): void {
    const obj = {
      version: this.cache.version,
      entries: Object.fromEntries(this.cache.entries),
    };
    try {
      fs.writeFileSync(this.cachePath, JSON.stringify(obj, null, 2));
    } catch {
      // Silently fail if we can't write cache
    }
  }

  clear(): void {
    this.cache.entries.clear();
    this.save();
  }
}

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
export declare class IncrementalCompiler {
    private cache;
    private cachePath;
    constructor(cachePath?: string);
    private hashContent;
    isCached(sourceId: string, content: string, stage?: string): boolean;
    updateCache(sourceId: string, content: string, dependencies: string[], stage: string): void;
    invalidate(sourceId: string): void;
    getCachedOutput(sourceId: string): string | null;
    private load;
    private save;
    clear(): void;
}
//# sourceMappingURL=incremental.d.ts.map
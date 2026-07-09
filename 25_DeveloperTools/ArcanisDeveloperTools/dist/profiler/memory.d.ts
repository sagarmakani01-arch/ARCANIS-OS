import { MemoryProfileResult } from './types.js';
export declare class MemoryProfiler {
    private allocations;
    private snapshots;
    private running;
    private interval;
    start(intervalMs?: number): void;
    stop(): MemoryProfileResult;
    private analyze;
}

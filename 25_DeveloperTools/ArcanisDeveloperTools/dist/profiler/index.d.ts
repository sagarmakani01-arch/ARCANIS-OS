import { CpuProfiler } from './cpu.js';
import { MemoryProfiler } from './memory.js';
import { ProfilerConfig, CpuProfileResult, MemoryProfileResult } from './types.js';
export { CpuProfiler, MemoryProfiler };
export type { ProfilerConfig, CpuProfileResult, MemoryProfileResult, CpuSample, FunctionStats, FlameNode, MemoryAllocation, LeakCandidate } from './types.js';
export declare class Profiler {
    readonly cpu: CpuProfiler;
    readonly memory: MemoryProfiler;
    private config;
    constructor(config?: Partial<ProfilerConfig>);
    profile(target: string): Promise<{
        cpu: CpuProfileResult;
        memory: MemoryProfileResult;
    }>;
}

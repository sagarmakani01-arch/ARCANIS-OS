export interface CpuSample {
    timestamp: number;
    function: string;
    file: string;
    line: number;
    depth: number;
}
export interface MemoryAllocation {
    timestamp: number;
    size: number;
    type: string;
    stackTrace: string[];
}
export interface CpuProfileResult {
    totalTime: number;
    sampleCount: number;
    functions: Map<string, FunctionStats>;
    flameGraph: FlameNode;
}
export interface FunctionStats {
    name: string;
    selfTime: number;
    totalTime: number;
    callCount: number;
}
export interface FlameNode {
    name: string;
    value: number;
    children: FlameNode[];
}
export interface MemoryProfileResult {
    heapUsed: number;
    heapTotal: number;
    external: number;
    allocations: MemoryAllocation[];
    leaks: LeakCandidate[];
}
export interface LeakCandidate {
    type: string;
    size: number;
    count: number;
    growthRate: number;
}
export interface ProfilerConfig {
    samplingInterval: number;
    maxSamples: number;
    memoryThreshold: number;
}

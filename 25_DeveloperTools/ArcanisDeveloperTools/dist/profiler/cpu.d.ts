import { CpuSample, CpuProfileResult } from './types.js';
export declare class CpuProfiler {
    private samples;
    private running;
    private interval;
    start(samplingIntervalMs?: number): void;
    stop(): CpuProfileResult;
    private analyze;
    getSamples(): CpuSample[];
}

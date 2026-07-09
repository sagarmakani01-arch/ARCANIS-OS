import { CpuProfiler } from './cpu.js';
import { MemoryProfiler } from './memory.js';
import { ProfilerConfig, CpuProfileResult, MemoryProfileResult } from './types.js';

export { CpuProfiler, MemoryProfiler };
export type { ProfilerConfig, CpuProfileResult, MemoryProfileResult, CpuSample, FunctionStats, FlameNode, MemoryAllocation, LeakCandidate } from './types.js';

export class Profiler {
  readonly cpu: CpuProfiler;
  readonly memory: MemoryProfiler;
  private config: ProfilerConfig;

  constructor(config?: Partial<ProfilerConfig>) {
    this.cpu = new CpuProfiler();
    this.memory = new MemoryProfiler();
    this.config = {
      samplingInterval: 1,
      maxSamples: 10000,
      memoryThreshold: 100 * 1024 * 1024,
      ...config,
    };
  }

  async profile(target: string): Promise<{ cpu: CpuProfileResult; memory: MemoryProfileResult }> {
    console.log(`[Profiler] Starting profile of ${target}`);
    this.cpu.start(this.config.samplingInterval);
    this.memory.start();

    const cpuResult = this.cpu.stop();
    const memoryResult = this.memory.stop();

    console.log(`[Profiler] Profile complete: ${cpuResult.sampleCount} samples`);
    return { cpu: cpuResult, memory: memoryResult };
  }
}

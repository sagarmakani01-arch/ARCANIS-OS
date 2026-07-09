import { CpuSample, CpuProfileResult, FunctionStats, FlameNode } from './types.js';

export class CpuProfiler {
  private samples: CpuSample[] = [];
  private running = false;
  private interval: ReturnType<typeof setInterval> | null = null;

  start(samplingIntervalMs: number = 1): void {
    if (this.running) return;
    this.running = true;
    this.samples = [];

    this.interval = setInterval(() => {
      const err = new Error();
      const stack = (err.stack || '').split('\n').slice(2);
      stack.forEach((frame, depth) => {
        const match = frame.match(/at\s+(?:(.+?)\s+\()?(.+?):(\d+):(\d+)/);
        if (match) {
          this.samples.push({
            timestamp: Date.now(),
            function: match[1] || '<anonymous>',
            file: match[2],
            line: parseInt(match[3], 10),
            depth,
          });
        }
      });
    }, samplingIntervalMs);
  }

  stop(): CpuProfileResult {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
    this.running = false;
    return this.analyze();
  }

  private analyze(): CpuProfileResult {
    const functions = new Map<string, FunctionStats>();

    for (const sample of this.samples) {
      const key = `${sample.function}@${sample.file}:${sample.line}`;
      const existing = functions.get(key);
      if (existing) {
        existing.selfTime++;
        existing.callCount++;
      } else {
        functions.set(key, {
          name: sample.function,
          selfTime: 1,
          totalTime: 1,
          callCount: 1,
        });
      }
    }

    const root: FlameNode = { name: 'root', value: this.samples.length, children: [] };
    return {
      totalTime: this.samples.length,
      sampleCount: this.samples.length,
      functions,
      flameGraph: root,
    };
  }

  getSamples(): CpuSample[] {
    return [...this.samples];
  }
}

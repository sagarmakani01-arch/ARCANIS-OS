import { MemoryAllocation, MemoryProfileResult, LeakCandidate } from './types.js';

export class MemoryProfiler {
  private allocations: MemoryAllocation[] = [];
  private snapshots: number[] = [];
  private running = false;
  private interval: ReturnType<typeof setInterval> | null = null;

  start(intervalMs: number = 1000): void {
    if (this.running) return;
    this.running = true;
    this.allocations = [];

    this.interval = setInterval(() => {
      const usage = process.memoryUsage();
      this.snapshots.push(usage.heapUsed);
    }, intervalMs);
  }

  stop(): MemoryProfileResult {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
    this.running = false;
    return this.analyze();
  }

  private analyze(): MemoryProfileResult {
    const usage = process.memoryUsage();
    const leaks: LeakCandidate[] = [];

    if (this.snapshots.length >= 2) {
      const first = this.snapshots[0];
      const last = this.snapshots[this.snapshots.length - 1];
      const growth = last - first;
      if (growth > 0) {
        leaks.push({
          type: 'heap',
          size: growth,
          count: this.snapshots.length,
          growthRate: growth / this.snapshots.length,
        });
      }
    }

    return {
      heapUsed: usage.heapUsed,
      heapTotal: usage.heapTotal,
      external: usage.external || 0,
      allocations: [...this.allocations],
      leaks,
    };
  }
}

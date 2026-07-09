import { Process } from "./process";
import { Priority, ProcessState } from "./types";

export class Scheduler {
  private processQueue: Map<Priority, Process[]> = new Map();
  private tickInterval: ReturnType<typeof setInterval> | null = null;
  private currentProcess: Process | null = null;

  constructor(private tickMs: number = 100) {
    for (const p of Object.values(Priority)) {
      this.processQueue.set(p, []);
    }
  }

  enqueue(process: Process): void {
    const queue = this.processQueue.get(process.priority);
    if (queue) {
      queue.push(process);
    }
  }

  dequeue(process: Process): void {
    for (const [, queue] of this.processQueue) {
      const idx = queue.indexOf(process);
      if (idx !== -1) {
        queue.splice(idx, 1);
        break;
      }
    }
  }

  private scheduleNext(): Process | null {
    for (const priority of [Priority.High, Priority.Normal, Priority.Low, Priority.Idle]) {
      const queue = this.processQueue.get(priority);
      if (queue && queue.length > 0) {
        const process = queue.shift()!;
        if (process.state === ProcessState.Running || process.state === ProcessState.Created) {
          queue.push(process);
          return process;
        }
        if (process.state === ProcessState.Suspended) {
          queue.push(process);
          continue;
        }
      }
    }
    return null;
  }

  start(): void {
    if (this.tickInterval) return;
    this.tickInterval = setInterval(() => {
      this.currentProcess = this.scheduleNext();
    }, this.tickMs);
  }

  stop(): void {
    if (this.tickInterval) {
      clearInterval(this.tickInterval);
      this.tickInterval = null;
    }
    this.currentProcess = null;
  }

  get activeCount(): number {
    let count = 0;
    for (const [, queue] of this.processQueue) {
      count += queue.filter(p => p.state === ProcessState.Running).length;
    }
    return count;
  }

  get totalCount(): number {
    let count = 0;
    for (const [, queue] of this.processQueue) {
      count += queue.length;
    }
    return count;
  }
}

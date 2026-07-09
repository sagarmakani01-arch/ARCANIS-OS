type TaskCallback = () => void;
type Task = { callback: TaskCallback; priority: TaskPriority; id: number };

export type TaskPriority = 'high' | 'normal' | 'low' | 'idle';

const PRIORITY_WEIGHTS: Record<TaskPriority, number> = {
  high: 4,
  normal: 2,
  low: 1,
  idle: 0,
};

export class Scheduler {
  private queue: Task[] = [];
  private isRunning = false;
  private taskIdCounter = 0;
  private frameId: number | null = null;
  private idleFrameId: number | null = null;
  private yieldInterval = 5;
  private startTime = 0;

  schedule(callback: TaskCallback, priority: TaskPriority = 'normal'): number {
    const id = ++this.taskIdCounter;
    this.queue.push({ callback, priority, id });
    this.queue.sort((a, b) => PRIORITY_WEIGHTS[b.priority] - PRIORITY_WEIGHTS[a.priority]);
    this.flush();
    return id;
  }

  cancel(taskId: number): void {
    this.queue = this.queue.filter((t) => t.id !== taskId);
  }

  private flush(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    this.startTime = performance.now();

    const processTask = (deadline: { timeRemaining: () => number }) => {
      while (this.queue.length > 0) {
        if (typeof deadline === 'object' && typeof deadline.timeRemaining === 'function') {
          if (deadline.timeRemaining() < 1) {
            this.scheduleYield();
            break;
          }
        }

        const elapsed = performance.now() - this.startTime;
        if (elapsed > 5) {
          this.scheduleYield();
          break;
        }

        const task = this.queue.shift()!;
        task.callback();
      }

      if (this.queue.length === 0) {
        this.isRunning = false;
      }
    };

    if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
      this.idleFrameId = requestIdleCallback(processTask as IdleRequestCallback, { timeout: 100 });
    } else {
      this.frameId = requestAnimationFrame(() => {
        const deadline = {
          timeRemaining: () => Math.max(0, 5 - (performance.now() - this.startTime)),
        };
        processTask(deadline);
      });
    }
  }

  private scheduleYield(): void {
    if (this.frameId !== null) {
      cancelAnimationFrame(this.frameId);
      this.frameId = null;
    }
    if (this.idleFrameId !== null) {
      cancelIdleCallback(this.idleFrameId);
      this.idleFrameId = null;
    }

    this.isRunning = false;
    setTimeout(() => {
      this.isRunning = false;
      this.flush();
    }, 0);
  }

  flushSync(callback: TaskCallback): void {
    callback();
  }

  microtask(callback: TaskCallback): void {
    Promise.resolve().then(callback);
  }

  get pendingCount(): number {
    return this.queue.length;
  }

  destroy(): void {
    this.queue = [];
    this.isRunning = false;
    if (this.frameId !== null) cancelAnimationFrame(this.frameId);
    if (this.idleFrameId !== null) cancelIdleCallback(this.idleFrameId);
  }
}

export const scheduler = new Scheduler();

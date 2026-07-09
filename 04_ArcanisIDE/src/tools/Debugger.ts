import { Breakpoint, StackFrame, Thread, Variable, IDisposable } from '../api/types';
import { EventBus } from '../core/EventBus';

export class Debugger {
  private breakpoints = new Map<string, Breakpoint[]>();
  private threads = new Map<number, Thread>();
  private state: 'idle' | 'running' | 'paused' | 'stepping' = 'idle';
  private breakpointCounter = 0;
  private active = false;

  constructor(private eventBus: EventBus) {}

  setBreakpoint(uri: string, line: number, condition?: string): Breakpoint {
    const bp: Breakpoint = {
      id: `bp_${++this.breakpointCounter}`,
      uri,
      line,
      enabled: true,
      condition,
    };

    const existing = this.breakpoints.get(uri) || [];
    existing.push(bp);
    this.breakpoints.set(uri, existing);

    return bp;
  }

  removeBreakpoint(id: string): void {
    for (const [uri, bps] of this.breakpoints) {
      const filtered = bps.filter(bp => bp.id !== id);
      if (filtered.length !== bps.length) {
        if (filtered.length === 0) {
          this.breakpoints.delete(uri);
        } else {
          this.breakpoints.set(uri, filtered);
        }
        return;
      }
    }
  }

  toggleBreakpoint(uri: string, line: number): Breakpoint | undefined {
    const existing = this.breakpoints.get(uri) || [];
    const found = existing.find(bp => bp.line === line);

    if (found) {
      this.removeBreakpoint(found.id);
      return undefined;
    }

    return this.setBreakpoint(uri, line);
  }

  getBreakpoints(uri?: string): Breakpoint[] {
    if (uri) {
      return this.breakpoints.get(uri) || [];
    }
    const result: Breakpoint[] = [];
    for (const bps of this.breakpoints.values()) {
      result.push(...bps);
    }
    return result;
  }

  async start(): Promise<void> {
    this.active = true;
    this.state = 'running';
    this.eventBus.emit('debugger:started', {});
  }

  async stop(): Promise<void> {
    this.active = false;
    this.state = 'idle';
    this.threads.clear();
    this.eventBus.emit('debugger:stopped', {});
  }

  async pause(): Promise<void> {
    if (this.state !== 'running') return;
    this.state = 'paused';
    this.eventBus.emit('debugger:paused', {});
  }

  async continue(): Promise<void> {
    if (this.state !== 'paused' && this.state !== 'stepping') return;
    this.state = 'running';
    this.eventBus.emit('debugger:continued', {});
  }

  async stepOver(): Promise<void> {
    if (this.state !== 'paused') return;
    this.state = 'stepping';
    this.eventBus.emit('debugger:continued', { action: 'stepOver' });
  }

  async stepInto(): Promise<void> {
    if (this.state !== 'paused') return;
    this.state = 'stepping';
    this.eventBus.emit('debugger:continued', { action: 'stepInto' });
  }

  async stepOut(): Promise<void> {
    if (this.state !== 'paused') return;
    this.state = 'stepping';
    this.eventBus.emit('debugger:continued', { action: 'stepOut' });
  }

  getThreads(): Thread[] {
    return Array.from(this.threads.values());
  }

  getStackFrames(threadId: number): StackFrame[] {
    const thread = this.threads.get(threadId);
    return thread ? thread.stackFrames : [];
  }

  getVariables(threadId: number, frameId: number): Variable[] {
    const thread = this.threads.get(threadId);
    if (!thread) return [];

    const frame = thread.stackFrames.find(f => f.id === frameId);
    if (!frame || !frame.scopes) return [];

    return frame.scopes.reduce((acc, scope) => acc.concat(scope.variables), [] as Variable[]);
  }

  async evaluate(expression: string, threadId: number, frameId: number): Promise<Variable> {
    return {
      name: expression,
      value: '<evaluation pending>',
      type: 'unknown',
    };
  }
}

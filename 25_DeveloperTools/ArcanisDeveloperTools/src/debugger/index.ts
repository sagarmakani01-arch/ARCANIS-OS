import { BreakpointManager } from './breakpoint.js';
import { StackTraceParser } from './stacktrace.js';
import { DebuggerConfig, ExecutionState, VariableInspector } from './types.js';

export { BreakpointManager, StackTraceParser };
export type { DebuggerConfig, ExecutionState, VariableInspector, Breakpoint, StackFrame, BreakpointCondition } from './types.js';

export class Debugger {
  readonly breakpoints: BreakpointManager;
  readonly stackTrace: StackTraceParser;
  private config: DebuggerConfig;
  private running = false;

  constructor(config?: Partial<DebuggerConfig>) {
    this.breakpoints = new BreakpointManager();
    this.stackTrace = new StackTraceParser();
    this.config = {
      port: 9229,
      host: '127.0.0.1',
      breakOnEntry: false,
      logLevel: 'info',
      ...config,
    };
  }

  async attach(target: string): Promise<void> {
    this.running = true;
    console.log(`[Debugger] Attached to ${target} on ${this.config.host}:${this.config.port}`);
  }

  async detach(): Promise<void> {
    this.running = false;
    console.log('[Debugger] Detached');
  }

  async stepOver(state: ExecutionState): Promise<ExecutionState> {
    return { ...state, line: state.line + 1 };
  }

  async stepInto(state: ExecutionState): Promise<ExecutionState> {
    return { ...state };
  }

  async stepOut(state: ExecutionState): Promise<ExecutionState> {
    return { ...state };
  }

  async continue(state: ExecutionState): Promise<ExecutionState> {
    return state;
  }

  isRunning(): boolean {
    return this.running;
  }

  getConfig(): DebuggerConfig {
    return { ...this.config };
  }
}

import { BreakpointManager } from './breakpoint.js';
import { StackTraceParser } from './stacktrace.js';
import { DebuggerConfig, ExecutionState } from './types.js';
export { BreakpointManager, StackTraceParser };
export type { DebuggerConfig, ExecutionState, VariableInspector, Breakpoint, StackFrame, BreakpointCondition } from './types.js';
export declare class Debugger {
    readonly breakpoints: BreakpointManager;
    readonly stackTrace: StackTraceParser;
    private config;
    private running;
    constructor(config?: Partial<DebuggerConfig>);
    attach(target: string): Promise<void>;
    detach(): Promise<void>;
    stepOver(state: ExecutionState): Promise<ExecutionState>;
    stepInto(state: ExecutionState): Promise<ExecutionState>;
    stepOut(state: ExecutionState): Promise<ExecutionState>;
    continue(state: ExecutionState): Promise<ExecutionState>;
    isRunning(): boolean;
    getConfig(): DebuggerConfig;
}

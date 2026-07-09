import { Breakpoint, BreakpointCondition, ExecutionState } from './types.js';
export declare class BreakpointManager {
    private breakpoints;
    setBreakpoint(file: string, line: number, condition?: BreakpointCondition): Breakpoint;
    removeBreakpoint(id: string): boolean;
    toggleBreakpoint(id: string): Breakpoint | undefined;
    clearAll(): void;
    evaluate(state: ExecutionState): Breakpoint | undefined;
    listBreakpoints(): Breakpoint[];
    getBreakpoint(id: string): Breakpoint | undefined;
}

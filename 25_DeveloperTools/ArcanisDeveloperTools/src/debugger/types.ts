export type BreakpointCondition = (state: ExecutionState) => boolean;

export interface Breakpoint {
  id: string;
  file: string;
  line: number;
  column?: number;
  condition?: BreakpointCondition;
  enabled: boolean;
  hitCount: number;
}

export interface ExecutionState {
  file: string;
  line: number;
  column: number;
  variables: Record<string, unknown>;
  callStack: StackFrame[];
}

export interface StackFrame {
  functionName: string;
  file: string;
  line: number;
  column: number;
  locals: Record<string, unknown>;
}

export interface DebuggerConfig {
  port: number;
  host: string;
  breakOnEntry: boolean;
  logLevel: 'error' | 'warn' | 'info' | 'debug';
}

export interface VariableInspector {
  getValue(name: string): unknown;
  setValue(name: string, value: unknown): void;
  listVariables(): string[];
  watchExpression(expr: string): unknown;
}

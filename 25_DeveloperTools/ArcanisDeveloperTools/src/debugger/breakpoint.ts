import { Breakpoint, BreakpointCondition, ExecutionState } from './types.js';

let breakpointCounter = 0;

export class BreakpointManager {
  private breakpoints: Map<string, Breakpoint> = new Map();

  setBreakpoint(file: string, line: number, condition?: BreakpointCondition): Breakpoint {
    const id = `bp_${++breakpointCounter}`;
    const bp: Breakpoint = { id, file, line, enabled: true, hitCount: 0 };
    if (condition) bp.condition = condition;
    this.breakpoints.set(id, bp);
    return bp;
  }

  removeBreakpoint(id: string): boolean {
    return this.breakpoints.delete(id);
  }

  toggleBreakpoint(id: string): Breakpoint | undefined {
    const bp = this.breakpoints.get(id);
    if (bp) {
      bp.enabled = !bp.enabled;
      return bp;
    }
  }

  clearAll(): void {
    this.breakpoints.clear();
  }

  evaluate(state: ExecutionState): Breakpoint | undefined {
    for (const bp of this.breakpoints.values()) {
      if (!bp.enabled) continue;
      if (bp.file !== state.file || bp.line !== state.line) continue;
      if (bp.condition && !bp.condition(state)) continue;
      bp.hitCount++;
      return bp;
    }
  }

  listBreakpoints(): Breakpoint[] {
    return Array.from(this.breakpoints.values());
  }

  getBreakpoint(id: string): Breakpoint | undefined {
    return this.breakpoints.get(id);
  }
}

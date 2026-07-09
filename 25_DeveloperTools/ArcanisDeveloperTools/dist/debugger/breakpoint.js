"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BreakpointManager = void 0;
let breakpointCounter = 0;
class BreakpointManager {
    breakpoints = new Map();
    setBreakpoint(file, line, condition) {
        const id = `bp_${++breakpointCounter}`;
        const bp = { id, file, line, enabled: true, hitCount: 0 };
        if (condition)
            bp.condition = condition;
        this.breakpoints.set(id, bp);
        return bp;
    }
    removeBreakpoint(id) {
        return this.breakpoints.delete(id);
    }
    toggleBreakpoint(id) {
        const bp = this.breakpoints.get(id);
        if (bp) {
            bp.enabled = !bp.enabled;
            return bp;
        }
    }
    clearAll() {
        this.breakpoints.clear();
    }
    evaluate(state) {
        for (const bp of this.breakpoints.values()) {
            if (!bp.enabled)
                continue;
            if (bp.file !== state.file || bp.line !== state.line)
                continue;
            if (bp.condition && !bp.condition(state))
                continue;
            bp.hitCount++;
            return bp;
        }
    }
    listBreakpoints() {
        return Array.from(this.breakpoints.values());
    }
    getBreakpoint(id) {
        return this.breakpoints.get(id);
    }
}
exports.BreakpointManager = BreakpointManager;
//# sourceMappingURL=breakpoint.js.map
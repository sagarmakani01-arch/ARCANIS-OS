"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Debugger = exports.StackTraceParser = exports.BreakpointManager = void 0;
const breakpoint_js_1 = require("./breakpoint.js");
Object.defineProperty(exports, "BreakpointManager", { enumerable: true, get: function () { return breakpoint_js_1.BreakpointManager; } });
const stacktrace_js_1 = require("./stacktrace.js");
Object.defineProperty(exports, "StackTraceParser", { enumerable: true, get: function () { return stacktrace_js_1.StackTraceParser; } });
class Debugger {
    breakpoints;
    stackTrace;
    config;
    running = false;
    constructor(config) {
        this.breakpoints = new breakpoint_js_1.BreakpointManager();
        this.stackTrace = new stacktrace_js_1.StackTraceParser();
        this.config = {
            port: 9229,
            host: '127.0.0.1',
            breakOnEntry: false,
            logLevel: 'info',
            ...config,
        };
    }
    async attach(target) {
        this.running = true;
        console.log(`[Debugger] Attached to ${target} on ${this.config.host}:${this.config.port}`);
    }
    async detach() {
        this.running = false;
        console.log('[Debugger] Detached');
    }
    async stepOver(state) {
        return { ...state, line: state.line + 1 };
    }
    async stepInto(state) {
        return { ...state };
    }
    async stepOut(state) {
        return { ...state };
    }
    async continue(state) {
        return state;
    }
    isRunning() {
        return this.running;
    }
    getConfig() {
        return { ...this.config };
    }
}
exports.Debugger = Debugger;
//# sourceMappingURL=index.js.map
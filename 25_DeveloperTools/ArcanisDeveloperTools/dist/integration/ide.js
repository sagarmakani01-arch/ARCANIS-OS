"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanisIDEIntegration = void 0;
class ArcanisIDEIntegration {
    name = '@arcanis/developer-tools-ide';
    version = '0.1.0';
    hooks = ['onDebug', 'onProfile', 'onAnalyze', 'onTest'];
    async activate() {
        console.log('[IDE] Arcanis Developer Tools extension activated');
        this.registerDebuggerPanel();
        this.registerProfilerView();
        this.registerAnalyzerPanel();
        this.registerTestRunner();
    }
    async deactivate() {
        console.log('[IDE] Arcanis Developer Tools extension deactivated');
    }
    registerDebuggerPanel() {
        console.log('[IDE] Debugger panel registered');
    }
    registerProfilerView() {
        console.log('[IDE] Profiler view registered');
    }
    registerAnalyzerPanel() {
        console.log('[IDE] Code analyzer panel registered');
    }
    registerTestRunner() {
        console.log('[IDE] Test runner panel registered');
    }
}
exports.ArcanisIDEIntegration = ArcanisIDEIntegration;
//# sourceMappingURL=ide.js.map
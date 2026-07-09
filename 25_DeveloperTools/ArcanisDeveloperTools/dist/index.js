"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanisDeveloperTools = exports.ArcanisLangIntegration = exports.ArcanisBuildIntegration = exports.ArcanisIDEIntegration = exports.MetricsCollector = exports.PerformanceMonitor = exports.spyOn = exports.createMock = exports.expect = exports.throws = exports.deepEqual = exports.equal = exports.assert = exports.TestRunner = exports.TestingTools = exports.DocRenderer = exports.DocParser = exports.DocumentationGenerator = exports.analyzeComplexity = exports.defaultRules = exports.CodeAnalyzer = exports.MemoryProfiler = exports.CpuProfiler = exports.Profiler = exports.StackTraceParser = exports.BreakpointManager = exports.Debugger = void 0;
const index_js_1 = require("./debugger/index.js");
Object.defineProperty(exports, "Debugger", { enumerable: true, get: function () { return index_js_1.Debugger; } });
Object.defineProperty(exports, "BreakpointManager", { enumerable: true, get: function () { return index_js_1.BreakpointManager; } });
Object.defineProperty(exports, "StackTraceParser", { enumerable: true, get: function () { return index_js_1.StackTraceParser; } });
const index_js_2 = require("./profiler/index.js");
Object.defineProperty(exports, "Profiler", { enumerable: true, get: function () { return index_js_2.Profiler; } });
Object.defineProperty(exports, "CpuProfiler", { enumerable: true, get: function () { return index_js_2.CpuProfiler; } });
Object.defineProperty(exports, "MemoryProfiler", { enumerable: true, get: function () { return index_js_2.MemoryProfiler; } });
const index_js_3 = require("./analyzer/index.js");
Object.defineProperty(exports, "CodeAnalyzer", { enumerable: true, get: function () { return index_js_3.CodeAnalyzer; } });
Object.defineProperty(exports, "defaultRules", { enumerable: true, get: function () { return index_js_3.defaultRules; } });
Object.defineProperty(exports, "analyzeComplexity", { enumerable: true, get: function () { return index_js_3.analyzeComplexity; } });
const index_js_4 = require("./docgen/index.js");
Object.defineProperty(exports, "DocumentationGenerator", { enumerable: true, get: function () { return index_js_4.DocumentationGenerator; } });
Object.defineProperty(exports, "DocParser", { enumerable: true, get: function () { return index_js_4.DocParser; } });
Object.defineProperty(exports, "DocRenderer", { enumerable: true, get: function () { return index_js_4.DocRenderer; } });
const index_js_5 = require("./testing/index.js");
Object.defineProperty(exports, "TestingTools", { enumerable: true, get: function () { return index_js_5.TestingTools; } });
Object.defineProperty(exports, "TestRunner", { enumerable: true, get: function () { return index_js_5.TestRunner; } });
Object.defineProperty(exports, "assert", { enumerable: true, get: function () { return index_js_5.assert; } });
Object.defineProperty(exports, "equal", { enumerable: true, get: function () { return index_js_5.equal; } });
Object.defineProperty(exports, "deepEqual", { enumerable: true, get: function () { return index_js_5.deepEqual; } });
Object.defineProperty(exports, "throws", { enumerable: true, get: function () { return index_js_5.throws; } });
Object.defineProperty(exports, "expect", { enumerable: true, get: function () { return index_js_5.expect; } });
Object.defineProperty(exports, "createMock", { enumerable: true, get: function () { return index_js_5.createMock; } });
Object.defineProperty(exports, "spyOn", { enumerable: true, get: function () { return index_js_5.spyOn; } });
const index_js_6 = require("./perfmon/index.js");
Object.defineProperty(exports, "PerformanceMonitor", { enumerable: true, get: function () { return index_js_6.PerformanceMonitor; } });
Object.defineProperty(exports, "MetricsCollector", { enumerable: true, get: function () { return index_js_6.MetricsCollector; } });
const ide_js_1 = require("./integration/ide.js");
Object.defineProperty(exports, "ArcanisIDEIntegration", { enumerable: true, get: function () { return ide_js_1.ArcanisIDEIntegration; } });
const build_js_1 = require("./integration/build.js");
Object.defineProperty(exports, "ArcanisBuildIntegration", { enumerable: true, get: function () { return build_js_1.ArcanisBuildIntegration; } });
const lang_js_1 = require("./integration/lang.js");
Object.defineProperty(exports, "ArcanisLangIntegration", { enumerable: true, get: function () { return lang_js_1.ArcanisLangIntegration; } });
class ArcanisDeveloperTools {
    debugger;
    profiler;
    analyzer;
    docgen;
    testing;
    perfmon;
    ide;
    build;
    lang;
    constructor() {
        this.debugger = new index_js_1.Debugger();
        this.profiler = new index_js_2.Profiler();
        this.analyzer = new index_js_3.CodeAnalyzer();
        this.docgen = new index_js_4.DocumentationGenerator();
        this.testing = new index_js_5.TestingTools();
        this.perfmon = new index_js_6.PerformanceMonitor();
        this.ide = new ide_js_1.ArcanisIDEIntegration();
        this.build = new build_js_1.ArcanisBuildIntegration();
        this.lang = new lang_js_1.ArcanisLangIntegration();
    }
    getVersion() {
        return '0.1.0';
    }
}
exports.ArcanisDeveloperTools = ArcanisDeveloperTools;
//# sourceMappingURL=index.js.map
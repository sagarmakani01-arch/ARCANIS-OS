"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Profiler = exports.MemoryProfiler = exports.CpuProfiler = void 0;
const cpu_js_1 = require("./cpu.js");
Object.defineProperty(exports, "CpuProfiler", { enumerable: true, get: function () { return cpu_js_1.CpuProfiler; } });
const memory_js_1 = require("./memory.js");
Object.defineProperty(exports, "MemoryProfiler", { enumerable: true, get: function () { return memory_js_1.MemoryProfiler; } });
class Profiler {
    cpu;
    memory;
    config;
    constructor(config) {
        this.cpu = new cpu_js_1.CpuProfiler();
        this.memory = new memory_js_1.MemoryProfiler();
        this.config = {
            samplingInterval: 1,
            maxSamples: 10000,
            memoryThreshold: 100 * 1024 * 1024,
            ...config,
        };
    }
    async profile(target) {
        console.log(`[Profiler] Starting profile of ${target}`);
        this.cpu.start(this.config.samplingInterval);
        this.memory.start();
        const cpuResult = this.cpu.stop();
        const memoryResult = this.memory.stop();
        console.log(`[Profiler] Profile complete: ${cpuResult.sampleCount} samples`);
        return { cpu: cpuResult, memory: memoryResult };
    }
}
exports.Profiler = Profiler;
//# sourceMappingURL=index.js.map
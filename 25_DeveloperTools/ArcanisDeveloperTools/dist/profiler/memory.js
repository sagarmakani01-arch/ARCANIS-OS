"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MemoryProfiler = void 0;
class MemoryProfiler {
    allocations = [];
    snapshots = [];
    running = false;
    interval = null;
    start(intervalMs = 1000) {
        if (this.running)
            return;
        this.running = true;
        this.allocations = [];
        this.interval = setInterval(() => {
            const usage = process.memoryUsage();
            this.snapshots.push(usage.heapUsed);
        }, intervalMs);
    }
    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
        this.running = false;
        return this.analyze();
    }
    analyze() {
        const usage = process.memoryUsage();
        const leaks = [];
        if (this.snapshots.length >= 2) {
            const first = this.snapshots[0];
            const last = this.snapshots[this.snapshots.length - 1];
            const growth = last - first;
            if (growth > 0) {
                leaks.push({
                    type: 'heap',
                    size: growth,
                    count: this.snapshots.length,
                    growthRate: growth / this.snapshots.length,
                });
            }
        }
        return {
            heapUsed: usage.heapUsed,
            heapTotal: usage.heapTotal,
            external: usage.external || 0,
            allocations: [...this.allocations],
            leaks,
        };
    }
}
exports.MemoryProfiler = MemoryProfiler;
//# sourceMappingURL=memory.js.map
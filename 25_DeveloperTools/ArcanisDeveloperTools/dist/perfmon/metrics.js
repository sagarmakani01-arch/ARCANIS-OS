"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.MetricsCollector = void 0;
const os = __importStar(require("os"));
class MetricsCollector {
    metrics = {
        cpu: [], memory: [], heap: [], eventLoop: [],
    };
    maxHistory;
    constructor(maxHistory = 3600) {
        this.maxHistory = maxHistory;
    }
    collect() {
        const now = Date.now();
        const usage = process.memoryUsage();
        this.addMetric('cpu', { timestamp: now, value: this.getCpuUsage(), unit: '%' });
        this.addMetric('memory', { timestamp: now, value: usage.rss, unit: 'bytes' });
        this.addMetric('heap', { timestamp: now, value: usage.heapUsed, unit: 'bytes' });
        this.addMetric('eventLoop', { timestamp: now, value: this.getEventLoopLag(), unit: 'ms' });
    }
    addMetric(category, point) {
        const arr = this.metrics[category];
        arr.push(point);
        if (arr.length > this.maxHistory)
            arr.shift();
    }
    getCpuUsage() {
        const cpus = os.cpus();
        let totalIdle = 0, totalTick = 0;
        for (const cpu of cpus) {
            for (const type in cpu.times) {
                totalTick += cpu.times[type];
            }
            totalIdle += cpu.times.idle;
        }
        return Math.round((1 - totalIdle / totalTick) * 100);
    }
    getEventLoopLag() {
        return 0;
    }
    getMetrics() {
        return {
            cpu: [...this.metrics.cpu],
            memory: [...this.metrics.memory],
            heap: [...this.metrics.heap],
            eventLoop: [...this.metrics.eventLoop],
        };
    }
    getLatest(category) {
        const arr = this.metrics[category];
        return arr.length > 0 ? arr[arr.length - 1] : undefined;
    }
}
exports.MetricsCollector = MetricsCollector;
//# sourceMappingURL=metrics.js.map
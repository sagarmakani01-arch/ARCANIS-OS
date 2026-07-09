# Profiler

The Profiler captures CPU and memory profiles to help identify performance bottlenecks and memory leaks.

## Features

- **CPU Profiling**: Sample-based profiling with function-level timing
- **Memory Profiling**: Heap allocation tracking and leak detection
- **Flame Graph Data**: Generate hierarchical flame graph data for visualization

## Usage

```typescript
import { Profiler } from '@arcanis/developer-tools';

const profiler = new Profiler({ samplingInterval: 5 });

// CPU profiling
profiler.cpu.start(5);
// ... run code
const cpuResult = profiler.cpu.stop();
console.log(`Samples: ${cpuResult.sampleCount}`);

// Memory profiling
profiler.memory.start(1000);
// ... run code  
const memResult = profiler.memory.stop();
console.log(`Heap: ${(memResult.heapUsed / 1024 / 1024).toFixed(2)} MB`);

// Full profile
const result = await profiler.profile('my-app');
```

## CLI

```bash
arcanis-dev profile --interval 5 app.js
```

## Key Types

| Type | Description |
|------|-------------|
| `CpuProfileResult` | Sample count, function stats, flame graph |
| `MemoryProfileResult` | Heap usage, allocations, leak candidates |
| `FunctionStats` | Self time, total time, call count per function |

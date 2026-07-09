// Performance Testing Module for ArcanisTesting Framework

import { TestRunner, TestRunnerOptions, createTestCase } from '../../core/testRunner';
import { assert } from '../../core/assertions';
import { generateId, delay, measurePerformance, calculateMean, calculateStandardDeviation } from '../../core/utilities';
import { TestCase, TestResult, TestType, TestMetadata, PerformanceMetrics, PerformanceMetric } from '../../core/types';
import { EventEmitter } from 'events';

export interface PerformanceTestOptions extends TestRunnerOptions {
  iterations?: number;
  warmupIterations?: number;
  concurrency?: number;
  rampUpTime?: number;
  thresholds?: PerformanceThresholds;
}

export interface PerformanceThresholds {
  responseTime: number;
  throughput: number;
  errorRate: number;
  cpuUsage: number;
  memoryUsage: number;
}

export interface PerformanceTestSuite {
  name: string;
  description?: string;
  tests: TestCase[];
  beforeAll?: () => Promise<void> | void;
  afterAll?: () => Promise<void> | void;
  beforeEach?: () => Promise<void> | void;
  afterEach?: () => Promise<void> | void;
}

export interface LoadTestConfig {
  duration: number;
  concurrency: number;
  rampUpTime: number;
  target: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: unknown;
}

export interface StressTestConfig {
  startConcurrency: number;
  endConcurrency: number;
  stepSize: number;
  stepDuration: number;
  target: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: unknown;
}

export interface SpikeTestConfig {
  normalConcurrency: number;
  spikeConcurrency: number;
  spikeDuration: number;
  normalDuration: number;
  totalDuration: number;
  target: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: unknown;
}

export interface SoakTestConfig {
  concurrency: number;
  duration: number;
  target: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: unknown;
}

export interface PerformanceResult {
  testId: string;
  testName: string;
  iterations: number;
  concurrency: number;
  metrics: PerformanceMetrics;
  timestamps: Date[];
  errors: Error[];
  status: 'passed' | 'failed';
}

export class PerformanceTestRunner extends EventEmitter {
  private runner: TestRunner;
  private suites: PerformanceTestSuite[] = [];
  private options: PerformanceTestOptions;
  private results: PerformanceResult[] = [];

  constructor(options: PerformanceTestOptions = {}) {
    super();
    this.options = {
      iterations: 100,
      warmupIterations: 10,
      concurrency: 1,
      rampUpTime: 0,
      thresholds: {
        responseTime: 200,
        throughput: 1000,
        errorRate: 0.01,
        cpuUsage: 80,
        memoryUsage: 80,
      },
      ...options,
    };
    this.runner = new TestRunner(options);
    
    this.runner.on('test:start', (test: TestCase) => this.emit('test:start', test));
    this.runner.on('test:pass', (result: TestResult) => this.emit('test:pass', result));
    this.runner.on('test:fail', (result: TestResult) => this.emit('test:fail', result));
    this.runner.on('test:error', (result: TestResult) => this.emit('test:error', result));
  }

  describe(name: string, fn: () => void, options?: Partial<PerformanceTestSuite>): void {
    const suite: PerformanceTestSuite = {
      name,
      tests: [],
      ...options,
    };

    this.suites.push(suite);
    fn();
  }

  it(name: string, fn: () => Promise<void> | void, options?: Partial<TestMetadata>): TestCase {
    const test = createTestCase(name, 'performance', fn, {
      timeout: this.options.timeout || 300000,
      ...options,
    });
    this.runner.addTest(test);
    return test;
  }

  test(name: string, fn: () => Promise<void> | void, options?: Partial<TestMetadata>): TestCase {
    return this.it(name, fn, options);
  }

  async measurePerformance(
    name: string,
    fn: () => Promise<void>,
    iterations: number = this.options.iterations || 100,
    concurrency: number = this.options.concurrency || 1
  ): Promise<PerformanceResult> {
    const timestamps: Date[] = [];
    const errors: Error[] = [];
    const durations: number[] = [];

    // Warmup
    const warmupIterations = this.options.warmupIterations || 10;
    for (let i = 0; i < warmupIterations; i++) {
      await fn();
    }

    // Actual measurement
    const startTime = performance.now();
    const promises: Promise<void>[] = [];

    for (let i = 0; i < iterations; i++) {
      const promise = (async () => {
        const start = performance.now();
        try {
          await fn();
          timestamps.push(new Date());
          durations.push(performance.now() - start);
        } catch (error) {
          errors.push(error as Error);
          timestamps.push(new Date());
          durations.push(performance.now() - start);
        }
      })();

      if (concurrency > 1) {
        promises.push(promise);
        if (promises.length >= concurrency) {
          await Promise.all(promises);
          promises.length = 0;
        }
      } else {
        await promise;
      }
    }

    if (promises.length > 0) {
      await Promise.all(promises);
    }

    const totalDuration = performance.now() - startTime;
    const metrics = this.calculateMetrics(durations, totalDuration, errors.length, iterations);

    const result: PerformanceResult = {
      testId: generateId(),
      testName: name,
      iterations,
      concurrency,
      metrics,
      timestamps,
      errors,
      status: this.checkThresholds(metrics) ? 'passed' : 'failed',
    };

    this.results.push(result);
    return result;
  }

  private calculateMetrics(
    durations: number[],
    totalDuration: number,
    errorCount: number,
    totalRequests: number
  ): PerformanceMetrics {
    const sorted = [...durations].sort((a, b) => a - b);

    return {
      responseTime: {
        avg: calculateMean(durations),
        min: sorted[0] || 0,
        max: sorted[sorted.length - 1] || 0,
        p50: sorted[Math.floor(sorted.length * 0.5)] || 0,
        p90: sorted[Math.floor(sorted.length * 0.9)] || 0,
        p95: sorted[Math.floor(sorted.length * 0.95)] || 0,
        p99: sorted[Math.floor(sorted.length * 0.99)] || 0,
      },
      throughput: {
        avg: totalRequests / (totalDuration / 1000),
        min: 0,
        max: 0,
        p50: 0,
        p90: 0,
        p95: 0,
        p99: 0,
      },
      errorRate: {
        avg: errorCount / totalRequests,
        min: 0,
        max: 0,
        p50: 0,
        p90: 0,
        p95: 0,
        p99: 0,
      },
      cpuUsage: {
        avg: 0,
        min: 0,
        max: 0,
        p50: 0,
        p90: 0,
        p95: 0,
        p99: 0,
      },
      memoryUsage: {
        avg: 0,
        min: 0,
        max: 0,
        p50: 0,
        p90: 0,
        p95: 0,
        p99: 0,
      },
    };
  }

  private checkThresholds(metrics: PerformanceMetrics): boolean {
    const thresholds = this.options.thresholds!;
    return (
      metrics.responseTime.avg <= thresholds.responseTime &&
      metrics.errorRate.avg <= thresholds.errorRate
    );
  }

  async runLoadTest(config: LoadTestConfig): Promise<PerformanceResult> {
    const iterations = Math.floor((config.duration / 1000) * config.concurrency);
    return this.measurePerformance(
      `Load Test: ${config.method} ${config.target}`,
      async () => {
        // Simulate HTTP request
        await delay(Math.random() * 100);
      },
      iterations,
      config.concurrency
    );
  }

  async runStressTest(config: StressTestConfig): Promise<PerformanceResult[]> {
    const results: PerformanceResult[] = [];
    const steps = Math.ceil((config.endConcurrency - config.startConcurrency) / config.stepSize);

    for (let i = 0; i <= steps; i++) {
      const concurrency = config.startConcurrency + i * config.stepSize;
      const iterations = Math.floor((config.stepDuration / 1000) * concurrency);

      const result = await this.measurePerformance(
        `Stress Test: ${config.method} ${config.target} (concurrency: ${concurrency})`,
        async () => {
          // Simulate HTTP request
          await delay(Math.random() * 100);
        },
        iterations,
        concurrency
      );

      results.push(result);
    }

    return results;
  }

  async runSpikeTest(config: SpikeTestConfig): Promise<PerformanceResult[]> {
    const results: PerformanceResult[] = [];

    // Normal load
    const normalIterations = Math.floor((config.normalDuration / 1000) * config.normalConcurrency);
    const normalResult = await this.measurePerformance(
      `Spike Test (Normal): ${config.method} ${config.target}`,
      async () => {
        await delay(Math.random() * 100);
      },
      normalIterations,
      config.normalConcurrency
    );
    results.push(normalResult);

    // Spike
    const spikeIterations = Math.floor((config.spikeDuration / 1000) * config.spikeConcurrency);
    const spikeResult = await this.measurePerformance(
      `Spike Test (Spike): ${config.method} ${config.target}`,
      async () => {
        await delay(Math.random() * 100);
      },
      spikeIterations,
      config.spikeConcurrency
    );
    results.push(spikeResult);

    // Return to normal
    const returnResult = await this.measurePerformance(
      `Spike Test (Return): ${config.method} ${config.target}`,
      async () => {
        await delay(Math.random() * 100);
      },
      normalIterations,
      config.normalConcurrency
    );
    results.push(returnResult);

    return results;
  }

  async runSoakTest(config: SoakTestConfig): Promise<PerformanceResult> {
    const iterations = Math.floor((config.duration / 1000) * config.concurrency);
    return this.measurePerformance(
      `Soak Test: ${config.method} ${config.target}`,
      async () => {
        await delay(Math.random() * 100);
      },
      iterations,
      config.concurrency
    );
  }

  async run(): Promise<TestResult[]> {
    console.log('Running performance tests...');

    for (const suite of this.suites) {
      if (suite.beforeAll) {
        await suite.beforeAll();
      }

      for (const test of suite.tests) {
        if (suite.beforeEach) {
          await suite.beforeEach();
        }

        await this.runner.runTest(test);

        if (suite.afterEach) {
          await suite.afterEach();
        }
      }

      if (suite.afterAll) {
        await suite.afterAll();
      }
    }

    return this.runner.getResults();
  }

  getResults(): TestResult[] {
    return this.runner.getResults();
  }

  getPerformanceResults(): PerformanceResult[] {
    return [...this.results];
  }

  getSummary() {
    return this.runner.getSummary();
  }

  generateReport(): string {
    let report = 'Performance Test Report\n';
    report += '======================\n\n';

    for (const result of this.results) {
      report += `Test: ${result.testName}\n`;
      report += `Status: ${result.status}\n`;
      report += `Iterations: ${result.iterations}\n`;
      report += `Concurrency: ${result.concurrency}\n`;
      report += `Errors: ${result.errors.length}\n`;
      report += `\nMetrics:\n`;
      report += `  Response Time:\n`;
      report += `    Avg: ${result.metrics.responseTime.avg.toFixed(2)}ms\n`;
      report += `    Min: ${result.metrics.responseTime.min.toFixed(2)}ms\n`;
      report += `    Max: ${result.metrics.responseTime.max.toFixed(2)}ms\n`;
      report += `    P50: ${result.metrics.responseTime.p50.toFixed(2)}ms\n`;
      report += `    P90: ${result.metrics.responseTime.p90.toFixed(2)}ms\n`;
      report += `    P95: ${result.metrics.responseTime.p95.toFixed(2)}ms\n`;
      report += `    P99: ${result.metrics.responseTime.p99.toFixed(2)}ms\n`;
      report += `  Throughput: ${result.metrics.throughput.avg.toFixed(2)} req/s\n`;
      report += `  Error Rate: ${(result.metrics.errorRate.avg * 100).toFixed(2)}%\n`;
      report += '\n';
    }

    return report;
  }
}

// Factory function for creating performance test runners
export const createPerformanceTestRunner = (options?: PerformanceTestOptions): PerformanceTestRunner => {
  return new PerformanceTestRunner(options);
};

// Helper function for creating load test configurations
export const createLoadTestConfig = (
  target: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
  options?: Partial<LoadTestConfig>
): LoadTestConfig => {
  return {
    duration: 60000,
    concurrency: 10,
    rampUpTime: 0,
    target,
    method,
    ...options,
  };
};

// Helper function for creating stress test configurations
export const createStressTestConfig = (
  target: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
  options?: Partial<StressTestConfig>
): StressTestConfig => {
  return {
    startConcurrency: 1,
    endConcurrency: 100,
    stepSize: 10,
    stepDuration: 10000,
    target,
    method,
    ...options,
  };
};

// Helper function for creating spike test configurations
export const createSpikeTestConfig = (
  target: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
  options?: Partial<SpikeTestConfig>
): SpikeTestConfig => {
  return {
    normalConcurrency: 10,
    spikeConcurrency: 100,
    spikeDuration: 5000,
    normalDuration: 10000,
    totalDuration: 30000,
    target,
    method,
    ...options,
  };
};

// Helper function for creating soak test configurations
export const createSoakTestConfig = (
  target: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
  options?: Partial<SoakTestConfig>
): SoakTestConfig => {
  return {
    concurrency: 10,
    duration: 3600000, // 1 hour
    target,
    method,
    ...options,
  };
};

// Benchmark utilities
export const benchmark = async (
  name: string,
  fn: () => Promise<void>,
  iterations: number = 100
): Promise<{ name: string; avg: number; min: number; max: number }> => {
  const result = await measurePerformance(fn, iterations);
  return {
    name,
    avg: result.avg,
    min: result.min,
    max: result.max,
  };
};

export const compareBenchmarks = (
  benchmarks: { name: string; avg: number }[]
): string => {
  const sorted = [...benchmarks].sort((a, b) => a.avg - b.avg);
  let report = 'Benchmark Comparison\n';
  report += '===================\n\n';
  
  sorted.forEach((b, index) => {
    const ratio = sorted[0].avg / b.avg;
    report += `${index + 1}. ${b.name}: ${b.avg.toFixed(2)}ms (${ratio.toFixed(2)}x)\n`;
  });

  return report;
};

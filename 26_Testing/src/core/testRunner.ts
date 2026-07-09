// Test Runner for ArcanisTesting Framework

import { EventEmitter } from 'events';
import { TestCase, TestResult, TestStatus, TestError, AssertionResult, TestMetadata, TestType } from './types';
import { generateId, formatDuration } from './utilities';
import { assert, AssertionError } from './assertions';

export interface TestRunnerOptions {
  timeout?: number;
  retries?: number;
  bail?: boolean;
  parallel?: boolean;
  maxWorkers?: number;
}

export interface TestRunnerEvents {
  'test:start': (test: TestCase) => void;
  'test:pass': (result: TestResult) => void;
  'test:fail': (result: TestResult) => void;
  'test:skip': (result: TestResult) => void;
  'test:error': (result: TestResult) => void;
  'suite:start': (name: string) => void;
  'suite:end': (name: string) => void;
}

export class TestRunner extends EventEmitter {
  private tests: TestCase[] = [];
  private results: TestResult[] = [];
  private options: TestRunnerOptions;

  constructor(options: TestRunnerOptions = {}) {
    super();
    this.options = {
      timeout: 5000,
      retries: 0,
      bail: false,
      parallel: false,
      maxWorkers: 4,
      ...options,
    };
  }

  addTest(test: TestCase): void {
    this.tests.push(test);
  }

  addTests(tests: TestCase[]): void {
    this.tests.push(...tests);
  }

  clearTests(): void {
    this.tests = [];
    this.results = [];
  }

  async runAll(): Promise<TestResult[]> {
    this.results = [];
    
    if (this.options.parallel) {
      await this.runParallel();
    } else {
      await this.runSequential();
    }

    return this.results;
  }

  private async runSequential(): Promise<void> {
    for (const test of this.tests) {
      if (this.options.bail && this.results.some(r => r.status === 'failed')) {
        break;
      }
      await this.runTest(test);
    }
  }

  private async runParallel(): Promise<void> {
    const chunks: TestCase[][] = [];
    const chunkSize = Math.ceil(this.tests.length / (this.options.maxWorkers || 4));
    
    for (let i = 0; i < this.tests.length; i += chunkSize) {
      chunks.push(this.tests.slice(i, i + chunkSize));
    }

    await Promise.all(chunks.map(chunk => this.runChunk(chunk)));
  }

  private async runChunk(tests: TestCase[]): Promise<void> {
    for (const test of tests) {
      if (this.options.bail && this.results.some(r => r.status === 'failed')) {
        break;
      }
      await this.runTest(test);
    }
  }

  async runTest(test: TestCase): Promise<TestResult> {
    const startTime = performance.now();
    this.emit('test:start', test);

    let status: TestStatus = 'passed';
    let error: TestError | undefined;
    let retries = 0;
    const maxRetries = test.metadata.retries || this.options.retries || 0;

    assert.clearResults();

    while (retries <= maxRetries) {
      try {
        if (test.setup) {
          await this.withTimeout(test.setup(), test.metadata.timeout || this.options.timeout!);
        }

        await this.withTimeout(test.execute(), test.metadata.timeout || this.options.timeout!);

        if (test.teardown) {
          await this.withTimeout(test.teardown(), test.metadata.timeout || this.options.timeout!);
        }

        status = 'passed';
        break;
      } catch (err) {
        if (err instanceof AssertionError) {
          error = {
            message: err.message,
            expected: err.expected,
            actual: err.actual,
          };
          status = 'failed';
        } else {
          error = {
            message: (err as Error).message,
            stack: (err as Error).stack,
          };
          status = 'error';
        }

        if (retries < maxRetries) {
          retries++;
          await new Promise(resolve => setTimeout(resolve, 100 * retries));
        }
      }
    }

    const duration = performance.now() - startTime;
    const assertions = assert.getResults();

    const result: TestResult = {
      id: generateId(),
      name: test.metadata.name,
      type: test.metadata.type,
      status,
      duration,
      error,
      assertions,
      metadata: test.metadata,
      timestamp: new Date(),
      logs: [],
    };

    this.results.push(result);

    if (status === 'passed') {
      this.emit('test:pass', result);
    } else if (status === 'failed') {
      this.emit('test:fail', result);
    } else if (status === 'error') {
      this.emit('test:error', result);
    }

    return result;
  }

  private async withTimeout<T>(promise: Promise<T>, timeout: number): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error(`Test timed out after ${formatDuration(timeout)}`));
      }, timeout);

      promise
        .then(result => {
          clearTimeout(timer);
          resolve(result);
        })
        .catch(err => {
          clearTimeout(timer);
          reject(err);
        });
    });
  }

  getResults(): TestResult[] {
    return [...this.results];
  }

  getSummary() {
    const total = this.results.length;
    const passed = this.results.filter(r => r.status === 'passed').length;
    const failed = this.results.filter(r => r.status === 'failed').length;
    const skipped = this.results.filter(r => r.status === 'skipped').length;
    const errors = this.results.filter(r => r.status === 'error').length;
    const duration = this.results.reduce((sum, r) => sum + r.duration, 0);

    return {
      total,
      passed,
      failed,
      skipped,
      errors,
      duration,
      successRate: total > 0 ? (passed / total) * 100 : 0,
    };
  }
}

// Factory function for creating test runners
export const createTestRunner = (options?: TestRunnerOptions): TestRunner => {
  return new TestRunner(options);
};

// Helper function for creating test cases
export const createTestCase = (
  name: string,
  type: TestType,
  execute: () => Promise<void> | void,
  options?: Partial<TestMetadata>
): TestCase => {
  return {
    metadata: {
      id: generateId(),
      name,
      type,
      priority: 'medium',
      tags: [],
      timeout: 5000,
      retries: 0,
      created: new Date(),
      ...options,
    },
    execute,
  };
};

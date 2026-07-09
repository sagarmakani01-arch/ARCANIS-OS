// Unit Testing Module for ArcanisTesting Framework

import { TestRunner, TestRunnerOptions, createTestCase } from '../../core/testRunner';
import { assert } from '../../core/assertions';
import { generateId, formatDuration } from '../../core/utilities';
import { TestCase, TestResult, TestType, TestMetadata } from '../../core/types';
import { EventEmitter } from 'events';

export interface UnitTestOptions extends TestRunnerOptions {
  coverage?: boolean;
  mockModules?: string[];
}

export interface UnitTestSuite {
  name: string;
  description?: string;
  tests: TestCase[];
  beforeEach?: () => Promise<void> | void;
  afterEach?: () => Promise<void> | void;
  beforeAll?: () => Promise<void> | void;
  afterAll?: () => Promise<void> | void;
}

export class UnitTestRunner extends EventEmitter {
  private runner: TestRunner;
  private suites: UnitTestSuite[] = [];
  private options: UnitTestOptions;

  constructor(options: UnitTestOptions = {}) {
    super();
    this.options = {
      coverage: true,
      mockModules: [],
      ...options,
    };
    this.runner = new TestRunner(options);
    
    this.runner.on('test:start', (test: TestCase) => this.emit('test:start', test));
    this.runner.on('test:pass', (result: TestResult) => this.emit('test:pass', result));
    this.runner.on('test:fail', (result: TestResult) => this.emit('test:fail', result));
    this.runner.on('test:error', (result: TestResult) => this.emit('test:error', result));
  }

  describe(name: string, fn: () => void, options?: Partial<UnitTestSuite>): void {
    const suite: UnitTestSuite = {
      name,
      tests: [],
      ...options,
    };

    const originalDescribe = global.describe;
    const originalIt = global.it;
    const originalBeforeEach = global.beforeEach;
    const originalAfterEach = global.afterEach;

    global.describe = (desc: string, descFn: () => void) => {
      const nestedSuite: UnitTestSuite = { name: desc, tests: [] };
      this.suites.push(nestedSuite);
      descFn();
    };

    global.it = (testName: string, testFn: () => Promise<void> | void, timeout?: number) => {
      const test = createTestCase(testName, 'unit', testFn, {
        timeout: timeout || this.options.timeout || 5000,
        tags: options?.name ? [options.name] : [],
      });
      suite.tests.push(test);
    };

    global.beforeEach = (fn: () => Promise<void> | void) => {
      suite.beforeEach = fn;
    };

    global.afterEach = (fn: () => Promise<void> | void) => {
      suite.afterEach = fn;
    };

    this.suites.push(suite);
    fn();

    global.describe = originalDescribe;
    global.it = originalIt;
    global.beforeEach = originalBeforeEach;
    global.afterEach = originalAfterEach;
  }

  it(name: string, fn: () => Promise<void> | void, timeout?: number): TestCase {
    const test = createTestCase(name, 'unit', fn, {
      timeout: timeout || this.options.timeout || 5000,
    });
    this.runner.addTest(test);
    return test;
  }

  test(name: string, fn: () => Promise<void> | void, timeout?: number): TestCase {
    return this.it(name, fn, timeout);
  }

  beforeEach(fn: () => Promise<void> | void): void {
    this.runner.on('test:start', async () => {
      await fn();
    });
  }

  afterEach(fn: () => Promise<void> | void): void {
    this.runner.on('test:pass', async () => {
      await fn();
    });
    this.runner.on('test:fail', async () => {
      await fn();
    });
  }

  async run(): Promise<TestResult[]> {
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

  getSummary() {
    return this.runner.getSummary();
  }

  // Utility methods for common test patterns
  mock<T>(implementation?: Partial<T>): T {
    const mockObj = {} as T;
    const keys = Object.keys(implementation || {}) as (keyof T)[];
    
    for (const key of keys) {
      const value = implementation?.[key];
      if (typeof value === 'function') {
        (mockObj as any)[key] = value;
      } else {
        (mockObj as any)[key] = value;
      }
    }

    return mockObj;
  }

  spy<T extends object>(obj: T, method: keyof T): jest.SpyInstance {
    const original = obj[method] as Function;
    const calls: unknown[][] = [];

    const spy = {
      calls,
      calledTimes: 0,
      calledWith: (...args: unknown[]) => calls.some(call => 
        call.length === args.length && call.every((arg, i) => arg === args[i])
      ),
      mockImplementation: (impl: Function) => {
        (obj as any)[method] = (...args: unknown[]) => {
          calls.push(args);
          spy.calledTimes++;
          return impl.apply(obj, args);
        };
      },
      restore: () => {
        (obj as any)[method] = original;
      },
    };

    spy.mockImplementation(original.bind(obj));
    return spy as jest.SpyInstance;
  }
}

// Factory function for creating unit test runners
export const createUnitTestRunner = (options?: UnitTestOptions): UnitTestRunner => {
  return new UnitTestRunner(options);
};

// Helper function for creating unit test suites
export const createUnitTestSuite = (
  name: string,
  fn: () => void,
  options?: Partial<UnitTestSuite>
): UnitTestSuite => {
  const suite: UnitTestSuite = {
    name,
    tests: [],
    ...options,
  };
  fn();
  return suite;
};

// Common test utilities
export const expect = assert;

export const describe = (name: string, fn: () => void) => {
  console.log(`\n  ${name}`);
  fn();
};

export const it = (name: string, fn: () => Promise<void> | void, timeout?: number) => {
  const start = performance.now();
  try {
    const result = fn();
    if (result instanceof Promise) {
      return result
        .then(() => {
          const duration = performance.now() - start;
          console.log(`    ✓ ${name} (${duration.toFixed(2)}ms)`);
        })
        .catch((err) => {
          const duration = performance.now() - start;
          console.log(`    ✗ ${name} (${duration.toFixed(2)}ms)`);
          console.log(`      ${err.message}`);
          throw err;
        });
    } else {
      const duration = performance.now() - start;
      console.log(`    ✓ ${name} (${duration.toFixed(2)}ms)`);
    }
  } catch (err) {
    const duration = performance.now() - start;
    console.log(`    ✗ ${name} (${duration.toFixed(2)}ms)`);
    console.log(`      ${(err as Error).message}`);
    throw err;
  }
};

export const beforeEach = (fn: () => Promise<void> | void) => {
  // This is a placeholder - in a real implementation, this would be hooked into the test runner
};

export const afterEach = (fn: () => Promise<void> | void) => {
  // This is a placeholder - in a real implementation, this would be hooked into the test runner
};

export const beforeAll = (fn: () => Promise<void> | void) => {
  // This is a placeholder - in a real implementation, this would be hooked into the test runner
};

export const afterAll = (fn: () => Promise<void> | void) => {
  // This is a placeholder - in a real implementation, this would be hooked into the test runner
};

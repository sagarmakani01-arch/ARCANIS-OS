// Integration Testing Module for ArcanisTesting Framework

import { TestRunner, TestRunnerOptions, createTestCase } from '../../core/testRunner';
import { assert } from '../../core/assertions';
import { generateId, delay, retry } from '../../core/utilities';
import { TestCase, TestResult, TestType, TestMetadata } from '../../core/types';
import { EventEmitter } from 'events';

export interface IntegrationTestOptions extends TestRunnerOptions {
  retries?: number;
  retryDelay?: number;
  cleanupAfterEach?: boolean;
  setupTimeout?: number;
  teardownTimeout?: number;
}

export interface IntegrationTestSuite {
  name: string;
  description?: string;
  tests: TestCase[];
  beforeAll?: () => Promise<void> | void;
  afterAll?: () => Promise<void> | void;
  beforeEach?: () => Promise<void> | void;
  afterEach?: () => Promise<void> | void;
}

export interface ExternalDependency {
  name: string;
  type: 'database' | 'api' | 'file' | 'queue' | 'cache' | 'custom';
  setup?: () => Promise<void> | void;
  teardown?: () => Promise<void> | void;
  healthCheck?: () => Promise<boolean>;
  isAvailable?: boolean;
}

export class IntegrationTestRunner extends EventEmitter {
  private runner: TestRunner;
  private suites: IntegrationTestSuite[] = [];
  private dependencies: ExternalDependency[] = [];
  private options: IntegrationTestOptions;

  constructor(options: IntegrationTestOptions = {}) {
    super();
    this.options = {
      retries: 3,
      retryDelay: 1000,
      cleanupAfterEach: true,
      setupTimeout: 10000,
      teardownTimeout: 5000,
      ...options,
    };
    this.runner = new TestRunner(options);
    
    this.runner.on('test:start', (test: TestCase) => this.emit('test:start', test));
    this.runner.on('test:pass', (result: TestResult) => this.emit('test:pass', result));
    this.runner.on('test:fail', (result: TestResult) => this.emit('test:fail', result));
    this.runner.on('test:error', (result: TestResult) => this.emit('test:error', result));
  }

  addDependency(dependency: ExternalDependency): void {
    this.dependencies.push(dependency);
  }

  addDependencies(dependencies: ExternalDependency[]): void {
    this.dependencies.push(...dependencies);
  }

  async checkDependencies(): Promise<boolean> {
    for (const dep of this.dependencies) {
      if (dep.healthCheck) {
        dep.isAvailable = await dep.healthCheck();
        if (!dep.isAvailable) {
          console.warn(`Dependency ${dep.name} is not available`);
          return false;
        }
      }
    }
    return true;
  }

  describe(name: string, fn: () => void, options?: Partial<IntegrationTestSuite>): void {
    const suite: IntegrationTestSuite = {
      name,
      tests: [],
      ...options,
    };

    this.suites.push(suite);
    fn();
  }

  it(name: string, fn: () => Promise<void> | void, options?: Partial<TestMetadata>): TestCase {
    const test = createTestCase(name, 'integration', fn, {
      timeout: this.options.timeout || 30000,
      retries: this.options.retries,
      ...options,
    });
    this.runner.addTest(test);
    return test;
  }

  test(name: string, fn: () => Promise<void> | void, options?: Partial<TestMetadata>): TestCase {
    return this.it(name, fn, options);
  }

  async withRetry<T>(
    fn: () => Promise<T>,
    maxRetries: number = this.options.retries || 3,
    delayMs: number = this.options.retryDelay || 1000
  ): Promise<T> {
    return retry(fn, maxRetries, delayMs);
  }

  async cleanup(): Promise<void> {
    if (this.options.cleanupAfterEach) {
      // Perform cleanup operations
      await delay(100);
    }
  }

  async setupDependencies(): Promise<void> {
    for (const dep of this.dependencies) {
      if (dep.setup) {
        await dep.setup();
      }
    }
  }

  async teardownDependencies(): Promise<void> {
    for (const dep of this.dependencies) {
      if (dep.teardown) {
        await dep.teardown();
      }
    }
  }

  async run(): Promise<TestResult[]> {
    // Check dependencies before running tests
    const depsAvailable = await this.checkDependencies();
    if (!depsAvailable) {
      console.warn('Some dependencies are not available. Tests may fail.');
    }

    // Setup dependencies
    await this.setupDependencies();

    // Run all suites
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

        // Cleanup after each test if enabled
        await this.cleanup();
      }

      if (suite.afterAll) {
        await suite.afterAll();
      }
    }

    // Teardown dependencies
    await this.teardownDependencies();

    return this.runner.getResults();
  }

  getResults(): TestResult[] {
    return this.runner.getResults();
  }

  getSummary() {
    return this.runner.getSummary();
  }

  getDependencyStatus(): { name: string; type: string; available: boolean }[] {
    return this.dependencies.map(dep => ({
      name: dep.name,
      type: dep.type,
      available: dep.isAvailable || false,
    }));
  }
}

// Factory function for creating integration test runners
export const createIntegrationTestRunner = (options?: IntegrationTestOptions): IntegrationTestRunner => {
  return new IntegrationTestRunner(options);
};

// Helper function for creating external dependencies
export const createDependency = (
  name: string,
  type: ExternalDependency['type'],
  options?: Partial<ExternalDependency>
): ExternalDependency => {
  return {
    name,
    type,
    ...options,
  };
};

// Database dependency helper
export const createDatabaseDependency = (
  name: string,
  connectionUrl: string,
  options?: Partial<ExternalDependency>
): ExternalDependency => {
  return createDependency(name, 'database', {
    setup: async () => {
      // Connect to database
      console.log(`Connecting to database: ${name}`);
    },
    teardown: async () => {
      // Disconnect from database
      console.log(`Disconnecting from database: ${name}`);
    },
    healthCheck: async () => {
      // Check database connection
      return true;
    },
    ...options,
  });
};

// API dependency helper
export const createApiDependency = (
  name: string,
  baseUrl: string,
  options?: Partial<ExternalDependency>
): ExternalDependency => {
  return createDependency(name, 'api', {
    setup: async () => {
      // Setup API client
      console.log(`Setting up API: ${name}`);
    },
    teardown: async () => {
      // Cleanup API client
      console.log(`Cleaning up API: ${name}`);
    },
    healthCheck: async () => {
      // Check API health
      return true;
    },
    ...options,
  });
};

// File dependency helper
export const createFileDependency = (
  name: string,
  filePath: string,
  options?: Partial<ExternalDependency>
): ExternalDependency => {
  return createDependency(name, 'file', {
    setup: async () => {
      // Setup file system
      console.log(`Setting up file: ${name}`);
    },
    teardown: async () => {
      // Cleanup file system
      console.log(`Cleaning up file: ${name}`);
    },
    ...options,
  });
};

// Queue dependency helper
export const createQueueDependency = (
  name: string,
  queueUrl: string,
  options?: Partial<ExternalDependency>
): ExternalDependency => {
  return createDependency(name, 'queue', {
    setup: async () => {
      // Setup queue connection
      console.log(`Setting up queue: ${name}`);
    },
    teardown: async () => {
      // Cleanup queue connection
      console.log(`Cleaning up queue: ${name}`);
    },
    healthCheck: async () => {
      // Check queue health
      return true;
    },
    ...options,
  });
};

// Cache dependency helper
export const createCacheDependency = (
  name: string,
  cacheUrl: string,
  options?: Partial<ExternalDependency>
): ExternalDependency => {
  return createDependency(name, 'cache', {
    setup: async () => {
      // Setup cache connection
      console.log(`Setting up cache: ${name}`);
    },
    teardown: async () => {
      // Cleanup cache connection
      console.log(`Cleaning up cache: ${name}`);
    },
    healthCheck: async () => {
      // Check cache health
      return true;
    },
    ...options,
  });
};

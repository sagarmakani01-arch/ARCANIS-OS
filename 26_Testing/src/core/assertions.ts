// Assertions module for ArcanisTesting Framework

export class AssertionError extends Error {
  constructor(
    message: string,
    public readonly expected?: unknown,
    public readonly actual?: unknown,
    public readonly operator?: string
  ) {
    super(message);
    this.name = 'AssertionError';
  }
}

export class Assertions {
  private results: { passed: boolean; message: string; duration: number }[] = [];

  private addResult(passed: boolean, message: string, duration: number) {
    this.results.push({ passed, message, duration });
    if (!passed) {
      throw new AssertionError(message);
    }
  }

  getResults() {
    return [...this.results];
  }

  clearResults() {
    this.results = [];
  }

  // Value assertions
  equal<T>(actual: T, expected: T, message?: string): void {
    const start = performance.now();
    const passed = actual === expected;
    const duration = performance.now() - start;
    const msg = message || `Expected ${JSON.stringify(actual)} to equal ${JSON.stringify(expected)}`;
    this.addResult(passed, msg, duration);
  }

  notEqual<T>(actual: T, expected: T, message?: string): void {
    const start = performance.now();
    const passed = actual !== expected;
    const duration = performance.now() - start;
    const msg = message || `Expected ${JSON.stringify(actual)} to not equal ${JSON.stringify(expected)}`;
    this.addResult(passed, msg, duration);
  }

  deepEqual<T>(actual: T, expected: T, message?: string): void {
    const start = performance.now();
    const passed = JSON.stringify(actual) === JSON.stringify(expected);
    const duration = performance.now() - start;
    const msg = message || `Expected ${JSON.stringify(actual)} to deeply equal ${JSON.stringify(expected)}`;
    this.addResult(passed, msg, duration);
  }

  // Boolean assertions
  isTrue(value: boolean, message?: string): void {
    const start = performance.now();
    const passed = value === true;
    const duration = performance.now() - start;
    const msg = message || `Expected ${value} to be true`;
    this.addResult(passed, msg, duration);
  }

  isFalse(value: boolean, message?: string): void {
    const start = performance.now();
    const passed = value === false;
    const duration = performance.now() - start;
    const msg = message || `Expected ${value} to be false`;
    this.addResult(passed, msg, duration);
  }

  // Null/Undefined assertions
  isNull(value: unknown, message?: string): void {
    const start = performance.now();
    const passed = value === null;
    const duration = performance.now() - start;
    const msg = message || `Expected ${value} to be null`;
    this.addResult(passed, msg, duration);
  }

  isNotNull(value: unknown, message?: string): void {
    const start = performance.now();
    const passed = value !== null;
    const duration = performance.now() - start;
    const msg = message || `Expected ${value} to not be null`;
    this.addResult(passed, msg, duration);
  }

  isUndefined(value: unknown, message?: string): void {
    const start = performance.now();
    const passed = value === undefined;
    const duration = performance.now() - start;
    const msg = message || `Expected ${value} to be undefined`;
    this.addResult(passed, msg, duration);
  }

  isDefined(value: unknown, message?: string): void {
    const start = performance.now();
    const passed = value !== undefined;
    const duration = performance.now() - start;
    const msg = message || `Expected ${value} to be defined`;
    this.addResult(passed, msg, duration);
  }

  // Type assertions
  isTypeOf(value: unknown, type: string, message?: string): void {
    const start = performance.now();
    const passed = typeof value === type;
    const duration = performance.now() - start;
    const msg = message || `Expected ${value} to be of type ${type}`;
    this.addResult(passed, msg, duration);
  }

  instanceOf<T>(value: unknown, type: new (...args: unknown[]) => T, message?: string): void {
    const start = performance.now();
    const passed = value instanceof type;
    const duration = performance.now() - start;
    const msg = message || `Expected ${value} to be an instance of ${type.name}`;
    this.addResult(passed, msg, duration);
  }

  // Collection assertions
  contains<T>(array: T[], item: T, message?: string): void {
    const start = performance.now();
    const passed = array.includes(item);
    const duration = performance.now() - start;
    const msg = message || `Expected array to contain ${JSON.stringify(item)}`;
    this.addResult(passed, msg, duration);
  }

  hasLength<T>(collection: T[] | string, length: number, message?: string): void {
    const start = performance.now();
    const passed = collection.length === length;
    const duration = performance.now() - start;
    const msg = message || `Expected collection to have length ${length}, but got ${collection.length}`;
    this.addResult(passed, msg, duration);
  }

  isEmpty<T>(collection: T[] | string, message?: string): void {
    const start = performance.now();
    const passed = collection.length === 0;
    const duration = performance.now() - start;
    const msg = message || `Expected collection to be empty`;
    this.addResult(passed, msg, duration);
  }

  // Range assertions
  greaterThan(actual: number, expected: number, message?: string): void {
    const start = performance.now();
    const passed = actual > expected;
    const duration = performance.now() - start;
    const msg = message || `Expected ${actual} to be greater than ${expected}`;
    this.addResult(passed, msg, duration);
  }

  lessThan(actual: number, expected: number, message?: string): void {
    const start = performance.now();
    const passed = actual < expected;
    const duration = performance.now() - start;
    const msg = message || `Expected ${actual} to be less than ${expected}`;
    this.addResult(passed, msg, duration);
  }

  greaterThanOrEqual(actual: number, expected: number, message?: string): void {
    const start = performance.now();
    const passed = actual >= expected;
    const duration = performance.now() - start;
    const msg = message || `Expected ${actual} to be greater than or equal to ${expected}`;
    this.addResult(passed, msg, duration);
  }

  lessThanOrEqual(actual: number, expected: number, message?: string): void {
    const start = performance.now();
    const passed = actual <= expected;
    const duration = performance.now() - start;
    const msg = message || `Expected ${actual} to be less than or equal to ${expected}`;
    this.addResult(passed, msg, duration);
  }

  // String assertions
  containsString(actual: string, expected: string, message?: string): void {
    const start = performance.now();
    const passed = actual.includes(expected);
    const duration = performance.now() - start;
    const msg = message || `Expected "${actual}" to contain "${expected}"`;
    this.addResult(passed, msg, duration);
  }

  matches(actual: string, pattern: RegExp, message?: string): void {
    const start = performance.now();
    const passed = pattern.test(actual);
    const duration = performance.now() - start;
    const msg = message || `Expected "${actual}" to match ${pattern}`;
    this.addResult(passed, msg, duration);
  }

  // Exception assertions
  async throwsAsync(
    fn: () => Promise<void>,
    expectedError?: new (...args: unknown[]) => Error,
    message?: string
  ): Promise<void> {
    const start = performance.now();
    try {
      await fn();
      const duration = performance.now() - start;
      this.addResult(false, message || 'Expected function to throw', duration);
    } catch (error) {
      const duration = performance.now() - start;
      if (expectedError && !(error instanceof expectedError)) {
        this.addResult(
          false,
          message || `Expected ${expectedError.name} to be thrown, but got ${(error as Error).name}`,
          duration
        );
      } else {
        this.addResult(true, message || 'Function threw as expected', duration);
      }
    }
  }

  // Approximate equality for floating point
  approximately(actual: number, expected: number, delta: number, message?: string): void {
    const start = performance.now();
    const passed = Math.abs(actual - expected) <= delta;
    const duration = performance.now() - start;
    const msg = message || `Expected ${actual} to be approximately ${expected} (±${delta})`;
    this.addResult(passed, msg, duration);
  }

  // Snapshot testing
  toMatchSnapshot(actual: unknown, expected: unknown, message?: string): void {
    const start = performance.now();
    const passed = JSON.stringify(actual, Object.keys(actual as object).sort()) === 
                   JSON.stringify(expected, Object.keys(expected as object).sort());
    const duration = performance.now() - start;
    const msg = message || `Snapshot mismatch`;
    this.addResult(passed, msg, duration);
  }
}

// Global assertions instance
export const assert = new Assertions();

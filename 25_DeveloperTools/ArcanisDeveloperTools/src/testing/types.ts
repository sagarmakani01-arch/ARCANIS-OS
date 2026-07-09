export type TestStatus = 'passed' | 'failed' | 'skipped' | 'running';

export interface TestCase {
  name: string;
  fn: () => void | Promise<void>;
  status: TestStatus;
  error?: Error;
  duration: number;
}

export interface TestSuite {
  name: string;
  tests: TestCase[];
  beforeAll?: () => void | Promise<void>;
  afterAll?: () => void | Promise<void>;
  beforeEach?: () => void | Promise<void>;
  afterEach?: () => void | Promise<void>;
}

export interface TestResult {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  duration: number;
  suites: TestSuiteResult[];
}

export interface TestSuiteResult {
  name: string;
  total: number;
  passed: number;
  failed: number;
  duration: number;
  tests: TestCaseResult[];
}

export interface TestCaseResult {
  name: string;
  status: TestStatus;
  error?: string;
  duration: number;
}

export interface Mock {
  calls: unknown[][];
  returns: unknown;
  implementation?: (...args: unknown[]) => unknown;
}

export interface AssertionError {
  message: string;
  expected: unknown;
  actual: unknown;
}

import { TestRunner } from './runner.js';
import { assert, equal, deepEqual, throws, expect } from './assert.js';
import { createMock, spyOn } from './mock.js';
import { TestResult, TestCase, TestSuite, TestCaseResult, TestSuiteResult, Mock } from './types.js';

export { TestRunner, assert, equal, deepEqual, throws, expect, createMock, spyOn };
export type { TestResult, TestCase, TestSuite, TestCaseResult, TestSuiteResult, Mock };

export class TestingTools {
  readonly runner: TestRunner;

  constructor() {
    this.runner = new TestRunner();
  }

  async runTests(suiteName: string, testFn: () => void): Promise<TestResult> {
    this.runner.describe(suiteName, testFn);
    return this.runner.run();
  }

  assert = assert;
  equal = equal;
  deepEqual = deepEqual;
  throws = throws;
  expect = expect;
  createMock = createMock;
  spyOn = spyOn;
}

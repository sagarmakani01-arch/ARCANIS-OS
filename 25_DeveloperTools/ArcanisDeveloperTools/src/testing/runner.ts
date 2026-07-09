import { TestCase, TestResult, TestSuite, TestSuiteResult, TestCaseResult } from './types.js';

export class TestRunner {
  private suites: TestSuite[] = [];
  private currentSuite: TestSuite | null = null;

  describe(name: string, fn: () => void): void {
    this.currentSuite = { name, tests: [] };
    fn();
    if (this.currentSuite) {
      this.suites.push(this.currentSuite);
    }
    this.currentSuite = null;
  }

  it(name: string, fn: () => void | Promise<void>): void {
    if (this.currentSuite) {
      this.currentSuite.tests.push({ name, fn, status: 'running', duration: 0 });
    }
  }

  async run(): Promise<TestResult> {
    const start = Date.now();
    const suiteResults: TestSuiteResult[] = [];

    for (const suite of this.suites) {
      const suiteStart = Date.now();
      const testResults: TestCaseResult[] = [];

      if (suite.beforeAll) await suite.beforeAll();

      for (const test of suite.tests) {
        const testStart = Date.now();
        try {
          if (suite.beforeEach) await suite.beforeEach();
          await test.fn();
          test.status = 'passed';
          if (suite.afterEach) await suite.afterEach();
        } catch (err) {
          test.status = 'failed';
          test.error = err as Error;
        }
        test.duration = Date.now() - testStart;
        testResults.push({
          name: test.name,
          status: test.status,
          error: test.error?.message,
          duration: test.duration,
        });
      }

      if (suite.afterAll) await suite.afterAll();

      suiteResults.push({
        name: suite.name,
        total: testResults.length,
        passed: testResults.filter(t => t.status === 'passed').length,
        failed: testResults.filter(t => t.status === 'failed').length,
        duration: Date.now() - suiteStart,
        tests: testResults,
      });
    }

    const total = suiteResults.reduce((a, s) => a + s.total, 0);
    const passed = suiteResults.reduce((a, s) => a + s.passed, 0);
    const failed = suiteResults.reduce((a, s) => a + s.failed, 0);

    return {
      total,
      passed,
      failed,
      skipped: 0,
      duration: Date.now() - start,
      suites: suiteResults,
    };
  }
}

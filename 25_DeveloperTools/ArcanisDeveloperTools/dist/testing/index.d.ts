import { TestRunner } from './runner.js';
import { assert, equal, deepEqual, throws, expect } from './assert.js';
import { createMock, spyOn } from './mock.js';
import { TestResult, TestCase, TestSuite, TestCaseResult, TestSuiteResult, Mock } from './types.js';
export { TestRunner, assert, equal, deepEqual, throws, expect, createMock, spyOn };
export type { TestResult, TestCase, TestSuite, TestCaseResult, TestSuiteResult, Mock };
export declare class TestingTools {
    readonly runner: TestRunner;
    constructor();
    runTests(suiteName: string, testFn: () => void): Promise<TestResult>;
    assert: typeof assert;
    equal: typeof equal;
    deepEqual: typeof deepEqual;
    throws: typeof throws;
    expect: {
        toBe: <T>(actual: T, expected: T) => void;
        toEqual: <T>(actual: T, expected: T) => void;
        toBeTruthy: (actual: unknown) => void;
        toBeFalsy: (actual: unknown) => void;
        toThrow: (fn: () => void, msg?: string) => void;
        toBeDefined: (actual: unknown) => void;
        toBeNull: (actual: unknown) => void;
    };
    createMock: typeof createMock;
    spyOn: typeof spyOn;
}

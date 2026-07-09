import { TestResult } from './types.js';
export declare class TestRunner {
    private suites;
    private currentSuite;
    describe(name: string, fn: () => void): void;
    it(name: string, fn: () => void | Promise<void>): void;
    run(): Promise<TestResult>;
}

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.expect = void 0;
exports.assert = assert;
exports.equal = equal;
exports.deepEqual = deepEqual;
exports.throws = throws;
exports.notNull = notNull;
function assert(condition, message) {
    if (!condition)
        throw new Error(message || 'Assertion failed');
}
function equal(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(message || `Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
    }
}
function deepEqual(actual, expected, message) {
    if (JSON.stringify(actual) !== JSON.stringify(expected)) {
        throw new Error(message || `Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
    }
}
function throws(fn, expectedMessage) {
    try {
        fn();
        throw new Error('Expected function to throw');
    }
    catch (err) {
        if (expectedMessage && !err.message.includes(expectedMessage)) {
            throw new Error(`Expected error to include "${expectedMessage}", got "${err.message}"`);
        }
    }
}
function notNull(value, message) {
    if (value == null)
        throw new Error(message || 'Expected value to be non-null');
    return value;
}
exports.expect = {
    toBe: (actual, expected) => equal(actual, expected),
    toEqual: (actual, expected) => deepEqual(actual, expected),
    toBeTruthy: (actual) => assert(!!actual, 'Expected truthy'),
    toBeFalsy: (actual) => assert(!actual, 'Expected falsy'),
    toThrow: (fn, msg) => throws(fn, msg),
    toBeDefined: (actual) => assert(actual !== undefined, 'Expected defined'),
    toBeNull: (actual) => assert(actual === null, `Expected null, got ${actual}`),
};
//# sourceMappingURL=assert.js.map
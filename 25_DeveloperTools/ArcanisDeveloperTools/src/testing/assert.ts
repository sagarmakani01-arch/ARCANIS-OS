export function assert(condition: boolean, message?: string): void {
  if (!condition) throw new Error(message || 'Assertion failed');
}

export function equal<T>(actual: T, expected: T, message?: string): void {
  if (actual !== expected) {
    throw new Error(message || `Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

export function deepEqual<T>(actual: T, expected: T, message?: string): void {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(message || `Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

export function throws(fn: () => void, expectedMessage?: string): void {
  try {
    fn();
    throw new Error('Expected function to throw');
  } catch (err) {
    if (expectedMessage && !(err as Error).message.includes(expectedMessage)) {
      throw new Error(`Expected error to include "${expectedMessage}", got "${(err as Error).message}"`);
    }
  }
}

export function notNull<T>(value: T | null | undefined, message?: string): T {
  if (value == null) throw new Error(message || 'Expected value to be non-null');
  return value;
}

export const expect = {
  toBe: <T>(actual: T, expected: T) => equal(actual, expected),
  toEqual: <T>(actual: T, expected: T) => deepEqual(actual, expected),
  toBeTruthy: (actual: unknown) => assert(!!actual, 'Expected truthy'),
  toBeFalsy: (actual: unknown) => assert(!actual, 'Expected falsy'),
  toThrow: (fn: () => void, msg?: string) => throws(fn, msg),
  toBeDefined: (actual: unknown) => assert(actual !== undefined, 'Expected defined'),
  toBeNull: (actual: unknown) => assert(actual === null, `Expected null, got ${actual}`),
};

export declare function assert(condition: boolean, message?: string): void;
export declare function equal<T>(actual: T, expected: T, message?: string): void;
export declare function deepEqual<T>(actual: T, expected: T, message?: string): void;
export declare function throws(fn: () => void, expectedMessage?: string): void;
export declare function notNull<T>(value: T | null | undefined, message?: string): T;
export declare const expect: {
    toBe: <T>(actual: T, expected: T) => void;
    toEqual: <T>(actual: T, expected: T) => void;
    toBeTruthy: (actual: unknown) => void;
    toBeFalsy: (actual: unknown) => void;
    toThrow: (fn: () => void, msg?: string) => void;
    toBeDefined: (actual: unknown) => void;
    toBeNull: (actual: unknown) => void;
};

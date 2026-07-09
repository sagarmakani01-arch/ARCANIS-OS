import { Mock } from './types.js';
export declare function createMock<T extends (...args: unknown[]) => unknown>(implementation?: T): T & Mock;
export declare function spyOn<T extends Record<string, unknown>, K extends keyof T>(obj: T, method: K): T[K] & Mock;

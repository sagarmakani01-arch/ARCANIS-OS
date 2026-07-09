import { Mock } from './types.js';

export function createMock<T extends (...args: unknown[]) => unknown>(implementation?: T): T & Mock {
  const mock: Mock = { calls: [], returns: undefined };
  const fn = ((...args: unknown[]) => {
    mock.calls.push(args);
    const result = mock.implementation ? mock.implementation(...args) : mock.returns;
    return result;
  }) as unknown as T & Mock;

  mock.calls = [];
  Object.defineProperty(fn, 'calls', { get: () => mock.calls });
  Object.defineProperty(fn, 'returns', {
    get: () => mock.returns,
    set: (v: unknown) => { mock.returns = v; },
  });
  Object.defineProperty(fn, 'implementation', {
    get: () => mock.implementation,
    set: (v: ((...args: unknown[]) => unknown) | undefined) => { mock.implementation = v; },
  });

  return fn;
}

export function spyOn<T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  method: K,
): T[K] & Mock {
  const original = obj[method] as unknown as (...args: unknown[]) => unknown;
  const mock = createMock(original);
  obj[method] = mock as unknown as T[K];
  return mock as unknown as T[K] & Mock;
}

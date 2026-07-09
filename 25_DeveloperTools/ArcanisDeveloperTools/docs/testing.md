# Testing Tools

A built-in test runner with assertions and mocking capabilities.

## Features

- **Test Runner**: Describe/it pattern with before/after hooks
- **Assertions**: `assert`, `equal`, `deepEqual`, `throws`, and chained `expect`
- **Mocking**: `createMock` and `spyOn` for function stubbing
- **Result Reporting**: Structured test results with pass/fail counts

## Usage

```typescript
import { TestingTools, expect } from '@arcanis/developer-tools';

const tools = new TestingTools();

// Test runner
tools.runner.describe('Calculator', () => {
  tools.runner.it('should add numbers', () => {
    expect.toBe(2 + 2, 4);
  });

  tools.runner.it('should throw on division by zero', () => {
    expect.toThrow(() => { divide(1, 0); });
  });
});

const result = await tools.runner.run();
console.log(`${result.passed}/${result.total} passed`);

// Assertions
import { assert, equal, deepEqual, throws, expect } from '@arcanis/developer-tools';
assert(true);
equal(1 + 1, 2);
deepEqual({ a: 1 }, { a: 1 });
throws(() => { throw new Error('fail'); });
expect.toBe('hello', 'hello');

// Mocking
import { createMock, spyOn } from '@arcanis/developer-tools';
const mockFn = createMock();
mockFn.returns = 42;
mockFn('hello');
console.log(mockFn.calls); // [['hello']]
```

## CLI

```bash
arcanis-dev test tests/
arcanis-dev test tests/unit/ tests/integration/
```

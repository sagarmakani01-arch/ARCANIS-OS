# Debugger

The Debugger provides breakpoint management, stack trace parsing, and variable inspection for Arcanis applications.

## Features

- **Breakpoint Manager**: Set, remove, toggle, and conditionally trigger breakpoints
- **Stack Trace Parser**: Parse and format stack traces from errors
- **Variable Inspection**: Inspect and modify runtime variables
- **Step Controls**: Step over, into, and out of function calls

## Usage

```typescript
import { Debugger } from '@arcanis/developer-tools';

const debugger_ = new Debugger({ port: 9229 });

// Manage breakpoints
debugger_.breakpoints.setBreakpoint('src/app.ts', 42);
debugger_.breakpoints.setBreakpoint('src/app.ts', 50, (state) => {
  return state.variables['x'] > 100;
});

// List breakpoints
debugger_.breakpoints.listBreakpoints();

// Parse stack traces
const frames = debugger_.stackTrace.parse(error.stack);
console.log(debugger_.stackTrace.format(frames));
```

## CLI

```bash
arcanis-dev debug --port 9229 app.js
```

## API

### BreakpointManager

| Method | Description |
|--------|-------------|
| `setBreakpoint(file, line, condition?)` | Create a breakpoint |
| `removeBreakpoint(id)` | Remove by ID |
| `toggleBreakpoint(id)` | Enable/disable |
| `clearAll()` | Remove all breakpoints |
| `evaluate(state)` | Check if breakpoint is hit |
| `listBreakpoints()` | Return all breakpoints |

### StackTraceParser

| Method | Description |
|--------|-------------|
| `parse(errorStack)` | Parse error stack to frames |
| `format(stack)` | Format frames as readable string |
| `capture()` | Capture current stack trace |

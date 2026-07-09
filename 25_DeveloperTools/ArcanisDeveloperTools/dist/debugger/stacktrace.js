"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StackTraceParser = void 0;
class StackTraceParser {
    parse(errorStack) {
        const lines = errorStack.split('\n').filter(l => l.includes('at '));
        return lines.map(line => {
            const match = line.match(/at\s+(?:(.+?)\s+\()?(?:(.+?):(\d+):(\d+)\)?)/);
            if (match) {
                return {
                    functionName: match[1] || '<anonymous>',
                    file: match[2],
                    line: parseInt(match[3], 10),
                    column: parseInt(match[4], 10),
                    locals: {},
                };
            }
            return {
                functionName: '<unknown>',
                file: '<unknown>',
                line: 0,
                column: 0,
                locals: {},
            };
        });
    }
    format(stack) {
        return stack
            .map(f => `  at ${f.functionName} (${f.file}:${f.line}:${f.column})`)
            .join('\n');
    }
    async capture() {
        return this.parse(new Error().stack || '');
    }
}
exports.StackTraceParser = StackTraceParser;
//# sourceMappingURL=stacktrace.js.map
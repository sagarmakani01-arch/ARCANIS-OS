"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ErrorReporter = exports.CompilerError = void 0;
exports.createCompilerError = createCompilerError;
const types_1 = require("./types");
class CompilerError extends Error {
    constructor(stage, message, range, hints = []) {
        super(message);
        this.stage = stage;
        this.range = range;
        this.hints = hints;
        this.name = 'CompilerError';
    }
    toDiagnostic() {
        return {
            severity: types_1.Severity.Error,
            message: this.message,
            range: this.range,
            hints: this.hints,
        };
    }
}
exports.CompilerError = CompilerError;
class ErrorReporter {
    constructor() {
        this.diagnostics = [];
        this.sourceCache = new Map();
    }
    setSource(sourceId, content) {
        this.sourceCache.set(sourceId, content.split('\n'));
    }
    report(diagnostic) {
        this.diagnostics.push(diagnostic);
    }
    error(stage, message, range, hints = []) {
        this.report({
            severity: types_1.Severity.Error,
            message,
            range,
            hints,
        });
    }
    warning(stage, message, range, hints = []) {
        this.report({
            severity: types_1.Severity.Warning,
            message,
            range,
            hints,
        });
    }
    info(stage, message, range) {
        this.report({
            severity: types_1.Severity.Info,
            message,
            range,
        });
    }
    getDiagnostics() {
        return [...this.diagnostics];
    }
    hasErrors() {
        return this.diagnostics.some((d) => d.severity === types_1.Severity.Error);
    }
    formatDiagnostic(diagnostic) {
        const parts = [];
        const severityTag = diagnostic.severity.toUpperCase();
        parts.push(`[${severityTag}]`);
        if (diagnostic.range) {
            const r = diagnostic.range;
            const loc = `${r.sourceId}:${r.start.line}:${r.start.column}`;
            parts.push(loc);
            parts.push(diagnostic.message);
            const lines = this.sourceCache.get(r.sourceId);
            if (lines && r.start.line > 0 && r.start.line <= lines.length) {
                const line = lines[r.start.line - 1];
                parts.push(`  | ${line}`);
                const underline = ' '.repeat(r.start.column - 1) + '^'.repeat(Math.max(1, r.end.column - r.start.column));
                parts.push(`  | ${underline}`);
            }
        }
        else {
            parts.push(diagnostic.message);
        }
        if (diagnostic.hints && diagnostic.hints.length > 0) {
            for (const hint of diagnostic.hints) {
                parts.push(`  Hint: ${hint}`);
            }
        }
        return parts.join('\n');
    }
    formatAll() {
        return this.diagnostics.map((d) => this.formatDiagnostic(d)).join('\n\n');
    }
    clear() {
        this.diagnostics = [];
        this.sourceCache.clear();
    }
}
exports.ErrorReporter = ErrorReporter;
function createCompilerError(stage, message, range, hints) {
    return new CompilerError(stage, message, range, hints);
}
//# sourceMappingURL=error.js.map
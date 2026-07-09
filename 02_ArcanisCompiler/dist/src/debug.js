"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DebugInfoBuilder = void 0;
exports.formatDebugInfo = formatDebugInfo;
class DebugInfoBuilder {
    constructor() {
        this.lineMappings = [];
        this.variables = [];
        this.functions = [];
    }
    addLineMapping(sourceLine, sourceColumn, outputOffset, outputLine) {
        this.lineMappings.push({ sourceLine, sourceColumn, outputOffset, outputLine });
    }
    addVariable(name, type, scope, sourceLocation) {
        this.variables.push({ name, type, scope, sourceLocation });
    }
    addFunction(name, sourceLocation) {
        this.functions.push({ name, sourceLocation, lineMappings: [] });
    }
    build(sourceId) {
        return {
            sourceId,
            lineMap: this.lineMappings,
            variables: this.variables,
            functions: this.functions,
        };
    }
    clear() {
        this.lineMappings = [];
        this.variables = [];
        this.functions = [];
    }
}
exports.DebugInfoBuilder = DebugInfoBuilder;
function formatDebugInfo(info) {
    const parts = [`Debug info for: ${info.sourceId}`];
    if (info.functions.length > 0) {
        parts.push('\nFunctions:');
        for (const fn of info.functions) {
            parts.push(`  ${fn.name} at ${fn.sourceLocation.start.line}:${fn.sourceLocation.start.column}`);
        }
    }
    if (info.variables.length > 0) {
        parts.push('\nVariables:');
        for (const v of info.variables) {
            parts.push(`  ${v.name}: ${v.type} (scope: ${v.scope})`);
        }
    }
    return parts.join('\n');
}
//# sourceMappingURL=debug.js.map
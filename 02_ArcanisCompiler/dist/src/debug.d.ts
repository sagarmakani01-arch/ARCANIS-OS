import { SourceRange } from './types';
export interface DebugInfo {
    sourceId: string;
    lineMap: LineMapping[];
    variables: VariableDebugInfo[];
    functions: FunctionDebugInfo[];
}
export interface LineMapping {
    sourceLine: number;
    sourceColumn: number;
    outputOffset: number;
    outputLine: number;
}
export interface VariableDebugInfo {
    name: string;
    type: string;
    scope: string;
    sourceLocation: SourceRange;
}
export interface FunctionDebugInfo {
    name: string;
    sourceLocation: SourceRange;
    lineMappings: LineMapping[];
}
export declare class DebugInfoBuilder {
    private lineMappings;
    private variables;
    private functions;
    addLineMapping(sourceLine: number, sourceColumn: number, outputOffset: number, outputLine: number): void;
    addVariable(name: string, type: string, scope: string, sourceLocation: SourceRange): void;
    addFunction(name: string, sourceLocation: SourceRange): void;
    build(sourceId: string): DebugInfo;
    clear(): void;
}
export declare function formatDebugInfo(info: DebugInfo): string;
//# sourceMappingURL=debug.d.ts.map
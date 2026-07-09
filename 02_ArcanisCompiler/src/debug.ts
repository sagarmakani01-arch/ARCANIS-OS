import { SourceLocation, SourceRange } from './types';

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

export class DebugInfoBuilder {
  private lineMappings: LineMapping[] = [];
  private variables: VariableDebugInfo[] = [];
  private functions: FunctionDebugInfo[] = [];

  addLineMapping(
    sourceLine: number,
    sourceColumn: number,
    outputOffset: number,
    outputLine: number,
  ): void {
    this.lineMappings.push({ sourceLine, sourceColumn, outputOffset, outputLine });
  }

  addVariable(name: string, type: string, scope: string, sourceLocation: SourceRange): void {
    this.variables.push({ name, type, scope, sourceLocation });
  }

  addFunction(name: string, sourceLocation: SourceRange): void {
    this.functions.push({ name, sourceLocation, lineMappings: [] });
  }

  build(sourceId: string): DebugInfo {
    return {
      sourceId,
      lineMap: this.lineMappings,
      variables: this.variables,
      functions: this.functions,
    };
  }

  clear(): void {
    this.lineMappings = [];
    this.variables = [];
    this.functions = [];
  }
}

export function formatDebugInfo(info: DebugInfo): string {
  const parts: string[] = [`Debug info for: ${info.sourceId}`];

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

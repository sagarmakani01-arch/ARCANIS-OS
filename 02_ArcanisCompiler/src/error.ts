import { SourceRange, CompilerDiagnostic, Severity, CompilerStage } from './types';

export class CompilerError extends Error {
  constructor(
    public readonly stage: CompilerStage,
    message: string,
    public readonly range?: SourceRange,
    public readonly hints: string[] = [],
  ) {
    super(message);
    this.name = 'CompilerError';
  }

  toDiagnostic(): CompilerDiagnostic {
    return {
      severity: Severity.Error,
      message: this.message,
      range: this.range,
      hints: this.hints,
    };
  }
}

export class ErrorReporter {
  private diagnostics: CompilerDiagnostic[] = [];
  private sourceCache: Map<string, string[]> = new Map();

  setSource(sourceId: string, content: string): void {
    this.sourceCache.set(sourceId, content.split('\n'));
  }

  report(diagnostic: CompilerDiagnostic): void {
    this.diagnostics.push(diagnostic);
  }

  error(stage: CompilerStage, message: string, range?: SourceRange, hints: string[] = []): void {
    this.report({
      severity: Severity.Error,
      message,
      range,
      hints,
    });
  }

  warning(stage: CompilerStage, message: string, range?: SourceRange, hints: string[] = []): void {
    this.report({
      severity: Severity.Warning,
      message,
      range,
      hints,
    });
  }

  info(stage: CompilerStage, message: string, range?: SourceRange): void {
    this.report({
      severity: Severity.Info,
      message,
      range,
    });
  }

  getDiagnostics(): CompilerDiagnostic[] {
    return [...this.diagnostics];
  }

  hasErrors(): boolean {
    return this.diagnostics.some((d) => d.severity === Severity.Error);
  }

  formatDiagnostic(diagnostic: CompilerDiagnostic): string {
    const parts: string[] = [];

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
    } else {
      parts.push(diagnostic.message);
    }

    if (diagnostic.hints && diagnostic.hints.length > 0) {
      for (const hint of diagnostic.hints) {
        parts.push(`  Hint: ${hint}`);
      }
    }

    return parts.join('\n');
  }

  formatAll(): string {
    return this.diagnostics.map((d) => this.formatDiagnostic(d)).join('\n\n');
  }

  clear(): void {
    this.diagnostics = [];
    this.sourceCache.clear();
  }
}

export function createCompilerError(
  stage: CompilerStage,
  message: string,
  range?: SourceRange,
  hints?: string[],
): CompilerError {
  return new CompilerError(stage, message, range, hints);
}

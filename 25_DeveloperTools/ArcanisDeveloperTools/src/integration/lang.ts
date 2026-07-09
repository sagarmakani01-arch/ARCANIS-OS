export class ArcanisLangIntegration {
  readonly name = '@arcanis/developer-tools-lang';
  readonly version = '0.1.0';

  async provideCompletions(context: { file: string; line: number; column: number; prefix: string }): Promise<string[]> {
    console.log(`[Lang] Providing completions for ${context.file}:${context.line}`);
    return [];
  }

  async provideDiagnostics(source: string, filePath: string): Promise<Diagnostic[]> {
    console.log(`[Lang] Diagnosing ${filePath}`);
    return [];
  }

  async provideHover(context: { file: string; line: number; column: number }): Promise<string | null> {
    console.log(`[Lang] Hover info for ${context.file}:${context.line}`);
    return null;
  }

  async provideDefinition(context: { file: string; line: number; column: number }): Promise<{ file: string; line: number; column: number } | null> {
    console.log(`[Lang] Definition lookup for ${context.file}:${context.line}`);
    return null;
  }

  getLanguageFeatures(): string[] {
    return ['completions', 'diagnostics', 'hover', 'goToDefinition'];
  }
}

export interface Diagnostic {
  file: string;
  line: number;
  column: number;
  endLine: number;
  endColumn: number;
  severity: 'error' | 'warning' | 'information' | 'hint';
  message: string;
  code: string;
}

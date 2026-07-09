export declare class ArcanisLangIntegration {
    readonly name = "@arcanis/developer-tools-lang";
    readonly version = "0.1.0";
    provideCompletions(context: {
        file: string;
        line: number;
        column: number;
        prefix: string;
    }): Promise<string[]>;
    provideDiagnostics(source: string, filePath: string): Promise<Diagnostic[]>;
    provideHover(context: {
        file: string;
        line: number;
        column: number;
    }): Promise<string | null>;
    provideDefinition(context: {
        file: string;
        line: number;
        column: number;
    }): Promise<{
        file: string;
        line: number;
        column: number;
    } | null>;
    getLanguageFeatures(): string[];
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

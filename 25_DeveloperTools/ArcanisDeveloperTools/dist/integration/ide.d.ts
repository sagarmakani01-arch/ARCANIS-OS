export interface IDEExtensionPoint {
    name: string;
    version: string;
    hooks: string[];
    activate(): Promise<void>;
    deactivate(): Promise<void>;
}
export declare class ArcanisIDEIntegration {
    readonly name = "@arcanis/developer-tools-ide";
    readonly version = "0.1.0";
    readonly hooks: string[];
    activate(): Promise<void>;
    deactivate(): Promise<void>;
    private registerDebuggerPanel;
    private registerProfilerView;
    private registerAnalyzerPanel;
    private registerTestRunner;
}

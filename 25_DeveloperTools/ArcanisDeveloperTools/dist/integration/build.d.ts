export declare class ArcanisBuildIntegration {
    readonly name = "@arcanis/developer-tools-build";
    readonly version = "0.1.0";
    beforeBuild(projectRoot: string): Promise<void>;
    afterBuild(projectRoot: string): Promise<void>;
    runAnalysisPipeline(projectRoot: string): Promise<void>;
    private lint;
    private checkTypes;
    private measureCoverage;
    getBuildHooks(): string[];
}

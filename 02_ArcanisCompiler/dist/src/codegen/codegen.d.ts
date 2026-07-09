import { Program } from '../parser/ast';
import { DebugInfoBuilder } from '../debug';
export interface CodeGenTarget {
    generate(program: Program, debugInfo?: DebugInfoBuilder): string;
    name(): string;
}
export declare class JavaScriptCodeGen implements CodeGenTarget {
    private indentLevel;
    private sourceId;
    private debugInfo?;
    private varCounter;
    constructor(sourceId?: string);
    name(): string;
    generate(program: Program, debugInfo?: DebugInfoBuilder): string;
    private generatePreamble;
    private generateFunction;
    private generateParam;
    private generateBlockBody;
    private generateStmt;
    private generateVarDecl;
    private generateIfStmt;
    private generateWhileStmt;
    private generateStmtCode;
    private generateExpr;
    private generateUnary;
    private generateBinary;
    private generateCall;
    private indent;
}
//# sourceMappingURL=codegen.d.ts.map
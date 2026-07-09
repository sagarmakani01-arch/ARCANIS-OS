import { Program } from '../parser/ast';
export declare class Optimizer {
    private changes;
    optimize(program: Program): Program;
    getChangeCount(): number;
    private optimizeFunction;
    private optimizeStmt;
    private optimizeVarDecl;
    private optimizeBlock;
    private optimizeIfStmt;
    private optimizeWhileStmt;
    private optimizeExpr;
    private optimizeBinary;
    private optimizeUnary;
}
//# sourceMappingURL=optimizer.d.ts.map
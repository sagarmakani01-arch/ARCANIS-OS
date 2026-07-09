import { Program } from '../parser/ast';
import { ErrorReporter } from '../error';
export declare class TypeChecker {
    private errors;
    private sourceId;
    constructor(sourceId: string, errors: ErrorReporter);
    check(program: Program): void;
    private checkStmt;
    private checkVarDecl;
    private checkBlockStmt;
    private checkIfStmt;
    private checkWhileStmt;
    private checkReturnStmt;
    private checkExpr;
    private checkIdentifier;
    private checkUnary;
    private checkBinary;
    private checkCall;
}
//# sourceMappingURL=checker.d.ts.map
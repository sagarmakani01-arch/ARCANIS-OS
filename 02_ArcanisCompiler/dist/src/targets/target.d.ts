import { Program } from '../parser/ast';
import { DebugInfoBuilder } from '../debug';
export interface Target {
    name: string;
    description: string;
    fileExtension: string;
    generate(program: Program, debugInfo?: DebugInfoBuilder): string;
}
export declare function listTargets(): Target[];
export declare function getTarget(name: string): Target | undefined;
//# sourceMappingURL=target.d.ts.map
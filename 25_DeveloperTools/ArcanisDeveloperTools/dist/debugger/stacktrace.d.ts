import { StackFrame } from './types.js';
export declare class StackTraceParser {
    parse(errorStack: string): StackFrame[];
    format(stack: StackFrame[]): string;
    capture(): Promise<StackFrame[]>;
}

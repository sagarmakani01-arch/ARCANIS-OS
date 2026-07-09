import { Program } from '../parser/ast';
import { DebugInfoBuilder } from '../debug';

export interface Target {
  name: string;
  description: string;
  fileExtension: string;
  generate(program: Program, debugInfo?: DebugInfoBuilder): string;
}

export function listTargets(): Target[] {
  return [
    {
      name: 'js',
      description: 'JavaScript (Node.js)',
      fileExtension: '.js',
      generate: (program, debugInfo) => {
        // Lazy import to avoid circular dependency
        const { JavaScriptCodeGen } = require('../codegen/codegen');
        const codegen = new JavaScriptCodeGen();
        return codegen.generate(program, debugInfo);
      },
    },
    {
      name: 'wasm',
      description: 'WebAssembly (future target)',
      fileExtension: '.wasm',
      generate: () => {
        throw new Error('WASM target is not yet implemented');
      },
    },
    {
      name: 'llvm',
      description: 'LLVM IR (future target)',
      fileExtension: '.ll',
      generate: () => {
        throw new Error('LLVM target is not yet implemented');
      },
    },
    {
      name: 'x86',
      description: 'x86-64 assembly (future target)',
      fileExtension: '.s',
      generate: () => {
        throw new Error('x86 target is not yet implemented');
      },
    },
  ];
}

export function getTarget(name: string): Target | undefined {
  return listTargets().find((t) => t.name === name);
}

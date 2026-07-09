#!/usr/bin/env node
import { Compiler } from './compiler';
import { listTargets } from './targets/target';
import * as fs from 'fs';
import * as path from 'path';

function printUsage(): void {
  console.log('ArcanisCompiler v0.1.0');
  console.log('Usage: arcanic [options] <file.arc>');
  console.log('');
  console.log('Options:');
  console.log('  -o, --out <file>       Output file (default: stdout)');
  console.log('  -t, --target <name>    Target output (default: js)');
  console.log('  -O, --optimize         Enable optimizations (default: on)');
  console.log('  -O0                    Disable optimizations');
  console.log('  -g, --debug            Enable debug information');
  console.log('  --emit <stage>         Only run up to a specific stage');
  console.log('  --list-targets         List available targets');
  console.log('  --help                 Show this help');
  console.log('');
  console.log('Stages: lexing, parsing, ast_generation, type_checking, optimization, code_generation');
}

function printTargets(): void {
  console.log('Available targets:');
  for (const target of listTargets()) {
    console.log(`  ${target.name.padEnd(10)} ${target.description} (${target.fileExtension})`);
  }
}

function main(): void {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('--help')) {
    printUsage();
    process.exit(0);
  }

  if (args.includes('--list-targets')) {
    printTargets();
    process.exit(0);
  }

  let inputFile: string | null = null;
  let outputFile: string | null = null;
  let target = 'js';
  let enableOptimizations = true;
  let enableDebugInfo = false;
  let emitOnly: string | null = null;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '-o' || arg === '--out') {
      outputFile = args[++i];
    } else if (arg === '-t' || arg === '--target') {
      target = args[++i];
    } else if (arg === '-O0') {
      enableOptimizations = false;
    } else if (arg === '-O' || arg === '--optimize') {
      enableOptimizations = true;
    } else if (arg === '-g' || arg === '--debug') {
      enableDebugInfo = true;
    } else if (arg === '--emit') {
      emitOnly = args[++i];
    } else if (!arg.startsWith('-')) {
      inputFile = arg;
    }
  }

  if (!inputFile) {
    console.error('Error: No input file specified');
    printUsage();
    process.exit(1);
  }

  // Read source
  let source: string;
  try {
    source = fs.readFileSync(inputFile, 'utf-8');
  } catch (e: any) {
    console.error(`Error reading file '${inputFile}': ${e.message}`);
    process.exit(1);
  }

  const sourceId = path.basename(inputFile);

  // Compile
  const compiler = new Compiler();
  compiler.setSource(source, sourceId);

  const allowedStages = emitOnly ? [emitOnly as any] : undefined;

  const result = compiler.compile({
    target,
    enableOptimizations,
    enableDebugInfo,
    emitOnly: allowedStages,
  });

  // Report diagnostics
  if (result.diagnostics.length > 0) {
    const reporter = compiler.getErrorReporter();
    console.error(reporter.formatAll());
  }

  // Output
  if (result.success && result.output) {
    if (outputFile) {
      try {
        fs.writeFileSync(outputFile, result.output, 'utf-8');
        console.log(`Written to ${outputFile}`);
      } catch (e: any) {
        console.error(`Error writing to '${outputFile}': ${e.message}`);
        process.exit(1);
      }
    } else {
      console.log(result.output);
    }
  }

  // Show debug info
  if (enableDebugInfo && result.debugInfo) {
    const { formatDebugInfo } = require('./debug');
    console.error('\n' + formatDebugInfo(result.debugInfo));
  }

  process.exit(result.success ? 0 : 1);
}

main();

#!/usr/bin/env node
"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const compiler_1 = require("./compiler");
const target_1 = require("./targets/target");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
function printUsage() {
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
function printTargets() {
    console.log('Available targets:');
    for (const target of (0, target_1.listTargets)()) {
        console.log(`  ${target.name.padEnd(10)} ${target.description} (${target.fileExtension})`);
    }
}
function main() {
    const args = process.argv.slice(2);
    if (args.length === 0 || args.includes('--help')) {
        printUsage();
        process.exit(0);
    }
    if (args.includes('--list-targets')) {
        printTargets();
        process.exit(0);
    }
    let inputFile = null;
    let outputFile = null;
    let target = 'js';
    let enableOptimizations = true;
    let enableDebugInfo = false;
    let emitOnly = null;
    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg === '-o' || arg === '--out') {
            outputFile = args[++i];
        }
        else if (arg === '-t' || arg === '--target') {
            target = args[++i];
        }
        else if (arg === '-O0') {
            enableOptimizations = false;
        }
        else if (arg === '-O' || arg === '--optimize') {
            enableOptimizations = true;
        }
        else if (arg === '-g' || arg === '--debug') {
            enableDebugInfo = true;
        }
        else if (arg === '--emit') {
            emitOnly = args[++i];
        }
        else if (!arg.startsWith('-')) {
            inputFile = arg;
        }
    }
    if (!inputFile) {
        console.error('Error: No input file specified');
        printUsage();
        process.exit(1);
    }
    // Read source
    let source;
    try {
        source = fs.readFileSync(inputFile, 'utf-8');
    }
    catch (e) {
        console.error(`Error reading file '${inputFile}': ${e.message}`);
        process.exit(1);
    }
    const sourceId = path.basename(inputFile);
    // Compile
    const compiler = new compiler_1.Compiler();
    compiler.setSource(source, sourceId);
    const allowedStages = emitOnly ? [emitOnly] : undefined;
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
            }
            catch (e) {
                console.error(`Error writing to '${outputFile}': ${e.message}`);
                process.exit(1);
            }
        }
        else {
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
//# sourceMappingURL=cli.js.map
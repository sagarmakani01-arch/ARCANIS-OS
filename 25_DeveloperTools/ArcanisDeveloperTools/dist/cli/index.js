#!/usr/bin/env node
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const commander_1 = require("commander");
const fs_1 = require("fs");
const path_1 = require("path");
const index_js_1 = require("../debugger/index.js");
const index_js_2 = require("../profiler/index.js");
const index_js_3 = require("../analyzer/index.js");
const index_js_4 = require("../docgen/index.js");
const index_js_5 = require("../testing/index.js");
const index_js_6 = require("../perfmon/index.js");
function walkDir(dir, ext, files = []) {
    const entries = (0, fs_1.readdirSync)(dir, { withFileTypes: true });
    for (const entry of entries) {
        const full = (0, path_1.join)(dir, entry.name);
        if (entry.isDirectory() && !entry.name.startsWith('.') && !entry.name.startsWith('node_modules')) {
            walkDir(full, ext, files);
        }
        else if (entry.isFile() && entry.name.endsWith(ext)) {
            files.push(full);
        }
    }
    return files;
}
function loadSourceFiles(patterns) {
    const files = new Map();
    for (const pattern of patterns) {
        try {
            const stat = (0, fs_1.statSync)(pattern);
            if (stat.isDirectory()) {
                const tsFiles = walkDir(pattern, '.ts');
                tsFiles.forEach(f => files.set(f, (0, fs_1.readFileSync)(f, 'utf-8')));
            }
            else if (stat.isFile()) {
                files.set(pattern, (0, fs_1.readFileSync)(pattern, 'utf-8'));
            }
        }
        catch {
            console.error(`Cannot read: ${pattern}`);
        }
    }
    return files;
}
const program = new commander_1.Command();
program
    .name('arcanis-dev')
    .description('Arcanis Developer Tools - CLI')
    .version('0.1.0');
program.command('debug')
    .description('Start the debugger')
    .option('-p, --port <port>', 'Debug port', '9229')
    .option('-h, --host <host>', 'Debug host', '127.0.0.1')
    .argument('[target]', 'Target to debug (script path or process id)')
    .action(async (target, opts) => {
    const debugger_ = new index_js_1.Debugger({ port: parseInt(opts.port), host: opts.host });
    await debugger_.attach(target || 'unknown');
    console.log('Breakpoints:', debugger_.breakpoints.listBreakpoints().length);
});
program.command('profile')
    .description('Profile CPU and memory usage')
    .option('-i, --interval <ms>', 'Sampling interval in ms', '1')
    .argument('[target]', 'Target to profile')
    .action(async (target, opts) => {
    const profiler = new index_js_2.Profiler({ samplingInterval: parseInt(opts.interval) });
    const result = await profiler.profile(target || 'application');
    console.log(`CPU samples: ${result.cpu.sampleCount}`);
    console.log(`Heap used: ${(result.memory.heapUsed / 1024 / 1024).toFixed(2)} MB`);
    console.log(`Leaks detected: ${result.memory.leaks.length}`);
});
program.command('analyze')
    .description('Analyze source code for issues and complexity')
    .argument('[files...]', 'Files or directories to analyze')
    .action(async (files) => {
    const patterns = files.length > 0 ? files : ['.'];
    const sources = loadSourceFiles(patterns);
    const analyzer = new index_js_3.CodeAnalyzer();
    let totalIssues = 0;
    for (const [filePath, source] of sources) {
        const result = await analyzer.analyzeFile(filePath, source);
        if (result.issues.length > 0) {
            console.log(`\n${filePath}:`);
            for (const issue of result.issues) {
                console.log(`  [${issue.severity}] ${issue.rule}: ${issue.message} (line ${issue.line})`);
                totalIssues++;
            }
        }
        console.log(`  Complexity: ${result.complexity.cyclomaticComplexity} (cyclomatic), ${result.complexity.linesOfCode} LOC`);
    }
    console.log(`\nTotal: ${totalIssues} issues found`);
});
program.command('docgen')
    .description('Generate documentation from source code')
    .option('-o, --output <dir>', 'Output directory', './docs')
    .option('-f, --format <format>', 'Output format (markdown|html)', 'markdown')
    .argument('[files...]', 'Files or directories to document')
    .action(async (files, opts) => {
    const patterns = files.length > 0 ? files : ['.'];
    const sources = loadSourceFiles(patterns);
    const docgen = new index_js_4.DocumentationGenerator({ outputDir: opts.output, format: opts.format });
    const pages = await docgen.generate(sources);
    const rendered = docgen.render(pages);
    rendered.forEach((content, i) => {
        const ext = opts.format === 'html' ? 'html' : 'md';
        const outPath = (0, path_1.join)(opts.output, `api-${i + 1}.${ext}`);
        (0, fs_1.mkdirSync)((0, path_1.dirname)(outPath), { recursive: true });
        (0, fs_1.writeFileSync)(outPath, content, 'utf-8');
        console.log(`Generated: ${outPath}`);
    });
    console.log(`Documentation generated for ${pages.length} files`);
});
program.command('test')
    .description('Run tests')
    .option('--watch', 'Watch mode')
    .argument('[files...]', 'Test files to run')
    .action(async (files, opts) => {
    const runner = new index_js_5.TestRunner();
    const patterns = files.length > 0 ? files : ['./src'];
    const sources = loadSourceFiles(patterns);
    console.log(`Running tests for ${sources.size} files...`);
    for (const [filePath, source] of sources) {
        if (filePath.includes('.test.') || filePath.includes('.spec.')) {
            runner.describe((0, path_1.relative)(process.cwd(), filePath), () => { });
        }
    }
    const result = await runner.run();
    console.log(`\nResults: ${result.passed} passed, ${result.failed} failed, ${result.total} total (${result.duration}ms)`);
});
program.command('perfmon')
    .description('Start performance monitoring')
    .option('-i, --interval <ms>', 'Monitoring interval', '1000')
    .option('-t, --timeout <ms>', 'Monitoring duration (0 = unlimited)', '0')
    .action(async (opts) => {
    const monitor = new index_js_6.PerformanceMonitor({ intervalMs: parseInt(opts.interval) });
    monitor.start();
    const duration = parseInt(opts.timeout);
    if (duration > 0) {
        await new Promise(resolve => setTimeout(resolve, duration));
        monitor.stop();
    }
    const metrics = monitor.metrics.getMetrics();
    const latestCpu = metrics.cpu[metrics.cpu.length - 1];
    const latestMem = metrics.memory[metrics.memory.length - 1];
    console.log(`CPU: ${latestCpu?.value ?? 'N/A'}%`);
    console.log(`Memory: ${latestMem ? `${(latestMem.value / 1024 / 1024).toFixed(2)} MB` : 'N/A'}`);
    console.log(`Alerts: ${monitor.getAlerts().length}`);
});
program.parse(process.argv);
//# sourceMappingURL=index.js.map
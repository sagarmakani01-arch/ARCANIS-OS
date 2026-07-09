#!/usr/bin/env node
import { Command } from 'commander';
import { readFileSync, writeFileSync, readdirSync, statSync, mkdirSync } from 'fs';
import { join, relative, dirname } from 'path';

import { Debugger } from '../debugger/index.js';
import { Profiler } from '../profiler/index.js';
import { CodeAnalyzer } from '../analyzer/index.js';
import { DocumentationGenerator } from '../docgen/index.js';
import { TestRunner } from '../testing/index.js';
import { PerformanceMonitor } from '../perfmon/index.js';

function walkDir(dir: string, ext: string, files: string[] = []): string[] {
  const entries = readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (entry.isDirectory() && !entry.name.startsWith('.') && !entry.name.startsWith('node_modules')) {
      walkDir(full, ext, files);
    } else if (entry.isFile() && entry.name.endsWith(ext)) {
      files.push(full);
    }
  }
  return files;
}

function loadSourceFiles(patterns: string[]): Map<string, string> {
  const files = new Map<string, string>();
  for (const pattern of patterns) {
    try {
      const stat = statSync(pattern);
      if (stat.isDirectory()) {
        const tsFiles = walkDir(pattern, '.ts');
        tsFiles.forEach(f => files.set(f, readFileSync(f, 'utf-8')));
      } else if (stat.isFile()) {
        files.set(pattern, readFileSync(pattern, 'utf-8'));
      }
    } catch {
      console.error(`Cannot read: ${pattern}`);
    }
  }
  return files;
}

const program = new Command();

program
  .name('arcanis-dev')
  .description('Arcanis Developer Tools - CLI')
  .version('0.1.0');

program.command('debug')
  .description('Start the debugger')
  .option('-p, --port <port>', 'Debug port', '9229')
  .option('-h, --host <host>', 'Debug host', '127.0.0.1')
  .argument('[target]', 'Target to debug (script path or process id)')
  .action(async (target: string | undefined, opts: { port: string; host: string }) => {
    const debugger_ = new Debugger({ port: parseInt(opts.port), host: opts.host });
    await debugger_.attach(target || 'unknown');
    console.log('Breakpoints:', debugger_.breakpoints.listBreakpoints().length);
  });

program.command('profile')
  .description('Profile CPU and memory usage')
  .option('-i, --interval <ms>', 'Sampling interval in ms', '1')
  .argument('[target]', 'Target to profile')
  .action(async (target: string | undefined, opts: { interval: string }) => {
    const profiler = new Profiler({ samplingInterval: parseInt(opts.interval) });
    const result = await profiler.profile(target || 'application');
    console.log(`CPU samples: ${result.cpu.sampleCount}`);
    console.log(`Heap used: ${(result.memory.heapUsed / 1024 / 1024).toFixed(2)} MB`);
    console.log(`Leaks detected: ${result.memory.leaks.length}`);
  });

program.command('analyze')
  .description('Analyze source code for issues and complexity')
  .argument('[files...]', 'Files or directories to analyze')
  .action(async (files: string[]) => {
    const patterns = files.length > 0 ? files : ['.'];
    const sources = loadSourceFiles(patterns);
    const analyzer = new CodeAnalyzer();
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
  .action(async (files: string[], opts: { output: string; format: string }) => {
    const patterns = files.length > 0 ? files : ['.'];
    const sources = loadSourceFiles(patterns);
    const docgen = new DocumentationGenerator({ outputDir: opts.output, format: opts.format as 'markdown' | 'html' });
    const pages = await docgen.generate(sources);
    const rendered = docgen.render(pages);

    rendered.forEach((content, i) => {
      const ext = opts.format === 'html' ? 'html' : 'md';
      const outPath = join(opts.output, `api-${i + 1}.${ext}`);
      mkdirSync(dirname(outPath), { recursive: true });
      writeFileSync(outPath, content, 'utf-8');
      console.log(`Generated: ${outPath}`);
    });
    console.log(`Documentation generated for ${pages.length} files`);
  });

program.command('test')
  .description('Run tests')
  .option('--watch', 'Watch mode')
  .argument('[files...]', 'Test files to run')
  .action(async (files: string[], opts: { watch: boolean }) => {
    const runner = new TestRunner();
    const patterns = files.length > 0 ? files : ['./src'];
    const sources = loadSourceFiles(patterns);

    console.log(`Running tests for ${sources.size} files...`);
    for (const [filePath, source] of sources) {
      if (filePath.includes('.test.') || filePath.includes('.spec.')) {
        runner.describe(relative(process.cwd(), filePath), () => {});
      }
    }

    const result = await runner.run();
    console.log(`\nResults: ${result.passed} passed, ${result.failed} failed, ${result.total} total (${result.duration}ms)`);
  });

program.command('perfmon')
  .description('Start performance monitoring')
  .option('-i, --interval <ms>', 'Monitoring interval', '1000')
  .option('-t, --timeout <ms>', 'Monitoring duration (0 = unlimited)', '0')
  .action(async (opts: { interval: string; timeout: string }) => {
    const monitor = new PerformanceMonitor({ intervalMs: parseInt(opts.interval) });
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

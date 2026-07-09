import { exec, ExecOptions } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import { BuildConfig } from '../api/types';
import { EventBus } from '../core/EventBus';
import { Configuration } from '../core/Configuration';

const execAsync = promisify(exec);

export interface BuildError {
  message: string;
  file?: string;
  line?: number;
  column?: number;
  code?: string;
}

export interface BuildWarning {
  message: string;
  file?: string;
  line?: number;
  code?: string;
}

export interface BuildResult {
  success: boolean;
  target: string;
  mode: string;
  duration: number;
  output: string;
  errors: BuildError[];
  warnings: BuildWarning[];
}

export interface TestCase {
  name: string;
  suite: string;
  status: 'passed' | 'failed' | 'skipped';
  duration: number;
  error?: string;
}

export interface TestResult {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  duration: number;
  tests: TestCase[];
}

export class BuildSystem {
  private config: BuildConfig;
  private cwd: string;
  private compilerPath: string;
  private buildToolPath: string;

  constructor(
    private eventBus: EventBus,
    private configuration: Configuration
  ) {
    this.config = {
      target: configuration.get<string>('build.defaultTarget', 'wasm32'),
      mode: configuration.get<'debug' | 'release'>('build.defaultMode', 'debug'),
      optimize: false,
      outputDir: 'build',
      sourceDir: 'src',
      compilerFlags: [],
    };
    this.cwd = configuration.get<string>('workspace.root', process.cwd());
    this.compilerPath = configuration.get<string>('build.compilerPath', 'python -m src.cli');
    this.buildToolPath = configuration.get<string>('build.toolPath', 'arcanis-build');
  }

  private async runCommand(cmd: string, options?: ExecOptions): Promise<{ stdout: string; stderr: string; exitCode: number }> {
    try {
      const result = await execAsync(cmd, {
        cwd: this.cwd,
        timeout: 120000,
        maxBuffer: 5 * 1024 * 1024,
        ...options,
      });
      return { stdout: result.stdout, stderr: result.stderr, exitCode: 0 };
    } catch (err: any) {
      return {
        stdout: err.stdout || '',
        stderr: err.stderr || err.message,
        exitCode: err.code || 1,
      };
    }
  }

  private parseErrors(output: string): BuildError[] {
    const errors: BuildError[] = [];
    const errorPattern = /(?:error|Error)[\s:]+(.+?)(?:\s+at\s+(.+?)(?::(\d+))?(?::(\d+))?)?$/gm;
    let match;
    while ((match = errorPattern.exec(output)) !== null) {
      errors.push({
        message: match[1].trim(),
        file: match[2],
        line: match[3] ? parseInt(match[3]) : undefined,
        column: match[4] ? parseInt(match[4]) : undefined,
      });
    }
    return errors;
  }

  private parseWarnings(output: string): BuildWarning[] {
    const warnings: BuildWarning[] = [];
    const warningPattern = /(?:warning|Warning)[\s:]+(.+?)(?:\s+at\s+(.+?)(?::(\d+))?)?$/gm;
    let match;
    while ((match = warningPattern.exec(output)) !== null) {
      warnings.push({
        message: match[1].trim(),
        file: match[2],
        line: match[3] ? parseInt(match[3]) : undefined,
      });
    }
    return warnings;
  }

  async build(config?: Partial<BuildConfig>): Promise<BuildResult> {
    const merged = { ...this.config, ...config };
    const startTime = Date.now();

    this.eventBus.emit('build:started', merged);

    let cmd: string;
    if (merged.target === 'native' || merged.target === 'wasm32') {
      const flags = [
        merged.mode === 'release' ? '--release' : '',
        merged.optimize ? '--optimize' : '',
        ...merged.compilerFlags,
      ].filter(Boolean).join(' ');
      cmd = `${this.compilerPath} ${merged.sourceDir} ${flags}`;
    } else {
      const targets = merged.target ? `--targets ${merged.target}` : '';
      const noTest = merged.mode === 'release' ? '--no-test' : '';
      cmd = `${this.buildToolPath} build ${targets} ${noTest}`;
    }

    const { stdout, stderr, exitCode } = await this.runCommand(cmd);
    const duration = Date.now() - startTime;
    const output = stdout + stderr;

    const result: BuildResult = {
      success: exitCode === 0,
      target: merged.target,
      mode: merged.mode,
      duration,
      output,
      errors: this.parseErrors(stderr),
      warnings: this.parseWarnings(stderr),
    };

    this.eventBus.emit('build:completed', result);
    return result;
  }

  async clean(config?: Partial<BuildConfig>): Promise<BuildResult> {
    const merged = { ...this.config, ...config };
    const startTime = Date.now();

    this.eventBus.emit('build:cleanStarted', merged);

    const { stdout, stderr, exitCode } = await this.runCommand(
      `${this.buildToolPath} clean`
    );

    const result: BuildResult = {
      success: exitCode === 0,
      target: merged.target,
      mode: merged.mode,
      duration: Date.now() - startTime,
      output: stdout || 'Cleaned build artifacts',
      errors: this.parseErrors(stderr),
      warnings: [],
    };

    this.eventBus.emit('build:cleanCompleted', result);
    return result;
  }

  async rebuild(config?: Partial<BuildConfig>): Promise<BuildResult> {
    const cleanResult = await this.clean(config);
    if (!cleanResult.success) return cleanResult;

    return this.build(config);
  }

  async runTests(config?: Partial<BuildConfig>): Promise<TestResult> {
    const merged = { ...this.config, ...config };
    this.eventBus.emit('test:started', merged);

    const startTime = Date.now();
    const { stdout, stderr } = await this.runCommand(
      `${this.buildToolPath} test`
    );

    const testResult: TestResult = {
      total: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      duration: Date.now() - startTime,
      tests: [],
    };

    const lines = stdout.split('\n');
    for (const line of lines) {
      const passMatch = line.match(/✓\s+(.+)/);
      const failMatch = line.match(/✗\s+(.+)/);
      const skipMatch = line.match(/○\s+(.+)/);
      const summaryMatch = line.match(/(\d+)\s+passed,\s+(\d+)\s+failed,\s+(\d+)\s+skipped/);

      if (passMatch) {
        testResult.tests.push({ name: passMatch[1], suite: 'default', status: 'passed', duration: 0 });
        testResult.passed++;
        testResult.total++;
      } else if (failMatch) {
        testResult.tests.push({ name: failMatch[1], suite: 'default', status: 'failed', duration: 0 });
        testResult.failed++;
        testResult.total++;
      } else if (skipMatch) {
        testResult.tests.push({ name: skipMatch[1], suite: 'default', status: 'skipped', duration: 0 });
        testResult.skipped++;
        testResult.total++;
      } else if (summaryMatch) {
        testResult.passed = parseInt(summaryMatch[1]);
        testResult.failed = parseInt(summaryMatch[2]);
        testResult.skipped = parseInt(summaryMatch[3]);
        testResult.total = testResult.passed + testResult.failed + testResult.skipped;
      }
    }

    this.eventBus.emit('test:completed', testResult);
    return testResult;
  }

  async compileFile(filePath: string, config?: Partial<BuildConfig>): Promise<BuildResult> {
    const merged = { ...this.config, ...config };
    const startTime = Date.now();

    this.eventBus.emit('build:compileFile', { filePath, config: merged });

    const flags = [
      merged.mode === 'release' ? '--release' : '',
      ...merged.compilerFlags,
    ].filter(Boolean).join(' ');

    const cmd = `${this.compilerPath} ${filePath} ${flags}`;
    const { stdout, stderr, exitCode } = await this.runCommand(cmd);

    const result: BuildResult = {
      success: exitCode === 0,
      target: merged.target,
      mode: merged.mode,
      duration: Date.now() - startTime,
      output: stdout + stderr,
      errors: this.parseErrors(stderr),
      warnings: this.parseWarnings(stderr),
    };

    this.eventBus.emit('build:compileFileCompleted', result);
    return result;
  }

  getCurrentConfig(): BuildConfig {
    return { ...this.config };
  }

  updateConfig(config: Partial<BuildConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

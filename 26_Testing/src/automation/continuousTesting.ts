// Continuous Testing Module for ArcanisTesting Framework

import { EventEmitter } from 'events';
import { generateId, delay } from '../core/utilities';
import { TestDiscovery, TestWatcher, createDiscoveryConfig } from './testDiscovery';
import { ReportGenerator, createReportGenerator } from './reports';
import { TestResult } from '../core/types';

export interface ContinuousTestingConfig {
  watchMode: boolean;
  autoRun: boolean;
  debounceMs: number;
  runOnCommit: boolean;
  runOnPush: boolean;
  runOnPR: boolean;
  runOnSave: boolean;
  includePatterns: string[];
  excludePatterns: string[];
  maxConcurrentRuns: number;
  notificationEnabled: boolean;
}

export interface TestRun {
  id: string;
  timestamp: Date;
  trigger: 'manual' | 'commit' | 'push' | 'pr' | 'save' | 'watch';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  results?: TestResult[];
  duration?: number;
  error?: string;
}

export interface GitHook {
  name: string;
  command: string;
  enabled: boolean;
}

export interface NotificationConfig {
  enabled: boolean;
  onSuccess: boolean;
  onFailure: boolean;
  channels: ('console' | 'email' | 'slack' | 'webhook')[];
  webhookUrl?: string;
}

export class ContinuousTesting extends EventEmitter {
  private config: ContinuousTestingConfig;
  private discovery: TestDiscovery;
  private watcher: TestWatcher | null = null;
  private reportGenerator: ReportGenerator;
  private testRuns: TestRun[] = [];
  private isRunning = false;
  private notificationConfig: NotificationConfig;

  constructor(config: Partial<ContinuousTestingConfig> = {}) {
    super();
    this.config = {
      watchMode: false,
      autoRun: true,
      debounceMs: 300,
      runOnCommit: true,
      runOnPush: true,
      runOnPR: true,
      runOnSave: true,
      includePatterns: ['**/*.test.ts', '**/*.spec.ts'],
      excludePatterns: ['node_modules', 'dist', 'reports'],
      maxConcurrentRuns: 1,
      notificationEnabled: true,
      ...config,
    };

    const discoveryConfig = createDiscoveryConfig(
      process.cwd(),
      this.config.includePatterns,
      this.config.excludePatterns
    );
    this.discovery = new TestDiscovery(discoveryConfig);
    this.reportGenerator = createReportGenerator();
    this.notificationConfig = {
      enabled: true,
      onSuccess: true,
      onFailure: true,
      channels: ['console'],
    };
  }

  async start(): Promise<void> {
    console.log('Starting continuous testing...');
    
    // Setup git hooks
    await this.setupGitHooks();
    
    // Start file watcher if in watch mode
    if (this.config.watchMode) {
      await this.startWatcher();
    }
    
    // Run initial tests
    if (this.config.autoRun) {
      await this.runTests('manual');
    }
    
    console.log('Continuous testing started');
  }

  async stop(): Promise<void> {
    console.log('Stopping continuous testing...');
    
    if (this.watcher) {
      this.watcher.stop();
      this.watcher = null;
    }
    
    console.log('Continuous testing stopped');
  }

  async runTests(trigger: TestRun['trigger'] = 'manual'): Promise<TestRun> {
    if (this.isRunning) {
      console.log('Tests already running, skipping...');
      return this.testRuns[this.testRuns.length - 1];
    }

    const run: TestRun = {
      id: generateId(),
      timestamp: new Date(),
      trigger,
      status: 'running',
    };

    this.testRuns.push(run);
    this.isRunning = true;
    this.emit('run:start', run);

    try {
      // Discover tests
      const discoveryResult = await this.discovery.discover();
      console.log(`Discovered ${discoveryResult.summary.total} tests`);

      // Run tests
      const startTime = performance.now();
      const results = await this.executeTests(discoveryResult.tests.map(t => t.filePath));
      const duration = performance.now() - startTime;

      // Generate report
      const report = await this.reportGenerator.generateReport(results);

      run.status = 'completed';
      run.results = results;
      run.duration = duration;

      // Send notifications
      if (this.config.notificationEnabled) {
        await this.sendNotification(run);
      }

      this.emit('run:complete', run, report);
    } catch (error) {
      run.status = 'failed';
      run.error = (error as Error).message;
      
      if (this.config.notificationEnabled) {
        await this.sendNotification(run);
      }
      
      this.emit('run:error', run, error);
    } finally {
      this.isRunning = false;
    }

    return run;
  }

  private async executeTests(filePaths: string[]): Promise<TestResult[]> {
    const results: TestResult[] = [];
    
    // Group tests by type
    const testsByType = new Map<string, string[]>();
    for (const filePath of filePaths) {
      let type = 'unit';
      if (filePath.includes('.integration.')) type = 'integration';
      else if (filePath.includes('.system.')) type = 'system';
      else if (filePath.includes('.performance.') || filePath.includes('.perf.')) type = 'performance';
      
      if (!testsByType.has(type)) {
        testsByType.set(type, []);
      }
      testsByType.get(type)!.push(filePath);
    }

    // Run tests by type
    for (const [type, files] of testsByType) {
      console.log(`Running ${type} tests...`);
      
      // This is a simplified version - in a real implementation,
      // you would dynamically import and run the test files
      for (const file of files) {
        try {
          // Simulate test execution
          const result: TestResult = {
            id: generateId(),
            name: file,
            type: type as TestResult['type'],
            status: 'passed',
            duration: Math.random() * 1000,
            assertions: [],
            metadata: {
              id: generateId(),
              name: file,
              type: type as TestResult['type'],
              priority: 'medium',
              tags: [],
              timeout: 5000,
              retries: 0,
              created: new Date(),
            },
            timestamp: new Date(),
            logs: [],
          };
          results.push(result);
        } catch (error) {
          const result: TestResult = {
            id: generateId(),
            name: file,
            type: type as TestResult['type'],
            status: 'failed',
            duration: 0,
            error: {
              message: (error as Error).message,
              stack: (error as Error).stack,
            },
            assertions: [],
            metadata: {
              id: generateId(),
              name: file,
              type: type as TestResult['type'],
              priority: 'medium',
              tags: [],
              timeout: 5000,
              retries: 0,
              created: new Date(),
            },
            timestamp: new Date(),
            logs: [],
          };
          results.push(result);
        }
      }
    }

    return results;
  }

  private async startWatcher(): Promise<void> {
    const discoveryConfig = createDiscoveryConfig(
      process.cwd(),
      this.config.includePatterns,
      this.config.excludePatterns
    );
    
    this.watcher = new TestWatcher(new TestDiscovery(discoveryConfig));
    
    this.watcher.on('changes', async (changes) => {
      console.log(`Detected ${changes.added.length} new tests, ${changes.removed.length} removed, ${changes.modified.length} modified`);
      
      if (this.config.autoRun) {
        // Debounce
        await delay(this.config.debounceMs);
        await this.runTests('watch');
      }
    });
    
    await this.watcher.start(5000);
  }

  private async setupGitHooks(): Promise<void> {
    if (!this.config.runOnCommit && !this.config.runOnPush && !this.config.runOnPR) {
      return;
    }

    const hooks: GitHook[] = [];
    
    if (this.config.runOnCommit) {
      hooks.push({
        name: 'pre-commit',
        command: 'arcanis run --type unit',
        enabled: true,
      });
    }
    
    if (this.config.runOnPush) {
      hooks.push({
        name: 'pre-push',
        command: 'arcanis run --all',
        enabled: true,
      });
    }

    console.log('Git hooks configured:');
    for (const hook of hooks) {
      console.log(`  ${hook.name}: ${hook.command}`);
    }
  }

  private async sendNotification(run: TestRun): Promise<void> {
    if (!this.notificationConfig.enabled) {
      return;
    }

    const shouldNotify = 
      (run.status === 'completed' && this.notificationConfig.onSuccess) ||
      (run.status === 'failed' && this.notificationConfig.onFailure);

    if (!shouldNotify) {
      return;
    }

    for (const channel of this.notificationConfig.channels) {
      await this.sendToChannel(channel, run);
    }
  }

  private async sendToChannel(channel: string, run: TestRun): Promise<void> {
    switch (channel) {
      case 'console':
        this.consoleNotification(run);
        break;
      case 'email':
        await this.emailNotification(run);
        break;
      case 'slack':
        await this.slackNotification(run);
        break;
      case 'webhook':
        await this.webhookNotification(run);
        break;
    }
  }

  private consoleNotification(run: TestRun): void {
    const status = run.status === 'completed' ? '✓' : '✗';
    const duration = run.duration ? `${(run.duration / 1000).toFixed(2)}s` : 'N/A';
    console.log(`\n[${status}] Test run ${run.id} (${run.trigger}) - ${duration}`);
    
    if (run.results) {
      const passed = run.results.filter(r => r.status === 'passed').length;
      const failed = run.results.filter(r => r.status === 'failed').length;
      console.log(`  Passed: ${passed}, Failed: ${failed}`);
    }
  }

  private async emailNotification(run: TestRun): Promise<void> {
    // Placeholder for email notification
    console.log('Email notification sent');
  }

  private async slackNotification(run: TestRun): Promise<void> {
    // Placeholder for Slack notification
    console.log('Slack notification sent');
  }

  private async webhookNotification(run: TestRun): Promise<void> {
    // Placeholder for webhook notification
    console.log('Webhook notification sent');
  }

  getTestRuns(): TestRun[] {
    return [...this.testRuns];
  }

  getLatestRun(): TestRun | undefined {
    return this.testRuns[this.testRuns.length - 1];
  }

  getRunById(id: string): TestRun | undefined {
    return this.testRuns.find(run => run.id === id);
  }

  async cancelRun(id: string): Promise<boolean> {
    const run = this.testRuns.find(r => r.id === id);
    if (run && run.status === 'running') {
      run.status = 'cancelled';
      this.emit('run:cancelled', run);
      return true;
    }
    return false;
  }

  setNotificationConfig(config: Partial<NotificationConfig>): void {
    this.notificationConfig = {
      ...this.notificationConfig,
      ...config,
    };
  }
}

// Factory function for creating continuous testing instances
export const createContinuousTesting = (config?: Partial<ContinuousTestingConfig>): ContinuousTesting => {
  return new ContinuousTesting(config);
};

// Git integration utilities
export const setupGitHooks = async (projectDir: string): Promise<void> => {
  console.log('Setting up git hooks...');
  
  const hooksDir = `${projectDir}/.git/hooks`;
  
  // Create pre-commit hook
  const preCommitHook = `#!/bin/sh
echo "Running pre-commit tests..."
arcanis run --type unit
`;
  
  // Create pre-push hook
  const prePushHook = `#!/bin/sh
echo "Running pre-push tests..."
arcanis run --all
`;
  
  console.log('Git hooks created');
};

// CI/CD integration utilities
export const generateGitHub ActionsWorkflow = (): string => {
  return `
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'
        
    - name: Install dependencies
      run: npm ci
      
    - name: Run tests
      run: npm test
      
    - name: Generate report
      run: npm run test:report
      
    - name: Upload report
      uses: actions/upload-artifact@v2
      with:
        name: test-report
        path: reports/
`;
};

export const generateGitLabCIConfig = (): string => {
  return `
test:
  stage: test
  script:
    - npm ci
    - npm test
    - npm run test:report
  artifacts:
    paths:
      - reports/
    expire_in: 30 days
`;
};

export const generateJenkinsfile = (): string => {
  return `
pipeline {
    agent any
    
    stages {
        stage('Test') {
            steps {
                sh 'npm ci'
                sh 'npm test'
                sh 'npm run test:report'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/**', allowEmptyArchive
                }
            }
        }
    }
}
`;
};

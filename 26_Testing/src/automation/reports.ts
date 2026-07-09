// Reports Module for ArcanisTesting Framework

import * as fs from 'fs';
import * as path from 'path';
import { EventEmitter } from 'events';
import { generateId, formatDuration, formatPercentage } from '../core/utilities';
import { TestReport, TestSummary, TestResult, SuiteResult, PerformanceMetrics, AIAnalysis } from '../core/types';

export interface ReportConfig {
  outputDir: string;
  formats: ('console' | 'json' | 'html' | 'csv' | 'xml')[];
  generateOnFailure: boolean;
  includeScreenshots: boolean;
  includeNetworkLogs: boolean;
  includePerformanceMetrics: boolean;
  includeAIAnalysis: boolean;
}

export interface ReportOptions {
  title?: string;
  description?: string;
  author?: string;
  version?: string;
  timestamp?: Date;
}

export class ReportGenerator extends EventEmitter {
  private config: ReportConfig;
  private reports: TestReport[] = [];

  constructor(config: Partial<ReportConfig> = {}) {
    super();
    this.config = {
      outputDir: './reports',
      formats: ['console', 'json'],
      generateOnFailure: true,
      includeScreenshots: true,
      includeNetworkLogs: true,
      includePerformanceMetrics: true,
      includeAIAnalysis: true,
      ...config,
    };
  }

  async generateReport(
    results: TestResult[],
    options?: ReportOptions
  ): Promise<TestReport> {
    const report: TestReport = {
      id: generateId(),
      timestamp: options?.timestamp || new Date(),
      duration: results.reduce((sum, r) => sum + r.duration, 0),
      summary: this.generateSummary(results),
      suites: this.groupBySuites(results),
    };

    // Add performance metrics if enabled
    if (this.config.includePerformanceMetrics) {
      report.performance = this.extractPerformanceMetrics(results);
    }

    // Add AI analysis if enabled
    if (this.config.includeAIAnalysis) {
      report.aiAnalysis = await this.generateAIAnalysis(results);
    }

    this.reports.push(report);

    // Generate reports in configured formats
    for (const format of this.config.formats) {
      await this.generateFormat(report, format, options);
    }

    this.emit('report:generated', report);
    return report;
  }

  private generateSummary(results: TestResult[]): TestSummary {
    const total = results.length;
    const passed = results.filter(r => r.status === 'passed').length;
    const failed = results.filter(r => r.status === 'failed').length;
    const skipped = results.filter(r => r.status === 'skipped').length;
    const errors = results.filter(r => r.status === 'error').length;
    const duration = results.reduce((sum, r) => sum + r.duration, 0);

    return {
      total,
      passed,
      failed,
      skipped,
      errors,
      duration,
    };
  }

  private groupBySuites(results: TestResult[]): SuiteResult[] {
    const suiteMap = new Map<string, TestResult[]>();

    for (const result of results) {
      const suiteName = result.metadata.tags[0] || 'Default Suite';
      if (!suiteMap.has(suiteName)) {
        suiteMap.set(suiteName, []);
      }
      suiteMap.get(suiteName)!.push(result);
    }

    return Array.from(suiteMap.entries()).map(([name, tests]) => ({
      id: generateId(),
      name,
      type: tests[0].type,
      tests,
      duration: tests.reduce((sum, t) => sum + t.duration, 0),
      timestamp: new Date(),
    }));
  }

  private extractPerformanceMetrics(results: TestResult[]): PerformanceMetrics | undefined {
    // Extract performance metrics from results
    // This is a simplified version - in a real implementation, you'd extract actual metrics
    return undefined;
  }

  private async generateAIAnalysis(results: TestResult[]): Promise<AIAnalysis | undefined> {
    // Generate AI analysis
    // This is a placeholder for AI integration
    return undefined;
  }

  private async generateFormat(
    report: TestReport,
    format: string,
    options?: ReportOptions
  ): Promise<void> {
    const outputDir = path.resolve(this.config.outputDir);
    
    // Ensure output directory exists
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    switch (format) {
      case 'console':
        await this.generateConsoleReport(report, options);
        break;
      case 'json':
        await this.generateJSONReport(report, outputDir, options);
        break;
      case 'html':
        await this.generateHTMLReport(report, outputDir, options);
        break;
      case 'csv':
        await this.generateCSVReport(report, outputDir, options);
        break;
      case 'xml':
        await this.generateXMLReport(report, outputDir, options);
        break;
    }
  }

  private async generateConsoleReport(
    report: TestReport,
    options?: ReportOptions
  ): Promise<void> {
    console.log('\n' + '='.repeat(60));
    console.log('TEST REPORT');
    console.log('='.repeat(60));
    
    if (options?.title) {
      console.log(`\nTitle: ${options.title}`);
    }
    
    console.log(`\nGenerated: ${report.timestamp.toISOString()}`);
    console.log(`Duration: ${formatDuration(report.duration)}`);
    
    console.log('\n' + '-'.repeat(60));
    console.log('SUMMARY');
    console.log('-'.repeat(60));
    console.log(`Total Tests: ${report.summary.total}`);
    console.log(`Passed: ${report.summary.passed}`);
    console.log(`Failed: ${report.summary.failed}`);
    console.log(`Skipped: ${report.summary.skipped}`);
    console.log(`Errors: ${report.summary.errors}`);
    console.log(`Success Rate: ${formatPercentage((report.summary.passed / report.summary.total) * 100)}`);
    
    if (report.summary.total > 0) {
      console.log('\n' + '-'.repeat(60));
      console.log('TEST RESULTS');
      console.log('-'.repeat(60));
      
      for (const suite of report.suites) {
        console.log(`\n${suite.name}:`);
        for (const test of suite.tests) {
          const status = test.status === 'passed' ? '✓' : test.status === 'failed' ? '✗' : '○';
          const duration = formatDuration(test.duration);
          console.log(`  ${status} ${test.name} (${duration})`);
          
          if (test.error) {
            console.log(`    Error: ${test.error.message}`);
          }
        }
      }
    }
    
    console.log('\n' + '='.repeat(60));
  }

  private async generateJSONReport(
    report: TestReport,
    outputDir: string,
    options?: ReportOptions
  ): Promise<void> {
    const fileName = `report-${report.id}.json`;
    const filePath = path.join(outputDir, fileName);
    
    const reportData = {
      ...report,
      options,
      generatedAt: new Date().toISOString(),
    };
    
    await fs.promises.writeFile(filePath, JSON.stringify(reportData, null, 2));
    console.log(`JSON report generated: ${filePath}`);
  }

  private async generateHTMLReport(
    report: TestReport,
    outputDir: string,
    options?: ReportOptions
  ): Promise<void> {
    const fileName = `report-${report.id}.html`;
    const filePath = path.join(outputDir, fileName);
    
    const html = this.generateHTMLContent(report, options);
    await fs.promises.writeFile(filePath, html);
    console.log(`HTML report generated: ${filePath}`);
  }

  private generateHTMLContent(report: TestReport, options?: ReportOptions): string {
    const successRate = (report.summary.passed / report.summary.total) * 100;
    
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${options?.title || 'Test Report'}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .summary-card { padding: 20px; border-radius: 8px; text-align: center; }
        .passed { background-color: #d4edda; color: #155724; }
        .failed { background-color: #f8d7da; color: #721c24; }
        .skipped { background-color: #fff3cd; color: #856404; }
        .error { background-color: #f5f5f5; color: #383d41; }
        .test-list { margin-top: 20px; }
        .test-item { padding: 10px; margin: 5px 0; border-radius: 4px; border-left: 4px solid; }
        .test-passed { border-color: #28a745; background-color: #f8f9fa; }
        .test-failed { border-color: #dc3545; background-color: #f8f9fa; }
        .test-error { border-color: #ffc107; background-color: #f8f9fa; }
        .test-info { display: flex; justify-content: space-between; align-items: center; }
        .test-name { font-weight: bold; }
        .test-duration { color: #6c757d; font-size: 0.9em; }
        .error-message { color: #dc3545; font-size: 0.9em; margin-top: 5px; }
        .suite { margin-bottom: 30px; }
        .suite-name { font-size: 1.5em; margin-bottom: 10px; color: #343a40; }
        .progress-bar { width: 100%; height: 20px; background-color: #e9ecef; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .progress-fill { height: 100%; background-color: #28a745; transition: width 0.3s; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>${options?.title || 'Test Report'}</h1>
            <p>Generated: ${report.timestamp.toISOString()}</p>
            ${options?.description ? `<p>${options.description}</p>` : ''}
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <p>${report.summary.total}</p>
            </div>
            <div class="summary-card passed">
                <h3>Passed</h3>
                <p>${report.summary.passed}</p>
            </div>
            <div class="summary-card failed">
                <h3>Failed</h3>
                <p>${report.summary.failed}</p>
            </div>
            <div class="summary-card skipped">
                <h3>Skipped</h3>
                <p>${report.summary.skipped}</p>
            </div>
            <div class="summary-card error">
                <h3>Errors</h3>
                <p>${report.summary.errors}</p>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${successRate}%"></div>
        </div>
        <p>Success Rate: ${formatPercentage(successRate)}</p>
        
        <div class="test-list">
            ${report.suites.map(suite => `
                <div class="suite">
                    <div class="suite-name">${suite.name}</div>
                    ${suite.tests.map(test => `
                        <div class="test-item test-${test.status}">
                            <div class="test-info">
                                <span class="test-name">${test.name}</span>
                                <span class="test-duration">${formatDuration(test.duration)}</span>
                            </div>
                            ${test.error ? `<div class="error-message">${test.error.message}</div>` : ''}
                        </div>
                    `).join('')}
                </div>
            `).join('')}
        </div>
    </div>
</body>
</html>
    `;
  }

  private async generateCSVReport(
    report: TestReport,
    outputDir: string,
    options?: ReportOptions
  ): Promise<void> {
    const fileName = `report-${report.id}.csv`;
    const filePath = path.join(outputDir, fileName);
    
    const csvRows = [
      ['Test Name', 'Status', 'Duration (ms)', 'Type', 'Error'].join(','),
    ];
    
    for (const suite of report.suites) {
      for (const test of suite.tests) {
        csvRows.push([
          `"${test.name}"`,
          test.status,
          test.duration.toFixed(2),
          test.type,
          test.error ? `"${test.error.message}"` : '',
        ].join(','));
      }
    }
    
    await fs.promises.writeFile(filePath, csvRows.join('\n'));
    console.log(`CSV report generated: ${filePath}`);
  }

  private async generateXMLReport(
    report: TestReport,
    outputDir: string,
    options?: ReportOptions
  ): Promise<void> {
    const fileName = `report-${report.id}.xml`;
    const filePath = path.join(outputDir, fileName);
    
    let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
    xml += '<testreport>\n';
    xml += `  <summary>\n`;
    xml += `    <total>${report.summary.total}</total>\n`;
    xml += `    <passed>${report.summary.passed}</passed>\n`;
    xml += `    <failed>${report.summary.failed}</failed>\n`;
    xml += `    <skipped>${report.summary.skipped}</skipped>\n`;
    xml += `    <errors>${report.summary.errors}</errors>\n`;
    xml += `    <duration>${report.duration.toFixed(2)}</duration>\n`;
    xml += `  </summary>\n`;
    xml += `  <tests>\n`;
    
    for (const suite of report.suites) {
      for (const test of suite.tests) {
        xml += `    <test name="${test.name}" status="${test.status}" duration="${test.duration.toFixed(2)}">\n`;
        if (test.error) {
          xml += `      <error message="${test.error.message}" />\n`;
        }
        xml += `    </test>\n`;
      }
    }
    
    xml += `  </tests>\n`;
    xml += '</testreport>';
    
    await fs.promises.writeFile(filePath, xml);
    console.log(`XML report generated: ${filePath}`);
  }

  getReports(): TestReport[] {
    return [...this.reports];
  }

  getLatestReport(): TestReport | undefined {
    return this.reports[this.reports.length - 1];
  }
}

// Factory function for creating report generators
export const createReportGenerator = (config?: Partial<ReportConfig>): ReportGenerator => {
  return new ReportGenerator(config);
};

// Report comparison utilities
export const compareReports = (report1: TestReport, report2: TestReport): {
  summary: {
    totalDiff: number;
    passedDiff: number;
    failedDiff: number;
    successRateDiff: number;
  };
  performance: {
    durationDiff: number;
  };
} => {
  const successRate1 = (report1.summary.passed / report1.summary.total) * 100;
  const successRate2 = (report2.summary.passed / report2.summary.total) * 100;

  return {
    summary: {
      totalDiff: report2.summary.total - report1.summary.total,
      passedDiff: report2.summary.passed - report1.summary.passed,
      failedDiff: report2.summary.failed - report1.summary.failed,
      successRateDiff: successRate2 - successRate1,
    },
    performance: {
      durationDiff: report2.duration - report1.duration,
    },
  };
};

// Trend analysis
export const analyzeTrend = (reports: TestReport[]): {
  successRateTrend: number[];
  durationTrend: number[];
  passCountTrend: number[];
  failCountTrend: number[];
} => {
  return {
    successRateTrend: reports.map(r => (r.summary.passed / r.summary.total) * 100),
    durationTrend: reports.map(r => r.duration),
    passCountTrend: reports.map(r => r.summary.passed),
    failCountTrend: reports.map(r => r.summary.failed),
  };
};

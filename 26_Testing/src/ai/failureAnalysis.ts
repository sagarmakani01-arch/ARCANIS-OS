// Failure Analysis Module for ArcanisTesting Framework

import * as fs from 'fs';
import * as path from 'path';
import { EventEmitter } from 'events';
import { generateId } from '../core/utilities';
import { TestResult, FailureAnalysis, TestError } from '../core/types';

export interface FailureAnalysisConfig {
  enabled: boolean;
  rootCauseAnalysis: boolean;
  suggestionGeneration: boolean;
  maxSuggestions: number;
  includeStackTraces: boolean;
}

export interface FailurePattern {
  id: string;
  name: string;
  description: string;
  regex: RegExp;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  suggestions: string[];
}

export interface AnalysisResult {
  id: string;
  timestamp: Date;
  testId: string;
  testName: string;
  error: TestError;
  rootCause?: string;
  suggestions: string[];
  relatedFailures: string[];
  pattern?: FailurePattern;
  confidence: number;
}

export class FailureAnalyzer extends EventEmitter {
  private config: FailureAnalysisConfig;
  private patterns: FailurePattern[] = [];
  private analysisHistory: AnalysisResult[] = [];

  constructor(config: Partial<FailureAnalysisConfig> = {}) {
    super();
    this.config = {
      enabled: true,
      rootCauseAnalysis: true,
      suggestionGeneration: true,
      maxSuggestions: 5,
      includeStackTraces: true,
      ...config,
    };

    this.initializePatterns();
  }

  private initializePatterns(): void {
    this.patterns = [
      {
        id: generateId(),
        name: 'Null Reference',
        description: 'Cannot read property of null or undefined',
        regex: /Cannot read propert(y|ies) of (null|undefined)/i,
        category: 'reference',
        severity: 'high',
        suggestions: [
          'Add null checks before accessing properties',
          'Use optional chaining (?.)',
          'Initialize variables with default values',
          'Use type guards',
        ],
      },
      {
        id: generateId(),
        name: 'Type Error',
        description: 'Type mismatch or invalid type operation',
        regex: /Type Error|type.*is not assignable/i,
        category: 'type',
        severity: 'medium',
        suggestions: [
          'Check type definitions',
          'Add type assertions',
          'Use proper type guards',
          'Review TypeScript configuration',
        ],
      },
      {
        id: generateId(),
        name: 'Network Error',
        description: 'Network request failed',
        regex: /network|ECONNREFUSED|ETIMEDOUT|fetch failed/i,
        category: 'network',
        severity: 'high',
        suggestions: [
          'Check network connectivity',
          'Verify server is running',
          'Increase timeout settings',
          'Check firewall settings',
        ],
      },
      {
        id: generateId(),
        name: 'Permission Error',
        description: 'Access denied or permission denied',
        regex: /permission|EACCES|EPERM|access denied/i,
        category: 'permission',
        severity: 'critical',
        suggestions: [
          'Check file permissions',
          'Run with appropriate privileges',
          'Verify user permissions',
          'Check security policies',
        ],
      },
      {
        id: generateId(),
        name: 'File Not Found',
        description: 'File or directory not found',
        regex: /ENOENT|file.*not found|no such file/i,
        category: 'filesystem',
        severity: 'medium',
        suggestions: [
          'Verify file path',
          'Check file exists',
          'Create missing directories',
          'Use absolute paths',
        ],
      },
      {
        id: generateId(),
        name: 'Memory Error',
        description: 'Out of memory or memory limit exceeded',
        regex: /out of memory|heap.*limit|memory/i,
        category: 'memory',
        severity: 'critical',
        suggestions: [
          'Increase memory limit',
          'Optimize memory usage',
          'Check for memory leaks',
          'Use streaming for large data',
        ],
      },
      {
        id: generateId(),
        name: 'Timeout Error',
        description: 'Operation timed out',
        regex: /timeout|timed out|deadline exceeded/i,
        category: 'timeout',
        severity: 'high',
        suggestions: [
          'Increase timeout value',
          'Optimize slow operations',
          'Check for deadlocks',
          'Use async/await properly',
        ],
      },
      {
        id: generateId(),
        name: 'Assertion Error',
        description: 'Test assertion failed',
        regex: /assertion|expected.*to.*be|assert.*failed/i,
        category: 'assertion',
        severity: 'low',
        suggestions: [
          'Review test expectations',
          'Check actual vs expected values',
          'Update test cases',
          'Verify business logic',
        ],
      },
    ];
  }

  async analyzeFailure(testResult: TestResult): Promise<AnalysisResult> {
    if (!this.config.enabled) {
      return this.createEmptyAnalysis(testResult);
    }

    const error = testResult.error;
    if (!error) {
      return this.createEmptyAnalysis(testResult);
    }

    const pattern = this.matchPattern(error.message);
    const rootCause = this.config.rootCauseAnalysis ? await this.findRootCause(error, testResult) : undefined;
    const suggestions = this.config.suggestionGeneration ? this.generateSuggestions(error, pattern) : [];
    const relatedFailures = await this.findRelatedFailures(testResult);

    const analysis: AnalysisResult = {
      id: generateId(),
      timestamp: new Date(),
      testId: testResult.id,
      testName: testResult.name,
      error,
      rootCause,
      suggestions: suggestions.slice(0, this.config.maxSuggestions),
      relatedFailures,
      pattern,
      confidence: this.calculateConfidence(pattern, error),
    };

    this.analysisHistory.push(analysis);
    this.emit('analysis:complete', analysis);

    return analysis;
  }

  private matchPattern(errorMessage: string): FailurePattern | undefined {
    return this.patterns.find(pattern => pattern.regex.test(errorMessage));
  }

  private async findRootCause(error: TestError, testResult: TestResult): Promise<string> {
    const stack = error.stack || '';
    const lines = stack.split('\n');

    // Find the first relevant stack frame
    for (const line of lines) {
      if (line.includes('node_modules')) continue;
      if (line.includes('at ')) {
        const match = line.match(/at\s+(.+?)\s+\((.+?):(\d+):(\d+)\)/);
        if (match) {
          const [, funcName, filePath, lineNumber] = match;
          return `Error in ${funcName} at ${filePath}:${lineNumber}`;
        }
      }
    }

    return 'Unable to determine root cause from stack trace';
  }

  private generateSuggestions(error: TestError, pattern?: FailurePattern): string[] {
    const suggestions: string[] = [];

    if (pattern) {
      suggestions.push(...pattern.suggestions);
    }

    // Add general suggestions based on error message
    const errorMessage = error.message.toLowerCase();

    if (errorMessage.includes('async') || errorMessage.includes('promise')) {
      suggestions.push('Ensure proper async/await usage');
      suggestions.push('Handle promise rejections');
    }

    if (errorMessage.includes('timeout')) {
      suggestions.push('Increase timeout for slow operations');
      suggestions.push('Check for blocking operations');
    }

    if (errorMessage.includes('memory') || errorMessage.includes('heap')) {
      suggestions.push('Check for memory leaks');
      suggestions.push('Optimize data structures');
    }

    // Remove duplicates
    return [...new Set(suggestions)];
  }

  private async findRelatedFailures(testResult: TestResult): Promise<string[]> {
    const related: string[] = [];

    for (const analysis of this.analysisHistory) {
      if (analysis.testId === testResult.id) continue;
      
      if (analysis.error.message === testResult.error?.message) {
        related.push(analysis.testId);
      }
    }

    return [...new Set(related)].slice(0, 5);
  }

  private calculateConfidence(pattern: FailurePattern | undefined, error: TestError): number {
    let confidence = 0.5;

    if (pattern) {
      confidence += 0.3;
    }

    if (error.stack) {
      confidence += 0.1;
    }

    if (error.expected !== undefined && error.actual !== undefined) {
      confidence += 0.1;
    }

    return Math.min(confidence, 1);
  }

  private createEmptyAnalysis(testResult: TestResult): AnalysisResult {
    return {
      id: generateId(),
      timestamp: new Date(),
      testId: testResult.id,
      testName: testResult.name,
      error: testResult.error || { message: 'No error details available' },
      suggestions: [],
      relatedFailures: [],
      confidence: 0,
    };
  }

  async analyzeMultipleFailures(testResults: TestResult[]): Promise<AnalysisResult[]> {
    const analyses: AnalysisResult[] = [];

    for (const result of testResults) {
      if (result.status === 'failed' || result.status === 'error') {
        const analysis = await this.analyzeFailure(result);
        analyses.push(analysis);
      }
    }

    return analyses;
  }

  getAnalysisHistory(): AnalysisResult[] {
    return [...this.analysisHistory];
  }

  getAnalysisById(id: string): AnalysisResult | undefined {
    return this.analysisHistory.find(a => a.id === id);
  }

  getAnalysisByTest(testId: string): AnalysisResult[] {
    return this.analysisHistory.filter(a => a.testId === testId);
  }

  getCommonPatterns(): { pattern: FailurePattern; count: number }[] {
    const patternCounts = new Map<string, number>();

    for (const analysis of this.analysisHistory) {
      if (analysis.pattern) {
        const count = patternCounts.get(analysis.pattern.id) || 0;
        patternCounts.set(analysis.pattern.id, count + 1);
      }
    }

    const results: { pattern: FailurePattern; count: number }[] = [];

    for (const [patternId, count] of patternCounts) {
      const pattern = this.patterns.find(p => p.id === patternId);
      if (pattern) {
        results.push({ pattern, count });
      }
    }

    return results.sort((a, b) => b.count - a.count);
  }

  generateReport(analyses: AnalysisResult[]): string {
    let report = 'Failure Analysis Report\n';
    report += '======================\n\n';
    report += `Total failures analyzed: ${analyses.length}\n\n`;

    // Common patterns
    const commonPatterns = this.getCommonPatterns();
    if (commonPatterns.length > 0) {
      report += 'Common Failure Patterns:\n';
      report += '------------------------\n';
      for (const { pattern, count } of commonPatterns.slice(0, 5)) {
        report += `${pattern.name} (${count} occurrences)\n`;
        report += `  Category: ${pattern.category}\n`;
        report += `  Severity: ${pattern.severity}\n\n`;
      }
    }

    // Individual analyses
    report += 'Detailed Analysis:\n';
    report += '------------------\n';
    for (const analysis of analyses.slice(0, 10)) {
      report += `\nTest: ${analysis.testName}\n`;
      report += `Error: ${analysis.error.message}\n`;
      
      if (analysis.rootCause) {
        report += `Root Cause: ${analysis.rootCause}\n`;
      }
      
      if (analysis.suggestions.length > 0) {
        report += 'Suggestions:\n';
        for (const suggestion of analysis.suggestions) {
          report += `  - ${suggestion}\n`;
        }
      }
      
      if (analysis.relatedFailures.length > 0) {
        report += `Related Failures: ${analysis.relatedFailures.length}\n`;
      }
      
      report += `Confidence: ${(analysis.confidence * 100).toFixed(1)}%\n`;
    }

    return report;
  }

  addCustomPattern(pattern: Omit<FailurePattern, 'id'>): void {
    this.patterns.push({
      id: generateId(),
      ...pattern,
    });
  }

  removePattern(patternId: string): boolean {
    const index = this.patterns.findIndex(p => p.id === patternId);
    if (index !== -1) {
      this.patterns.splice(index, 1);
      return true;
    }
    return false;
  }

  getPatterns(): FailurePattern[] {
    return [...this.patterns];
  }
}

// Factory function for creating failure analyzers
export const createFailureAnalyzer = (config?: Partial<FailureAnalysisConfig>): FailureAnalyzer => {
  return new FailureAnalyzer(config);
};

// Helper function for parsing stack traces
export const parseStackTrace = (stack: string): {
  function: string;
  file: string;
  line: number;
  column: number;
}[] => {
  const frames: {
    function: string;
    file: string;
    line: number;
    column: number;
  }[] = [];

  const lines = stack.split('\n');
  for (const line of lines) {
    const match = line.match(/at\s+(.+?)\s+\((.+?):(\d+):(\d+)\)/);
    if (match) {
      frames.push({
        function: match[1],
        file: match[2],
        line: parseInt(match[3]),
        column: parseInt(match[4]),
      });
    }
  }

  return frames;
};

// Helper function for error classification
export const classifyError = (error: TestError): {
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  isTransient: boolean;
} => {
  const message = error.message.toLowerCase();

  if (message.includes('timeout') || message.includes('network')) {
    return {
      category: 'transient',
      severity: 'medium',
      isTransient: true,
    };
  }

  if (message.includes('memory') || message.includes('crash')) {
    return {
      category: 'critical',
      severity: 'critical',
      isTransient: false,
    };
  }

  if (message.includes('assertion') || message.includes('expected')) {
    return {
      category: 'logic',
      severity: 'low',
      isTransient: false,
    };
  }

  return {
    category: 'unknown',
    severity: 'medium',
    isTransient: false,
  };
};

// Helper function for generating fix suggestions
export const generateFixSuggestions = (error: TestError): string[] => {
  const suggestions: string[] = [];
  const message = error.message.toLowerCase();

  if (message.includes('null') || message.includes('undefined')) {
    suggestions.push('Add null/undefined checks');
    suggestions.push('Use optional chaining (?.)');
    suggestions.push('Initialize variables properly');
  }

  if (message.includes('type')) {
    suggestions.push('Review type definitions');
    suggestions.push('Add type assertions');
    suggestions.push('Use proper type guards');
  }

  if (message.includes('async') || message.includes('promise')) {
    suggestions.push('Ensure proper async/await usage');
    suggestions.push('Handle promise rejections');
    suggestions.push('Check for unhandled promises');
  }

  if (suggestions.length === 0) {
    suggestions.push('Review the error message and stack trace');
    suggestions.push('Check the relevant code section');
    suggestions.push('Add debugging logs');
  }

  return suggestions;
};

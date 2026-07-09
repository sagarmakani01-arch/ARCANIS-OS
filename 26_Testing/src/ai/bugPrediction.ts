// Bug Prediction Module for ArcanisTesting Framework

import * as fs from 'fs';
import * as path from 'path';
import { EventEmitter } from 'events';
import { generateId } from '../core/utilities';
import { BugPrediction, TestResult } from '../core/types';

export interface BugPredictionConfig {
  enabled: boolean;
  model: 'local' | 'api';
  threshold: number;
  features: string[];
  weights: Record<string, number>;
}

export interface CodeMetrics {
  filePath: string;
  linesOfCode: number;
  complexity: number;
  duplicatedLines: number;
  testCoverage: number;
  lastModified: Date;
  changeFrequency: number;
  bugHistory: number;
  authorCount: number;
  age: number;
}

export interface PredictionResult {
  id: string;
  timestamp: Date;
  predictions: BugPrediction[];
  confidence: number;
  model: string;
}

export class BugPredictor extends EventEmitter {
  private config: BugPredictionConfig;
  private metrics: Map<string, CodeMetrics> = new Map();

  constructor(config: Partial<BugPredictionConfig> = {}) {
    super();
    this.config = {
      enabled: true,
      model: 'local',
      threshold: 0.7,
      features: [
        'complexity',
        'duplicatedLines',
        'testCoverage',
        'changeFrequency',
        'bugHistory',
        'age',
      ],
      weights: {
        complexity: 0.25,
        duplicatedLines: 0.2,
        testCoverage: 0.2,
        changeFrequency: 0.15,
        bugHistory: 0.15,
        age: 0.05,
      },
      ...config,
    };
  }

  async analyzeCode(filePath: string): Promise<CodeMetrics> {
    const content = await fs.promises.readFile(filePath, 'utf-8');
    const stats = await fs.promises.stat(filePath);

    const metrics: CodeMetrics = {
      filePath,
      linesOfCode: content.split('\n').length,
      complexity: this.calculateComplexity(content),
      duplicatedLines: this.calculateDuplicatedLines(content),
      testCoverage: await this.estimateTestCoverage(filePath),
      lastModified: stats.mtime,
      changeFrequency: await this.calculateChangeFrequency(filePath),
      bugHistory: await this.calculateBugHistory(filePath),
      authorCount: await this.calculateAuthorCount(filePath),
      age: Date.now() - stats.birthtime.getTime(),
    };

    this.metrics.set(filePath, metrics);
    return metrics;
  }

  private calculateComplexity(content: string): number {
    // Simplified cyclomatic complexity calculation
    let complexity = 1;
    const lines = content.split('\n');

    for (const line of lines) {
      const trimmed = line.trim();
      if (
        trimmed.startsWith('if ') ||
        trimmed.startsWith('else if ') ||
        trimmed.includes('&&') ||
        trimmed.includes('||')
      ) {
        complexity++;
      }
      if (trimmed.startsWith('for ') || trimmed.startsWith('while ')) {
        complexity++;
      }
      if (trimmed.startsWith('case ')) {
        complexity++;
      }
      if (trimmed.includes('catch ')) {
        complexity++;
      }
    }

    return complexity;
  }

  private calculateDuplicatedLines(content: string): number {
    const lines = content.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    const uniqueLines = new Set(lines);
    return lines.length - uniqueLines.size;
  }

  private async estimateTestCoverage(filePath: string): Promise<number> {
    // Estimate test coverage based on test file existence
    const dir = path.dirname(filePath);
    const ext = path.extname(filePath);
    const baseName = path.basename(filePath, ext);

    const testPatterns = [
      `${baseName}.test${ext}`,
      `${baseName}.spec${ext}`,
      `${baseName}.integration${ext}`,
    ];

    for (const pattern of testPatterns) {
      const testPath = path.join(dir, pattern);
      if (fs.existsSync(testPath)) {
        return 80; // Assume 80% coverage if test file exists
      }
    }

    return 0;
  }

  private async calculateChangeFrequency(filePath: string): Promise<number> {
    // This is a simplified version - in a real implementation,
    // you would use git history to calculate change frequency
    return Math.floor(Math.random() * 10);
  }

  private async calculateBugHistory(filePath: string): Promise<number> {
    // This is a simplified version - in a real implementation,
    // you would query a bug tracking system
    return Math.floor(Math.random() * 5);
  }

  private async calculateAuthorCount(filePath: string): Promise<number> {
    // This is a simplified version - in a real implementation,
    // you would use git history
    return Math.floor(Math.random() * 5) + 1;
  }

  async predictBugs(filePath: string): Promise<BugPrediction> {
    const metrics = await this.analyzeCode(filePath);
    const probability = this.calculateProbability(metrics);
    const reason = this.generateReason(metrics, probability);

    const prediction: BugPrediction = {
      file: filePath,
      probability,
      reason,
      severity: this.determineSeverity(probability),
    };

    this.emit('prediction', prediction);
    return prediction;
  }

  private calculateProbability(metrics: CodeMetrics): number {
    let score = 0;

    // Normalize metrics to 0-1 range
    const normalizedComplexity = Math.min(metrics.complexity / 50, 1);
    const normalizedDuplication = Math.min(metrics.duplicatedLines / 100, 1);
    const normalizedCoverage = 1 - metrics.testCoverage / 100;
    const normalizedChangeFrequency = Math.min(metrics.changeFrequency / 20, 1);
    const normalizedBugHistory = Math.min(metrics.bugHistory / 10, 1);
    const normalizedAge = Math.min(metrics.age / (365 * 24 * 60 * 60 * 1000), 1);

    // Apply weights
    score += normalizedComplexity * this.config.weights.complexity;
    score += normalizedDuplication * this.config.weights.duplicatedLines;
    score += normalizedCoverage * this.config.weights.testCoverage;
    score += normalizedChangeFrequency * this.config.weights.changeFrequency;
    score += normalizedBugHistory * this.config.weights.bugHistory;
    score += normalizedAge * this.config.weights.age;

    return Math.min(score, 1);
  }

  private generateReason(metrics: CodeMetrics, probability: number): string {
    const reasons: string[] = [];

    if (metrics.complexity > 20) {
      reasons.push(`High complexity (${metrics.complexity})`);
    }
    if (metrics.duplicatedLines > 50) {
      reasons.push(`Significant code duplication (${metrics.duplicatedLines} lines)`);
    }
    if (metrics.testCoverage < 50) {
      reasons.push(`Low test coverage (${metrics.testCoverage}%)`);
    }
    if (metrics.changeFrequency > 10) {
      reasons.push(`Frequent changes (${metrics.changeFrequency} times)`);
    }
    if (metrics.bugHistory > 3) {
      reasons.push(`History of bugs (${metrics.bugHistory} bugs)`);
    }

    if (reasons.length === 0) {
      if (probability > 0.7) {
        reasons.push('Multiple risk factors detected');
      } else {
        reasons.push('Moderate risk profile');
      }
    }

    return reasons.join('; ');
  }

  private determineSeverity(probability: number): BugPrediction['severity'] {
    if (probability >= 0.9) return 'critical';
    if (probability >= 0.7) return 'high';
    if (probability >= 0.4) return 'medium';
    return 'low';
  }

  async predictBugsInDirectory(dirPath: string, patterns: string[] = ['**/*.ts']): Promise<BugPrediction[]> {
    const predictions: BugPrediction[] = [];

    // This is a simplified version - in a real implementation,
    // you would recursively scan the directory
    const files = await this.getFiles(dirPath, patterns);

    for (const file of files) {
      const prediction = await this.predictBugs(file);
      if (prediction.probability >= this.config.threshold) {
        predictions.push(prediction);
      }
    }

    // Sort by probability (highest first)
    predictions.sort((a, b) => b.probability - a.probability);

    return predictions;
  }

  private async getFiles(dirPath: string, patterns: string[]): Promise<string[]> {
    const files: string[] = [];
    
    try {
      const entries = await fs.promises.readdir(dirPath, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dirPath, entry.name);
        
        if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
          const subFiles = await this.getFiles(fullPath, patterns);
          files.push(...subFiles);
        } else if (entry.isFile()) {
          const ext = path.extname(entry.name);
          if (patterns.some(p => p.endsWith(ext) || p.includes('*'))) {
            files.push(fullPath);
          }
        }
      }
    } catch (error) {
      // Ignore errors
    }

    return files;
  }

  getMetrics(filePath: string): CodeMetrics | undefined {
    return this.metrics.get(filePath);
  }

  getAllMetrics(): CodeMetrics[] {
    return Array.from(this.metrics.values());
  }

  generateReport(predictions: BugPrediction[]): string {
    let report = 'Bug Prediction Report\n';
    report += '====================\n\n';
    report += `Total files analyzed: ${this.metrics.size}\n`;
    report += `High-risk files: ${predictions.filter(p => p.probability >= 0.7).length}\n`;
    report += `Critical files: ${predictions.filter(p => p.severity === 'critical').length}\n\n`;

    report += 'Top Risky Files:\n';
    report += '----------------\n';

    for (const prediction of predictions.slice(0, 10)) {
      report += `${prediction.file}\n`;
      report += `  Probability: ${(prediction.probability * 100).toFixed(1)}%\n`;
      report += `  Severity: ${prediction.severity}\n`;
      report += `  Reason: ${prediction.reason}\n\n`;
    }

    return report;
  }
}

// Factory function for creating bug predictors
export const createBugPredictor = (config?: Partial<BugPredictionConfig>): BugPredictor => {
  return new BugPredictor(config);
};

// Helper function for analyzing code complexity
export const analyzeComplexity = (content: string): {
  cyclomatic: number;
  cognitive: number;
  halsteadVolume: number;
} => {
  // Simplified complexity analysis
  let cyclomatic = 1;
  let cognitive = 0;

  const lines = content.split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('if ') || trimmed.startsWith('else if ')) {
      cyclomatic++;
      cognitive++;
    }
    if (trimmed.startsWith('for ') || trimmed.startsWith('while ')) {
      cyclomatic++;
      cognitive += 2;
    }
  }

  return {
    cyclomatic,
    cognitive,
    halsteadVolume: Math.log2(cyclomatic + 1) * lines.length,
  };
};

// Helper function for detecting code smells
export const detectCodeSmells = (content: string): string[] => {
  const smells: string[] = [];
  const lines = content.split('\n');

  // Long methods
  let methodLength = 0;
  let inMethod = false;
  for (const line of lines) {
    if (line.includes('function') || line.includes('=>')) {
      inMethod = true;
      methodLength = 0;
    }
    if (inMethod) {
      methodLength++;
      if (methodLength > 50) {
        smells.push('Long method detected');
        inMethod = false;
      }
    }
  }

  // God class (simplified)
  if (lines.length > 500) {
    smells.push('Large file detected');
  }

  // Duplicate code (simplified)
  const uniqueLines = new Set(lines.map(l => l.trim()).filter(l => l.length > 0));
  if (lines.length - uniqueLines.size > 50) {
    smells.push('Significant code duplication');
  }

  return smells;
};

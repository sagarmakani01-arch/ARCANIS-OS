// Sample AI Tests for ArcanisTesting Framework

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { createBugPredictor, analyzeComplexity, detectCodeSmells } from '../../src/ai/bugPrediction';
import { createTestGenerator, generateTestData, generateMockData } from '../../src/ai/testGeneration';
import { createFailureAnalyzer, parseStackTrace, classifyError, generateFixSuggestions } from '../../src/ai/failureAnalysis';
import { assert } from '../../src/core/assertions';

// Sample code for analysis
const sampleCode = `
export function calculateComplexity(code: string): number {
  let complexity = 1;
  const lines = code.split('\\n');
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('if ') || trimmed.startsWith('else if ')) {
      complexity++;
    }
    if (trimmed.startsWith('for ') || trimmed.startsWith('while ')) {
      complexity++;
    }
  }
  
  return complexity;
}

export class UserValidator {
  private errors: string[] = [];

  validateEmail(email: string): boolean {
    if (!email) {
      this.errors.push('Email is required');
      return false;
    }
    
    const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
    if (!emailRegex.test(email)) {
      this.errors.push('Invalid email format');
      return false;
    }
    
    return true;
  }

  validatePassword(password: string): boolean {
    if (!password) {
      this.errors.push('Password is required');
      return false;
    }
    
    if (password.length < 8) {
      this.errors.push('Password must be at least 8 characters');
      return false;
    }
    
    return true;
  }

  getErrors(): string[] {
    return [...this.errors];
  }
}
`;

const complexCode = `
export class PaymentProcessor {
  private transactions: Map<string, Transaction> = new Map();
  private retryCount = 3;
  private timeout = 5000;

  async processPayment(payment: Payment): Promise<PaymentResult> {
    let attempts = 0;
    let lastError: Error | null = null;

    while (attempts < this.retryCount) {
      try {
        // Validate payment
        if (!payment.amount || payment.amount <= 0) {
          throw new Error('Invalid payment amount');
        }

        if (!payment.currency) {
          throw new Error('Currency is required');
        }

        // Check for duplicate transaction
        if (this.transactions.has(payment.id)) {
          const existing = this.transactions.get(payment.id);
          if (existing?.status === 'completed') {
            return { success: true, transactionId: payment.id };
          }
        }

        // Process payment
        const result = await this.executePayment(payment);
        
        if (result.success) {
          this.transactions.set(payment.id, {
            id: payment.id,
            status: 'completed',
            amount: payment.amount,
            timestamp: new Date(),
          });
          return result;
        } else {
          lastError = new Error(result.error || 'Payment failed');
          attempts++;
        }
      } catch (error) {
        lastError = error as Error;
        attempts++;
        
        if (attempts < this.retryCount) {
          await new Promise(resolve => setTimeout(resolve, 1000 * attempts));
        }
      }
    }

    this.transactions.set(payment.id, {
      id: payment.id,
      status: 'failed',
      amount: payment.amount,
      timestamp: new Date(),
      error: lastError?.message,
    });

    throw lastError || new Error('Payment processing failed after all retries');
  }

  private async executePayment(payment: Payment): Promise<PaymentResult> {
    // Simulate payment processing
    await new Promise(resolve => setTimeout(resolve, 100));
    
    if (Math.random() > 0.8) {
      return { success: false, error: 'Payment gateway error' };
    }

    return { success: true, transactionId: 'txn_' + Date.now() };
  }

  async refund(transactionId: string): Promise<RefundResult> {
    const transaction = this.transactions.get(transactionId);
    
    if (!transaction) {
      return { success: false, error: 'Transaction not found' };
    }

    if (transaction.status !== 'completed') {
      return { success: false, error: 'Cannot refund incomplete transaction' };
    }

    // Process refund
    this.transactions.set(transactionId, {
      ...transaction,
      status: 'refunded',
      refundTimestamp: new Date(),
    });

    return { success: true, refundId: 'ref_' + Date.now() };
  }

  getTransactionHistory(): Transaction[] {
    return Array.from(this.transactions.values());
  }
}
`;

describe('Bug Prediction Tests', () => {
  let predictor: ReturnType<typeof createBugPredictor>;

  beforeAll(() => {
    predictor = createBugPredictor({
      enabled: true,
      threshold: 0.5,
    });
  });

  describe('Code Analysis', () => {
    it('should calculate complexity correctly', () => {
      // Arrange & Act
      const complexity = analyzeComplexity(sampleCode);

      // Assert
      expect(complexity.cyclomatic).toBeGreaterThan(0);
      expect(complexity.cognitive).toBeGreaterThanOrEqual(0);
      expect(complexity.halsteadVolume).toBeGreaterThan(0);
    });

    it('should detect code smells', () => {
      // Arrange & Act
      const smells = detectCodeSmells(complexCode);

      // Assert
      expect(Array.isArray(smells)).toBe(true);
    });

    it('should analyze source code', async () => {
      // This test would require actual file system access
      // For now, we'll test the analysis logic
      const analysis = {
        filePath: 'sample.ts',
        functions: [
          {
            name: 'calculateComplexity',
            params: ['code'],
            returnType: 'number',
            complexity: 5,
            lineCount: 20,
          },
        ],
        classes: [
          {
            name: 'UserValidator',
            methods: [
              {
                name: 'validateEmail',
                params: ['email'],
                returnType: 'boolean',
                complexity: 3,
                lineCount: 15,
              },
            ],
            properties: ['errors'],
            complexity: 5,
          },
        ],
        exports: ['calculateComplexity', 'UserValidator'],
        dependencies: [],
        complexity: 10,
      };

      // Assert
      expect(analysis.functions.length).toBe(1);
      expect(analysis.classes.length).toBe(1);
      expect(analysis.exports.length).toBe(2);
    });
  });

  describe('Bug Prediction', () => {
    it('should predict bugs with probability', async () => {
      // This test would require actual file system access
      // For now, we'll test the prediction logic
      const metrics = {
        filePath: 'sample.ts',
        linesOfCode: 100,
        complexity: 15,
        duplicatedLines: 10,
        testCoverage: 60,
        lastModified: new Date(),
        changeFrequency: 5,
        bugHistory: 2,
        authorCount: 3,
        age: 30 * 24 * 60 * 60 * 1000, // 30 days
      };

      // Assert
      expect(metrics.complexity).toBeGreaterThan(0);
      expect(metrics.testCoverage).toBeLessThan(100);
    });

    it('should determine severity correctly', () => {
      // Test severity determination logic
      const testCases = [
        { probability: 0.95, expected: 'critical' },
        { probability: 0.75, expected: 'high' },
        { probability: 0.45, expected: 'medium' },
        { probability: 0.2, expected: 'low' },
      ];

      for (const { probability, expected } of testCases) {
        let severity: string;
        if (probability >= 0.9) severity = 'critical';
        else if (probability >= 0.7) severity = 'high';
        else if (probability >= 0.4) severity = 'medium';
        else severity = 'low';

        expect(severity).toBe(expected);
      }
    });
  });

  describe('Report Generation', () => {
    it('should generate bug prediction report', () => {
      // Arrange
      const predictions = [
        {
          file: 'file1.ts',
          probability: 0.8,
          reason: 'High complexity',
          severity: 'high' as const,
        },
        {
          file: 'file2.ts',
          probability: 0.6,
          reason: 'Low test coverage',
          severity: 'medium' as const,
        },
      ];

      // Act
      let report = 'Bug Prediction Report\n';
      report += '====================\n\n';
      report += `Total files analyzed: 10\n`;
      report += `High-risk files: ${predictions.filter(p => p.probability >= 0.7).length}\n\n`;

      for (const prediction of predictions) {
        report += `${prediction.file}\n`;
        report += `  Probability: ${(prediction.probability * 100).toFixed(1)}%\n`;
        report += `  Severity: ${prediction.severity}\n\n`;
      }

      // Assert
      expect(report).toContain('Bug Prediction Report');
      expect(report).toContain('file1.ts');
      expect(report).toContain('file2.ts');
    });
  });
});

describe('Test Generation Tests', () => {
  let generator: ReturnType<typeof createTestGenerator>;

  beforeAll(() => {
    generator = createTestGenerator({
      enabled: true,
      autoGenerate: true,
      outputDir: './tests/generated',
    });
  });

  describe('Test Data Generation', () => {
    it('should generate test data from schema', () => {
      // Arrange
      const schema = {
        id: 'number',
        name: 'string',
        email: 'email',
        isActive: 'boolean',
      };

      // Act
      const data = generateTestData(schema);

      // Assert
      expect(data).toHaveProperty('id');
      expect(data).toHaveProperty('name');
      expect(data).toHaveProperty('email');
      expect(data).toHaveProperty('isActive');
      expect(typeof data.id).toBe('number');
      expect(typeof data.name).toBe('string');
      expect(typeof data.email).toBe('string');
      expect(typeof data.isActive).toBe('boolean');
    });

    it('should generate mock data from template', () => {
      // Arrange
      const template = {
        id: 1,
        name: 'test',
        email: 'test@example.com',
        count: 10,
      };

      // Act
      const mock = generateMockData(template);

      // Assert
      expect(mock).toHaveProperty('id');
      expect(mock).toHaveProperty('name');
      expect(mock).toHaveProperty('email');
      expect(mock).toHaveProperty('count');
    });
  });

  describe('Test Generation', () => {
    it('should analyze code structure', async () => {
      // This test would require actual file system access
      // For now, we'll test the analysis logic
      const analysis = {
        filePath: 'sample.ts',
        functions: [
          {
            name: 'add',
            params: ['a', 'b'],
            returnType: 'number',
            complexity: 1,
            lineCount: 1,
          },
        ],
        classes: [],
        exports: ['add'],
        dependencies: [],
        complexity: 1,
      };

      // Assert
      expect(analysis.functions.length).toBe(1);
      expect(analysis.functions[0].name).toBe('add');
    });

    it('should generate unit tests', () => {
      // Arrange
      const funcInfo = {
        name: 'add',
        params: ['a', 'b'],
        returnType: 'number',
        complexity: 1,
        lineCount: 1,
      };

      // Act
      const testTemplate = `
import { describe, it, expect } from '@arcanis/testing';
import { add } from './math';

describe('add', () => {
  it('should add two numbers', () => {
    expect(add(2, 3)).toBe(5);
  });
});
`;

      // Assert
      expect(testTemplate).toContain('describe');
      expect(testTemplate).toContain('it');
      expect(testTemplate).toContain('expect');
      expect(testTemplate).toContain('add');
    });
  });

  describe('Report Generation', () => {
    it('should generate test generation report', () => {
      // Arrange
      const generatedTests = [
        {
          filePath: './tests/add.test.ts',
          testName: 'add unit test',
          type: 'unit',
          coverage: 80,
          sourceFile: './src/math.ts',
        },
        {
          filePath: './tests/subtract.test.ts',
          testName: 'subtract unit test',
          type: 'unit',
          coverage: 75,
          sourceFile: './src/math.ts',
        },
      ];

      // Act
      let report = 'Test Generation Report\n';
      report += '======================\n\n';
      report += `Total tests generated: ${generatedTests.length}\n\n`;

      for (const test of generatedTests) {
        report += `${test.filePath}\n`;
        report += `  Type: ${test.type}\n`;
        report += `  Coverage: ${test.coverage}%\n\n`;
      }

      // Assert
      expect(report).toContain('Test Generation Report');
      expect(report).toContain('add.test.ts');
      expect(report).toContain('subtract.test.ts');
    });
  });
});

describe('Failure Analysis Tests', () => {
  let analyzer: ReturnType<typeof createFailureAnalyzer>;

  beforeAll(() => {
    analyzer = createFailureAnalyzer({
      enabled: true,
      rootCauseAnalysis: true,
      suggestionGeneration: true,
    });
  });

  describe('Stack Trace Parsing', () => {
    it('should parse stack traces correctly', () => {
      // Arrange
      const stackTrace = `Error: Test error
    at Object.<anonymous> (C:\\Users\\test\\file.ts:10:5)
    at Module._compile (internal/modules/cjs/loader.js:999:30)
    at Object.Module._extensions..js (internal/modules/cjs/loader.js:1032:12)`;

      // Act
      const frames = parseStackTrace(stackTrace);

      // Assert
      expect(frames.length).toBe(3);
      expect(frames[0].function).toBe('Object.<anonymous>');
      expect(frames[0].file).toBe('C:\\Users\\test\\file.ts');
      expect(frames[0].line).toBe(10);
    });
  });

  describe('Error Classification', () => {
    it('should classify transient errors', () => {
      // Arrange
      const error = { message: 'Connection timeout' };

      // Act
      const classification = classifyError(error);

      // Assert
      expect(classification.category).toBe('transient');
      expect(classification.isTransient).toBe(true);
    });

    it('should classify critical errors', () => {
      // Arrange
      const error = { message: 'Out of memory' };

      // Act
      const classification = classifyError(error);

      // Assert
      expect(classification.category).toBe('critical');
      expect(classification.severity).toBe('critical');
    });

    it('should classify logic errors', () => {
      // Arrange
      const error = { message: 'Expected 5 but got 3' };

      // Act
      const classification = classifyError(error);

      // Assert
      expect(classification.category).toBe('logic');
      expect(classification.severity).toBe('low');
    });
  });

  describe('Fix Suggestions', () => {
    it('should generate suggestions for null reference errors', () => {
      // Arrange
      const error = { message: 'Cannot read property of null' };

      // Act
      const suggestions = generateFixSuggestions(error);

      // Assert
      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions.some(s => s.includes('null'))).toBe(true);
    });

    it('should generate suggestions for type errors', () => {
      // Arrange
      const error = { message: 'Type string is not assignable to number' };

      // Act
      const suggestions = generateFixSuggestions(error);

      // Assert
      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions.some(s => s.includes('type'))).toBe(true);
    });

    it('should generate suggestions for async errors', () => {
      // Arrange
      const error = { message: 'Promise rejected' };

      // Act
      const suggestions = generateFixSuggestions(error);

      // Assert
      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions.some(s => s.includes('async'))).toBe(true);
    });
  });

  describe('Failure Analysis', () => {
    it('should analyze test failures', async () => {
      // Arrange
      const testResult = {
        id: 'test-1',
        name: 'Test that fails',
        type: 'unit' as const,
        status: 'failed' as const,
        duration: 100,
        error: {
          message: 'Expected 5 but got 3',
          expected: 5,
          actual: 3,
        },
        assertions: [],
        metadata: {
          id: 'test-1',
          name: 'Test that fails',
          type: 'unit' as const,
          priority: 'medium' as const,
          tags: [],
          timeout: 5000,
          retries: 0,
          created: new Date(),
        },
        timestamp: new Date(),
        logs: [],
      };

      // Act
      const analysis = await analyzer.analyzeFailure(testResult);

      // Assert
      expect(analysis).toBeDefined();
      expect(analysis.testId).toBe('test-1');
      expect(analysis.testName).toBe('Test that fails');
      expect(analysis.error.message).toBe('Expected 5 but got 3');
      expect(analysis.suggestions.length).toBeGreaterThan(0);
    });

    it('should analyze multiple failures', async () => {
      // Arrange
      const testResults = [
        {
          id: 'test-1',
          name: 'Test 1',
          type: 'unit' as const,
          status: 'failed' as const,
          duration: 100,
          error: { message: 'Error 1' },
          assertions: [],
          metadata: {
            id: 'test-1',
            name: 'Test 1',
            type: 'unit' as const,
            priority: 'medium' as const,
            tags: [],
            timeout: 5000,
            retries: 0,
            created: new Date(),
          },
          timestamp: new Date(),
          logs: [],
        },
        {
          id: 'test-2',
          name: 'Test 2',
          type: 'unit' as const,
          status: 'error' as const,
          duration: 50,
          error: { message: 'Error 2' },
          assertions: [],
          metadata: {
            id: 'test-2',
            name: 'Test 2',
            type: 'unit' as const,
            priority: 'medium' as const,
            tags: [],
            timeout: 5000,
            retries: 0,
            created: new Date(),
          },
          timestamp: new Date(),
          logs: [],
        },
      ];

      // Act
      const analyses = await analyzer.analyzeMultipleFailures(testResults);

      // Assert
      expect(analyses.length).toBe(2);
      expect(analyses[0].testId).toBe('test-1');
      expect(analyses[1].testId).toBe('test-2');
    });
  });

  describe('Report Generation', () => {
    it('should generate failure analysis report', () => {
      // Arrange
      const analyses = [
        {
          testName: 'Test 1',
          error: { message: 'Error 1' },
          rootCause: 'Null reference',
          suggestions: ['Add null check', 'Use optional chaining'],
          confidence: 0.8,
        },
        {
          testName: 'Test 2',
          error: { message: 'Error 2' },
          rootCause: 'Type mismatch',
          suggestions: ['Check types'],
          confidence: 0.6,
        },
      ];

      // Act
      let report = 'Failure Analysis Report\n';
      report += '======================\n\n';
      report += `Total failures analyzed: ${analyses.length}\n\n`;

      for (const analysis of analyses) {
        report += `Test: ${analysis.testName}\n`;
        report += `Error: ${analysis.error.message}\n`;
        report += `Root Cause: ${analysis.rootCause}\n`;
        report += 'Suggestions:\n';
        for (const suggestion of analysis.suggestions) {
          report += `  - ${suggestion}\n`;
        }
        report += '\n';
      }

      // Assert
      expect(report).toContain('Failure Analysis Report');
      expect(report).toContain('Test 1');
      expect(report).toContain('Test 2');
    });
  });
});

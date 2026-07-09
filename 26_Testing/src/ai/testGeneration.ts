// Test Generation Module for ArcanisTesting Framework

import * as fs from 'fs';
import * as path from 'path';
import { EventEmitter } from 'events';
import { generateId } from '../core/utilities';
import { TestCase, TestType, TestPriority } from '../core/types';

export interface TestGenerationConfig {
  enabled: boolean;
  autoGenerate: boolean;
  coverageTarget: number;
  outputDir: string;
  templates: TestTemplate[];
}

export interface TestTemplate {
  name: string;
  type: TestType;
  template: string;
  variables: string[];
}

export interface GeneratedTest {
  id: string;
  filePath: string;
  testName: string;
  type: TestType;
  content: string;
  timestamp: Date;
  sourceFile: string;
  coverage: number;
}

export interface CodeAnalysis {
  filePath: string;
  functions: FunctionInfo[];
  classes: ClassInfo[];
  exports: string[];
  dependencies: string[];
  complexity: number;
}

export interface FunctionInfo {
  name: string;
  params: string[];
  returnType: string;
  complexity: number;
  lineCount: number;
}

export interface ClassInfo {
  name: string;
  methods: FunctionInfo[];
  properties: string[];
  complexity: number;
}

export class TestGenerator extends EventEmitter {
  private config: TestGenerationConfig;
  private generatedTests: GeneratedTest[] = [];

  constructor(config: Partial<TestGenerationConfig> = {}) {
    super();
    this.config = {
      enabled: true,
      autoGenerate: true,
      coverageTarget: 80,
      outputDir: './tests/generated',
      templates: this.getDefaultTemplates(),
      ...config,
    };
  }

  private getDefaultTemplates(): TestTemplate[] {
    return [
      {
        name: 'unit-test',
        type: 'unit',
        template: `
import { describe, it, expect } from '@arcanis/testing';
import { {{functionName}} } from '{{importPath}}';

describe('{{functionName}}', () => {
  it('should handle normal case', async () => {
    // Arrange
    const input = {{testInput}};
    
    // Act
    const result = {{functionName}}({{callParams}});
    
    // Assert
    expect(result).toEqual({{expectedOutput}});
  });

  it('should handle edge cases', async () => {
    // Arrange
    const input = {{edgeInput}};
    
    // Act
    const result = {{functionName}}({{edgeCallParams}});
    
    // Assert
    expect(result).toEqual({{edgeExpectedOutput}});
  });

  it('should throw error for invalid input', async () => {
    // Arrange
    const input = {{invalidInput}};
    
    // Act & Assert
    expect(() => {{functionName}}({{invalidCallParams}})).toThrow({{errorMessage}});
  });
});
`,
        variables: [
          'functionName',
          'importPath',
          'testInput',
          'callParams',
          'expectedOutput',
          'edgeInput',
          'edgeCallParams',
          'edgeExpectedOutput',
          'invalidInput',
          'invalidCallParams',
          'errorMessage',
        ],
      },
      {
        name: 'integration-test',
        type: 'integration',
        template: `
import { describe, it, expect, beforeAll, afterAll } from '@arcanis/testing';
import {{className}} from '{{importPath}}';

describe('{{className}} Integration', () => {
  let instance: {{className}};

  beforeAll(async () => {
    instance = new {{className}}();
    await instance.initialize();
  });

  afterAll(async () => {
    await instance.cleanup();
  });

  it('should perform {{operation}} successfully', async () => {
    // Arrange
    const input = {{testInput}};
    
    // Act
    const result = await instance.{{methodName}}({{callParams}});
    
    // Assert
    expect(result).toBeDefined();
    expect(result.{{assertProperty}}).toEqual({{expectedValue}});
  });

  it('should handle errors gracefully', async () => {
    // Arrange
    const invalidInput = {{invalidInput}};
    
    // Act & Assert
    await expect(instance.{{methodName}}({{invalidCallParams}})).rejects.toThrow({{errorMessage}});
  });
});
`,
        variables: [
          'className',
          'importPath',
          'operation',
          'methodName',
          'testInput',
          'callParams',
          'assertProperty',
          'expectedValue',
          'invalidInput',
          'invalidCallParams',
          'errorMessage',
        ],
      },
      {
        name: 'performance-test',
        type: 'performance',
        template: `
import { describe, it, expect } from '@arcanis/testing';
import { benchmark, compareBenchmarks } from '@arcanis/testing/performance';
import {{functionName}} from '{{importPath}}';

describe('{{functionName}} Performance', () => {
  it('should complete within acceptable time', async () => {
    // Arrange
    const input = {{testInput}};
    const maxDuration = {{maxDuration}};
    
    // Act
    const result = await benchmark('{{functionName}}', async () => {
      {{functionName}}({{callParams}});
    }, {{iterations}});
    
    // Assert
    expect(result.avg).toBeLessThan(maxDuration);
  });

  it('should handle load efficiently', async () => {
    // Arrange
    const concurrency = {{concurrency}};
    const iterations = {{iterations}};
    
    // Act
    const promises = Array(concurrency).fill(null).map(() =>
      benchmark('{{functionName}}-load', async () => {
        {{functionName}}({{callParams}});
      }, iterations)
    );
    
    const results = await Promise.all(promises);
    
    // Assert
    results.forEach(result => {
      expect(result.avg).toBeLessThan({{maxDuration}});
    });
  });
});
`,
        variables: [
          'functionName',
          'importPath',
          'testInput',
          'maxDuration',
          'callParams',
          'iterations',
          'concurrency',
        ],
      },
    ];
  }

  async analyzeSource(filePath: string): Promise<CodeGenalysis> {
    const content = await fs.promises.readFile(filePath, 'utf-8');
    return this.parseCode(content, filePath);
  }

  private parseCode(content: string, filePath: string): CodeAnalysis {
    const functions = this.extractFunctions(content);
    const classes = this.extractClasses(content);
    const exports = this.extractExports(content);
    const dependencies = this.extractDependencies(content);
    const complexity = this.calculateComplexity(content);

    return {
      filePath,
      functions,
      classes,
      exports,
      dependencies,
      complexity,
    };
  }

  private extractFunctions(content: string): FunctionInfo[] {
    const functions: FunctionInfo[] = [];
    const functionPattern = /(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*(\w+))?\s*\{/g;
    let match;

    while ((match = functionPattern.exec(content)) !== null) {
      functions.push({
        name: match[1],
        params: match[2].split(',').map(p => p.trim().split(':')[0].trim()),
        returnType: match[3] || 'void',
        complexity: this.calculateFunctionComplexity(content, match[1]),
        lineCount: this.countFunctionLines(content, match[1]),
      });
    }

    return functions;
  }

  private extractClasses(content: string): ClassInfo[] {
    const classes: ClassInfo[] = [];
    const classPattern = /(?:export\s+)?class\s+(\w+)[^{]*\{/g;
    let match;

    while ((match = classPattern.exec(content)) !== null) {
      const className = match[1];
      const classContent = this.extractClassContent(content, match.index);
      
      classes.push({
        name: className,
        methods: this.extractFunctions(classContent),
        properties: this.extractProperties(classContent),
        complexity: this.calculateComplexity(classContent),
      });
    }

    return classes;
  }

  private extractClassContent(content: string, startIndex: number): string {
    let braceCount = 0;
    let inClass = false;
    let classContent = '';

    for (let i = startIndex; i < content.length; i++) {
      if (content[i] === '{') {
        braceCount++;
        inClass = true;
      } else if (content[i] === '}') {
        braceCount--;
        if (inClass && braceCount === 0) {
          return classContent;
        }
      }
      if (inClass) {
        classContent += content[i];
      }
    }

    return classContent;
  }

  private extractProperties(content: string): string[] {
    const properties: string[] = [];
    const propertyPattern = /(?:private|protected|public)\s+(\w+)\s*[=:]/g;
    let match;

    while ((match = propertyPattern.exec(content)) !== null) {
      properties.push(match[1]);
    }

    return properties;
  }

  private extractExports(content: string): string[] {
    const exports: string[] = [];
    const exportPattern = /export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)/g;
    let match;

    while ((match = exportPattern.exec(content)) !== null) {
      exports.push(match[1]);
    }

    return exports;
  }

  private extractDependencies(content: string): string[] {
    const dependencies: string[] = [];
    const importPattern = /import\s+.*?\s+from\s+['"]([^'"]+)['"]/g;
    let match;

    while ((match = importPattern.exec(content)) !== null) {
      dependencies.push(match[1]);
    }

    return dependencies;
  }

  private calculateComplexity(content: string): number {
    let complexity = 1;
    const lines = content.split('\n');

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('if ') || trimmed.startsWith('else if ')) {
        complexity++;
      }
      if (trimmed.startsWith('for ') || trimmed.startsWith('while ')) {
        complexity++;
      }
      if (trimmed.startsWith('switch ')) {
        complexity++;
      }
      if (trimmed.includes('&&') || trimmed.includes('||')) {
        complexity++;
      }
    }

    return complexity;
  }

  private calculateFunctionComplexity(content: string, functionName: string): number {
    const functionPattern = new RegExp(`function\\s+${functionName}\\s*\\([^)]*\\)\\s*\\{([\\s\\S]*?)\\}`, 'g');
    const match = functionPattern.exec(content);
    
    if (match) {
      return this.calculateComplexity(match[1]);
    }
    
    return 1;
  }

  private countFunctionLines(content: string, functionName: string): number {
    const functionPattern = new RegExp(`function\\s+${functionName}\\s*\\([^)]*\\)\\s*\\{([\\s\\S]*?)\\}`, 'g');
    const match = functionPattern.exec(content);
    
    if (match) {
      return match[1].split('\n').length;
    }
    
    return 0;
  }

  async generateTests(filePath: string): Promise<GeneratedTest[]> {
    const analysis = await this.analyzeSource(filePath);
    const tests: GeneratedTest[] = [];

    // Generate tests for functions
    for (const func of analysis.functions) {
      const test = await this.generateFunctionTest(filePath, func);
      if (test) {
        tests.push(test);
      }
    }

    // Generate tests for classes
    for (const cls of analysis.classes) {
      const classTests = await this.generateClassTests(filePath, cls);
      tests.push(...classTests);
    }

    this.generatedTests.push(...tests);
    this.emit('tests:generated', tests);

    return tests;
  }

  private async generateFunctionTest(
    sourceFile: string,
    func: FunctionInfo
  ): Promise<GeneratedTest | null> {
    if (func.params.length === 0 && func.returnType === 'void') {
      return null;
    }

    const template = this.config.templates.find(t => t.type === 'unit');
    if (!template) {
      return null;
    }

    const importPath = this.generateImportPath(sourceFile);
    const testContent = this.fillTemplate(template.template, {
      functionName: func.name,
      importPath,
      testInput: this.generateTestInput(func),
      callParams: this.generateCallParams(func),
      expectedOutput: this.generateExpectedOutput(func),
      edgeInput: this.generateEdgeInput(func),
      edgeCallParams: this.generateCallParams(func),
      edgeExpectedOutput: this.generateExpectedOutput(func),
      invalidInput: this.generateInvalidInput(func),
      invalidCallParams: this.generateInvalidCallParams(func),
      errorMessage: this.generateErrorMessage(func),
    });

    const testFileName = `${func.name}.test.ts`;
    const testFilePath = path.join(this.config.outputDir, testFileName);

    return {
      id: generateId(),
      filePath: testFilePath,
      testName: `${func.name} unit test`,
      type: 'unit',
      content: testContent,
      timestamp: new Date(),
      sourceFile,
      coverage: 80,
    };
  }

  private async generateClassTests(
    sourceFile: string,
    cls: ClassInfo
  ): Promise<GeneratedTest[]> {
    const tests: GeneratedTest[] = [];

    for (const method of cls.methods) {
      const test = await this.generateMethodTest(sourceFile, cls.name, method);
      if (test) {
        tests.push(test);
      }
    }

    return tests;
  }

  private async generateMethodTest(
    sourceFile: string,
    className: string,
    method: FunctionInfo
  ): Promise<GeneratedTest | null> {
    const template = this.config.templates.find(t => t.type === 'integration');
    if (!template) {
      return null;
    }

    const importPath = this.generateImportPath(sourceFile);
    const testContent = this.fillTemplate(template.template, {
      className,
      importPath,
      operation: method.name,
      methodName: method.name,
      testInput: this.generateTestInput(method),
      callParams: this.generateCallParams(method),
      assertProperty: 'result',
      expectedValue: this.generateExpectedOutput(method),
      invalidInput: this.generateInvalidInput(method),
      invalidCallParams: this.generateInvalidCallParams(method),
      errorMessage: this.generateErrorMessage(method),
    });

    const testFileName = `${className}.${method.name}.integration.test.ts`;
    const testFilePath = path.join(this.config.outputDir, testFileName);

    return {
      id: generateId(),
      filePath: testFilePath,
      testName: `${className}.${method.name} integration test`,
      type: 'integration',
      content: testContent,
      timestamp: new Date(),
      sourceFile,
      coverage: 70,
    };
  }

  private generateImportPath(filePath: string): string {
    const relativePath = path.relative(this.config.outputDir, filePath);
    return relativePath.replace(/\.ts$/, '').replace(/\\/g, '/');
  }

  private generateTestInput(func: FunctionInfo): string {
    if (func.params.length === 0) {
      return 'undefined';
    }

    const inputs: string[] = [];
    for (const param of func.params) {
      inputs.push(this.generateTestValue(param));
    }

    return inputs.join(', ');
  }

  private generateTestValue(paramName: string): string {
    // Generate test values based on parameter name
    const lowerName = paramName.toLowerCase();
    
    if (lowerName.includes('id')) {
      return '1';
    }
    if (lowerName.includes('name')) {
      return "'test'";
    }
    if (lowerName.includes('email')) {
      return "'test@example.com'";
    }
    if (lowerName.includes('count') || lowerName.includes('number')) {
      return '10';
    }
    if (lowerName.includes('flag') || lowerName.includes('boolean')) {
      return 'true';
    }
    if (lowerName.includes('array') || lowerName.includes('list')) {
      return '[]';
    }
    if (lowerName.includes('object') || lowerName.includes('data')) {
      return '{}';
    }

    return "'test'";
  }

  private generateCallParams(func: FunctionInfo): string {
    return func.params.map(p => this.generateTestValue(p)).join(', ');
  }

  private generateExpectedOutput(func: FunctionInfo): string {
    if (func.returnType === 'void') {
      return 'undefined';
    }
    if (func.returnType === 'string') {
      return "'expected'";
    }
    if (func.returnType === 'number') {
      return '42';
    }
    if (func.returnType === 'boolean') {
      return 'true';
    }
    if (func.returnType.includes('[]')) {
      return '[]';
    }

    return '{}';
  }

  private generateEdgeInput(func: FunctionInfo): string {
    if (func.params.length === 0) {
      return 'undefined';
    }

    const inputs: string[] = [];
    for (const param of func.params) {
      inputs.push(this.generateEdgeValue(param));
    }

    return inputs.join(', ');
  }

  private generateEdgeValue(paramName: string): string {
    const lowerName = paramName.toLowerCase();
    
    if (lowerName.includes('id')) {
      return '0';
    }
    if (lowerName.includes('name')) {
      return "''";
    }
    if (lowerName.includes('email')) {
      return "'invalid-email'";
    }
    if (lowerName.includes('count') || lowerName.includes('number')) {
      return '-1';
    }

    return 'null';
  }

  private generateInvalidInput(func: FunctionInfo): string {
    if (func.params.length === 0) {
      return 'undefined';
    }

    return 'null';
  }

  private generateInvalidCallParams(func: FunctionInfo): string {
    return func.params.map(() => 'null').join(', ');
  }

  private generateErrorMessage(func: FunctionInfo): string {
    return `'Invalid input for ${func.name}'`;
  }

  private fillTemplate(template: string, variables: Record<string, string>): string {
    let result = template;
    
    for (const [key, value] of Object.entries(variables)) {
      result = result.replace(new RegExp(`{{${key}}}`, 'g'), value);
    }

    return result;
  }

  async saveTests(tests: GeneratedTest[]): Promise<void> {
    // Ensure output directory exists
    if (!fs.existsSync(this.config.outputDir)) {
      fs.mkdirSync(this.config.outputDir, { recursive: true });
    }

    for (const test of tests) {
      await fs.promises.writeFile(test.filePath, test.content);
      this.emit('test:saved', test);
    }
  }

  getGeneratedTests(): GeneratedTest[] {
    return [...this.generatedTests];
  }

  getTestsByType(type: TestType): GeneratedTest[] {
    return this.generatedTests.filter(t => t.type === type);
  }

  generateReport(): string {
    let report = 'Test Generation Report\n';
    report += '======================\n\n';
    report += `Total tests generated: ${this.generatedTests.length}\n`;
    report += `Unit tests: ${this.getGeneratedTests().filter(t => t.type === 'unit').length}\n`;
    report += `Integration tests: ${this.getGeneratedTests().filter(t => t.type === 'integration').length}\n`;
    report += `Performance tests: ${this.getGeneratedTests().filter(t => t.type === 'performance').length}\n\n`;

    report += 'Generated Files:\n';
    report += '----------------\n';

    for (const test of this.generatedTests) {
      report += `${test.filePath}\n`;
      report += `  Type: ${test.type}\n`;
      report += `  Coverage: ${test.coverage}%\n`;
      report += `  Source: ${test.sourceFile}\n\n`;
    }

    return report;
  }
}

// Factory function for creating test generators
export const createTestGenerator = (config?: Partial<TestGenerationConfig>): TestGenerator => {
  return new TestGenerator(config);
};

// Helper function for generating test data
export const generateTestData = (schema: Record<string, string>): Record<string, unknown> => {
  const data: Record<string, unknown> = {};

  for (const [key, type] of Object.entries(schema)) {
    switch (type) {
      case 'string':
        data[key] = `test_${key}`;
        break;
      case 'number':
        data[key] = Math.floor(Math.random() * 100);
        break;
      case 'boolean':
        data[key] = Math.random() > 0.5;
        break;
      case 'email':
        data[key] = `test_${Date.now()}@example.com`;
        break;
      case 'date':
        data[key] = new Date().toISOString();
        break;
      case 'array':
        data[key] = [];
        break;
      case 'object':
        data[key] = {};
        break;
      default:
        data[key] = null;
    }
  }

  return data;
};

// Helper function for generating mock data
export const generateMockData = <T>(template: T): T => {
  const mock = { ...template };
  
  for (const key of Object.keys(mock)) {
    const value = (mock as any)[key];
    if (typeof value === 'string') {
      (mock as any)[key] = `mock_${key}`;
    } else if (typeof value === 'number') {
      (mock as any)[key] = Math.floor(Math.random() * 100);
    } else if (typeof value === 'boolean') {
      (mock as any)[key] = Math.random() > 0.5;
    }
  }

  return mock;
};

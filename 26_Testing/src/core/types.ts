// Core types for ArcanisTesting Framework

export type TestType = 'unit' | 'integration' | 'system' | 'performance';

export type TestStatus = 'pending' | 'running' | 'passed' | 'failed' | 'skipped' | 'error';

export type TestPriority = 'low' | 'medium' | 'high' | 'critical';

export interface TestMetadata {
  id: string;
  name: string;
  type: TestType;
  priority: TestPriority;
  tags: string[];
  timeout: number;
  retries: number;
  created: Date;
  lastRun?: Date;
}

export interface TestCase {
  metadata: TestMetadata;
  setup?: () => Promise<void> | void;
  execute: () => Promise<void> | void;
  teardown?: () => Promise<void> | void;
}

export interface TestResult {
  id: string;
  name: string;
  type: TestType;
  status: TestStatus;
  duration: number;
  error?: TestError;
  assertions: AssertionResult[];
  metadata: TestMetadata;
  timestamp: Date;
  logs: string[];
}

export interface TestError {
  message: string;
  stack?: string;
  expected?: unknown;
  actual?: unknown;
}

export interface AssertionResult {
  passed: boolean;
  message: string;
  expected?: unknown;
  actual?: unknown;
  duration: number;
}

export interface TestSuite {
  id: string;
  name: string;
  description: string;
  type: TestType;
  tests: TestCase[];
  beforeEach?: () => Promise<void> | void;
  afterEach?: () => Promise<void> | void;
  beforeAll?: () => Promise<void> | void;
  afterAll?: () => Promise<void> | void;
}

export interface SuiteResult {
  id: string;
  name: string;
  type: TestType;
  tests: TestResult[];
  duration: number;
  timestamp: Date;
}

export interface TestReport {
  id: string;
  timestamp: Date;
  duration: number;
  summary: TestSummary;
  suites: SuiteResult[];
  performance?: PerformanceMetrics;
  aiAnalysis?: AIAnalysis;
}

export interface TestSummary {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  errors: number;
  duration: number;
  coverage?: CoverageReport;
}

export interface CoverageReport {
  lines: CoverageMetric;
  functions: CoverageMetric;
  branches: CoverageMetric;
  statements: CoverageMetric;
}

export interface CoverageMetric {
  total: number;
  covered: number;
  skipped: number;
  percentage: number;
}

export interface PerformanceMetrics {
  responseTime: PerformanceMetric;
  throughput: PerformanceMetric;
  errorRate: PerformanceMetric;
  cpuUsage: PerformanceMetric;
  memoryUsage: PerformanceMetric;
}

export interface PerformanceMetric {
  avg: number;
  min: number;
  max: number;
  p50: number;
  p90: number;
  p95: number;
  p99: number;
}

export interface AIAnalysis {
  bugPrediction: BugPrediction[];
  testSuggestions: TestSuggestion[];
  failureAnalysis: FailureAnalysis[];
}

export interface BugPrediction {
  file: string;
  line?: number;
  probability: number;
  reason: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface TestSuggestion {
  file: string;
  type: TestType;
  description: string;
  priority: TestPriority;
}

export interface FailureAnalysis {
  testId: string;
  testName: string;
  error: string;
  rootCause?: string;
  suggestions: string[];
  relatedFailures: string[];
}

export interface TestConfig {
  framework: {
    name: string;
    version: string;
    defaultTimeout: number;
    parallel: boolean;
    maxWorkers: number;
  };
  testing: {
    unit: {
      enabled: boolean;
      timeout: number;
      coverageThreshold: number;
    };
    integration: {
      enabled: boolean;
      timeout: number;
      retryCount: number;
    };
    system: {
      enabled: boolean;
      timeout: number;
      screenshotOnFailure: boolean;
    };
    performance: {
      enabled: boolean;
      thresholds: PerformanceThresholds;
    };
  };
  reports: ReportConfig;
  ai: AIConfig;
  automation: AutomationConfig;
}

export interface PerformanceThresholds {
  responseTime: number;
  throughput: number;
  errorRate: number;
  cpuUsage: number;
  memoryUsage: number;
}

export interface ReportConfig {
  formats: string[];
  outputDir: string;
  generateOnFailure: boolean;
  includeScreenshots: boolean;
}

export interface AIConfig {
  enabled: boolean;
  bugPrediction: {
    enabled: boolean;
    model: string;
    threshold: number;
  };
  testGeneration: {
    enabled: boolean;
    autoGenerate: boolean;
    coverageTarget: number;
  };
  failureAnalysis: {
    enabled: boolean;
    rootCauseAnalysis: boolean;
    suggestionGeneration: boolean;
  };
}

export interface AutomationConfig {
  discovery: {
    enabled: boolean;
    patterns: string[];
    exclude: string[];
  };
  continuousTesting: {
    enabled: boolean;
    watchMode: boolean;
    onCommit: boolean;
    onPush: boolean;
    onPR: boolean;
  };
}

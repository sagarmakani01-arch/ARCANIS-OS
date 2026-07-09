# ArcanisTesting Framework

**Complete Testing Ecosystem with AI-Powered Features**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)

## Overview

ArcanisTesting is a comprehensive testing framework that provides:

- **Testing**: Unit, Integration, System, and Performance testing
- **Automation**: Test discovery, reports, and continuous testing
- **AI Features**: Bug prediction, test generation, and failure analysis

## Features

### Testing Capabilities

#### Unit Testing
- Fast and isolated test execution
- Rich assertion library
- Mocking and spying utilities
- Test isolation and cleanup

#### Integration Testing
- External dependency management
- Database, API, file, and cache testing
- Retry mechanisms for flaky tests
- Automatic cleanup and setup

#### System Testing
- End-to-end application testing
- Page Object Model support
- Network request/response capture
- Screenshot and video recording

#### Performance Testing
- Load testing with configurable concurrency
- Stress testing to find breaking points
- Spike testing for sudden load increases
- Soak testing for endurance validation
- Benchmarking and comparison utilities

### Automation Features

#### Test Discovery
- Automatic test file detection
- Pattern-based discovery
- Test categorization and filtering
- Watch mode for continuous discovery

#### Test Reports
- Multiple output formats (Console, JSON, HTML, CSV, XML)
- Detailed test summaries
- Performance metrics
- Historical trend analysis

#### Continuous Testing
- Git hook integration
- Watch mode with debouncing
- CI/CD pipeline support
- Notification system

### AI-Powered Features

#### Bug Prediction
- Code complexity analysis
- Risk factor identification
- Probability-based predictions
- Severity classification

#### Test Generation
- Automatic test creation
- Template-based generation
- Test data generation
- Mock data creation

#### Failure Analysis
- Root cause analysis
- Pattern matching
- Fix suggestion generation
- Related failure detection

## Installation

```bash
npm install arcanis-testing
```

## Quick Start

### Basic Unit Test

```typescript
import { describe, it, expect } from '@arcanis/testing';

describe('Math Operations', () => {
  it('should add two numbers', () => {
    expect(2 + 3).toBe(5);
  });

  it('should subtract two numbers', () => {
    expect(5 - 3).toBe(2);
  });
});
```

### Integration Test

```typescript
import { describe, it, expect, beforeAll, afterAll } from '@arcanis/testing';
import { createDatabaseDependency } from '@arcanis/testing/integration';

describe('Database Operations', () => {
  let db: Database;

  beforeAll(async () => {
    db = await createDatabase('test-db');
    await db.connect();
  });

  afterAll(async () => {
    await db.disconnect();
  });

  it('should insert and retrieve data', async () => {
    await db.insert({ id: 1, name: 'Test' });
    const result = await db.findById(1);
    expect(result).toEqual({ id: 1, name: 'Test' });
  });
});
```

### Performance Test

```typescript
import { describe, it, expect } from '@arcanis/testing';
import { benchmark } from '@arcanis/testing/performance';

describe('Performance', () => {
  it('should sort array efficiently', async () => {
    const arr = Array.from({ length: 10000 }, () => Math.random());
    
    const result = await benchmark('Sort', async () => {
      arr.sort((a, b) => a - b);
    }, 100);

    expect(result.avg).toBeLessThan(10); // Less than 10ms
  });
});
```

### AI-Powered Bug Prediction

```typescript
import { createBugPredictor } from '@arcanis/testing/ai';

const predictor = createBugPredictor();

async function analyzeCode(filePath: string) {
  const prediction = await predictor.predictBugs(filePath);
  
  console.log(`File: ${prediction.file}`);
  console.log(`Probability: ${(prediction.probability * 100).toFixed(1)}%`);
  console.log(`Severity: ${prediction.severity}`);
  console.log(`Reason: ${prediction.reason}`);
}
```

### Test Generation

```typescript
import { createTestGenerator } from '@arcanis/testing/ai';

const generator = createTestGenerator();

async function generateTests(sourceFile: string) {
  const tests = await generator.generateTests(sourceFile);
  
  for (const test of tests) {
    console.log(`Generated: ${test.testName}`);
    console.log(`Type: ${test.type}`);
    console.log(`File: ${test.filePath}`);
  }
  
  await generator.saveTests(tests);
}
```

### Failure Analysis

```typescript
import { createFailureAnalyzer } from '@arcanis/testing/ai';

const analyzer = createFailureAnalyzer();

async function analyzeFailure(testResult: TestResult) {
  const analysis = await analyzer.analyzeFailure(testResult);
  
  console.log(`Test: ${analysis.testName}`);
  console.log(`Error: ${analysis.error.message}`);
  
  if (analysis.rootCause) {
    console.log(`Root Cause: ${analysis.rootCause}`);
  }
  
  console.log('Suggestions:');
  for (const suggestion of analysis.suggestions) {
    console.log(`  - ${suggestion}`);
  }
}
```

## Configuration

### arcanis.config.json

```json
{
  "framework": {
    "name": "ArcanisTesting",
    "version": "1.0.0",
    "defaultTimeout": 5000,
    "parallel": false,
    "maxWorkers": 4
  },
  "testing": {
    "unit": {
      "enabled": true,
      "timeout": 10000,
      "coverageThreshold": 80
    },
    "integration": {
      "enabled": true,
      "timeout": 30000,
      "retryCount": 3
    },
    "system": {
      "enabled": true,
      "timeout": 60000,
      "screenshotOnFailure": true
    },
    "performance": {
      "enabled": true,
      "thresholds": {
        "responseTime": 200,
        "throughput": 1000,
        "errorRate": 0.01,
        "cpuUsage": 80,
        "memoryUsage": 80
      }
    }
  },
  "reports": {
    "formats": ["console", "json", "html"],
    "outputDir": "./reports",
    "generateOnFailure": true
  },
  "ai": {
    "enabled": true,
    "bugPrediction": {
      "enabled": true,
      "threshold": 0.7
    },
    "testGeneration": {
      "enabled": true,
      "autoGenerate": true,
      "coverageTarget": 85
    },
    "failureAnalysis": {
      "enabled": true,
      "rootCauseAnalysis": true,
      "suggestionGeneration": true
    }
  }
}
```

## API Reference

### Core

#### Assertions

```typescript
import { assert } from '@arcanis/testing';

// Value assertions
assert.equal(actual, expected);
assert.notEqual(actual, expected);
assert.deepEqual(actual, expected);

// Boolean assertions
assert.isTrue(value);
assert.isFalse(value);

// Null assertions
assert.isNull(value);
assert.isNotNull(value);
assert.isDefined(value);

// Type assertions
assert.isTypeOf(value, 'string');
assert.instanceOf(value, MyClass);

// Collection assertions
assert.contains(array, item);
assert.hasLength(collection, length);
assert.isEmpty(collection);

// Range assertions
assert.greaterThan(actual, expected);
assert.lessThan(actual, expected);

// String assertions
assert.containsString(actual, expected);
assert.matches(actual, /pattern/);

// Async assertions
await assert.throwsAsync(fn, ErrorClass);
```

### Testing

#### Unit Testing

```typescript
import { 
  UnitTestRunner, 
  createUnitTestRunner,
  describe, 
  it, 
  expect,
  beforeEach,
  afterEach 
} from '@arcanis/testing/unit';

const runner = createUnitTestRunner({ timeout: 5000 });

runner.describe('My Suite', () => {
  runner.it('should do something', () => {
    expect(true).toBe(true);
  });
});

await runner.run();
```

#### Integration Testing

```typescript
import { 
  IntegrationTestRunner,
  createIntegrationTestRunner,
  createDatabaseDependency,
  createApiDependency 
} from '@arcanis/testing/integration';

const runner = createIntegrationTestRunner();

runner.addDependency(
  createDatabaseDependency('test-db', 'postgres://localhost/test')
);

runner.addDependency(
  createApiDependency('user-api', 'http://localhost:3000/api')
);

runner.describe('API Integration', () => {
  runner.it('should fetch users', async () => {
    const users = await api.getUsers();
    expect(users.length).toBeGreaterThan(0);
  });
});

await runner.run();
```

#### System Testing

```typescript
import { 
  SystemTestRunner,
  createSystemTestRunner,
  createSystemConfig,
  LoginPage,
  DashboardPage 
} from '@arcanis/testing/system';

const config = createSystemConfig('http://localhost:3000', 'http://localhost:3000/api');
const runner = createSystemTestRunner(config);

runner.describe('Login Flow', () => {
  runner.it('should login successfully', async () => {
    const loginPage = new LoginPage(config, runner);
    await loginPage.navigate('/login');
    await loginPage.login('user', 'pass');
    
    const dashboard = new DashboardPage(config, runner);
    const title = await dashboard.getTitle();
    expect(title).toBe('Dashboard');
  });
});

await runner.run();
```

#### Performance Testing

```typescript
import { 
  PerformanceTestRunner,
  createPerformanceTestRunner,
  createLoadTestConfig,
  benchmark 
} from '@arcanis/testing/performance';

const runner = createPerformanceTestRunner({
  iterations: 100,
  concurrency: 10
});

runner.describe('API Performance', () => {
  runner.it('should handle load', async () => {
    const result = await benchmark('API Call', async () => {
      await api.getUsers();
    }, 1000);
    
    expect(result.avg).toBeLessThan(200);
  });
});

await runner.run();
```

### Automation

#### Test Discovery

```typescript
import { TestDiscovery, createDiscoveryConfig } from '@arcanis/testing/automation';

const config = createDiscoveryConfig('./src', ['**/*.test.ts']);
const discovery = new TestDiscovery(config);

const result = await discovery.discover();
console.log(`Found ${result.summary.total} tests`);
console.log(`By type: ${JSON.stringify(result.summary.byType)}`);
```

#### Reports

```typescript
import { ReportGenerator, createReportGenerator } from '@arcanis/testing/automation';

const generator = createReportGenerator({
  formats: ['console', 'json', 'html'],
  outputDir: './reports'
});

const report = await generator.generateReport(testResults);
console.log(`Report generated: ${report.id}`);
```

#### Continuous Testing

```typescript
import { ContinuousTesting, createContinuousTesting } from '@arcanis/testing/automation';

const ct = createContinuousTesting({
  watchMode: true,
  autoRun: true,
  runOnCommit: true
});

ct.on('run:complete', (run, report) => {
  console.log(`Tests completed: ${run.status}`);
  console.log(`Duration: ${run.duration}ms`);
});

await ct.start();
```

### AI Features

#### Bug Prediction

```typescript
import { BugPredictor, createBugPredictor } from '@arcanis/testing/ai';

const predictor = createBugPredictor({
  threshold: 0.7,
  weights: {
    complexity: 0.3,
    testCoverage: 0.25,
    changeFrequency: 0.2,
    bugHistory: 0.15,
    age: 0.1
  }
});

const predictions = await predictor.predictBugsInDirectory('./src');
for (const pred of predictions) {
  console.log(`${pred.file}: ${(pred.probability * 100).toFixed(1)}% - ${pred.reason}`);
}
```

#### Test Generation

```typescript
import { TestGenerator, createTestGenerator } from '@arcanis/testing/ai';

const generator = createTestGenerator({
  coverageTarget: 85,
  outputDir: './tests/generated'
});

const tests = await generator.generateTests('./src/myModule.ts');
await generator.saveTests(tests);
console.log(`Generated ${tests.length} tests`);
```

#### Failure Analysis

```typescript
import { FailureAnalyzer, createFailureAnalyzer } from '@arcanis/testing/ai';

const analyzer = createFailureAnalyzer({
  rootCauseAnalysis: true,
  suggestionGeneration: true,
  maxSuggestions: 5
});

const analysis = await analyzer.analyzeFailure(testResult);
console.log(`Confidence: ${(analysis.confidence * 100).toFixed(1)}%`);
console.log(`Root Cause: ${analysis.rootCause}`);
console.log('Suggestions:', analysis.suggestions);
```

## Project Structure

```
arcanis-testing/
├── src/
│   ├── core/                    # Core framework
│   │   ├── types.ts            # TypeScript type definitions
│   │   ├── assertions.ts       # Assertion library
│   │   ├── utilities.ts        # Utility functions
│   │   └── testRunner.ts       # Test runner core
│   ├── testing/                 # Testing modules
│   │   ├── unit/               # Unit testing
│   │   ├── integration/        # Integration testing
│   │   ├── system/             # System testing
│   │   └── performance/        # Performance testing
│   ├── automation/              # Automation features
│   │   ├── testDiscovery.ts    # Test discovery
│   │   ├── reports.ts          # Report generation
│   │   └── continuousTesting.ts # Continuous testing
│   ├── ai/                      # AI features
│   │   ├── bugPrediction.ts    # Bug prediction
│   │   ├── testGeneration.ts   # Test generation
│   │   └── failureAnalysis.ts  # Failure analysis
│   └── index.ts                 # Main entry point
├── tests/                       # Sample tests
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   ├── system/                 # System tests
│   ├── performance/            # Performance tests
│   └── ai/                     # AI tests
├── package.json
├── tsconfig.json
├── arcanis.config.json
└── README.md
```

## Commands

```bash
# Run all tests
npm test

# Run specific test types
npm run test:unit
npm run test:integration
npm run test:system
npm run test:performance

# Generate reports
npm run test:report

# Discover tests
npm run test:discover

# Build project
npm run build

# Lint code
npm run lint
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: [docs.arcanis-testing.dev](https://docs.arcanis-testing.dev)
- Issues: [GitHub Issues](https://github.com/arcanis-lab/arcanis-testing/issues)
- Email: support@arcanis-lab.dev

## Acknowledgments

- Built with TypeScript
- Inspired by Jest, Mocha, and other testing frameworks
- AI features powered by machine learning algorithms

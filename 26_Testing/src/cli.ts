#!/usr/bin/env node

// ArcanisTesting CLI - Command Line Interface

import * as fs from 'fs';
import * as path from 'path';
import { createTestDiscovery, createDiscoveryConfig } from './automation/testDiscovery';
import { createReportGenerator } from './automation/reports';
import { createContinuousTesting } from './automation/continuousTesting';
import { createBugPredictor } from './ai/bugPrediction';
import { createTestGenerator } from './ai/testGeneration';
import { createFailureAnalyzer } from './ai/failureAnalysis';

// Load configuration
const loadConfig = () => {
  const configPath = path.join(process.cwd(), 'arcanis.config.json');
  if (fs.existsSync(configPath)) {
    return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
  }
  return null;
};

// Main CLI function
const main = async () => {
  const args = process.argv.slice(2);
  const command = args[0];
  const options = args.slice(1);

  console.log('ArcanisTesting CLI v1.0.0');
  console.log('========================\n');

  const config = loadConfig();

  switch (command) {
    case 'run':
      await runTests(options, config);
      break;
    case 'discover':
      await discoverTests(config);
      break;
    case 'report':
      await generateReport(config);
      break;
    case 'analyze':
      await analyzeCode(options, config);
      break;
    case 'generate':
      await generateTests(options, config);
      break;
    case 'predict':
      await predictBugs(options, config);
      break;
    case 'help':
      showHelp();
      break;
    default:
      console.log('Unknown command. Use "arcanis help" for usage information.');
      process.exit(1);
  }
};

// Run tests
const runTests = async (options: string[], config: any) => {
  console.log('Running tests...\n');

  const type = options.find(o => o.startsWith('--type='))?.split('=')[1] || 'all';
  const parallel = options.includes('--parallel');
  const bail = options.includes('--bail');

  console.log(`Type: ${type}`);
  console.log(`Parallel: ${parallel}`);
  console.log(`Bail: ${bail}\n`);

  // Discover tests
  const discovery = createTestDiscovery(
    createDiscoveryConfig(
      process.cwd(),
      config?.automation?.discovery?.patterns || ['**/*.test.ts', '**/*.spec.ts']
    )
  );

  const result = await discovery.discover();
  console.log(`Discovered ${result.summary.total} tests\n`);

  // Filter by type if specified
  let tests = result.tests;
  if (type !== 'all') {
    tests = tests.filter(t => t.type === type);
    console.log(`Running ${tests.length} ${type} tests\n`);
  }

  // Run tests (simplified - in real implementation, you'd execute the test files)
  console.log('Test execution would happen here...');
  console.log('For now, this is a placeholder.\n');

  // Generate report
  const reportGenerator = createReportGenerator({
    formats: ['console', 'json'],
    outputDir: config?.reports?.outputDir || './reports'
  });

  console.log('Test run completed!');
};

// Discover tests
const discoverTests = async (config: any) => {
  console.log('Discovering tests...\n');

  const discovery = createTestDiscovery(
    createDiscoveryConfig(
      process.cwd(),
      config?.automation?.discovery?.patterns || ['**/*.test.ts', '**/*.spec.ts']
    )
  );

  const result = await discovery.discover();

  console.log('Discovery Results:');
  console.log('=================\n');
  console.log(`Total tests: ${result.summary.total}`);
  console.log('\nBy Type:');
  for (const [type, count] of Object.entries(result.summary.byType)) {
    console.log(`  ${type}: ${count}`);
  }
  console.log('\nBy Priority:');
  for (const [priority, count] of Object.entries(result.summary.byPriority)) {
    console.log(`  ${priority}: ${count}`);
  }
  console.log('\nTest Files:');
  for (const test of result.tests.slice(0, 20)) {
    console.log(`  ${test.filePath}:${test.testName}`);
  }
  if (result.tests.length > 20) {
    console.log(`  ... and ${result.tests.length - 20} more`);
  }
};

// Generate report
const generateReport = async (config: any) => {
  console.log('Generating report...\n');

  const reportGenerator = createReportGenerator({
    formats: ['console', 'json', 'html'],
    outputDir: config?.reports?.outputDir || './reports'
  });

  // In a real implementation, you'd load test results here
  console.log('Report generation would happen here...');
  console.log('For now, this is a placeholder.\n');

  console.log('Report generated successfully!');
};

// Analyze code
const analyzeCode = async (options: string[], config: any) => {
  console.log('Analyzing code...\n');

  const filePath = options[0];
  if (!filePath) {
    console.log('Please provide a file path to analyze.');
    console.log('Usage: arcanis analyze <file-path>');
    return;
  }

  const predictor = createBugPredictor(config?.ai?.bugPrediction);
  
  try {
    const prediction = await predictor.predictBugs(filePath);
    
    console.log('Analysis Results:');
    console.log('=================\n');
    console.log(`File: ${prediction.file}`);
    console.log(`Bug Probability: ${(prediction.probability * 100).toFixed(1)}%`);
    console.log(`Severity: ${prediction.severity}`);
    console.log(`Reason: ${prediction.reason}`);
  } catch (error) {
    console.log(`Error analyzing file: ${(error as Error).message}`);
  }
};

// Generate tests
const generateTests = async (options: string[], config: any) => {
  console.log('Generating tests...\n');

  const sourceFile = options[0];
  if (!sourceFile) {
    console.log('Please provide a source file to generate tests for.');
    console.log('Usage: arcanis generate <source-file>');
    return;
  }

  const generator = createTestGenerator(config?.ai?.testGeneration);
  
  try {
    const tests = await generator.generateTests(sourceFile);
    
    console.log('Generated Tests:');
    console.log('================\n');
    for (const test of tests) {
      console.log(`  ${test.testName}`);
      console.log(`    Type: ${test.type}`);
      console.log(`    File: ${test.filePath}`);
      console.log('');
    }

    // Save tests
    await generator.saveTests(tests);
    console.log(`Saved ${tests.length} test files`);
  } catch (error) {
    console.log(`Error generating tests: ${(error as Error).message}`);
  }
};

// Predict bugs
const predictBugs = async (options: string[], config: any) => {
  console.log('Predicting bugs...\n');

  const directory = options[0] || './src';
  
  const predictor = createBugPredictor(config?.ai?.bugPrediction);
  
  try {
    const predictions = await predictor.predictBugsInDirectory(directory);
    
    console.log('Bug Predictions:');
    console.log('================\n');
    console.log(`Found ${predictions.length} potential bugs\n`);
    
    for (const prediction of predictions.slice(0, 10)) {
      console.log(`  ${prediction.file}`);
      console.log(`    Probability: ${(prediction.probability * 100).toFixed(1)}%`);
      console.log(`    Severity: ${prediction.severity}`);
      console.log(`    Reason: ${prediction.reason}`);
      console.log('');
    }
    
    if (predictions.length > 10) {
      console.log(`  ... and ${predictions.length - 10} more predictions`);
    }
  } catch (error) {
    console.log(`Error predicting bugs: ${(error as Error).message}`);
  }
};

// Show help
const showHelp = () => {
  console.log('Usage: arcanis <command> [options]\n');
  console.log('Commands:');
  console.log('  run           Run tests');
  console.log('  discover      Discover test files');
  console.log('  report        Generate test report');
  console.log('  analyze       Analyze code for bugs');
  console.log('  generate      Generate tests from source');
  console.log('  predict       Predict bugs in codebase');
  console.log('  help          Show this help message\n');
  console.log('Options:');
  console.log('  --type=<type>     Filter by test type (unit, integration, system, performance)');
  console.log('  --parallel        Run tests in parallel');
  console.log('  --bail            Stop on first failure');
  console.log('  --help            Show help for specific command\n');
  console.log('Examples:');
  console.log('  arcanis run --type=unit');
  console.log('  arcanis discover');
  console.log('  arcanis analyze ./src/myModule.ts');
  console.log('  arcanis generate ./src/myModule.ts');
  console.log('  arcanis predict ./src');
};

// Run CLI
main().catch(error => {
  console.error('CLI Error:', error);
  process.exit(1);
});

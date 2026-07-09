// ArcanisTesting Framework - Main Entry Point
// Complete Testing Ecosystem with AI-Powered Features

// Core
export * from './core/types';
export * from './core/assertions';
export * from './core/utilities';
export * from './core/testRunner';

// Testing
export * from './testing/unit/unitTest';
export * from './testing/integration/integrationTest';
export * from './testing/system/systemTest';
export * from './testing/performance/performanceTest';

// Automation
export * from './automation/testDiscovery';
export * from './automation/reports';
export * from './automation/continuousTesting';

// AI Features
export * from './ai/bugPrediction';
export * from './ai/testGeneration';
export * from './ai/failureAnalysis';

// Version
export const VERSION = '1.0.0';

// Framework info
export const FRAMEWORK_INFO = {
  name: 'ArcanisTesting',
  version: VERSION,
  description: 'Complete Testing Ecosystem with AI-Powered Features',
  features: [
    'Unit Testing',
    'Integration Testing',
    'System Testing',
    'Performance Testing',
    'Test Discovery',
    'Test Reports',
    'Continuous Testing',
    'Bug Prediction',
    'Test Generation',
    'Failure Analysis',
  ],
};

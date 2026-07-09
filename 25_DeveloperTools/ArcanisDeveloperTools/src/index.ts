import { Debugger, BreakpointManager, StackTraceParser } from './debugger/index.js';
import { Profiler, CpuProfiler, MemoryProfiler } from './profiler/index.js';
import { CodeAnalyzer, defaultRules, analyzeComplexity } from './analyzer/index.js';
import { DocumentationGenerator, DocParser, DocRenderer } from './docgen/index.js';
import { TestingTools, TestRunner, assert, equal, deepEqual, throws, expect, createMock, spyOn } from './testing/index.js';
import { PerformanceMonitor, MetricsCollector } from './perfmon/index.js';
import { ArcanisIDEIntegration } from './integration/ide.js';
import { ArcanisBuildIntegration } from './integration/build.js';
import { ArcanisLangIntegration } from './integration/lang.js';

export { Debugger, BreakpointManager, StackTraceParser };
export { Profiler, CpuProfiler, MemoryProfiler };
export { CodeAnalyzer, defaultRules, analyzeComplexity };
export { DocumentationGenerator, DocParser, DocRenderer };
export { TestingTools, TestRunner, assert, equal, deepEqual, throws, expect, createMock, spyOn };
export { PerformanceMonitor, MetricsCollector };
export { ArcanisIDEIntegration };
export { ArcanisBuildIntegration };
export { ArcanisLangIntegration };

export class ArcanisDeveloperTools {
  readonly debugger: Debugger;
  readonly profiler: Profiler;
  readonly analyzer: CodeAnalyzer;
  readonly docgen: DocumentationGenerator;
  readonly testing: TestingTools;
  readonly perfmon: PerformanceMonitor;
  readonly ide: ArcanisIDEIntegration;
  readonly build: ArcanisBuildIntegration;
  readonly lang: ArcanisLangIntegration;

  constructor() {
    this.debugger = new Debugger();
    this.profiler = new Profiler();
    this.analyzer = new CodeAnalyzer();
    this.docgen = new DocumentationGenerator();
    this.testing = new TestingTools();
    this.perfmon = new PerformanceMonitor();
    this.ide = new ArcanisIDEIntegration();
    this.build = new ArcanisBuildIntegration();
    this.lang = new ArcanisLangIntegration();
  }

  getVersion(): string {
    return '0.1.0';
  }
}

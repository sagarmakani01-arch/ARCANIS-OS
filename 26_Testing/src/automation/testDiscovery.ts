// Test Discovery Module for ArcanisTesting Framework

import * as fs from 'fs';
import * as path from 'path';
import { EventEmitter } from 'events';
import { generateId } from '../core/utilities';

export interface DiscoveryConfig {
  patterns: string[];
  exclude: string[];
  rootDir: string;
  maxDepth?: number;
}

export interface DiscoveredTest {
  id: string;
  filePath: string;
  fileName: string;
  testName: string;
  type: 'unit' | 'integration' | 'system' | 'performance';
  tags: string[];
  priority: 'low' | 'medium' | 'high' | 'critical';
  lastModified: Date;
}

export interface DiscoveryResult {
  id: string;
  timestamp: Date;
  rootDir: string;
  tests: DiscoveredTest[];
  summary: {
    total: number;
    byType: Record<string, number>;
    byPriority: Record<string, number>;
  };
}

export class TestDiscovery extends EventEmitter {
  private config: DiscoveryConfig;
  private discoveredTests: DiscoveredTest[] = [];

  constructor(config: DiscoveryConfig) {
    super();
    this.config = {
      maxDepth: 10,
      ...config,
    };
  }

  async discover(): Promise<DiscoveryResult> {
    this.discoveredTests = [];
    
    for (const pattern of this.config.patterns) {
      await this.discoverByPattern(pattern);
    }

    // Filter excluded paths
    this.discoveredTests = this.discoveredTests.filter(test => 
      !this.config.exclude.some(exclude => 
        test.filePath.includes(exclude)
      )
    );

    return this.generateResult();
  }

  private async discoverByPattern(pattern: string): Promise<void> {
    const regex = this.patternToRegex(pattern);
    await this.walkDirectory(this.config.rootDir, regex, 0);
  }

  private patternToRegex(pattern: string): RegExp {
    // Convert glob pattern to regex
    let regexStr = pattern
      .replace(/\./g, '\\.')
      .replace(/\*/g, '.*')
      .replace(/\?/g, '.')
      .replace(/\{([^}]+)\}/g, (_, group) => {
        const options = group.split(',');
        return `(${options.join('|')})`;
      });
    
    return new RegExp(regexStr, 'i');
  }

  private async walkDirectory(
    dir: string,
    pattern: RegExp,
    depth: number
  ): Promise<void> {
    if (depth > (this.config.maxDepth || 10)) {
      return;
    }

    try {
      const entries = await fs.promises.readdir(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
          if (!this.config.exclude.includes(entry.name)) {
            await this.walkDirectory(fullPath, pattern, depth + 1);
          }
        } else if (entry.isFile() && pattern.test(entry.name)) {
          await this.processTestFile(fullPath);
        }
      }
    } catch (error) {
      this.emit('error', error);
    }
  }

  private async processTestFile(filePath: string): Promise<void> {
    try {
      const content = await fs.promises.readFile(filePath, 'utf-8');
      const stats = await fs.promises.stat(filePath);
      
      // Extract test information from file content
      const testInfo = this.extractTestInfo(content, filePath, stats.mtime);
      this.discoveredTests.push(...testInfo);
      
      this.emit('file:discovered', filePath, testInfo);
    } catch (error) {
      this.emit('error', error);
    }
  }

  private extractTestInfo(
    content: string,
    filePath: string,
    lastModified: Date
  ): DiscoveredTest[] {
    const tests: DiscoveredTest[] = [];
    const fileName = path.basename(filePath);

    // Determine test type from file name or content
    let type: DiscoveredTest['type'] = 'unit';
    if (fileName.includes('.integration.')) {
      type = 'integration';
    } else if (fileName.includes('.system.')) {
      type = 'system';
    } else if (fileName.includes('.performance.') || fileName.includes('.perf.')) {
      type = 'performance';
    }

    // Extract test names from content
    const testPatterns = [
      /describe\s*\(\s*['"`]([^'"`]+)['"`]/g,
      /it\s*\(\s*['"`]([^'"`]+)['"`]/g,
      /test\s*\(\s*['"`]([^'"`]+)['"`]/g,
    ];

    const foundTests = new Set<string>();
    
    for (const pattern of testPatterns) {
      let match;
      while ((match = pattern.exec(content)) !== null) {
        foundTests.add(match[1]);
      }
    }

    // If no tests found, create a single entry for the file
    if (foundTests.size === 0) {
      tests.push({
        id: generateId(),
        filePath,
        fileName,
        testName: fileName,
        type,
        tags: this.extractTags(content),
        priority: this.extractPriority(content),
        lastModified,
      });
    } else {
      // Create entries for each found test
      for (const testName of foundTests) {
        tests.push({
          id: generateId(),
          filePath,
          fileName,
          testName,
          type,
          tags: this.extractTags(content),
          priority: this.extractPriority(content),
          lastModified,
        });
      }
    }

    return tests;
  }

  private extractTags(content: string): string[] {
    const tags: string[] = [];
    const tagPattern = /@(\w+)/g;
    let match;

    while ((match = tagPattern.exec(content)) !== null) {
      tags.push(match[1]);
    }

    return [...new Set(tags)];
  }

  private extractPriority(content: string): DiscoveredTest['priority'] {
    if (content.includes('@critical') || content.includes('@high')) {
      return 'high';
    }
    if (content.includes('@medium')) {
      return 'medium';
    }
    if (content.includes('@low')) {
      return 'low';
    }
    return 'medium';
  }

  private generateResult(): DiscoveryResult {
    const byType: Record<string, number> = {};
    const byPriority: Record<string, number> = {};

    for (const test of this.discoveredTests) {
      byType[test.type] = (byType[test.type] || 0) + 1;
      byPriority[test.priority] = (byPriority[test.priority] || 0) + 1;
    }

    return {
      id: generateId(),
      timestamp: new Date(),
      rootDir: this.config.rootDir,
      tests: this.discoveredTests,
      summary: {
        total: this.discoveredTests.length,
        byType,
        byPriority,
      },
    };
  }

  getTests(): DiscoveredTest[] {
    return [...this.discoveredTests];
  }

  getTestsByType(type: DiscoveredTest['type']): DiscoveredTest[] {
    return this.discoveredTests.filter(test => test.type === type);
  }

  getTestsByPriority(priority: DiscoveredTest['priority']): DiscoveredTest[] {
    return this.discoveredTests.filter(test => test.priority === priority);
  }

  getTestsByTag(tag: string): DiscoveredTest[] {
    return this.discoveredTests.filter(test => test.tags.includes(tag));
  }

  filterTests(predicate: (test: DiscoveredTest) => boolean): DiscoveredTest[] {
    return this.discoveredTests.filter(predicate);
  }
}

// Factory function for creating test discovery instances
export const createTestDiscovery = (config: DiscoveryConfig): TestDiscovery => {
  return new TestDiscovery(config);
};

// Helper function for creating discovery configurations
export const createDiscoveryConfig = (
  rootDir: string,
  patterns?: string[],
  exclude?: string[]
): DiscoveryConfig => {
  return {
    rootDir,
    patterns: patterns || ['**/*.test.ts', '**/*.spec.ts', '**/*.integration.ts', '**/*.system.ts', '**/*.performance.ts'],
    exclude: exclude || ['node_modules', 'dist', 'reports', '.git'],
  };
};

// File watcher for continuous discovery
export class TestWatcher extends EventEmitter {
  private discovery: TestDiscovery;
  private watchInterval: NodeJS.Timeout | null = null;
  private lastDiscovery: DiscoveryResult | null = null;

  constructor(discovery: TestDiscovery) {
    super();
    this.discovery = discovery;
  }

  async start(interval: number = 5000): Promise<void> {
    // Initial discovery
    this.lastDiscovery = await this.discovery.discover();
    this.emit('discovery', this.lastDiscovery);

    // Start watching
    this.watchInterval = setInterval(async () => {
      const newDiscovery = await this.discovery.discover();
      
      // Compare with last discovery
      const changes = this.detectChanges(this.lastDiscovery!, newDiscovery);
      
      if (changes.added.length > 0 || changes.removed.length > 0 || changes.modified.length > 0) {
        this.emit('changes', changes);
      }

      this.lastDiscovery = newDiscovery;
    }, interval);
  }

  stop(): void {
    if (this.watchInterval) {
      clearInterval(this.watchInterval);
      this.watchInterval = null;
    }
  }

  private detectChanges(
    oldDiscovery: DiscoveryResult,
    newDiscovery: DiscoveryResult
  ): { added: DiscoveredTest[]; removed: DiscoveredTest[]; modified: DiscoveredTest[] } {
    const oldIds = new Set(oldDiscovery.tests.map(t => t.id));
    const newIds = new Set(newDiscovery.tests.map(t => t.id));

    const added = newDiscovery.tests.filter(t => !oldIds.has(t.id));
    const removed = oldDiscovery.tests.filter(t => !newIds.has(t.id));
    const modified = newDiscovery.tests.filter(t => {
      if (!oldIds.has(t.id)) return false;
      const oldTest = oldDiscovery.tests.find(ot => ot.id === t.id);
      return oldTest && oldTest.lastModified < t.lastModified;
    });

    return { added, removed, modified };
  }
}

// Test categorization
export const categorizeTests = (tests: DiscoveredTest[]): Record<string, DiscoveredTest[]> => {
  const categories: Record<string, DiscoveredTest[]> = {};

  for (const test of tests) {
    if (!categories[test.type]) {
      categories[test.type] = [];
    }
    categories[test.type].push(test);
  }

  return categories;
};

// Test filtering utilities
export const filterByTag = (tests: DiscoveredTest[], tag: string): DiscoveredTest[] => {
  return tests.filter(test => test.tags.includes(tag));
};

export const filterByPriority = (tests: DiscoveredTest[], priority: DiscoveredTest['priority']): DiscoveredTest[] => {
  return tests.filter(test => test.priority === priority);
};

export const filterByFileType = (tests: DiscoveredTest[], fileType: string): DiscoveredTest[] => {
  return tests.filter(test => test.fileName.endsWith(fileType));
};

// Test sorting utilities
export const sortByPriority = (tests: DiscoveredTest[]): DiscoveredTest[] => {
  const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
  return [...tests].sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);
};

export const sortByLastModified = (tests: DiscoveredTest[], descending: boolean = false): DiscoveredTest[] => {
  return [...tests].sort((a, b) => {
    const diff = a.lastModified.getTime() - b.lastModified.getTime();
    return descending ? -diff : diff;
  });
};

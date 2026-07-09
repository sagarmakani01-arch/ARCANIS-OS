import { BuildSystem } from '../../src/tools/BuildSystem';
import { EventBus } from '../../src/core/EventBus';
import { Configuration } from '../../src/core/Configuration';

describe('BuildSystem', () => {
  let buildSystem: BuildSystem;
  let eventBus: EventBus;
  let configuration: Configuration;

  beforeEach(() => {
    eventBus = new EventBus();
    configuration = new Configuration();
    buildSystem = new BuildSystem(eventBus, configuration);
  });

  describe('constructor', () => {
    it('should accept eventBus and configuration', () => {
      expect(buildSystem).toBeInstanceOf(BuildSystem);
    });

    it('should initialize config from configuration defaults', () => {
      const config = buildSystem.getCurrentConfig();
      expect(config.target).toBe('wasm32');
      expect(config.mode).toBe('debug');
      expect(config.optimize).toBe(false);
      expect(config.outputDir).toBe('build');
      expect(config.sourceDir).toBe('src');
      expect(config.compilerFlags).toEqual([]);
    });
  });

  describe('getCurrentConfig', () => {
    it('should return a copy of the config', () => {
      const config = buildSystem.getCurrentConfig();
      config.target = 'x86_64';
      const configAgain = buildSystem.getCurrentConfig();
      expect(configAgain.target).toBe('wasm32');
    });
  });

  describe('updateConfig', () => {
    it('should update individual config fields', () => {
      buildSystem.updateConfig({ target: 'x86_64', mode: 'release', optimize: true });
      const config = buildSystem.getCurrentConfig();
      expect(config.target).toBe('x86_64');
      expect(config.mode).toBe('release');
      expect(config.optimize).toBe(true);
    });

    it('should not affect fields not in the partial update', () => {
      buildSystem.updateConfig({ target: 'arm' });
      const config = buildSystem.getCurrentConfig();
      expect(config.mode).toBe('debug');
      expect(config.outputDir).toBe('build');
    });
  });

  describe('build', () => {
    it('should return a BuildResult with success true', async () => {
      const result = await buildSystem.build();
      expect(result.success).toBe(true);
      expect(result.target).toBe('wasm32');
      expect(result.mode).toBe('debug');
    });

    it('should merge provided config overrides', async () => {
      const result = await buildSystem.build({ target: 'x86_64', mode: 'release' });
      expect(result.target).toBe('x86_64');
      expect(result.mode).toBe('release');
    });

    it('should return a non-negative duration', async () => {
      const result = await buildSystem.build();
      expect(result.duration).toBeGreaterThanOrEqual(0);
    });

    it('should emit build events', async () => {
      const startedHandler = jest.fn();
      const completedHandler = jest.fn();
      eventBus.on('build:started', startedHandler);
      eventBus.on('build:completed', completedHandler);

      await buildSystem.build();
      expect(startedHandler).toHaveBeenCalled();
      expect(completedHandler).toHaveBeenCalled();
    });

    it('should output a BuildResult with expected shape', async () => {
      const result = await buildSystem.build();
      expect(result).toHaveProperty('success');
      expect(result).toHaveProperty('target');
      expect(result).toHaveProperty('mode');
      expect(result).toHaveProperty('duration');
      expect(result).toHaveProperty('output');
      expect(result).toHaveProperty('errors');
      expect(result).toHaveProperty('warnings');
      expect(Array.isArray(result.errors)).toBe(true);
      expect(Array.isArray(result.warnings)).toBe(true);
    });
  });

  describe('clean', () => {
    it('should return a BuildResult with success true', async () => {
      const result = await buildSystem.clean();
      expect(result.success).toBe(true);
    });

    it('should use current config by default', async () => {
      const result = await buildSystem.clean();
      expect(result.target).toBe('wasm32');
      expect(result.mode).toBe('debug');
    });

    it('should accept config overrides', async () => {
      const result = await buildSystem.clean({ target: 'arm' });
      expect(result.target).toBe('arm');
    });
  });

  describe('rebuild', () => {
    it('should run clean then build and return a BuildResult', async () => {
      const result = await buildSystem.rebuild();
      expect(result.success).toBe(true);
    });

    it('should propagate config overrides through clean and build', async () => {
      const result = await buildSystem.rebuild({ target: 'custom', mode: 'release' });
      expect(result.target).toBe('custom');
      expect(result.mode).toBe('release');
    });
  });

  describe('runTests', () => {
    it('should return a TestResult', async () => {
      const result = await buildSystem.runTests();
      expect(result).toHaveProperty('total');
      expect(result).toHaveProperty('passed');
      expect(result).toHaveProperty('failed');
      expect(result).toHaveProperty('skipped');
      expect(result).toHaveProperty('duration');
      expect(result).toHaveProperty('tests');
    });

    it('should emit test events', async () => {
      const startedHandler = jest.fn();
      const completedHandler = jest.fn();
      eventBus.on('test:started', startedHandler);
      eventBus.on('test:completed', completedHandler);

      await buildSystem.runTests();
      expect(startedHandler).toHaveBeenCalled();
      expect(completedHandler).toHaveBeenCalled();
    });
  });
});

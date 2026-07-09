import { PluginManager } from '../../src/core/PluginManager';
import { EventBus } from '../../src/core/EventBus';
import { CommandRegistry } from '../../src/core/CommandRegistry';
import { Configuration } from '../../src/core/Configuration';

describe('PluginManager', () => {
  let pluginManager: PluginManager;
  let eventBus: EventBus;
  let commandRegistry: CommandRegistry;
  let configuration: Configuration;

  beforeEach(() => {
    eventBus = new EventBus();
    commandRegistry = new CommandRegistry();
    configuration = new Configuration();
    pluginManager = new PluginManager(eventBus, commandRegistry, configuration);
  });

  describe('constructor', () => {
    it('should accept eventBus, commandRegistry, and configuration', () => {
      expect(pluginManager).toBeInstanceOf(PluginManager);
    });
  });

  describe('scanAndLoadPlugins', () => {
    it('should warn and return when directory does not exist', async () => {
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});

      await pluginManager.scanAndLoadPlugins('C:\\nonexistent\\plugins\\dir');

      expect(warnSpy).toHaveBeenCalledWith(
        expect.stringContaining('Plugins directory not found'),
      );
      warnSpy.mockRestore();
    });

    it('should not throw when directory does not exist', async () => {
      await expect(
        pluginManager.scanAndLoadPlugins('C:\\nonexistent\\plugins\\dir'),
      ).resolves.not.toThrow();
    });
  });

  describe('getPlugins', () => {
    it('should return an empty array initially', () => {
      expect(pluginManager.getPlugins()).toEqual([]);
    });
  });

  describe('isLoaded', () => {
    it('should return false for any plugin name initially', () => {
      expect(pluginManager.isLoaded('any-plugin')).toBe(false);
    });
  });

  describe('onPluginLoaded', () => {
    it('should return an IDisposable', () => {
      const handler = jest.fn();
      const disposable = pluginManager.onPluginLoaded(handler);
      expect(disposable).toHaveProperty('dispose');
      expect(typeof disposable.dispose).toBe('function');
    });
  });

  describe('onPluginUnloaded', () => {
    it('should return an IDisposable', () => {
      const handler = jest.fn();
      const disposable = pluginManager.onPluginUnloaded(handler);
      expect(disposable).toHaveProperty('dispose');
      expect(typeof disposable.dispose).toBe('function');
    });
  });

  describe('getPlugin', () => {
    it('should return undefined for unloaded plugin', () => {
      expect(pluginManager.getPlugin('nonexistent')).toBeUndefined();
    });
  });

  describe('loadPlugin', () => {
    it('should reject with an error for non-existent path', async () => {
      await expect(
        pluginManager.loadPlugin('C:\\nonexistent\\plugin\\path'),
      ).rejects.toThrow();
    });
  });

  describe('unloadPlugin', () => {
    it('should reject with an error for unloaded plugin', async () => {
      await expect(
        pluginManager.unloadPlugin('not-loaded'),
      ).rejects.toThrow('Plugin "not-loaded" is not loaded.');
    });
  });
});

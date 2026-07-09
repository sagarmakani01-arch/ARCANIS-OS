import * as path from 'path';
import * as fs from 'fs';
import { PluginManifest, PluginContext, IDisposable } from '../api/types';
import { EventBus, IEventBus } from './EventBus';
import { CommandRegistry, ICommandRegistry } from './CommandRegistry';
import { Configuration, IConfiguration } from './Configuration';

export interface PluginInstance {
  manifest: PluginManifest;
  context: PluginContext;
  activate: () => void | Promise<void>;
  deactivate?: () => void | Promise<void>;
}

export interface IPluginManager {
  loadPlugin(pluginPath: string): Promise<PluginInstance>;
  unloadPlugin(name: string): Promise<void>;
  getPlugin(name: string): PluginInstance | undefined;
  getPlugins(): PluginInstance[];
  scanAndLoadPlugins(pluginsDir: string): Promise<void>;
  isLoaded(name: string): boolean;
  onPluginLoaded(handler: (plugin: PluginInstance) => void): IDisposable;
  onPluginUnloaded(handler: (name: string) => void): IDisposable;
}

export class PluginManager implements IPluginManager {
  private plugins = new Map<string, PluginInstance>();
  private eventBus: IEventBus;
  private commandRegistry: ICommandRegistry;
  private configuration: IConfiguration;

  constructor(eventBus: IEventBus, commandRegistry: ICommandRegistry, configuration: IConfiguration) {
    this.eventBus = eventBus;
    this.commandRegistry = commandRegistry;
    this.configuration = configuration;
  }

  async loadPlugin(pluginPath: string): Promise<PluginInstance> {
    const manifestPath = path.join(pluginPath, 'manifest.json');
    if (!fs.existsSync(manifestPath)) {
      throw new Error(`Plugin manifest not found at ${manifestPath}`);
    }

    const manifest: PluginManifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));

    if (this.plugins.has(manifest.name)) {
      throw new Error(`Plugin "${manifest.name}" is already loaded.`);
    }

    const mainPath = path.join(pluginPath, manifest.main);
    if (!fs.existsSync(mainPath)) {
      throw new Error(`Plugin main file not found at ${mainPath}`);
    }

    let pluginModule: { activate: (ctx: PluginContext) => void | Promise<void>; deactivate?: () => void | Promise<void> };
    try {
      pluginModule = await import(mainPath);
    } catch (err) {
      throw new Error(`Failed to load plugin module "${manifest.name}": ${err}`);
    }

    const stateStorage = new Map<string, unknown>();
    const pluginContext: PluginContext = {
      subscriptions: [],
      extensionPath: pluginPath,
      workspaceState: {
        get: <T>(key: string): T | undefined => stateStorage.get(key) as T,
        set: <T>(key: string, value: T): void => { stateStorage.set(key, value); },
        delete: (key: string): void => { stateStorage.delete(key); },
        keys: (): string[] => [...stateStorage.keys()],
      },
      globalState: {
        get: <T>(key: string): T | undefined => stateStorage.get(key) as T,
        set: <T>(key: string, value: T): void => { stateStorage.set(key, value); },
        delete: (key: string): void => { stateStorage.delete(key); },
        keys: (): string[] => [...stateStorage.keys()],
      },
      log: (message: string) => console.log(`[Plugin:${manifest.name}] ${message}`),
    };

    const instance: PluginInstance = {
      manifest,
      context: pluginContext,
      activate: () => pluginModule.activate(pluginContext),
      deactivate: pluginModule.deactivate,
    };

    this.plugins.set(manifest.name, instance);

    if (manifest.contributes?.commands) {
      for (const cmd of manifest.contributes.commands) {
        const disposable = this.commandRegistry.registerCommand(
          cmd.id,
          async (...args: unknown[]) => {
            this.eventBus.emit(`command:${cmd.id}`, { args, plugin: manifest.name });
          },
          manifest.name
        );
        pluginContext.subscriptions.push(disposable);
      }
    }

    try {
      await instance.activate();
      this.eventBus.emit('plugin:loaded', { name: manifest.name, version: manifest.version });
    } catch (err) {
      this.plugins.delete(manifest.name);
      throw new Error(`Failed to activate plugin "${manifest.name}": ${err}`);
    }

    return instance;
  }

  async unloadPlugin(name: string): Promise<void> {
    const instance = this.plugins.get(name);
    if (!instance) {
      throw new Error(`Plugin "${name}" is not loaded.`);
    }

    if (instance.deactivate) {
      try {
        await instance.deactivate();
      } catch (err) {
        console.error(`[PluginManager] Error deactivating plugin "${name}":`, err);
      }
    }

    for (const sub of instance.context.subscriptions) {
      try { sub.dispose(); } catch { /* ignore */ }
    }

    this.plugins.delete(name);
    this.eventBus.emit('plugin:unloaded', { name });
  }

  getPlugin(name: string): PluginInstance | undefined {
    return this.plugins.get(name);
  }

  getPlugins(): PluginInstance[] {
    return Array.from(this.plugins.values());
  }

  async scanAndLoadPlugins(pluginsDir: string): Promise<void> {
    if (!fs.existsSync(pluginsDir)) {
      console.warn(`[PluginManager] Plugins directory not found: ${pluginsDir}`);
      return;
    }

    const entries = fs.readdirSync(pluginsDir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isDirectory()) {
        const pluginPath = path.join(pluginsDir, entry.name);
        try {
          await this.loadPlugin(pluginPath);
          console.log(`[PluginManager] Loaded plugin: ${entry.name}`);
        } catch (err) {
          console.error(`[PluginManager] Failed to load plugin "${entry.name}":`, err);
        }
      }
    }
  }

  isLoaded(name: string): boolean {
    return this.plugins.has(name);
  }

  onPluginLoaded(handler: (plugin: PluginInstance) => void): IDisposable {
    return this.eventBus.on('plugin:loaded', handler as (event: unknown) => void);
  }

  onPluginUnloaded(handler: (name: string) => void): IDisposable {
    return this.eventBus.on('plugin:unloaded', handler as (event: unknown) => void);
  }
}

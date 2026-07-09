import { IDisposable, BuildConfig, GitStatus } from './types';
import {
  PluginAPI, EventAPI, WorkspaceAPI, EditorAPI, AIAPI, DebugAPI,
  TerminalAPI, BuildAPI, PackageAPI, GitAPI, UIAPI, ConfigAPI, LogAPI,
} from './PluginAPI';
import { PluginManager, PluginInstance } from '../core/PluginManager';
import { EventBus, EventHandler } from '../core/EventBus';
import { CommandRegistry } from '../core/CommandRegistry';
import { Configuration } from '../core/Configuration';
import { EditorEngine } from '../editor/EditorEngine';
import { AIAssistant } from '../ai/AIAssistant';
import { Debugger } from '../tools/Debugger';
import { Terminal } from '../tools/Terminal';
import { BuildSystem } from '../tools/BuildSystem';
import { PackageManager } from '../tools/PackageManager';
import { GitIntegration } from '../tools/GitIntegration';
import { UIEngine } from '../ui/UIEngine';

export class IDEAPI {
  readonly events: EventAPI;
  readonly commands: CommandRegistry;
  readonly workspace: WorkspaceAPI;
  readonly editor: EditorAPI;
  readonly ai: AIAPI;
  readonly debug: DebugAPI;
  readonly terminal: TerminalAPI;
  readonly build: BuildAPI;
  readonly packages: PackageAPI;
  readonly git: GitAPI;
  readonly ui: UIAPI;
  readonly config: ConfigAPI;
  readonly log: LogAPI;
  readonly plugins: PluginManagementAPI;
  readonly pluginApi: PluginAPI;

  constructor(
    private eventBus: EventBus,
    commandRegistry: CommandRegistry,
    configuration: Configuration,
    editorEngine: EditorEngine,
    aiAssistant: AIAssistant,
    debugger_: Debugger,
    terminal: Terminal,
    buildSystem: BuildSystem,
    packageManager: PackageManager,
    gitIntegration: GitIntegration,
    uiEngine: UIEngine,
    private pluginManager: PluginManager,
  ) {
    this.pluginApi = new PluginAPI(
      eventBus, commandRegistry, configuration, editorEngine, aiAssistant,
      debugger_, terminal, buildSystem, packageManager, gitIntegration, uiEngine,
    );
    this.events = new EventAPI(eventBus);
    this.commands = commandRegistry;
    this.workspace = new WorkspaceAPI(configuration);
    this.editor = new EditorAPI(editorEngine);
    this.ai = new AIAPI(aiAssistant);
    this.debug = new DebugAPI(debugger_);
    this.terminal = new TerminalAPI(terminal);
    this.build = new BuildAPI(buildSystem);
    this.packages = new PackageAPI(packageManager);
    this.git = new GitAPI(gitIntegration);
    this.ui = new UIAPI(uiEngine);
    this.config = new ConfigAPI(configuration);
    this.log = new LogAPI();
    this.plugins = new PluginManagementAPI(pluginManager);
  }

  dispose(): void {
    this.eventBus.clear();
  }

  getVersion(): string {
    return '0.1.0';
  }
}

class PluginManagementAPI {
  constructor(private pluginManager: PluginManager) {}

  async loadPlugin(pluginPath: string): Promise<PluginInstance> {
    return this.pluginManager.loadPlugin(pluginPath);
  }

  async unloadPlugin(name: string): Promise<void> {
    return this.pluginManager.unloadPlugin(name);
  }

  getPlugin(name: string): PluginInstance | undefined {
    return this.pluginManager.getPlugin(name);
  }

  getPlugins(): PluginInstance[] {
    return this.pluginManager.getPlugins();
  }

  async scanAndLoadPlugins(pluginsDir: string): Promise<void> {
    return this.pluginManager.scanAndLoadPlugins(pluginsDir);
  }

  onPluginLoaded(handler: (plugin: PluginInstance) => void): IDisposable {
    return this.pluginManager.onPluginLoaded(handler);
  }

  onPluginUnloaded(handler: (name: string) => void): IDisposable {
    return this.pluginManager.onPluginUnloaded(handler);
  }
}

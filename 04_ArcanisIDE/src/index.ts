import { EventBus } from './core/EventBus';
import { CommandRegistry } from './core/CommandRegistry';
import { Configuration } from './core/Configuration';
import { PluginManager } from './core/PluginManager';
import { EditorEngine } from './editor/EditorEngine';
import { AIAssistant } from './ai/AIAssistant';
import { Debugger } from './tools/Debugger';
import { Terminal } from './tools/Terminal';
import { BuildSystem } from './tools/BuildSystem';
import { PackageManager } from './tools/PackageManager';
import { GitIntegration } from './tools/GitIntegration';
import { UIEngine } from './ui/UIEngine';
import { PluginAPI } from './api/PluginAPI';
import { IDEAPI } from './api/IDEAPI';

export interface ArcanisIDEOptions {
  workspacePath?: string;
  configPath?: string;
  pluginsPath?: string;
}

export class ArcanisIDE {
  private eventBus: EventBus;
  private commandRegistry: CommandRegistry;
  private configuration: Configuration;
  private pluginManager: PluginManager;
  private editorEngine: EditorEngine;
  private aiAssistant: AIAssistant;
  private debugger: Debugger;
  private terminal: Terminal;
  private buildSystem: BuildSystem;
  private packageManager: PackageManager;
  private gitIntegration: GitIntegration;
  private uiEngine: UIEngine;
  private ideApi: IDEAPI;
  private pluginApi: PluginAPI;

  constructor(private options?: ArcanisIDEOptions) {
    this.eventBus = new EventBus();
    this.commandRegistry = new CommandRegistry();
    this.configuration = new Configuration();
    this.pluginManager = new PluginManager(this.eventBus, this.commandRegistry, this.configuration);
    this.editorEngine = new EditorEngine();
    this.aiAssistant = new AIAssistant(this.eventBus);
    this.debugger = new Debugger(this.eventBus);
    this.terminal = new Terminal(this.eventBus);
    this.buildSystem = new BuildSystem(this.eventBus, this.configuration);
    this.packageManager = new PackageManager(this.eventBus);
    this.gitIntegration = new GitIntegration(this.eventBus, this.configuration);
    this.uiEngine = new UIEngine(this.eventBus, this.configuration);

    this.pluginApi = new PluginAPI(
      this.eventBus, this.commandRegistry, this.configuration, this.editorEngine,
      this.aiAssistant, this.debugger, this.terminal, this.buildSystem,
      this.packageManager, this.gitIntegration, this.uiEngine,
    );

    this.ideApi = new IDEAPI(
      this.eventBus, this.commandRegistry, this.configuration, this.editorEngine,
      this.aiAssistant, this.debugger, this.terminal, this.buildSystem,
      this.packageManager, this.gitIntegration, this.uiEngine, this.pluginManager,
    );
  }

  async initialize(): Promise<void> {
    this.registerDefaultCommands();

    if (this.options?.workspacePath) {
      this.configuration.set('workspace.path', this.options.workspacePath);
    }

    if (this.options?.pluginsPath) {
      await this.pluginManager.scanAndLoadPlugins(this.options.pluginsPath);
    }

    await this.uiEngine.initialize();
  }

  async dispose(): Promise<void> {
    this.eventBus.clear();
    this.commandRegistry['commands'].clear();
  }

  getAPI(): IDEAPI {
    return this.ideApi;
  }

  getPluginAPI(): PluginAPI {
    return this.pluginApi;
  }

  static async create(options?: ArcanisIDEOptions): Promise<ArcanisIDE> {
    const ide = new ArcanisIDE(options);
    await ide.initialize();
    return ide;
  }

  private registerDefaultCommands(): void {
    this.commandRegistry.registerCommand('arcanis.about', () => {
      this.uiEngine.showMessageBox({
        message: 'ArcanisIDE',
        detail: 'Version 0.1.0\nArcanis Labs',
        buttons: ['OK'],
      });
    });

    this.commandRegistry.registerCommand('arcanis.toggleSidebar', () => {
      this.uiEngine.togglePanel('sidebar');
    });

    this.commandRegistry.registerCommand('arcanis.togglePanel', () => {
      this.uiEngine.togglePanel('panel');
    });

    this.commandRegistry.registerCommand('arcanis.openFile', async () => {
      const result = await this.uiEngine.showInputBox({ prompt: 'File path to open' });
      if (result) {
        await this.editorEngine.openDocument(result);
      }
    });

    this.commandRegistry.registerCommand('arcanis.saveFile', () => {
      const doc = this.editorEngine.getActiveDocument();
      if (doc) {
        this.eventBus.emit('file:save', { uri: doc.uri });
      }
    });

    this.commandRegistry.registerCommand('arcanis.saveAll', () => {
      this.eventBus.emit('file:saveAll', {});
    });

    this.commandRegistry.registerCommand('arcanis.closeFile', () => {
      const doc = this.editorEngine.getActiveDocument();
      if (doc) {
        this.editorEngine.closeDocument(doc.uri);
      }
    });

    this.commandRegistry.registerCommand('arcanis.build', async () => {
      await this.buildSystem.build();
    });

    this.commandRegistry.registerCommand('arcanis.run', async () => {
      this.eventBus.emit('project:run', {});
    });

    this.commandRegistry.registerCommand('arcanis.debug', async () => {
      await this.debugger.start();
    });

    this.commandRegistry.registerCommand('arcanis.git.commit', async () => {
      const message = await this.uiEngine.showInputBox({ prompt: 'Commit message' });
      if (message) {
        await this.gitIntegration.commit(message);
      }
    });

    this.commandRegistry.registerCommand('arcanis.git.push', async () => {
      await this.gitIntegration.push();
    });

    this.commandRegistry.registerCommand('arcanis.ai.explain', async () => {
      const doc = this.editorEngine.getActiveDocument();
      if (doc) {
        await this.aiAssistant.explainCode(doc, {
          start: { line: 0, column: 0 },
          end: { line: doc.lineCount, column: 0 },
        });
      }
    });

    this.commandRegistry.registerCommand('arcanis.ai.suggest', async () => {
      const doc = this.editorEngine.getActiveDocument();
      if (doc) {
        await this.aiAssistant.getSuggestions(doc);
      }
    });
  }
}

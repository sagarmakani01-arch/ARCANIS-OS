import { IDisposable, BuildConfig, GitStatus } from './types';
import { EventBus, EventHandler } from '../core/EventBus';
import { CommandRegistry } from '../core/CommandRegistry';
import { Configuration } from '../core/Configuration';
import { EditorEngine } from '../editor/EditorEngine';
import { AIAssistant } from '../ai/AIAssistant';
import { Debugger } from '../tools/Debugger';
import { Terminal, TerminalOptions } from '../tools/Terminal';
import { BuildSystem, BuildResult, TestResult } from '../tools/BuildSystem';
import { PackageManager, PackageOptions, PackageResult, PackageSearchResult, InstalledPackage, PackageInfo } from '../tools/PackageManager';
import { GitIntegration, GitResult, GitBranch, GitCommit } from '../tools/GitIntegration';
import { UIEngine, NotificationType, InputBoxOptions, QuickPickItem, QuickPickOptions, MessageBoxOptions, MessageBoxResult } from '../ui/UIEngine';
import { TextDocument, FileItem, WorkspaceFolder, Breakpoint, StackFrame, Thread, Variable, AISuggestion, AICompletionContext, AICompletionResult, Range } from './types';

export class EventAPI {
  constructor(private eventBus: EventBus) {}

  on<T>(event: string, handler: EventHandler<T>): IDisposable {
    return this.eventBus.on(event, handler);
  }

  once<T>(event: string, handler: EventHandler<T>): IDisposable {
    return this.eventBus.once(event, handler);
  }

  off<T>(event: string, handler: EventHandler<T>): void {
    this.eventBus.off(event, handler);
  }

  emit<T>(event: string, payload: T): void {
    this.eventBus.emit(event, payload);
  }
}

export class WorkspaceAPI {
  constructor(
    private configuration: Configuration,
  ) {}

  async openFolder(uri: string): Promise<void> {
    this.configuration.set('workspace.path', uri);
  }

  getWorkspaceFolders(): WorkspaceFolder[] {
    const path = this.configuration.get<string>('workspace.path');
    if (!path) return [];
    return [{
      uri: `file://${path}`,
      name: path.split(/[/\\]/).pop() || path,
      path,
    }];
  }

  getFileTree(): FileItem[] {
    return [];
  }

  async createFile(path: string): Promise<void> {
  }

  async deleteFile(path: string): Promise<void> {
  }

  async renameFile(oldPath: string, newPath: string): Promise<void> {
  }
}

export class EditorAPI {
  constructor(
    private editorEngine: EditorEngine,
  ) {}

  async openDocument(uri: string): Promise<TextDocument> {
    return this.editorEngine.openDocument(uri);
  }

  closeDocument(uri: string): void {
    this.editorEngine.closeDocument(uri);
  }

  getActiveDocument(): TextDocument | undefined {
    return this.editorEngine.getActiveDocument();
  }

  getDocument(uri: string): TextDocument | undefined {
    return this.editorEngine.getDocument(uri);
  }

  onDidOpenDocument(handler: (event: { uri: string; document: TextDocument }) => void): IDisposable {
    return this.editorEngine.onDocumentOpened(handler);
  }

  onDidCloseDocument(handler: (event: { uri: string }) => void): IDisposable {
    return this.editorEngine.onDocumentClosed(handler);
  }

  onDidChangeDocument(handler: (event: { uri: string; document: TextDocument; version: number }) => void): IDisposable {
    return this.editorEngine.onDocumentChanged(handler);
  }
}

export class AIAPI {
  constructor(private aiAssistant: AIAssistant) {}

  async generateCompletion(context: AICompletionContext): Promise<AICompletionResult> {
    return this.aiAssistant.generateCompletion(context);
  }

  async getSuggestions(document: TextDocument): Promise<AISuggestion[]> {
    return this.aiAssistant.getSuggestions(document);
  }

  async explainCode(document: TextDocument, range: Range): Promise<string> {
    return this.aiAssistant.explainCode(document, range);
  }

  async detectBugs(document: TextDocument): Promise<AISuggestion[]> {
    return this.aiAssistant.detectBugs(document);
  }

  async generateDocumentation(document: TextDocument, range: Range): Promise<string> {
    return this.aiAssistant.generateDocumentation(document, range);
  }
}

export class DebugAPI {
  constructor(private dbg: Debugger) {}

  setBreakpoint(uri: string, line: number, condition?: string): Breakpoint {
    return this.dbg.setBreakpoint(uri, line, condition);
  }

  removeBreakpoint(id: string): void {
    this.dbg.removeBreakpoint(id);
  }

  async start(): Promise<void> {
    return this.dbg.start();
  }

  async stop(): Promise<void> {
    return this.dbg.stop();
  }

  async stepOver(): Promise<void> {
    return this.dbg.stepOver();
  }

  async stepInto(): Promise<void> {
    return this.dbg.stepInto();
  }

  async stepOut(): Promise<void> {
    return this.dbg.stepOut();
  }

  getThreads(): Thread[] {
    return this.dbg.getThreads();
  }

  getStackFrames(threadId: number): StackFrame[] {
    return this.dbg.getStackFrames(threadId);
  }

  getVariables(threadId: number, frameId: number): Variable[] {
    return this.dbg.getVariables(threadId, frameId);
  }

  async evaluate(expression: string, threadId: number, frameId: number): Promise<Variable> {
    return this.dbg.evaluate(expression, threadId, frameId);
  }
}

export class TerminalAPI {
  constructor(private terminal: Terminal) {}

  async open(options?: TerminalOptions): Promise<number> {
    return this.terminal.open(options);
  }

  close(terminalId: number): void {
    this.terminal.close(terminalId);
  }

  write(terminalId: number, data: string): void {
    this.terminal.write(terminalId, data);
  }

  onData(terminalId: number, handler: (data: string) => void): IDisposable {
    return this.terminal.onData(terminalId, handler);
  }
}

export class BuildAPI {
  constructor(private buildSystem: BuildSystem) {}

  async build(config?: Partial<BuildConfig>): Promise<BuildResult> {
    return this.buildSystem.build(config);
  }

  async clean(config?: Partial<BuildConfig>): Promise<BuildResult> {
    return this.buildSystem.clean(config);
  }

  async rebuild(config?: Partial<BuildConfig>): Promise<BuildResult> {
    return this.buildSystem.rebuild(config);
  }

  async runTests(config?: Partial<BuildConfig>): Promise<TestResult> {
    return this.buildSystem.runTests(config);
  }

  getConfig(): BuildConfig {
    return this.buildSystem.getCurrentConfig();
  }

  updateConfig(config: Partial<BuildConfig>): void {
    this.buildSystem.updateConfig(config);
  }
}

export class PackageAPI {
  constructor(private packageManager: PackageManager) {}

  async install(packageName: string, version?: string, options?: PackageOptions): Promise<PackageResult> {
    return this.packageManager.install(packageName, version, options);
  }

  async uninstall(packageName: string): Promise<PackageResult> {
    return this.packageManager.uninstall(packageName);
  }

  async update(packageName?: string): Promise<PackageResult> {
    return this.packageManager.update(packageName);
  }

  async search(query: string): Promise<PackageSearchResult[]> {
    return this.packageManager.search(query);
  }

  async list(): Promise<InstalledPackage[]> {
    return this.packageManager.list();
  }

  async publish(packagePath: string): Promise<PackageResult> {
    return this.packageManager.publish(packagePath);
  }

  async info(packageName: string): Promise<PackageInfo | undefined> {
    return this.packageManager.info(packageName);
  }
}

export class GitAPI {
  constructor(private gitIntegration: GitIntegration) {}

  async status(): Promise<GitStatus> {
    return this.gitIntegration.status();
  }

  async add(files?: string[]): Promise<GitResult> {
    return this.gitIntegration.add(files);
  }

  async commit(message: string): Promise<GitResult> {
    return this.gitIntegration.commit(message);
  }

  async push(remote?: string, branch?: string): Promise<GitResult> {
    return this.gitIntegration.push(remote, branch);
  }

  async pull(remote?: string, branch?: string): Promise<GitResult> {
    return this.gitIntegration.pull(remote, branch);
  }

  async branch(name?: string): Promise<GitBranch[]> {
    return this.gitIntegration.branch(name);
  }

  async checkout(target: string): Promise<GitResult> {
    return this.gitIntegration.checkout(target);
  }

  async log(maxCount?: number): Promise<GitCommit[]> {
    return this.gitIntegration.log(maxCount);
  }

  async diff(file?: string): Promise<string> {
    return this.gitIntegration.diff(file);
  }

  async stash(message?: string): Promise<GitResult> {
    return this.gitIntegration.stash(message);
  }

  async stashPop(): Promise<GitResult> {
    return this.gitIntegration.stashPop();
  }
}

export class UIAPI {
  constructor(private uiEngine: UIEngine) {}

  showNotification(message: string, type: NotificationType): void {
    this.uiEngine.showNotification(message, type);
  }

  showInputBox(options: InputBoxOptions): Promise<string | undefined> {
    return this.uiEngine.showInputBox(options);
  }

  showQuickPick<T>(items: QuickPickItem<T>[], options?: QuickPickOptions): Promise<T | undefined> {
    return this.uiEngine.showQuickPick(items, options);
  }

  showMessageBox(options: MessageBoxOptions): Promise<MessageBoxResult> {
    return this.uiEngine.showMessageBox(options);
  }

  showPanel(panelId: string): void {
    this.uiEngine.showPanel(panelId);
  }

  hidePanel(panelId: string): void {
    this.uiEngine.hidePanel(panelId);
  }

  togglePanel(panelId: string): void {
    this.uiEngine.togglePanel(panelId);
  }
}

export class ConfigAPI {
  constructor(private configuration: Configuration) {}

  get<T>(key: string, defaultValue?: T): T {
    return this.configuration.get(key, defaultValue);
  }

  set<T>(key: string, value: T): void {
    this.configuration.set(key, value);
  }

  has(key: string): boolean {
    return this.configuration.has(key);
  }

  delete(key: string): void {
    this.configuration.delete(key);
  }

  onDidChange(key: string, handler: EventHandler<unknown>): IDisposable {
    return this.configuration.onDidChange(key, handler);
  }
}

export class LogAPI {
  info(message: string, ...args: unknown[]): void {
    console.log(`[INFO] ${message}`, ...args);
  }

  warn(message: string, ...args: unknown[]): void {
    console.warn(`[WARN] ${message}`, ...args);
  }

  error(message: string, ...args: unknown[]): void {
    console.error(`[ERROR] ${message}`, ...args);
  }

  debug(message: string, ...args: unknown[]): void {
    console.debug(`[DEBUG] ${message}`, ...args);
  }
}

export class PluginAPI {
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

  constructor(
    eventBus: EventBus,
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
  ) {
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
  }
}

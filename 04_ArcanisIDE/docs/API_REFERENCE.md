# API Reference

## IDEAPI

**File:** `src/api/IDEAPI.ts`

The top-level API exposed by `ArcanisIDE.getAPI()`. Provides access to all IDE subsystems.

```typescript
class IDEAPI {
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
}
```

| Property | Type | Description |
|----------|------|-------------|
| `events` | `EventAPI` | EventBus publish/subscribe |
| `commands` | `CommandRegistry` | Command registration and execution |
| `workspace` | `WorkspaceAPI` | Workspace and file management |
| `editor` | `EditorAPI` | Document operations |
| `ai` | `AIAPI` | AI-powered code assistance |
| `debug` | `DebugAPI` | Debugger control |
| `terminal` | `TerminalAPI` | Terminal instances |
| `build` | `BuildAPI` | Build system |
| `packages` | `PackageAPI` | Package management |
| `git` | `GitAPI` | Git integration |
| `ui` | `UIAPI` | User interface dialogs |
| `config` | `ConfigAPI` | Configuration management |
| `log` | `LogAPI` | Logging |
| `plugins` | `PluginManagementAPI` | Plugin lifecycle management |

### Methods

```typescript
dispose(): void
```
Clears all EventBus listeners.

```typescript
getVersion(): string
```
Returns the IDE version string (`'0.1.0'`).

---

## PluginAPI

**File:** `src/api/PluginAPI.ts`

The API exposed to plugins. Identical to `IDEAPI` except it does not expose the `plugins` sub-API (plugins cannot manage other plugins).

```typescript
class PluginAPI {
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
}
```

---

## Sub-API References

### EventAPI

**File:** `src/api/PluginAPI.ts:15`

```typescript
class EventAPI {
  on<T>(event: string, handler: EventHandler<T>): IDisposable;
  once<T>(event: string, handler: EventHandler<T>): IDisposable;
  off<T>(event: string, handler: EventHandler<T>): void;
  emit<T>(event: string, payload: T): void;
}
```

| Method | Description |
|--------|-------------|
| `on` | Subscribe to an event. Returns an `IDisposable` that unsubscribes on `dispose()`. |
| `once` | Subscribe for a single invocation. Automatically removed after first emit. |
| `off` | Explicitly unsubscribe a handler. |
| `emit` | Publish an event with a typed payload to all subscribers. |

---

### CommandRegistry

**File:** `src/core/CommandRegistry.ts`

```typescript
class CommandRegistry {
  registerCommand(id: string, handler: CommandHandler, context?: string): IDisposable;
  executeCommand(id: string, ...args: unknown[]): Promise<unknown>;
  getCommand(id: string): CommandDescriptor | undefined;
  getCommands(context?: string): CommandDescriptor[];
  hasCommand(id: string): boolean;
}
```

| Method | Description |
|--------|-------------|
| `registerCommand` | Register a command handler. Overrides existing with warning. |
| `executeCommand` | Execute a command by ID. Throws if not found. |
| `getCommand` | Look up a command descriptor by ID. |
| `getCommands` | List all commands, optionally filtered by context string. |
| `hasCommand` | Check whether a command ID is registered. |

---

### WorkspaceAPI

**File:** `src/api/PluginAPI.ts:35`

```typescript
class WorkspaceAPI {
  async openFolder(uri: string): Promise<void>;
  getWorkspaceFolders(): WorkspaceFolder[];
  getFileTree(): FileItem[];
  async createFile(path: string): Promise<void>;
  async deleteFile(path: string): Promise<void>;
  async renameFile(oldPath: string, newPath: string): Promise<void>;
}
```

| Method | Description |
|--------|-------------|
| `openFolder` | Set the workspace path. |
| `getWorkspaceFolders` | Return array of open workspace folders. |
| `getFileTree` | Return the project file tree as a nested `FileItem[]`. |
| `createFile` | Create a new file at the given path. |
| `deleteFile` | Delete a file at the given path. |
| `renameFile` | Rename a file from old path to new path. |

---

### EditorAPI

**File:** `src/api/PluginAPI.ts:68`

```typescript
class EditorAPI {
  async openDocument(uri: string): Promise<TextDocument>;
  closeDocument(uri: string): void;
  getActiveDocument(): TextDocument | undefined;
  getDocument(uri: string): TextDocument | undefined;
  onDidOpenDocument(handler: (event: { uri: string; document: TextDocument }) => void): IDisposable;
  onDidCloseDocument(handler: (event: { uri: string }) => void): IDisposable;
  onDidChangeDocument(handler: (event: { uri: string; document: TextDocument; version: number }) => void): IDisposable;
}
```

| Method | Description |
|--------|-------------|
| `openDocument` | Open a document by URI. Returns existing document if already open. |
| `closeDocument` | Close a document and clean up associated state. |
| `getActiveDocument` | Get the currently active document, or `undefined`. |
| `getDocument` | Get a document by URI, or `undefined` if not open. |
| `onDidOpenDocument` | Fired when a document is opened. |
| `onDidCloseDocument` | Fired when a document is closed. |
| `onDidChangeDocument` | Fired when a document's content changes. Includes version number. |

---

### AIAPI

**File:** `src/api/PluginAPI.ts:102`

```typescript
class AIAPI {
  async generateCompletion(context: AICompletionContext): Promise<AICompletionResult>;
  async getSuggestions(document: TextDocument): Promise<AISuggestion[]>;
  async explainCode(document: TextDocument, range: Range): Promise<string>;
  async detectBugs(document: TextDocument): Promise<AISuggestion[]>;
  async generateDocumentation(document: TextDocument, range: Range): Promise<string>;
}
```

| Method | Description |
|--------|-------------|
| `generateCompletion` | Generate inline code completions based on document context, position, prefix/suffix. |
| `getSuggestions` | Analyze document for improvement suggestions (performance, style, security). |
| `explainCode` | Generate a natural-language explanation of the code in the given range. |
| `detectBugs` | Scan document for common bug patterns (loose equality, off-by-one, null references). |
| `generateDocumentation` | Generate JSDoc-style documentation for the code in the given range. |

---

### DebugAPI

**File:** `src/api/PluginAPI.ts:126`

```typescript
class DebugAPI {
  setBreakpoint(uri: string, line: number, condition?: string): Breakpoint;
  removeBreakpoint(id: string): void;
  async start(): Promise<void>;
  async stop(): Promise<void>;
  async stepOver(): Promise<void>;
  async stepInto(): Promise<void>;
  async stepOut(): Promise<void>;
  getThreads(): Thread[];
  getStackFrames(threadId: number): StackFrame[];
  getVariables(threadId: number, frameId: number): Variable[];
  async evaluate(expression: string, threadId: number, frameId: number): Promise<Variable>;
}
```

| Method | Description |
|--------|-------------|
| `setBreakpoint` | Set a breakpoint on a file at a line, with optional condition. |
| `removeBreakpoint` | Remove a breakpoint by its ID. |
| `start` | Start the debugging session. |
| `stop` | Stop the debugging session. |
| `stepOver` | Step over the current line. |
| `stepInto` | Step into the current function call. |
| `stepOut` | Step out of the current function. |
| `getThreads` | Get all active threads. |
| `getStackFrames` | Get stack frames for a given thread. |
| `getVariables` | Get variables for a given thread and frame. |
| `evaluate` | Evaluate an expression in the context of a thread and frame. |

---

### TerminalAPI

**File:** `src/api/PluginAPI.ts:174`

```typescript
class TerminalAPI {
  async open(options?: TerminalOptions): Promise<number>;
  close(terminalId: number): void;
  write(terminalId: number, data: string): void;
  onData(terminalId: number, handler: (data: string) => void): IDisposable;
}
```

| Method | Description |
|--------|-------------|
| `open` | Open a new terminal. Returns the terminal ID. |
| `close` | Close a terminal by ID. |
| `write` | Write data to a terminal's input buffer. |
| `onData` | Subscribe to data output from a terminal. |

**TerminalOptions:**
```typescript
interface TerminalOptions {
  title?: string;
  shellPath?: string;
  shellArgs?: string[];
  cwd?: string;
  env?: Record<string, string>;
}
```

**TerminalInstance:**
```typescript
interface TerminalInstance {
  id: number;
  title: string;
  process?: string;
  cols: number;
  rows: number;
  buffer: string[];
}
```

---

### BuildAPI

**File:** `src/api/PluginAPI.ts:194`

```typescript
class BuildAPI {
  async build(config?: Partial<BuildConfig>): Promise<BuildResult>;
  async clean(config?: Partial<BuildConfig>): Promise<BuildResult>;
  async rebuild(config?: Partial<BuildConfig>): Promise<BuildResult>;
  async runTests(config?: Partial<BuildConfig>): Promise<TestResult>;
  getConfig(): BuildConfig;
  updateConfig(config: Partial<BuildConfig>): void;
}
```

| Method | Description |
|--------|-------------|
| `build` | Execute a build with optional config overrides. |
| `clean` | Clean build artifacts. |
| `rebuild` | Clean then build. |
| `runTests` | Run the test suite. |
| `getConfig` | Get the current build configuration. |
| `updateConfig` | Update build configuration with partial overrides. |

**BuildResult:**
```typescript
interface BuildResult {
  success: boolean;
  target: string;
  mode: string;
  duration: number;
  output: string;
  errors: BuildError[];
  warnings: BuildWarning[];
}
```

**TestResult:**
```typescript
interface TestResult {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  duration: number;
  tests: TestCase[];
}
```

---

### PackageAPI

**File:** `src/api/PluginAPI.ts:222`

```typescript
class PackageAPI {
  async install(packageName: string, version?: string, options?: PackageOptions): Promise<PackageResult>;
  async uninstall(packageName: string): Promise<PackageResult>;
  async update(packageName?: string): Promise<PackageResult>;
  async search(query: string): Promise<PackageSearchResult[]>;
  async list(): Promise<InstalledPackage[]>;
  async publish(packagePath: string): Promise<PackageResult>;
  async info(packageName: string): Promise<PackageInfo | undefined>;
}
```

| Method | Description |
|--------|-------------|
| `install` | Install a package by name, optionally specifying version and options. |
| `uninstall` | Uninstall a package. |
| `update` | Update a specific package or all packages. |
| `search` | Search the package registry for packages matching the query. |
| `list` | List all installed packages. |
| `publish` | Publish a package from the given directory path. |
| `info` | Get detailed information about a package. |

---

### GitAPI

**File:** `src/api/PluginAPI.ts:254`

```typescript
class GitAPI {
  async status(): Promise<GitStatus>;
  async add(files?: string[]): Promise<GitResult>;
  async commit(message: string): Promise<GitResult>;
  async push(remote?: string, branch?: string): Promise<GitResult>;
  async pull(remote?: string, branch?: string): Promise<GitResult>;
  async branch(name?: string): Promise<GitBranch[]>;
  async checkout(target: string): Promise<GitResult>;
  async log(maxCount?: number): Promise<GitCommit[]>;
  async diff(file?: string): Promise<string>;
  async stash(message?: string): Promise<GitResult>;
  async stashPop(): Promise<GitResult>;
}
```

| Method | Description |
|--------|-------------|
| `status` | Get the current repository status. |
| `add` | Stage files (all files if no argument). |
| `commit` | Commit staged changes with a message. |
| `push` | Push commits to a remote branch. |
| `pull` | Pull changes from a remote branch. |
| `branch` | List branches or create a new branch. |
| `checkout` | Switch to a branch or commit. |
| `log` | View commit history. |
| `diff` | View diff for a file or working tree. |
| `stash` | Stash working directory changes. |
| `stashPop` | Restore the most recent stash. |

---

### UIAPI

**File:** `src/api/PluginAPI.ts:302`

```typescript
class UIAPI {
  showNotification(message: string, type: NotificationType): void;
  showInputBox(options: InputBoxOptions): Promise<string | undefined>;
  showQuickPick<T>(items: QuickPickItem<T>[], options?: QuickPickOptions): Promise<T | undefined>;
  showMessageBox(options: MessageBoxOptions): Promise<MessageBoxResult>;
  showPanel(panelId: string): void;
  hidePanel(panelId: string): void;
  togglePanel(panelId: string): void;
}
```

| Method | Description |
|--------|-------------|
| `showNotification` | Show a toast notification in one of the bottom corners. |
| `showInputBox` | Show a text input dialog with optional validation. |
| `showQuickPick` | Show a searchable selection list. |
| `showMessageBox` | Show a modal dialog with customizable buttons. |
| `showPanel` | Show a panel (e.g., `'output'`, `'problems'`, `'debug'`, `'terminal'`). |
| `hidePanel` | Hide a panel. |
| `togglePanel` | Toggle a panel's visibility. |

---

### ConfigAPI

**File:** `src/api/PluginAPI.ts:334`

```typescript
class ConfigAPI {
  get<T>(key: string, defaultValue?: T): T;
  set<T>(key: string, value: T): void;
  has(key: string): boolean;
  delete(key: string): void;
  onDidChange(key: string, handler: EventHandler<unknown>): IDisposable;
}
```

| Method | Description |
|--------|-------------|
| `get` | Get a configuration value. Falls back to default, then provided default. |
| `set` | Set a configuration value and emit change events. |
| `has` | Check if a key exists in config or defaults. |
| `delete` | Remove a user-set value (reverts to default). |
| `onDidChange` | Subscribe to value changes for a specific key. |

---

### LogAPI

**File:** `src/api/PluginAPI.ts:358`

```typescript
class LogAPI {
  info(message: string, ...args: unknown[]): void;
  warn(message: string, ...args: unknown[]): void;
  error(message: string, ...args: unknown[]): void;
  debug(message: string, ...args: unknown[]): void;
}
```

Logs messages to the console with level prefixes (`[INFO]`, `[WARN]`, `[ERROR]`, `[DEBUG]`).

---

### PluginManagementAPI

**File:** `src/api/IDEAPI.ts:79`

Only available through `IDEAPI.plugins` (not exposed to plugins).

```typescript
class PluginManagementAPI {
  async loadPlugin(pluginPath: string): Promise<PluginInstance>;
  async unloadPlugin(name: string): Promise<void>;
  getPlugin(name: string): PluginInstance | undefined;
  getPlugins(): PluginInstance[];
  async scanAndLoadPlugins(pluginsDir: string): Promise<void>;
  onPluginLoaded(handler: (plugin: PluginInstance) => void): IDisposable;
  onPluginUnloaded(handler: (name: string) => void): IDisposable;
}
```

| Method | Description |
|--------|-------------|
| `loadPlugin` | Load and activate a plugin from a directory. |
| `unloadPlugin` | Deactivate and unload a plugin by name. |
| `getPlugin` | Get a loaded plugin instance by name. |
| `getPlugins` | Get all loaded plugin instances. |
| `scanAndLoadPlugins` | Scan a directory and load all plugin subdirectories. |
| `onPluginLoaded` | Subscribe to plugin loaded events. |
| `onPluginUnloaded` | Subscribe to plugin unloaded events. |

---

## Core Types Reference

**File:** `src/api/types.ts`

### Document / Editor Types

#### TextDocument
```typescript
interface TextDocument {
  uri: string;
  fileName: string;
  languageId: string;
  version: number;
  getText(): string;
  getText(range: Range): string;
  lineAt(line: number): TextLine;
  lineCount: number;
}
```

#### TextLine
```typescript
interface TextLine {
  lineNumber: number;
  text: string;
  range: Range;
  firstNonWhitespaceCharacterIndex: number;
  isEmptyOrWhitespace: boolean;
}
```

#### Position
```typescript
interface Position {
  line: number;
  column: number;
}
```

#### Range
```typescript
interface Range {
  start: Position;
  end: Position;
}
```

#### EditorConfig
```typescript
interface EditorConfig {
  fontSize: number;
  fontFamily: string;
  tabSize: number;
  insertSpaces: boolean;
  wordWrap: 'off' | 'on' | 'wordWrapColumn';
  wordWrapColumn: number;
  lineNumbers: 'on' | 'off' | 'relative';
  minimap: boolean;
  bracketPairColorization: boolean;
  autoClosingBrackets: boolean;
  autoClosingQuotes: boolean;
  formatOnPaste: boolean;
  formatOnSave: boolean;
  suggestOnTriggerCharacters: boolean;
}
```

### Language Types

#### Token
```typescript
interface Token {
  type: TokenType;
  value: string;
  range: Range;
}
```

#### TokenType
```
enum TokenType {
  Keyword, Type, Function, String, Number, Comment,
  Operator, Variable, Parameter, Property, Decorator,
  Punctuation, Whitespace, Identifier, Unknown
}
```

#### CompletionItem
```typescript
interface CompletionItem {
  label: string;
  kind: CompletionItemKind;
  detail?: string;
  documentation?: string;
  insertText?: string;
  filterText?: string;
  sortText?: string;
  range?: Range;
  commitCharacters?: string[];
}
```

#### CompletionItemKind
```
enum CompletionItemKind {
  Method, Function, Constructor, Field, Variable,
  Class, Struct, Interface, Module, Property, Event,
  Operator, Unit, Value, Constant, Enum, EnumMember,
  Keyword, Snippet, Color, File, Reference, Folder, TypeParameter
}
```

#### Diagnostic
```typescript
interface Diagnostic {
  range: Range;
  severity: DiagnosticSeverity;
  message: string;
  source: string;
  code: string | number;
  relatedInformation?: DiagnosticRelatedInfo[];
}
```

#### DiagnosticSeverity
```
enum DiagnosticSeverity {
  Error = 0,
  Warning = 1,
  Information = 2,
  Hint = 3
}
```

#### CodeAction
```typescript
interface CodeAction {
  title: string;
  kind: CodeActionKind;
  diagnostics?: Diagnostic[];
  edit?: WorkspaceEdit;
  command?: Command;
}
```

#### CodeActionKind
```
enum CodeActionKind {
  QuickFix = 'quickfix',
  Refactor = 'refactor',
  RefactorExtract = 'refactor.extract',
  RefactorInline = 'refactor.inline',
  RefactorRewrite = 'refactor.rewrite',
  Source = 'source',
  SourceOrganizeImports = 'source.organizeImports'
}
```

#### LanguageService
```typescript
interface LanguageService {
  languageId: string;
  provideTokens(document: TextDocument): Token[];
  provideCompletions(document: TextDocument, position: Position, context?: CompletionContext): CompletionItem[];
  provideDiagnostics(document: TextDocument): Diagnostic[];
  provideCodeActions(document: TextDocument, range: Range, context: CodeActionContext): CodeAction[];
  provideHover(document: TextDocument, position: Position): string | undefined;
  provideSignatureHelp(document: TextDocument, position: Position): SignatureHelp | undefined;
  provideDocumentFormatting(document: TextDocument, options: FormattingOptions): TextEdit[];
  provideDefinition(document: TextDocument, position: Position): Location | undefined;
  provideReferences(document: TextDocument, position: Position): Location[];
  provideRename(document: TextDocument, position: Position, newName: string): WorkspaceEdit | undefined;
}
```

#### CompletionContext / CompletionTriggerKind
```typescript
interface CompletionContext {
  triggerKind: CompletionTriggerKind;
  triggerCharacter?: string;
}

enum CompletionTriggerKind {
  Invoke = 0,
  TriggerCharacter = 1,
  TriggerForIncompleteCompletions = 2
}
```

### AI Types

#### AISuggestion
```typescript
interface AISuggestion {
  id: string;
  type: 'improvement' | 'bug' | 'performance' | 'security' | 'style' | 'documentation';
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  range?: Range;
  code?: string;
  explanation: string;
}
```

#### AICompletionContext
```typescript
interface AICompletionContext {
  document: TextDocument;
  position: Position;
  prefix: string;
  suffix: string;
  language: string;
  recentFiles: string[];
  projectStructure: string[];
}
```

#### AICompletionResult
```typescript
interface AICompletionResult {
  completions: AICompletion[];
  requestId: string;
}
```

#### AICompletion
```typescript
interface AICompletion {
  text: string;
  confidence: number;
  explanation?: string;
}
```

### Tool Types

#### Breakpoint
```typescript
interface Breakpoint {
  id: string;
  uri: string;
  line: number;
  column?: number;
  enabled: boolean;
  condition?: string;
  hitCondition?: string;
  logMessage?: string;
}
```

#### StackFrame
```typescript
interface StackFrame {
  id: number;
  name: string;
  source?: string;
  line: number;
  column: number;
  scopes?: Scope[];
}
```

#### Variable
```typescript
interface Variable {
  name: string;
  value: string;
  type: string;
  reference?: number;
  children?: Variable[];
}
```

#### Thread
```typescript
interface Thread {
  id: number;
  name: string;
  stopped: boolean;
  stackFrames: StackFrame[];
}
```

#### BuildConfig
```typescript
interface BuildConfig {
  target: string;
  mode: 'debug' | 'release';
  optimize: boolean;
  outputDir: string;
  sourceDir: string;
  compilerFlags: string[];
}
```

#### GitStatus
```typescript
interface GitStatus {
  branch: string;
  changes: GitChange[];
  ahead: number;
  behind: number;
  staged: number;
  modified: number;
  untracked: number;
  conflicts: number;
}
```

#### GitChange
```typescript
interface GitChange {
  path: string;
  status: 'added' | 'modified' | 'deleted' | 'renamed' | 'untracked' | 'conflict';
}
```

### Plugin Types

#### PluginManifest
```typescript
interface PluginManifest {
  name: string;
  version: string;
  description: string;
  author: string;
  license?: string;
  main: string;
  contributes?: {
    commands?: CommandDefinition[];
    languages?: LanguageContribution[];
    themes?: ThemeContribution[];
    menuItems?: MenuContribution[];
    keybindings?: KeybindingContribution[];
  };
  activationEvents?: string[];
  dependencies?: string[];
}
```

#### PluginContext
```typescript
interface PluginContext {
  subscriptions: IDisposable[];
  extensionPath: string;
  workspaceState: Memento;
  globalState: Memento;
  log: (message: string) => void;
}
```

### UI Types

#### FileItem
```typescript
interface FileItem {
  name: string;
  path: string;
  isDirectory: boolean;
  children?: FileItem[];
  size?: number;
  modifiedAt?: Date;
}
```

#### WorkspaceFolder
```typescript
interface WorkspaceFolder {
  uri: string;
  name: string;
  path: string;
}
```

---

## Event Reference

### EventBus Events

All events are emitted via `EventBus.emit(event, payload)`.

| Event | Payload | Emitter | Description |
|-------|---------|---------|-------------|
| `document:opened` | `{ uri: string, document: TextDocument }` | EditorEngine | A document was opened |
| `document:closed` | `{ uri: string }` | EditorEngine | A document was closed |
| `document:changed` | `{ uri: string, document: TextDocument, version: number }` | EditorEngine | Document content changed |
| `editor:activeDocumentChanged` | `{ uri: string }` | EditorEngine | Active editor tab changed |
| `diagnostics:updated` | `{ uri: string, diagnostics: Diagnostic[] }` | DiagnosticEngine | Diagnostics refreshed for a document |
| `ai:completion` | `AICompletionResult` | AIAssistant | AI completion generated |
| `ai:suggestion` | `{ uri: string, suggestions: AISuggestion[] }` | AIAssistant | AI suggestions generated |
| `ai:explanation` | `{ uri: string, range: Range, explanation: string }` | AIAssistant | Code explanation generated |
| `ai:bug` | `{ uri: string, bugs: AISuggestion[] }` | AIAssistant | Bug detection results |
| `ai:doc` | `{ uri: string, range: Range, docs: string }` | AIAssistant | Documentation generated |
| `debugger:started` | `{}` | Debugger | Debug session started |
| `debugger:stopped` | `{}` | Debugger | Debug session stopped |
| `debugger:paused` | `{}` | Debugger | Execution paused |
| `debugger:continued` | `{} \| { action: 'stepOver' \| 'stepInto' \| 'stepOut' }` | Debugger | Execution resumed |
| `terminal:opened` | `TerminalInstance` | Terminal | Terminal created |
| `terminal:closed` | `{ id: number }` | Terminal | Terminal closed |
| `terminal:data` | `{ id: number, data: string }` | Terminal | Terminal output data |
| `build:started` | `BuildConfig` | BuildSystem | Build process started |
| `build:completed` | `BuildResult` | BuildSystem | Build process completed |
| `test:started` | `BuildConfig` | BuildSystem | Test run started |
| `test:completed` | `TestResult` | BuildSystem | Test run completed |
| `package:installed` | `InstalledPackage` | PackageManager | Package installed |
| `package:uninstalled` | `InstalledPackage` | PackageManager | Package uninstalled |
| `package:updated` | `InstalledPackage` | PackageManager | Package updated |
| `git:operationStart` | `{ operation: string, ... }` | GitIntegration | Git operation started |
| `git:operationEnd` | `{ operation: string, result: GitResult }` | GitIntegration | Git operation ended |
| `plugin:loaded` | `{ name: string, version: string }` | PluginManager | Plugin loaded and activated |
| `plugin:unloaded` | `{ name: string }` | PluginManager | Plugin unloaded |
| `ui:initialized` | `{ timestamp: number }` | UIEngine | UI engine initialized |
| `ui:componentRegistered` | `{ id: string, component: UIComponent }` | UIEngine | Component registered |
| `ui:panelShown` | `{ panelId: string }` | UIEngine | Panel shown |
| `ui:panelHidden` | `{ panelId: string }` | UIEngine | Panel hidden |
| `ui:themeChanged` | `{ themeId: string, theme: Theme }` | ThemeManager | Theme changed |
| `ui:notification` | `{ message: string, type: NotificationType, timestamp: number }` | UIEngine | Notification requested |
| `ui:showInputBox` | `{ options: InputBoxOptions, resolve: Function }` | UIEngine | Input box requested |
| `ui:showQuickPick` | `{ items: QuickPickItem[], options: QuickPickOptions, resolve: Function }` | UIEngine | Quick pick requested |
| `ui:showMessageBox` | `{ options: MessageBoxOptions, resolve: Function }` | UIEngine | Message box requested |
| `config:changed` | `{ key: string, value: unknown, oldValue: unknown }` | Configuration | Any config value changed |
| `config:changed:<key>` | `<value>` | Configuration | Specific config key changed |
| `command:<id>` | `{ args: unknown[], plugin: string }` | PluginManager | Plugin command executed |
| `file:save` | `{ uri: string }` | ArcanisIDE | File save requested |
| `file:saveAll` | `{}` | ArcanisIDE | Save all files requested |
| `project:run` | `{}` | ArcanisIDE | Project run requested |

---

## Command Reference

### Built-in Commands

Registered by `ArcanisIDE.registerDefaultCommands()` in `src/index.ts:98`.

| Command ID | Description |
|------------|-------------|
| `arcanis.about` | Show the About dialog with version info |
| `arcanis.toggleSidebar` | Toggle sidebar panel visibility |
| `arcanis.togglePanel` | Toggle bottom panel visibility |
| `arcanis.openFile` | Prompt for a file path and open it |
| `arcanis.saveFile` | Save the active document |
| `arcanis.saveAll` | Save all open documents |
| `arcanis.closeFile` | Close the active document |
| `arcanis.build` | Execute the build system |
| `arcanis.run` | Run the project |
| `arcanis.debug` | Start a debug session |
| `arcanis.git.commit` | Prompt for commit message and commit |
| `arcanis.git.push` | Push to remote |
| `arcanis.ai.explain` | Explain the active document's code |
| `arcanis.ai.suggest` | Get AI suggestions for the active document |

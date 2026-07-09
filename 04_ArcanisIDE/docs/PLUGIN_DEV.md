# Plugin Development Guide

## Introduction

ArcanisIDE's plugin system allows you to extend the IDE with new functionality — custom language support, AI model adapters, developer tools, UI components, and more. Plugins are self-contained directories with a `manifest.json` and a JavaScript/TypeScript entry point.

The plugin system is built on top of the core `PluginManager` (`src/core/PluginManager.ts`), which handles discovery, loading, activation, and cleanup. Plugins receive a controlled API surface (`PluginAPI`) that mirrors the internal `IDEAPI` but excludes plugin management.

---

## Quick Start

Create a minimal plugin in three steps:

### 1. Directory Structure

```
my-plugin/
  manifest.json
  index.js
```

### 2. manifest.json

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "My first ArcanisIDE plugin",
  "author": "You",
  "main": "index.js"
}
```

### 3. index.js

```javascript
function activate(ctx) {
  const api = arcanis.getPluginAPI();
  const disposable = api.commands.registerCommand('my-plugin.hello', () => {
    api.ui.showNotification('Hello from my plugin!', 'info');
  });
  ctx.subscriptions.push(disposable);
  api.log.info('my-plugin activated');
}

function deactivate() {
  console.log('my-plugin deactivated');
}

module.exports = { activate, deactivate };
```

Place `my-plugin/` in the IDE's plugins directory. On next startup, it will be loaded and activated automatically.

---

## Plugin Manifest Reference

**Type:** `PluginManifest` (`src/api/types.ts:285`)

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "A description of the plugin",
  "author": "Author Name",
  "license": "MIT",
  "main": "dist/index.js",
  "contributes": {
    "commands": [],
    "languages": [],
    "themes": [],
    "menuItems": [],
    "keybindings": []
  },
  "activationEvents": ["onLanguage:typescript"],
  "dependencies": ["another-plugin"]
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Unique plugin identifier (kebab-case) |
| `version` | `string` | Yes | Semver version |
| `description` | `string` | Yes | Short description |
| `author` | `string` | Yes | Author name |
| `license` | `string` | No | SPDX license identifier |
| `main` | `string` | Yes | Entry point relative to plugin root |
| `contributes` | `object` | No | IDE contributions (see below) |
| `activationEvents` | `string[]` | No | Events that trigger activation |
| `dependencies` | `string[]` | No | Required plugin names |

### Contributes Section

#### commands

```json
{
  "commands": [
    {
      "id": "my-plugin.doThing",
      "title": "Do Something",
      "category": "My Plugin",
      "icon": "icon-name",
      "keybinding": "ctrl+shift+d"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique command ID (namespaced, e.g., `plugin-name.commandId`) |
| `title` | `string` | Human-readable command name |
| `category` | `string` | Optional grouping category |
| `icon` | `string` | Optional icon identifier |
| `keybinding` | `string` | Optional default keybinding |

Command handlers are automatically registered by the PluginManager. When executed, the command fires an event on the EventBus. The plugin must subscribe to `command:<id>` events to handle them.

#### languages

```json
{
  "languages": [
    {
      "id": "myLang",
      "extensions": [".mylang", ".ml"],
      "aliases": ["My Language"],
      "filenamePatterns": ["*.mylang"],
      "configuration": "./syntaxes/myLang.json"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Language identifier |
| `extensions` | `string[]` | Associated file extensions |
| `aliases` | `string[]` | Human-readable aliases |
| `filenamePatterns` | `string[]` | Glob patterns for file matching |
| `configuration` | `string` | Path to language config (grammar, snippets) |

#### themes

```json
{
  "themes": [
    {
      "id": "my-theme",
      "label": "My Theme",
      "type": "dark",
      "path": "./themes/my-theme.json"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique theme identifier |
| `label` | `string` | Display name |
| `type` | `'dark' \| 'light' \| 'highContrast'` | Theme type |
| `path` | `string` | Path to theme JSON file |

#### menuItems

```json
{
  "menuItems": [
    {
      "id": "my-plugin.menuItem",
      "label": "My Action",
      "command": "my-plugin.doThing",
      "group": "navigation",
      "order": 1,
      "when": "editorHasSelection"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Menu item identifier |
| `label` | `string` | Display label |
| `command` | `string` | Command ID to execute |
| `group` | `string` | Grouping for menu ordering |
| `order` | `number` | Sort order within group |
| `when` | `string` | Conditional context expression |

#### keybindings

```json
{
  "keybindings": [
    {
      "command": "my-plugin.doThing",
      "key": "ctrl+shift+d",
      "when": "editorFocus",
      "mac": "cmd+shift+d",
      "linux": "ctrl+shift+d",
      "win": "ctrl+shift+d"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `command` | `string` | Command ID |
| `key` | `string` | Default keybinding |
| `when` | `string` | Context condition |
| `mac` | `string` | macOS-specific binding |
| `linux` | `string` | Linux-specific binding |
| `win` | `string` | Windows-specific binding |

---

## Plugin API Reference

The `PluginAPI` object is accessible via the module parameter in `activate()` or through the IDE's `getPluginAPI()` method.

```javascript
// In activate(ctx):
// ctx contains the PluginContext
// For full API access:
const api = arcanis.getPluginAPI();
```

### events

**Class:** `EventAPI` (`src/api/PluginAPI.ts:15`)

Subscribe and publish to the EventBus.

```javascript
api.events.on('document:opened', (event) => {
  api.log.info(`Document opened: ${event.uri}`);
});
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `on` | `on<T>(event: string, handler: EventHandler<T>): IDisposable` | Subscribe to an event |
| `once` | `once<T>(event: string, handler: EventHandler<T>): IDisposable` | Subscribe once |
| `off` | `off<T>(event: string, handler: EventHandler<T>): void` | Unsubscribe |
| `emit` | `emit<T>(event: string, payload: T): void` | Publish an event |

### commands

**Class:** `CommandRegistry` (direct reference, `src/core/CommandRegistry.ts`)

Register and execute commands.

```javascript
api.commands.registerCommand('my-plugin.format', async (documentUri) => {
  // format logic
  return 'formatted';
});

const result = await api.commands.executeCommand('my-plugin.format', docUri);
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `registerCommand` | `(id: string, handler: CommandHandler, context?: string): IDisposable` | Register a command |
| `executeCommand` | `(id: string, ...args: unknown[]): Promise<unknown>` | Execute a command |
| `getCommand` | `(id: string): CommandDescriptor \| undefined` | Lookup command info |
| `getCommands` | `(context?: string): CommandDescriptor[]` | List all commands |
| `hasCommand` | `(id: string): boolean` | Check if command exists |

### workspace

**Class:** `WorkspaceAPI` (`src/api/PluginAPI.ts:35`)

Manage workspace folders and files.

```javascript
const folders = api.workspace.getWorkspaceFolders();
await api.workspace.openFolder('/path/to/project');
const files = api.workspace.getFileTree();
await api.workspace.createFile('/path/to/new/file.ts');
await api.workspace.deleteFile('/path/to/old/file.ts');
await api.workspace.renameFile('/old.ts', '/new.ts');
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `openFolder` | `(uri: string): Promise<void>` | Open a workspace folder |
| `getWorkspaceFolders` | `(): WorkspaceFolder[]` | Get workspace folders |
| `getFileTree` | `(): FileItem[]` | Get project file tree |
| `createFile` | `(path: string): Promise<void>` | Create a new file |
| `deleteFile` | `(path: string): Promise<void>` | Delete a file |
| `renameFile` | `(oldPath: string, newPath: string): Promise<void>` | Rename a file |

### editor

**Class:** `EditorAPI` (`src/api/PluginAPI.ts:68`)

Open, close, and manage documents.

```javascript
const doc = await api.editor.openDocument('file:///path/to/file.ts');
const active = api.editor.getActiveDocument();
api.editor.closeDocument(doc.uri);
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `openDocument` | `(uri: string): Promise<TextDocument>` | Open a document |
| `closeDocument` | `(uri: string): void` | Close a document |
| `getActiveDocument` | `(): TextDocument \| undefined` | Get active document |
| `getDocument` | `(uri: string): TextDocument \| undefined` | Get document by URI |
| `onDidOpenDocument` | `(handler): IDisposable` | Document opened event |
| `onDidCloseDocument` | `(handler): IDisposable` | Document closed event |
| `onDidChangeDocument` | `(handler): IDisposable` | Document changed event |

### ai

**Class:** `AIAPI` (`src/api/PluginAPI.ts:102`)

Access AI-powered code assistance.

```javascript
const result = await api.ai.generateCompletion({
  document: activeDoc,
  position: { line: 10, column: 5 },
  prefix: 'const x = ',
  suffix: ';',
  language: 'typescript',
  recentFiles: [],
  projectStructure: [],
});

const suggestions = await api.ai.getSuggestions(activeDoc);
const explanation = await api.ai.explainCode(activeDoc, { start: { line: 0, column: 0 }, end: { line: 5, column: 0 } });
const bugs = await api.ai.detectBugs(activeDoc);
const docs = await api.ai.generateDocumentation(activeDoc, range);
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `generateCompletion` | `(context: AICompletionContext): Promise<AICompletionResult>` | Get inline code completions |
| `getSuggestions` | `(document: TextDocument): Promise<AISuggestion[]>` | Get improvement suggestions |
| `explainCode` | `(document: TextDocument, range: Range): Promise<string>` | Explain selected code |
| `detectBugs` | `(document: TextDocument): Promise<AISuggestion[]>` | Detect bugs in document |
| `generateDocumentation` | `(document: TextDocument, range: Range): Promise<string>` | Generate documentation comments |

### debug

**Class:** `DebugAPI` (`src/api/PluginAPI.ts:126`)

Control the debugger.

```javascript
const bp = api.debug.setBreakpoint(docUri, 42, 'x > 5');
await api.debug.start();
await api.debug.stepOver();
await api.debug.stepInto();
await api.debug.stepOut();
const threads = api.debug.getThreads();
const frames = api.debug.getStackFrames(threadId);
const variables = api.debug.getVariables(threadId, frameId);
const result = await api.debug.evaluate('myVar', threadId, frameId);
await api.debug.stop();
api.debug.removeBreakpoint(bp.id);
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `setBreakpoint` | `(uri: string, line: number, condition?: string): Breakpoint` | Set a breakpoint |
| `removeBreakpoint` | `(id: string): void` | Remove a breakpoint |
| `start` | `(): Promise<void>` | Start debugging session |
| `stop` | `(): Promise<void>` | Stop debugging session |
| `stepOver` | `(): Promise<void>` | Step over |
| `stepInto` | `(): Promise<void>` | Step into |
| `stepOut` | `(): Promise<void>` | Step out |
| `getThreads` | `(): Thread[]` | Get all threads |
| `getStackFrames` | `(threadId: number): StackFrame[]` | Get stack frames |
| `getVariables` | `(threadId: number, frameId: number): Variable[]` | Get variables |
| `evaluate` | `(expression: string, threadId: number, frameId: number): Promise<Variable>` | Evaluate expression |

### terminal

**Class:** `TerminalAPI` (`src/api/PluginAPI.ts:174`)

Manage terminal instances.

```javascript
const termId = await api.terminal.open({ title: 'Build', cwd: '/project' });
api.terminal.write(termId, 'npm run build\n');
const disposable = api.terminal.onData(termId, (data) => {
  api.log.info('Terminal output:', data);
});
api.terminal.close(termId);
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `open` | `(options?: TerminalOptions): Promise<number>` | Open a new terminal |
| `close` | `(terminalId: number): void` | Close a terminal |
| `write` | `(terminalId: number, data: string): void` | Write to a terminal |
| `onData` | `(terminalId: number, handler): IDisposable` | Subscribe to terminal output |

### build

**Class:** `BuildAPI` (`src/api/PluginAPI.ts:194`)

Build, clean, and test.

```javascript
const result = await api.build.build({ mode: 'release' });
const cleanResult = await api.build.clean();
const rebuildResult = await api.build.rebuild();
const testResult = await api.build.runTests();
const config = api.build.getConfig();
api.build.updateConfig({ target: 'wasm32', optimize: true });
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `build` | `(config?: Partial<BuildConfig>): Promise<BuildResult>` | Execute build |
| `clean` | `(config?: Partial<BuildConfig>): Promise<BuildResult>` | Clean build artifacts |
| `rebuild` | `(config?: Partial<BuildConfig>): Promise<BuildResult>` | Clean and rebuild |
| `runTests` | `(config?: Partial<BuildConfig>): Promise<TestResult>` | Run tests |
| `getConfig` | `(): BuildConfig` | Get current build config |
| `updateConfig` | `(config: Partial<BuildConfig>): void` | Update build config |

### packages

**Class:** `PackageAPI` (`src/api/PluginAPI.ts:222`)

Manage Arcanis packages.

```javascript
await api.packages.install('my-package', '^1.0.0', { isDev: true });
await api.packages.uninstall('my-package');
await api.packages.update();
const results = await api.packages.search('template');
const installed = await api.packages.list();
const info = await api.packages.info('my-package');
await api.packages.publish('./my-package');
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `install` | `(name: string, version?: string, options?: PackageOptions): Promise<PackageResult>` | Install a package |
| `uninstall` | `(name: string): Promise<PackageResult>` | Uninstall a package |
| `update` | `(name?: string): Promise<PackageResult>` | Update packages |
| `search` | `(query: string): Promise<PackageSearchResult[]>` | Search packages |
| `list` | `(): Promise<InstalledPackage[]>` | List installed packages |
| `publish` | `(path: string): Promise<PackageResult>` | Publish a package |
| `info` | `(name: string): Promise<PackageInfo \| undefined>` | Get package info |

### git

**Class:** `GitAPI` (`src/api/PluginAPI.ts:254`)

Git integration.

```javascript
const status = await api.git.status();
await api.git.add(['src/index.ts']);
await api.git.commit('feat: add new feature');
await api.git.push('origin', 'main');
await api.git.pull('origin', 'main');
const branches = await api.git.branch();
await api.git.checkout('feature-branch');
const commits = await api.git.log(10);
const diff = await api.git.diff('src/index.ts');
await api.git.stash('WIP: refactoring');
await api.git.stashPop();
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `status` | `(): Promise<GitStatus>` | Get repository status |
| `add` | `(files?: string[]): Promise<GitResult>` | Stage files |
| `commit` | `(message: string): Promise<GitResult>` | Commit staged changes |
| `push` | `(remote?: string, branch?: string): Promise<GitResult>` | Push to remote |
| `pull` | `(remote?: string, branch?: string): Promise<GitResult>` | Pull from remote |
| `branch` | `(name?: string): Promise<GitBranch[]>` | List or create branches |
| `checkout` | `(target: string): Promise<GitResult>` | Checkout branch or commit |
| `log` | `(maxCount?: number): Promise<GitCommit[]>` | View commit log |
| `diff` | `(file?: string): Promise<string>` | View diff |
| `stash` | `(message?: string): Promise<GitResult>` | Stash changes |
| `stashPop` | `(): Promise<GitResult>` | Pop stashed changes |

### ui

**Class:** `UIAPI` (`src/api/PluginAPI.ts:302`)

Show UI dialogs and control panels.

```javascript
api.ui.showNotification('Build complete', 'success');

const name = await api.ui.showInputBox({
  title: 'New File',
  prompt: 'Enter file name',
  placeholder: 'myFile.ts',
  validateInput: (v) => v.length < 1 ? 'Name required' : undefined,
});

const selected = await api.ui.showQuickPick(
  [
    { label: 'Option A', value: 'a' },
    { label: 'Option B', value: 'b' },
  ],
  { placeholder: 'Choose an option' }
);

const result = await api.ui.showMessageBox({
  title: 'Confirm',
  message: 'Are you sure?',
  buttons: ['Yes', 'No'],
  cancelButton: 1,
});

api.ui.showPanel('output');
api.ui.hidePanel('debug');
api.ui.togglePanel('terminal');
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `showNotification` | `(message: string, type: NotificationType): void` | Show toast notification |
| `showInputBox` | `(options: InputBoxOptions): Promise<string \| undefined>` | Show text input dialog |
| `showQuickPick` | `<T>(items: QuickPickItem<T>[], options?: QuickPickOptions): Promise<T \| undefined>` | Show selection list |
| `showMessageBox` | `(options: MessageBoxOptions): Promise<MessageBoxResult>` | Show modal dialog |
| `showPanel` | `(panelId: string): void` | Show a panel |
| `hidePanel` | `(panelId: string): void` | Hide a panel |
| `togglePanel` | `(panelId: string): void` | Toggle a panel |

### config

**Class:** `ConfigAPI` (`src/api/PluginAPI.ts:334`)

Read and write configuration.

```javascript
const fontSize = api.config.get('editor.fontSize', 14);
api.config.set('my-plugin.setting', 'value');
if (api.config.has('my-plugin.setting')) {
  const val = api.config.get('my-plugin.setting');
}
api.config.delete('my-plugin.setting');
const disposable = api.config.onDidChange('editor.fontSize', (newValue) => {
  api.log.info(`Font size changed to ${newValue}`);
});
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `get` | `<T>(key: string, defaultValue?: T): T` | Get config value |
| `set` | `<T>(key: string, value: T): void` | Set config value |
| `has` | `(key: string): boolean` | Check if key exists |
| `delete` | `(key: string): void` | Delete config key |
| `onDidChange` | `(key: string, handler): IDisposable` | Subscribe to changes |

### log

**Class:** `LogAPI` (`src/api/PluginAPI.ts:358`)

Structured logging with level prefixes.

```javascript
api.log.info('Plugin initialized', { version: '1.0.0' });
api.log.warn('Deprecated API used');
api.log.error('Failed to process file', err);
api.log.debug('Verbose debug info');
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `info` | `(message: string, ...args: unknown[]): void` | Info level |
| `warn` | `(message: string, ...args: unknown[]): void` | Warning level |
| `error` | `(message: string, ...args: unknown[]): void` | Error level |
| `debug` | `(message: string, ...args: unknown[]): void` | Debug level |

---

## Plugin Lifecycle

### Activation

Activation occurs during `PluginManager.loadPlugin()`:

1. **Manifest validation** — `manifest.json` is read and parsed
2. **Duplicate check** — Plugin name must be unique
3. **Module loading** — The `main` entry point is dynamically imported
4. **Context creation** — A `PluginContext` is constructed with extension path, state storage, and logging
5. **Command registration** — Commands declared in `contributes.commands` are registered automatically
6. **Activation call** — The module's `activate(ctx)` function is called with the context
7. **Event emission** — `plugin:loaded` event fires with plugin name and version

### Deactivation

On `PluginManager.unloadPlugin()`:

1. **Deactivation call** — The module's `deactivate()` function is called if exported
2. **Subscription cleanup** — All items in `ctx.subscriptions` are disposed
3. **Registry removal** — Plugin is removed from the internal map
4. **Event emission** — `plugin:unloaded` event fires

### PluginContext

```typescript
interface PluginContext {
  subscriptions: IDisposable[];
  extensionPath: string;
  workspaceState: Memento;
  globalState: Memento;
  log: (message: string) => void;
}
```

- **subscriptions** — Push disposables here; they are automatically cleaned up on deactivation
- **extensionPath** — Absolute path to the plugin directory
- **workspaceState** — Persistent key-value storage scoped to the current workspace
- **globalState** — Persistent key-value storage shared across workspaces
- **log** — Convenience logger with plugin name prefix

---

## Best Practices

1. **Namespacing** — Prefix all command IDs with your plugin name (e.g., `my-plugin.commandId`) to avoid collisions.
2. **Disposable management** — Always push subscriptions and registrations to `ctx.subscriptions` for automatic cleanup.
3. **Async activation** — The `activate()` function can be async; use it for setup tasks like file watchers or network connections.
4. **Graceful degradation** — Handle cases where dependencies or features are unavailable.
5. **State storage** — Use `workspaceState` for per-project settings and `globalState` for user-level preferences.
6. **Minimal activation** — Use `activationEvents` to defer loading until needed (e.g., `onLanguage:typescript`).
7. **Error handling** — Wrap risky operations in try-catch; errors during activation unload the plugin.
8. **Versioning** — Follow semver for your plugin; declare dependencies with compatible version ranges.

---

## Example: Complete Plugin Walkthrough

### Plugin: Markdown Preview

**Directory structure:**
```
markdown-preview/
  manifest.json
  index.js
  preview.css
```

**manifest.json:**
```json
{
  "name": "markdown-preview",
  "version": "0.1.0",
  "description": "Live Markdown preview panel",
  "author": "Arcanis Labs",
  "main": "index.js",
  "activationEvents": ["onLanguage:markdown"],
  "contributes": {
    "commands": [
      {
        "id": "markdown-preview.open",
        "title": "Open Markdown Preview",
        "category": "Markdown"
      }
    ]
  }
}
```

**index.js:**
```javascript
function activate(ctx) {
  const api = arcanis.getPluginAPI();

  // Register command
  const cmd = api.commands.registerCommand('markdown-preview.open', async () => {
    const doc = api.editor.getActiveDocument();
    if (!doc || doc.languageId !== 'markdown') {
      api.ui.showNotification('No markdown document active', 'warning');
      return;
    }

    const html = renderMarkdown(doc.getText());

    api.ui.showPanel('markdown-preview');
    api.ui.showNotification('Markdown preview opened', 'info');
  });
  ctx.subscriptions.push(cmd);

  // Listen for document changes
  const changeHandler = api.editor.onDidChangeDocument(({ uri, document }) => {
    if (document.languageId === 'markdown') {
      api.log.debug(`Markdown doc changed: ${uri}`);
    }
  });
  ctx.subscriptions.push(changeHandler);

  // Config binding
  const configWatch = api.config.onDidChange('markdown-preview.enabled', (val) => {
    api.log.info(`Preview ${val ? 'enabled' : 'disabled'}`);
  });
  ctx.subscriptions.push(configWatch);
}

function deactivate() {
  // Cleanup is automatic via subscriptions
}

function renderMarkdown(text) {
  // Simple markdown rendering
  return text
    .split('\n')
    .map(line => {
      if (line.startsWith('# ')) return `<h1>${line.slice(2)}</h1>`;
      if (line.startsWith('## ')) return `<h2>${line.slice(3)}</h2>`;
      if (line.startsWith('```')) return `<pre>${line.slice(3)}</pre>`;
      return `<p>${line}</p>`;
    })
    .join('\n');
}

module.exports = { activate, deactivate };
```

---

## Testing Plugins

### Manual Testing

1. Set `plugin.developmentMode` to `true` in configuration
2. Place your plugin directory in the configured plugins path
3. Restart the IDE or call `api.plugins.scanAndLoadPlugins(pluginsDir)` programmatically
4. Check the console for `[Plugin:my-plugin]` log output
5. Test commands via the command palette or keybindings

### Automated Testing

Create a test harness using the IDE's API:

```javascript
const { ArcanisIDE } = require('arcanis-ide');

async function testPlugin() {
  const ide = await ArcanisIDE.create({
    workspacePath: '/tmp/test-workspace',
    pluginsPath: '/path/to/plugins',
  });

  const api = ide.getAPI();

  // Verify plugin loaded
  const plugin = api.plugins.getPlugin('my-plugin');
  assert(plugin, 'Plugin should be loaded');

  // Test command
  await api.commands.executeCommand('my-plugin.hello');

  // Test event subscription
  const events = [];
  const disposable = api.events.on('my-plugin:event', (e) => events.push(e));
  // ... trigger event ...
  assert(events.length > 0);
  disposable.dispose();

  await ide.dispose();
}
```

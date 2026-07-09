# ArcanisIDE Architecture

## Overview

ArcanisIDE is a modular, extensible integrated development environment built with TypeScript. It follows a layered architecture with core services at the foundation, domain-specific subsystems (Editor, AI, Tools, UI) in the middle, and a unified API layer on top that exposes capabilities to both internal components and external plugins.

The IDE is designed around an event-driven communication model where components interact through a central EventBus rather than direct coupling. The CommandRegistry provides a command abstraction, while the PluginManager enables runtime extensibility.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ArcanisIDE                                   │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │   Editor    │  │      AI      │  │    Tools     │  │    UI     │  │
│  │─────────────│  │──────────────│  │──────────────│  │───────────│  │
│  │ Highlight   │  │ Assistant    │  │ Debugger     │  │ Explorer  │  │
│  │ Completion  │  │ Explanation  │  │ Terminal     │  │ Tabs      │  │
│  │ Diagnostics │  │ Bug Detection│  │ Build System │  │ Panels    │  │
│  │ Refactoring │  │ Suggestions  │  │ Packages     │  │ Status    │  │
│  │ LanguageSvc │  │ Doc Gen      │  │ Git          │  │ Themes    │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘  │
│         └────────────────┼─────────────────┼────────────────┘        │
│                          │                 │                          │
│                 ┌────────▼─────────────────▼────────────┐             │
│                 │           Core Services                │             │
│                 │  ┌──────────┐ ┌────────────────────┐  │             │
│                 │  │ EventBus │ │  CommandRegistry   │  │             │
│                 │  ├──────────┤ ├────────────────────┤  │             │
│                 │  │ Config   │ │  PluginManager     │  │             │
│                 │  └──────────┘ └────────────────────┘  │             │
│                 └───────────────────────────────────────┘             │
│                                   │                                   │
│                 ┌─────────────────▼───────────────────┐               │
│                 │            API Layer                 │               │
│                 │  ┌────────────┐  ┌────────────────┐  │               │
│                 │  │ PluginAPI  │  │    IDEAPI      │  │               │
│                 │  └────────────┘  └────────────────┘  │               │
│                 └──────────────────────────────────────┘               │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Core Services

### EventBus
**File:** `src/core/EventBus.ts`

The EventBus is the central publish-subscribe mechanism. All inter-component communication flows through it, preventing direct dependencies between subsystems.

- **`on<T>(event, handler)`** — Subscribe to an event; returns an `IDisposable` for unsubscription.
- **`once<T>(event, handler)`** — Subscribe for a single invocation.
- **`off<T>(event, handler)`** — Unsubscribe explicitly.
- **`emit<T>(event, payload)`** — Publish an event to all listeners.
- **`listenerCount(event)`** — Get the number of registered handlers.
- **`clear()`** — Remove all listeners.

The EventBus wraps each handler call in a try-catch to prevent a single failing handler from breaking the chain. Error messages are logged to console with the event name.

### CommandRegistry
**File:** `src/core/CommandRegistry.ts`

Central registry for all IDE commands. Commands are identified by string IDs and can be registered with an optional context (e.g., plugin name) for organization.

- **`registerCommand(id, handler, context?)`** — Register a command; returns `IDisposable`.
- **`executeCommand(id, ...args)`** — Execute a command by ID; throws if not found.
- **`getCommand(id)`** — Look up a command descriptor.
- **`getCommands(context?)`** — List all commands, optionally filtered by context.
- **`hasCommand(id)`** — Check if a command exists.

Commands registered with the same ID override previous registrations with a warning. Execution errors propagate after logging.

### Configuration
**File:** `src/core/Configuration.ts`

Typed key-value configuration store with change notifications, default values, and a composite `get()` lookup that checks user-set values first, then defaults.

**Default configuration keys include:**

| Key | Default | Description |
|-----|---------|-------------|
| `editor.fontSize` | `14` | Editor font size in pixels |
| `editor.fontFamily` | `'Cascadia Code, Fira Code, Consolas, monospace'` | Editor font family |
| `editor.tabSize` | `4` | Tab character width |
| `editor.insertSpaces` | `true` | Use spaces for indentation |
| `editor.wordWrap` | `'off'` | Word wrap mode |
| `editor.lineNumbers` | `'on'` | Line number display mode |
| `editor.minimap` | `true` | Show minimap |
| `editor.bracketPairColorization` | `true` | Colorize bracket pairs |
| `editor.formatOnSave` | `true` | Format on file save |
| `ai.enabled` | `true` | Enable AI features |
| `ai.model` | `'arcanis-coder'` | AI model identifier |
| `ai.maxTokens` | `2048` | Maximum AI response tokens |
| `ai.temperature` | `0.2` | AI generation temperature |
| `build.defaultTarget` | `'wasm32'` | Default build target |
| `build.defaultMode` | `'debug'` | Default build mode |
| `terminal.shell` | `'powershell'` | Default terminal shell |
| `git.enabled` | `true` | Enable Git integration |
| `plugin.developmentMode` | `false` | Enable plugin dev mode |
| `theme` | `'arcanis-dark'` | Active theme ID |

- **`getEditorConfig()`** — Returns a fully-typed `EditorConfig` object populated from keys.
- **`onDidChange(key, handler)`** — Subscribe to changes for a specific key.

### PluginManager
**File:** `src/core/PluginManager.ts`

Manages loading, activating, deactivating, and unloading plugins at runtime.

- **`loadPlugin(pluginPath)`** — Reads `manifest.json` from the directory, imports the module, registers contributed commands, then calls `activate()`.
- **`unloadPlugin(name)`** — Calls `deactivate()`, disposes all subscriptions, removes from registry.
- **`scanAndLoadPlugins(pluginsDir)`** — Iterates subdirectories and loads each as a plugin.
- **`onPluginLoaded(handler)`** / **`onPluginUnloaded(handler)`** — Lifecycle event subscriptions.

Plugins receive a `PluginContext` with storage (workspace/global state), logging, and a subscriptions array that is automatically cleaned up on deactivation.

---

## Editor Engine

**File:** `src/core/EditorEngine.ts`

The EditorEngine manages open documents, delegates to sub-engines for language-specific features, and coordinates with the rest of the IDE via events.

### Sub-Engines

| Engine | File | Responsibility |
|--------|------|----------------|
| **SyntaxHighlighter** | `src/editor/SyntaxHighlighter.ts` | Tokenizes documents into `TokenizedLine[]` with caching. Delegates to registered `LanguageService` providers. |
| **CompletionProvider** | `src/editor/CompletionProvider.ts` | Provides code completion items. Has built-in default completions (keywords, snippets) and delegates to language-specific providers. Filters and sorts by prefix matching. |
| **DiagnosticEngine** | `src/editor/DiagnosticEngine.ts` | Runs language-specific diagnostic providers and emits `diagnostics:updated` events. Deduplicates results. |
| **RefactoringEngine** | `src/editor/RefactoringEngine.ts` | Provides code actions, rename support, extract function, and organize imports. Aggregates results from language services and registered providers. |

### Language Services

**File:** `src/editor/languages/LanguageService.ts`

Abstract base class for language support. Each language can implement:

- `provideTokens` — Syntax tokenization
- `provideCompletions` — Code completion
- `provideDiagnostics` — Error/warning detection
- `provideCodeActions` — Quick fixes and refactoring
- `provideHover` — Hover information
- `provideSignatureHelp` — Signature help for functions
- `provideDocumentFormatting` — Document formatting
- `provideDefinition` — Go-to-definition
- `provideReferences` — Find all references
- `provideRename` — Rename symbol

Current built-in language services: **Arcanis** (`src/editor/languages/ArcanisLang.ts`), with tokenizer support (`src/editor/languages/Tokenizer.ts`).

### Document Model

Documents are represented by the `TextDocument` interface with URI, filename, language ID, version number, and methods for text access (`getText()`, `lineAt()`). The editor tracks a version counter and emits change events on each update.

---

## AI Integration

**File:** `src/ai/AIAssistant.ts`

The AI subsystem provides intelligent code assistance through a pluggable `ModelAdapter` interface. The default implementation is `LocalModelAdapter`.

### Capabilities

| Method | Description |
|--------|-------------|
| `generateCompletion(context)` | Generates inline code completions based on context. Returns `AICompletionResult` with `requestId`. |
| `getSuggestions(document)` | Analyzes the document and returns improvement suggestions covering performance, style, security. |
| `explainCode(document, range)` | Explains the selected code block in natural language. |
| `detectBugs(document)` | Scans the document for common bug patterns (loose equality, off-by-one, null references). |
| `generateDocumentation(document, range)` | Generates JSDoc-style documentation comments for functions, classes, and code blocks. |

### ModelAdapter Interface

The `ModelAdapter` can be replaced via `setModelAdapter()` to use external AI APIs (e.g., OpenAI, Anthropic, or a dedicated Arcanis model server).

### Events

All AI operations emit events through the EventBus: `ai:completion`, `ai:suggestion`, `ai:explanation`, `ai:bug`, `ai:doc`.

---

## Developer Tools

### Debugger
**File:** `src/tools/Debugger.ts`

Manages breakpoints, threads, stack frames, and variable inspection.

- **Breakpoints** — Set by URI and line number, with optional condition, hit condition, and log message. Toggle support.
- **Session control** — `start()`, `stop()`, `pause()`, `continue()`, `stepOver()`, `stepInto()`, `stepOut()`.
- **Inspection** — `getThreads()`, `getStackFrames(threadId)`, `getVariables(threadId, frameId)`, `evaluate(expression, threadId, frameId)`.
- **States** — `idle` | `running` | `paused` | `stepping`.

Events: `debugger:started`, `debugger:stopped`, `debugger:paused`, `debugger:continued`.

### Terminal
**File:** `src/tools/Terminal.ts`

Manages multiple terminal instances with a buffer, resize support, and data event handling.

- Methods: `open()`, `close()`, `write()`, `onData()`, `resize()`, `clear()`, `getTerminals()`.
- Events: `terminal:opened`, `terminal:closed`, `terminal:data`.

### BuildSystem
**File:** `src/tools/BuildSystem.ts`

Provides build, clean, rebuild, and test execution against a `BuildConfig`.

- Default target: `wasm32`, default mode: `debug`.
- Methods: `build()`, `clean()`, `rebuild()`, `runTests()`, `getCurrentConfig()`, `updateConfig()`.
- Events: `build:started`, `build:completed`, `test:started`, `test:completed`.

### PackageManager
**File:** `src/tools/PackageManager.ts`

Package management for the Arcanis ecosystem.

- Methods: `install()`, `uninstall()`, `update()`, `search()`, `list()`, `publish()`, `info()`.
- Events: `package:installed`, `package:uninstalled`, `package:updated`.

### GitIntegration
**File:** `src/tools/GitIntegration.ts`

Git operations with event-driven lifecycle.

- Methods: `init()`, `clone()`, `status()`, `add()`, `commit()`, `push()`, `pull()`, `branch()`, `checkout()`, `log()`, `diff()`, `stash()`, `stashPop()`, `getRemotes()`.
- Events: `git:operationStart`, `git:operationEnd`.

---

## UI Layer

**File:** `src/ui/UIEngine.ts`

The UI engine manages component registration, theming, panel visibility, and user-facing dialogs.

### Layout Structure

The rendered layout consists of:
- **Menu bar** (top) — Application menus
- **Sidebar** (left, 260px) — Houses `project-explorer` component
- **Editor area** (center) — Houses `editor-view` component
- **Panel** (bottom) — Houses `panel` component (output, problems, debug, terminal)
- **Status bar** (bottom) — Houses `status-bar` component

### Component System

Components implement the `UIComponent` interface with `render()`, `onMount()`, `onUnmount()`, and `update()`.

### User Dialogs

| Method | Description |
|--------|-------------|
| `showNotification(message, type)` | Toast notification (`info`, `warning`, `error`, `success`) |
| `showInputBox(options)` | Text input prompt with optional validation |
| `showQuickPick(items, options)` | Quick-pick selection list |
| `showMessageBox(options)` | Modal dialog with multiple buttons |

### Theme System

**File:** `src/ui/themes/ThemeManager.ts`

Three built-in themes:

| Theme ID | Type | Colors |
|----------|------|--------|
| `arcanis-dark` | Dark | Catppuccin Mocha-inspired |
| `arcanis-light` | Light | Catppuccin Latte-inspired |
| `arcanis-hc` | High Contrast | Black/white with accent colors |

Themes define colors for editor surface, sidebar, status bar, panels, tabs, buttons, inputs, lists, scrollbars, notifications, and accents. Custom themes can be registered via `registerTheme()`.

Events: `ui:themeChanged`.

---

## API Layer

### IDEAPI
**File:** `src/api/IDEAPI.ts`

The top-level API exposed to consumers of the IDE. Provides access to all subsystems:

- **`events`** — EventAPI (publish/subscribe)
- **`commands`** — CommandRegistry (direct reference)
- **`workspace`** — WorkspaceAPI (folder management)
- **`editor`** — EditorAPI (document operations)
- **`ai`** — AIAPI (AI assistance)
- **`debug`** — DebugAPI (debugger control)
- **`terminal`** — TerminalAPI (terminal instances)
- **`build`** — BuildAPI (build system)
- **`packages`** — PackageAPI (package management)
- **`git`** — GitAPI (Git operations)
- **`ui`** — UIAPI (user interface dialogs)
- **`config`** — ConfigAPI (configuration)
- **`log`** — LogAPI (logging)
- **`plugins`** — PluginManagementAPI (plugin lifecycle)
- **`getVersion()`** — Returns `'0.1.0'`
- **`dispose()`** — Clears EventBus

### PluginAPI
**File:** `src/api/PluginAPI.ts`

Same structure as IDEAPI without the plugin management sub-API. This is the API exposed to plugin `activate()` functions. It also omits the `plugins` property since plugins should not manage other plugins.

---

## Plugin System

### Plugin Lifecycle

1. **Discovery** — `scanAndLoadPlugins()` iterates the plugins directory
2. **Manifest Loading** — Reads and validates `manifest.json`
3. **Module Import** — Dynamically imports the `main` entry point
4. **Command Registration** — Any commands declared in `contributes.commands` are registered automatically and forward to an event-based handler
5. **Activation** — Calls the module's `activate(PluginContext)` function
6. **Deactivation** — On unload, calls `deactivate()` and disposes all subscriptions
7. **Cleanup** — Plugin is removed from the registry; event emitted

### Plugin Context

Plugins receive a `PluginContext` object containing:
- `subscriptions` — Array of `IDisposable` cleaned up on deactivation
- `extensionPath` — Absolute path to the plugin directory
- `workspaceState` — Key-value store scoped to the current workspace
- `globalState` — Key-value store persistent across workspaces
- `log(message)` — Prefixed logging helper

### Manifest Contributions

Plugins declare contributions in `manifest.json`:
- `commands` — Additional command definitions
- `languages` — Language support (file extensions, aliases)
- `themes` — Color themes
- `menuItems` — Context menu and menu bar items
- `keybindings` — Keyboard shortcuts

---

## Data Flow

```
User Action (keystroke, click)
       │
       ▼
  UI Component
       │
       ▼
  CommandRegistry.executeCommand(id, ...args)
       │
       ▼
  Handler invokes Subsystem API
       │
       ├──► EditorEngine (document edit, completion request)
       ├──► AIAssistant (explain, suggest, detect bugs)
       ├──► Debugger (step, continue, evaluate)
       ├──► Terminal (write, resize)
       ├──► BuildSystem (build, test)
       ├──► PackageManager (install, publish)
       ├──► GitIntegration (commit, push, pull)
       └──► Plugin (via registered command or event subscription)
       │
       ▼
  EventBus.emit(event, payload)
       │
       ▼
  Listeners (UI updates, status bar, panel refresh, notifications)
```

---

## Extension Points

1. **Language Services** — Implement the `LanguageService` abstract class and register via `editorEngine.registerLanguageService()`.
2. **Model Adapters** — Implement `ModelAdapter` and inject via `aiAssistant.setModelAdapter()`.
3. **Themes** — Create a `Theme` object and register via `themeManager.registerTheme()`.
4. **Plugins** — Create a plugin directory with `manifest.json` and an entry module exporting `activate()`.
5. **Commands** — Register new commands via `commandRegistry.registerCommand()`.
6. **Code Action Providers** — Register via `refactoringEngine.registerCodeActionProvider()`.
7. **Completion Providers** — Register per language via `completionProvider.registerProvider()`.
8. **Diagnostic Providers** — Register per language via `diagnosticEngine.registerProvider()`.
9. **UI Components** — Register via `uiEngine.registerComponent()`.
10. **Event Subscriptions** — Subscribe to any EventBus event via `eventBus.on()`.

All extension points return `IDisposable` for clean teardown.

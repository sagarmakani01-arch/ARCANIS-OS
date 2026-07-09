# ArcanisIDE User Guide

## Introduction

ArcanisIDE is a modern, extensible integrated development environment designed for the Arcanis programming language and ecosystem. It provides intelligent code editing, AI-powered assistance, integrated developer tools, and a full-featured plugin system.

Built with TypeScript and an event-driven architecture, ArcanisIDE offers:
- **Syntax highlighting** for Arcanis, TypeScript, JavaScript, Python, Rust, and more
- **Code completion** with intelligent filtering and sorting
- **AI Assistant** for code generation, explanation, bug detection, and documentation
- **Integrated debugger** with breakpoints, stepping, and variable inspection
- **Built-in terminal**, build system, package manager, and Git integration
- **Full plugin API** for extensibility

---

## Installation and Setup

### Prerequisites
- Node.js 18+ and npm
- A terminal emulator (PowerShell, bash, zsh)

### Install

```bash
npm install -g arcanis-ide
```

Or run from source:

```bash
git clone https://github.com/arcanis-labs/arcanis-ide
cd arcanis-ide
npm install
npm run build
npm start
```

### Configuration File

ArcanisIDE reads configuration from `~/.config/arcanis/settings.json`. You can also configure settings through the IDE's configuration UI.

---

## Getting Started

### Opening a Project

```bash
arcanis /path/to/your/project
```

Or from within the IDE, use the command palette (`Ctrl+Shift+P`) and run `arcanis.openFile` or use the project explorer to navigate to your project.

### Creating and Opening Files

- **New file:** `Ctrl+N` or right-click in the project explorer and select "New File"
- **Open file:** `Ctrl+O` or double-click in the project explorer
- **Open recent:** `Ctrl+R`
- **Switch between open files:** `Ctrl+Tab`

### Editor Basics

| Action | Shortcut |
|--------|----------|
| Move cursor | Arrow keys |
| Select text | `Shift` + Arrow keys |
| Select word | `Ctrl+D` |
| Select line | `Ctrl+L` |
| Scroll line by line | `Ctrl+Up` / `Ctrl+Down` |
| Scroll page by page | `PageUp` / `PageDown` |
| Go to line | `Ctrl+G` |
| Go to definition | `F12` |
| Go back | `Alt+Left` |
| Go forward | `Alt+Right` |

### Editor Layout

The default layout consists of:
- **Left sidebar** — Project Explorer showing the file tree
- **Center area** — Editor tabs for open files
- **Bottom panel** — Output, Problems, Debug Console, Terminal (tabs)
- **Status bar** — Bottom bar showing line/column, language, encoding, Git branch

---

## Editor Features

### Syntax Highlighting

Syntax highlighting is applied automatically based on the file extension and language ID. Supported languages include:

| Language | Extensions |
|----------|------------|
| Arcanis | `.arc`, `.arcanis` |
| TypeScript | `.ts`, `.tsx` |
| JavaScript | `.js`, `.jsx`, `.mjs` |
| JSON | `.json` |
| Markdown | `.md` |
| HTML | `.html`, `.htm` |
| CSS | `.css` |
| Python | `.py` |
| Rust | `.rs` |
| Plaintext | (fallback) |

The highlighter breaks documents into tokens with semantic types (keyword, string, comment, function, etc.) and colorizes them according to the active theme.

### Code Completion

Trigger completions by typing or manually invoke with `Ctrl+Space`.

- **Filtering** — Results are filtered based on the word under the cursor
- **Sorting** — Exact matches rank highest, then prefix matches, then keywords/snippets
- **Snippets** — Built-in snippets include `ifelse`, `forloop`, and language-specific templates
- **Documentation** — Detail and documentation strings appear in the completion widget

Completions are provided by language-specific providers. If no provider is registered for the current language, a set of default keyword completions is used.

### Error Detection

Diagnostics (errors, warnings, informational hints) are shown as:
- **Wavy underlines** in the editor (red for errors, yellow for warnings, blue for info)
- **Problem markers** in the scrollbar
- **Problems panel** at the bottom (list view with file, line, message)

To view the Problems panel: click the "Problems" tab in the bottom panel or run `arcanis.togglePanel`.

**Quick Fixes:** Hover over a diagnostic and click the lightbulb icon, or press `Ctrl+.` to see available quick fixes. These include automatic corrections for common issues.

### Refactoring

Available refactoring operations:

| Operation | Shortcut | Description |
|-----------|----------|-------------|
| Rename Symbol | `F2` | Rename a variable, function, or class across the file |
| Extract Function | `Ctrl+Shift+R` | Extract selected code into a new function |
| Organize Imports | `Shift+Alt+O` | Sort and group import statements |
| Code Actions | `Ctrl+.` | Context-dependent quick fixes and refactors |

**Rename Symbol:** Place the cursor on a symbol, press `F2`, type the new name, and press Enter. All references are updated.

**Extract Function:** Select the code block, press `Ctrl+Shift+R`, enter a function name, and the extracted function is inserted at the top of the file.

### Multi-Cursor Editing

| Action | Shortcut |
|--------|----------|
| Add cursor | `Alt+Click` |
| Add cursor above/below | `Ctrl+Alt+Up` / `Ctrl+Alt+Down` |
| Select all occurrences | `Ctrl+Shift+L` |
| Add next occurrence | `Ctrl+D` |

### Find and Replace

| Action | Shortcut |
|--------|----------|
| Find | `Ctrl+F` |
| Find in files | `Ctrl+Shift+F` |
| Replace | `Ctrl+H` |
| Replace in files | `Ctrl+Shift+H` |
| Find next | `F3` |
| Find previous | `Shift+F3` |
| Select all matches | `Alt+Enter` |

Find options include: case-sensitive, whole word, regex, and search scope (current file or all files in workspace).

### Minimap

The minimap shows a scaled-down view of the entire file on the right side of the editor. Toggle it via `View > Toggle Minimap` or the `editor.minimap` configuration setting.

### Breadcrumbs

Breadcrumbs appear above the editor showing the file path and the current symbol location. Click any breadcrumb segment to navigate. Toggle via `View > Toggle Breadcrumbs`.

---

## Project Explorer

The project explorer is in the left sidebar and shows the file tree of the open workspace.

### Navigation

- **Expand/collapse folders** — Click the arrow or double-click
- **Open file** — Single click or Enter
- **Focus explorer** — `Ctrl+Shift+E`

### File Operations

| Action | How |
|--------|-----|
| New file | Right-click folder > "New File" |
| New folder | Right-click > "New Folder" |
| Rename | Right-click > "Rename" or `F2` |
| Delete | Right-click > "Delete" or `Delete` key |
| Copy path | Right-click > "Copy Path" |
| Reveal in Explorer | Right-click > "Reveal in File Explorer" |

### Search in Files

Press `Ctrl+Shift+F` to open the search panel. Enter a query to search across all files in the workspace. Results are grouped by file with line numbers and matching line previews.

Options:
- Case-sensitive toggle
- Whole word toggle
- Regex mode toggle
- Include/exclude patterns (glob syntax)

---

## AI Assistant

The AI Assistant is available through commands, context menus, and keyboard shortcuts. It uses a pluggable `ModelAdapter` — by default a local model is used, but you can configure it to use external AI APIs.

### Features

#### Code Completions

While typing, the AI generates inline completions. Press `Tab` to accept a completion, or `Esc` to dismiss. Completions include confidence scores and optional explanations.

Trigger manually with `Alt+\` (backslash).

#### Code Explanation

Select a block of code and run `arcanis.ai.explain` (or right-click > "AI > Explain Code"). The assistant analyzes the selected code and provides a natural-language explanation describing its structure, complexity, and purpose.

Default shortcut: `Ctrl+Shift+E` (when focus is in editor).

#### Bug Detection

Run `arcanis.ai.suggest` (or right-click > "AI > Detect Bugs") to scan the active document for common bug patterns:

- **Loose equality** (`==` instead of `===`)
- **Off-by-one errors** (`<=` in loop conditions)
- **Null references** (accessing properties on potentially null values)
- **Debug log statements** left in production code

Each finding includes severity, location, and an explanation of the issue.

#### Improvement Suggestions

The AI suggests code improvements covering:
- **Performance** — Large files that could be split into modules
- **Style** — `var`/`let` that should be `const`
- **Security** — Potential vulnerabilities
- **Documentation** — Missing or incomplete comments

#### Documentation Generation

Select a function, class, or code block and run "AI > Generate Documentation". The assistant generates JSDoc-style comments with `@param` and `@returns` annotations.

### Configuring AI Settings

Settings are available under the `ai.*` configuration namespace:

| Setting | Default | Description |
|---------|---------|-------------|
| `ai.enabled` | `true` | Enable/disable AI features |
| `ai.model` | `'arcanis-coder'` | AI model identifier |
| `ai.maxTokens` | `2048` | Maximum tokens per request |
| `ai.temperature` | `0.2` | Generation temperature (0.0–1.0) |
| `ai.suggestionsEnabled` | `true` | Enable improvement suggestions |
| `ai.bugDetectionEnabled` | `true` | Enable bug detection |
| `ai.docGenerationEnabled` | `true` | Enable documentation generation |

---

## Developer Tools

### Debugger

**File:** `src/tools/Debugger.ts`

#### Setting Breakpoints

Click in the gutter (left of the line numbers) or press `F9` to toggle a breakpoint on the current line.

Breakpoints support:
- **Condition** — Only break when the condition evaluates to true
- **Hit count** — Only break after N hits
- **Log message** — Log a message instead of breaking (tracepoints)

View and manage breakpoints in the Breakpoints panel.

#### Debug Session Control

| Action | Shortcut | Description |
|--------|----------|-------------|
| Start Debugging | `F5` | Start or continue debugging |
| Pause | `F6` | Pause execution |
| Stop | `Shift+F5` | Stop debugging |
| Step Over | `F10` | Execute current line, step over function calls |
| Step Into | `F11` | Step into a function call |
| Step Out | `Shift+F11` | Step out of the current function |
| Restart | `Ctrl+Shift+F5` | Restart the debug session |

#### Inspecting State

When paused, the Debug panel shows:
- **Variables** — Local, closure, and global variables for the selected stack frame
- **Watch** — Custom expressions to evaluate
- **Call Stack** — Stack frames with source location
- **Threads** — All running threads and their state

Hover over a variable in the editor to see its value in a tooltip.

### Terminal

**File:** `src/tools/Terminal.ts`

#### Opening Terminals

| Action | Shortcut |
|--------|----------|
| Open terminal | `Ctrl+\`` |
| Open new terminal | `Ctrl+Shift+\`` |
| Focus terminal | `Ctrl+\`` |
| Close terminal | Type `exit` or click close button |

#### Managing Terminals

- Multiple terminal instances are supported (each with its own ID and title)
- Switch between terminals using tabs in the terminal panel
- Configure the default shell via `terminal.shell` setting
- Terminal buffer is scrollable; use the scrollbar or `Shift+PageUp`/`Shift+PageDown`

#### Terminal Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `terminal.shell` | `'powershell'` | Default shell executable |
| `terminal.fontSize` | `13` | Terminal font size in pixels |

### Build System

**File:** `src/tools/BuildSystem.ts`

#### Building

Run the build system with `Ctrl+Shift+B` or the command `arcanis.build`. Results appear in the Output panel showing success/failure, duration, errors, and warnings.

#### Build Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `build.defaultTarget` | `'wasm32'` | Default build target |
| `build.defaultMode` | `'debug'` | Build mode (`debug` or `release`) |

Available commands:
- **Build** — Compile the project
- **Clean** — Remove build artifacts
- **Rebuild** — Clean then build
- **Run Tests** — Execute the test suite

### Package Manager

**File:** `src/tools/PackageManager.ts`

The package manager handles Arcanis packages. Access it through commands or the API.

| Command | Description |
|---------|-------------|
| `arcanis.package.install` | Install a package from the registry |
| `arcanis.package.uninstall` | Remove an installed package |
| `arcanis.package.update` | Update a package to the latest version |
| `arcanis.package.search` | Search the package registry |
| `arcanis.package.list` | List installed packages |
| `arcanis.package.publish` | Publish a package to the registry |

### Git Integration

**File:** `src/tools/GitIntegration.ts`

#### Common Operations

| Action | Shortcut | Command |
|--------|----------|---------|
| View status | — | `arcanis.git.status` |
| Stage files | — | `arcanis.git.add` |
| Commit | `Ctrl+Enter` (in source control) | `arcanis.git.commit` |
| Push | — | `arcanis.git.push` |
| Pull | — | `arcanis.git.pull` |
| Create branch | — | `arcanis.git.branch` |
| Checkout | — | `arcanis.git.checkout` |
| View log | — | `arcanis.git.log` |
| View diff | — | `arcanis.git.diff` |

#### Git Status Panel

The source control panel shows:
- **Branch** — Current branch name
- **Changes** — List of modified, added, deleted, untracked files
- **Staged changes** — Files ready for commit
- **Ahead/Behind** — Commit count relative to remote

Each change shows a diff preview when selected.

---

## UI Customization

### Themes

**File:** `src/ui/themes/ThemeManager.ts`

ArcanisIDE comes with three built-in themes:

| Theme | Type | Description |
|-------|------|-------------|
| `arcanis-dark` | Dark | Catppuccin Mocha-inspired dark theme (default) |
| `arcanis-light` | Light | Catppuccin Latte-inspired light theme |
| `arcanis-hc` | High Contrast | High-contrast black/white theme for accessibility |

**Switch themes:** `Settings > Theme` or via the command palette (`Ctrl+Shift+P` > "Theme: Select Theme").

#### Custom Themes

Create a custom theme plugin with the following structure:

```json
{
  "name": "my-theme",
  "version": "1.0.0",
  "description": "My custom theme",
  "author": "You",
  "main": "index.js",
  "contributes": {
    "themes": [{
      "id": "my-custom-theme",
      "label": "My Custom Theme",
      "type": "dark",
      "path": "./my-theme.json"
    }]
  }
}
```

Theme JSON format:

```json
{
  "id": "my-custom-theme",
  "name": "My Custom Theme",
  "type": "dark",
  "colors": {
    "editor.background": "#1e1e2e",
    "editor.foreground": "#cdd6f4",
    "sidebar.background": "#181825",
    "statusBar.background": "#11111b",
    "panel.background": "#181825",
    "accent.primary": "#cba6f7"
  }
}
```

Available color keys: editor.*, sidebar.*, statusBar.*, panel.*, tab.*, button.*, input.*, list.*, scrollbar.*, notification.*, accent.*, text.*.

### Panels

The bottom panel contains tabbed views:

| Panel | Description | Toggle |
|-------|-------------|--------|
| **Output** | Build output, logs, and process output | `Ctrl+Shift+U` |
| **Problems** | Diagnostics, errors, warnings, hints | `Ctrl+Shift+M` |
| **Debug Console** | Debugger output and REPL | `Ctrl+Shift+Y` |
| **Terminal** | Integrated terminal emulator | `Ctrl+\`` |

Panels can be shown, hidden, or toggled individually via commands or the API.

### Status Bar

The status bar at the bottom displays:
- **Left:** Git branch, errors/warnings count, language mode, encoding
- **Right:** Line/column position, indentation settings, file type, encoding

Click on status bar items to change settings (e.g., click the language to change syntax highlighting mode).

### Keybindings

View and customize keybindings via `Settings > Keyboard Shortcuts` or by editing the keybindings JSON file.

Default keybindings are stored in `~/.config/arcanis/keybindings.json`:

```json
[
  {
    "key": "ctrl+shift+p",
    "command": "arcanis.commandPalette"
  },
  {
    "key": "ctrl+,",
    "command": "arcanis.openSettings"
  }
]
```

### Configuration Settings Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `editor.fontSize` | `14` | Editor font size |
| `editor.fontFamily` | `'Cascadia Code, Fira Code, Consolas, monospace'` | Editor font family |
| `editor.tabSize` | `4` | Tab width |
| `editor.insertSpaces` | `true` | Use spaces for indentation |
| `editor.wordWrap` | `'off'` | Word wrapping mode |
| `editor.wordWrapColumn` | `120` | Column for word wrap |
| `editor.lineNumbers` | `'on'` | Line number display |
| `editor.minimap` | `true` | Show minimap |
| `editor.bracketPairColorization` | `true` | Colorize bracket pairs |
| `editor.autoClosingBrackets` | `true` | Auto-close brackets |
| `editor.autoClosingQuotes` | `true` | Auto-close quotes |
| `editor.formatOnPaste` | `false` | Format pasted code |
| `editor.formatOnSave` | `true` | Format on save |
| `editor.suggestOnTriggerCharacters` | `true` | Trigger completion on `.`, `(`, etc. |
| `ai.enabled` | `true` | Enable AI assistance |
| `ai.model` | `'arcanis-coder'` | AI model identifier |
| `ai.maxTokens` | `2048` | Max tokens per AI request |
| `ai.temperature` | `0.2` | AI generation temperature |
| `ai.suggestionsEnabled` | `true` | Enable code suggestions |
| `ai.bugDetectionEnabled` | `true` | Enable bug detection |
| `ai.docGenerationEnabled` | `true` | Enable doc generation |
| `build.defaultTarget` | `'wasm32'` | Default build target |
| `build.defaultMode` | `'debug'` | Build mode |
| `terminal.shell` | `'powershell'` | Terminal shell |
| `terminal.fontSize` | `13` | Terminal font size |
| `git.enabled` | `true` | Enable Git integration |
| `git.autoFetch` | `true` | Auto-fetch from remote |
| `plugin.developmentMode` | `false` | Plugin development mode |
| `theme` | `'arcanis-dark'` | Active theme |

---

## Plugin Management

### Installing Plugins

1. Open the command palette (`Ctrl+Shift+P`)
2. Run "Extensions: Install Extension"
3. Search for the plugin and click Install

Or install from the command line:

```bash
arcanis --install-plugin plugin-name
```

### Managing Plugins

- **View installed:** `Extensions > Show Installed Extensions`
- **Disable/Enable:** Click the gear icon next to a plugin
- **Uninstall:** Click the gear icon > "Uninstall"
- **Update:** Click the update button when available

### Creating Plugins

See the [Plugin Development Guide](PLUGIN_DEV.md) for a complete walkthrough.

---

## Keyboard Shortcuts Reference

### General

| Shortcut | Command |
|----------|---------|
| `Ctrl+Shift+P` | Command Palette |
| `Ctrl+,` | Settings |
| `Ctrl+K Ctrl+S` | Keyboard Shortcuts |
| `Ctrl+Shift+E` | Show Explorer |
| `Ctrl+Shift+F` | Search in Files |
| `Ctrl+Shift+G` | Source Control |
| `Ctrl+Shift+D` | Debug |
| `Ctrl+Shift+X` | Extensions |

### Editor

| Shortcut | Command |
|----------|---------|
| `Ctrl+N` | New File |
| `Ctrl+O` | Open File |
| `Ctrl+S` | Save |
| `Ctrl+Shift+S` | Save As |
| `Ctrl+W` | Close Tab |
| `Ctrl+Tab` | Next Tab |
| `Ctrl+Shift+Tab` | Previous Tab |
| `Ctrl+\`` | Toggle Terminal |
| `Ctrl+B` | Toggle Sidebar |
| `Ctrl+J` | Toggle Panel |

### Navigation

| Shortcut | Command |
|----------|---------|
| `Ctrl+G` | Go to Line |
| `Ctrl+P` | Go to File |
| `F12` | Go to Definition |
| `Alt+F12` | Peek Definition |
| `Shift+F12` | Find References |
| `Ctrl+Shift+O` | Go to Symbol |
| `Alt+Left` | Go Back |
| `Alt+Right` | Go Forward |

### Editing

| Shortcut | Command |
|----------|---------|
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+X` | Cut Line |
| `Ctrl+C` | Copy Line |
| `Ctrl+V` | Paste |
| `Ctrl+Shift+K` | Delete Line |
| `Ctrl+/` | Toggle Comment |
| `Ctrl+]` | Indent |
| `Ctrl+[` | Outdent |
| `Alt+Up/Down` | Move Line Up/Down |
| `Shift+Alt+Up/Down` | Copy Line Up/Down |

### Selection

| Shortcut | Command |
|----------|---------|
| `Ctrl+A` | Select All |
| `Ctrl+L` | Select Current Line |
| `Ctrl+D` | Select Word / Next Occurrence |
| `Ctrl+Shift+L` | Select All Occurrences |
| `Alt+Click` | Add Cursor |
| `Ctrl+Alt+Up/Down` | Add Cursor Above/Below |
| `Shift+Alt+I` | Insert Cursor at End of Each Line |

### Find and Replace

| Shortcut | Command |
|----------|---------|
| `Ctrl+F` | Find |
| `Ctrl+H` | Replace |
| `F3` | Find Next |
| `Shift+F3` | Find Previous |
| `Alt+Enter` | Select All Matches |

### Debug

| Shortcut | Command |
|----------|---------|
| `F5` | Start / Continue |
| `F6` | Pause |
| `Shift+F5` | Stop |
| `F9` | Toggle Breakpoint |
| `F10` | Step Over |
| `F11` | Step Into |
| `Shift+F11` | Step Out |
| `Ctrl+Shift+F5` | Restart |

### AI

| Shortcut | Command |
|----------|---------|
| `Alt+\`` | AI Completions |
| `Ctrl+Shift+E` | AI Explain Code |
| `Ctrl+Shift+S` | AI Suggestions |
| `Ctrl+Shift+B` | AI Detect Bugs |

### Build

| Shortcut | Command |
|----------|---------|
| `Ctrl+Shift+B` | Build |
| `Ctrl+Shift+T` | Run Tests |
| `Ctrl+F5` | Run Project |

---

## Troubleshooting

### Common Issues

**Editor not showing syntax highlighting:**
- Verify the file extension is recognized (see supported languages)
- Check that a language service is registered for your language
- Try switching the language mode via the status bar

**AI features not working:**
- Ensure `ai.enabled` is set to `true` in settings
- Check the console for model adapter errors
- The local model adapter provides basic completions; for full features, configure an external API adapter

**Plugins not loading:**
- Verify `manifest.json` exists and is valid JSON
- Check that the `main` entry point path exists
- Look for `[PluginManager]` errors in the console
- Ensure `plugin.developmentMode` is enabled if developing

**Build fails:**
- Check the Output panel for error details
- Verify `build.defaultTarget` and build configuration
- Ensure the source directory exists and contains valid source files

**Git operations fail:**
- Ensure Git is installed and available on the system PATH
- Verify the workspace is a Git repository
- Check `git.enabled` setting

### Logs

Logs are written to the console with structured prefixes:
- `[INFO]` — General information
- `[WARN]` — Warnings that don't prevent operation
- `[ERROR]` — Errors that may require action
- `[DEBUG]` — Detailed debug information (verbose)

Plugin logs appear as `[Plugin:<name>] <message>`.

### Getting Help

- **Documentation:** See the `docs/` directory in your ArcanisIDE installation
- **Issues:** Report bugs at https://github.com/arcanis-labs/arcanis-ide/issues
- **Plugin Development:** See [PLUGIN_DEV.md](PLUGIN_DEV.md)
- **API Reference:** See [API_REFERENCE.md](API_REFERENCE.md)

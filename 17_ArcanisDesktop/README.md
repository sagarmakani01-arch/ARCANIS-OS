# ArcanisDesktop

**AI-native desktop experience.**

ArcanisDesktop is a web-based desktop environment with AI-first features, built on the Arcanis platform (ArcanisUI, ArcanisShell, ArcanisBrain).

## Quick Start

Open `index.html` in any modern browser.

## Architecture

```
arcanisd-desktop/
├── index.html                    # Entry point
├── css/
│   ├── variables.css             # Theme system (dark/light/midnight)
│   ├── desktop.css               # Core layout & desktop
│   ├── taskbar.css               # Taskbar & start menu
│   ├── windows.css               # Window manager UI
│   ├── notifications.css         # Notifications & toasts
│   ├── apps.css                  # All application styles
│   └── ai-center.css             # AI Command Center
├── js/
│   ├── core/
│   │   ├── window-manager.js     # Window lifecycle, drag, resize
│   │   ├── taskbar.js            # Taskbar, app launcher, clock
│   │   ├── notifications.js      # Notification system
│   │   ├── desktop.js            # Desktop icons, context menu
│   │   └── workspace.js          # Virtual desktops
│   ├── apps/
│   │   ├── terminal.js           # Terminal with virtual filesystem
│   │   ├── file-manager.js       # File browser
│   │   ├── settings.js           # System settings panel
│   │   ├── text-editor.js        # Text/code editor
│   │   └── browser.js            # Web browser
│   ├── ai/
│   │   ├── ai-center.js          # AI Command Center (ArcanisBrain)
│   │   └── workflows.js          # Automated workflow engine
│   ├── integration.js            # ArcanisUI/Shell/Brain integration
│   └── main.js                   # App bootstrap & registry
└── assets/
    ├── icons/
    └── wallpapers/
```

## Features

### Desktop Environment
- **Window Manager**: Drag, resize, minimize, maximize, close windows. Focus management, z-index stacking.
- **Taskbar**: Running apps, clock, system tray, app launcher with search.
- **Start Menu**: Pinned apps, all apps list, search filtering.
- **Context Menu**: Right-click desktop for quick actions.
- **Desktop Icons**: Double-click to launch apps.

### AI-First Features
- **AI Command Center** (ArcanisBrain): Natural language interface for controlling the desktop.
- **Smart Workspace Management**: Virtual desktops with keyboard shortcuts (Ctrl+1/2/3).
- **Automated Workflows**: Create multi-step automations (launch apps, notifications, theme changes).

### Built-in Applications
| App | Description |
|-----|-------------|
| Terminal | Full shell with commands, virtual filesystem, command history, autocomplete |
| File Manager | Virtual file browser with sidebar, navigation, file/folder icons |
| Text Editor | Syntax-aware editor with find, save, keyboard shortcuts |
| Browser | Web browser with URL bar, navigation, sandboxed iframes |
| Settings | Theme, desktop, notifications, AI, workspace configuration |

### Integration Layer
Three bridges expose the desktop API to external systems:

- **ArcanisUI**: Theme, accent color, settings, notifications
- **ArcanisShell**: App launch/close, window management, workspaces
- **ArcanisBrain**: AI command processing, workflows, conversation history

```javascript
// Access via window.arcanisDesktop.integration
arcanisDesktop.integration.ArcanisUI.setTheme('midnight');
arcanisDesktop.integration.ArcanisShell.openApp('terminal');
arcanisDesktop.integration.ArcanisBrain.processCommand('open browser');
```

## AI Commands

| Command | Action |
|---------|--------|
| `open terminal` | Launch Terminal |
| `open files` | Launch File Manager |
| `open browser` | Launch Browser |
| `open editor` | Launch Text Editor |
| `open settings` | Launch Settings |
| `change theme to dark/light/midnight` | Switch theme |
| `minimize all` | Minimize all windows |
| `close all` | Close all windows |
| `maximize` | Toggle maximize active window |
| `switch to workspace 1-3` | Switch virtual desktop |
| `create workflow` | Open workflow creator |
| `list workflows` | Show saved workflows |
| `system info` | Display system information |
| `show notifications` | Toggle notifications panel |
| `help` | Show all commands |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+1/2/3 | Switch workspace |
| Ctrl+Tab | Cycle workspaces |
| Ctrl+S | Save (in Text Editor) |
| Ctrl+L | Clear terminal |
| Escape | Close AI Center / Start Menu |
| Tab | Autocomplete (in Terminal) |

## Themes

Three built-in themes: **Dark**, **Light**, **Midnight**. Persisted to localStorage.

## Workflows

Create multi-step automations via the AI Command Center or Settings. Steps include:
- Launch app
- Send notification
- Set theme
- Close/minimize all windows
- Wait (delay)
- Run AI command

Workflows are persisted to localStorage.

## Requirements

- Modern browser (Chrome, Firefox, Edge, Safari)
- No build tools or dependencies required

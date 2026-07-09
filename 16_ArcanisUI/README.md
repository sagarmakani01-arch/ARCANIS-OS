# ArcanisUI

**Lightweight, modular, cross-platform interface framework**

A comprehensive UI framework for building Arcanis applications with a virtual DOM, component system, theme engine, animations, accessibility, and AI-powered features.

## Features

### UI System
- **Virtual DOM** - Efficient diffing and reconciliation
- **Component System** - React-like hooks (useState, useEffect, useMemo, useCallback)
- **Theme Engine** - Light/dark modes with CSS custom properties
- **Animation Engine** - Hardware-accelerated animations with easing functions
- **Accessibility** - ARIA support, focus management, screen reader announcements

### AI Features
- **Adaptive Interface** - Learns user patterns and auto-adjusts
- **Voice-Controlled UI** - Speech recognition with command system
- **Context-Aware Layouts** - Responsive to viewport, time, user behavior

### Developer Tools
- **UI Designer** - Visual design tool with drag-and-drop
- **Component Library** - Pre-built, documented components
- **Documentation System** - Searchable docs with API references

## Quick Start

```typescript
import { createApp, h, Button } from '@arcanis/ui';

const App = () => h('div', {},
  h('h1', {}, 'Hello ArcanisUI'),
  h(Button, { variant: 'primary', onClick: () => alert('Clicked!') }, 'Click Me')
);

createApp(App).mount(document.getElementById('root')!);
```

## Components

| Component | Description |
|-----------|-------------|
| `Button` | Interactive buttons with variants |
| `Input` | Text inputs with validation |
| `Select` | Dropdown select menus |
| `Modal` | Dialog overlays |
| `Card` | Content containers |
| `Badge` | Status indicators |
| `Tabs` | Tabbed navigation |
| `Avatar` | User avatars |
| `Tooltip` | Context hints |
| `Checkbox` / `Radio` / `Switch` | Form toggles |
| `Stack` / `Flex` / `Grid` | Layout primitives |

## Project Structure

```
src/
├── core/           # Framework core (DOM, renderer, scheduler, components)
├── components/     # UI components
├── theme/          # Theme system
├── animation/      # Animation engine
├── accessibility/  # A11y features
├── ai/             # AI features (adaptive, voice, context)
├── devtools/       # Developer tools
└── types/          # TypeScript types
```

## License

MIT

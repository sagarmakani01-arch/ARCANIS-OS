import { EventBus } from '../../core/EventBus';
import { Configuration } from '../../core/Configuration';

export interface Theme {
  id: string;
  name: string;
  type: 'dark' | 'light' | 'highContrast';
  colors: Record<string, string>;
}

const ARCANIS_DARK: Theme = {
  id: 'arcanis-dark',
  name: 'Arcanis Dark',
  type: 'dark',
  colors: {
    'editor.background': '#1e1e2e',
    'editor.foreground': '#cdd6f4',
    'editor.lineHighlight': '#2a2a3e',
    'editor.selection': '#45475a',
    'editor.cursor': '#f5e0dc',
    'editorLineNumber.foreground': '#6c7086',
    'editorWhitespace.foreground': '#45475a',
    'editor.findMatchHighlight': '#f9e2af44',
    'editorError.foreground': '#f38ba8',
    'editorWarning.foreground': '#fab387',
    'editorInfo.foreground': '#89b4fa',
    'sidebar.background': '#181825',
    'sidebar.foreground': '#cdd6f4',
    'sidebar.selectionBackground': '#313244',
    'statusBar.background': '#11111b',
    'statusBar.foreground': '#cdd6f4',
    'panel.background': '#181825',
    'panel.foreground': '#cdd6f4',
    'tab.activeBackground': '#1e1e2e',
    'tab.inactiveBackground': '#181825',
    'button.primaryBackground': '#cba6f7',
    'button.primaryForeground': '#11111b',
    'input.background': '#313244',
    'input.foreground': '#cdd6f4',
    'input.border': '#45475a',
    'list.hoverBackground': '#313244',
    'list.activeSelectionBackground': '#45475a',
    'scrollbar.sliderBackground': '#45475a66',
    'scrollbar.sliderHoverBackground': '#45475aaa',
    'notification.infoBackground': '#89b4fa',
    'notification.warningBackground': '#fab387',
    'notification.errorBackground': '#f38ba8',
    'accent.primary': '#cba6f7',
    'accent.secondary': '#94e2d5',
    'text.link': '#89b4fa',
    'text.codeBlock': '#313244',
  },
};

const ARCANIS_LIGHT: Theme = {
  id: 'arcanis-light',
  name: 'Arcanis Light',
  type: 'light',
  colors: {
    'editor.background': '#eff1f5',
    'editor.foreground': '#4c4f69',
    'editor.lineHighlight': '#e6e9ef',
    'editor.selection': '#acb0be',
    'editor.cursor': '#dc8a78',
    'editorLineNumber.foreground': '#9ca0b0',
    'editorWhitespace.foreground': '#ccd0da',
    'editor.findMatchHighlight': '#df8e1d33',
    'editorError.foreground': '#d20f39',
    'editorWarning.foreground': '#e64553',
    'editorInfo.foreground': '#04a5e5',
    'sidebar.background': '#e6e9ef',
    'sidebar.foreground': '#4c4f69',
    'sidebar.selectionBackground': '#ccd0da',
    'statusBar.background': '#dce0e8',
    'statusBar.foreground': '#4c4f69',
    'panel.background': '#e6e9ef',
    'panel.foreground': '#4c4f69',
    'tab.activeBackground': '#eff1f5',
    'tab.inactiveBackground': '#e6e9ef',
    'button.primaryBackground': '#7287fd',
    'button.primaryForeground': '#ffffff',
    'input.background': '#e6e9ef',
    'input.foreground': '#4c4f69',
    'input.border': '#ccd0da',
    'list.hoverBackground': '#ccd0da',
    'list.activeSelectionBackground': '#acb0be',
    'scrollbar.sliderBackground': '#acb0be66',
    'scrollbar.sliderHoverBackground': '#acb0beaa',
    'notification.infoBackground': '#04a5e5',
    'notification.warningBackground': '#e64553',
    'notification.errorBackground': '#d20f39',
    'accent.primary': '#7287fd',
    'accent.secondary': '#40a02b',
    'text.link': '#04a5e5',
    'text.codeBlock': '#ccd0da',
  },
};

const ARCANIS_HC: Theme = {
  id: 'arcanis-hc',
  name: 'Arcanis High Contrast',
  type: 'highContrast',
  colors: {
    'editor.background': '#000000',
    'editor.foreground': '#ffffff',
    'editor.lineHighlight': '#1a1a1a',
    'editor.selection': '#3a3a3a',
    'editor.cursor': '#ffffff',
    'editorLineNumber.foreground': '#888888',
    'editorWhitespace.foreground': '#444444',
    'editor.findMatchHighlight': '#ffff0044',
    'editorError.foreground': '#ff6b6b',
    'editorWarning.foreground': '#ffd700',
    'editorInfo.foreground': '#7fc7ff',
    'sidebar.background': '#0a0a0a',
    'sidebar.foreground': '#ffffff',
    'sidebar.selectionBackground': '#333333',
    'statusBar.background': '#000000',
    'statusBar.foreground': '#ffffff',
    'panel.background': '#0a0a0a',
    'panel.foreground': '#ffffff',
    'tab.activeBackground': '#000000',
    'tab.inactiveBackground': '#0a0a0a',
    'button.primaryBackground': '#ffffff',
    'button.primaryForeground': '#000000',
    'input.background': '#1a1a1a',
    'input.foreground': '#ffffff',
    'input.border': '#ffffff',
    'list.hoverBackground': '#222222',
    'list.activeSelectionBackground': '#333333',
    'scrollbar.sliderBackground': '#66666666',
    'scrollbar.sliderHoverBackground': '#888888aa',
    'notification.infoBackground': '#7fc7ff',
    'notification.warningBackground': '#ffd700',
    'notification.errorBackground': '#ff6b6b',
    'accent.primary': '#ffffff',
    'accent.secondary': '#ffffff',
    'text.link': '#7fc7ff',
    'text.codeBlock': '#1a1a1a',
  },
};

export class ThemeManager {
  private currentTheme: Theme;
  private themes: Map<string, Theme> = new Map();

  constructor(
    private eventBus: EventBus,
    private configuration: Configuration,
  ) {
    this.registerTheme(ARCANIS_DARK);
    this.registerTheme(ARCANIS_LIGHT);
    this.registerTheme(ARCANIS_HC);

    const savedThemeId = this.configuration.get<string>('theme', 'arcanis-dark');
    this.currentTheme = this.themes.get(savedThemeId) || ARCANIS_DARK;
  }

  getTheme(): Theme {
    return this.currentTheme;
  }

  setTheme(themeId: string): void {
    const theme = this.themes.get(themeId);
    if (!theme) {
      console.warn(`[ThemeManager] Theme "${themeId}" not found`);
      return;
    }
    this.currentTheme = theme;
    this.configuration.set('theme', themeId);
    this.eventBus.emit('ui:themeChanged', { themeId, theme });
  }

  registerTheme(theme: Theme): void {
    this.themes.set(theme.id, theme);
  }

  getRegisteredThemes(): Theme[] {
    return Array.from(this.themes.values());
  }

  getColor(colorId: string): string {
    return this.currentTheme.colors[colorId] || '#000000';
  }
}

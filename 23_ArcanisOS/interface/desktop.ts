import { DesktopConfig, ThemeConfig, WidgetConfig, AppShortcut } from "./types";

const DEFAULT_THEME: ThemeConfig = {
  mode: "dark",
  primaryColor: "#6366f1",
  accentColor: "#22d3ee",
  fontFamily: "'Inter', system-ui, sans-serif",
  fontSize: 14,
  borderRadius: 12,
  glassmorphism: true,
};

export class ArcanisDesktop {
  public config: DesktopConfig;
  private shortcuts: Map<string, AppShortcut> = new Map();
  private widgets: Map<string, WidgetConfig> = new Map();
  private listeners: Array<(event: string, data: unknown) => void> = [];

  constructor() {
    this.config = {
      theme: DEFAULT_THEME,
      wallpaper: "default",
      widgets: [],
      dock: [],
      notifications: {
        enabled: true,
        position: "top-right",
        sound: true,
        doNotDisturb: false,
      },
    };
  }

  setTheme(theme: Partial<ThemeConfig>): void {
    this.config.theme = { ...this.config.theme, ...theme };
    this.emit("theme:changed", this.config.theme);
  }

  setWallpaper(path: string): void {
    this.config.wallpaper = path;
    this.emit("wallpaper:changed", path);
  }

  addShortcut(shortcut: AppShortcut): void {
    this.shortcuts.set(shortcut.id, shortcut);
    this.config.dock = Array.from(this.shortcuts.values());
    this.emit("shortcut:added", shortcut);
  }

  removeShortcut(id: string): void {
    this.shortcuts.delete(id);
    this.config.dock = Array.from(this.shortcuts.values());
    this.emit("shortcut:removed", id);
  }

  addWidget(widget: WidgetConfig): void {
    this.widgets.set(widget.id, widget);
    this.config.widgets = Array.from(this.widgets.values());
    this.emit("widget:added", widget);
  }

  removeWidget(id: string): void {
    this.widgets.delete(id);
    this.config.widgets = Array.from(this.widgets.values());
    this.emit("widget:removed", id);
  }

  onEvent(callback: (event: string, data: unknown) => void): void {
    this.listeners.push(callback);
  }

  private emit(event: string, data: unknown): void {
    for (const listener of this.listeners) {
      listener(event, data);
    }
  }
}

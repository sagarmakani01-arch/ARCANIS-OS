export interface DesktopConfig {
  theme: ThemeConfig;
  wallpaper: string;
  widgets: WidgetConfig[];
  dock: AppShortcut[];
  notifications: NotificationConfig;
}

export interface ThemeConfig {
  mode: "light" | "dark" | "auto";
  primaryColor: string;
  accentColor: string;
  fontFamily: string;
  fontSize: number;
  borderRadius: number;
  glassmorphism: boolean;
}

export interface WidgetConfig {
  id: string;
  type: string;
  position: Position;
  size: Size;
  config: Record<string, unknown>;
}

export interface Position {
  x: number;
  y: number;
}

export interface Size {
  width: number;
  height: number;
}

export interface AppShortcut {
  id: string;
  name: string;
  icon: string;
  command: string;
  category: string;
}

export interface NotificationConfig {
  enabled: boolean;
  position: "top-right" | "top-left" | "bottom-right" | "bottom-left";
  sound: boolean;
  doNotDisturb: boolean;
}

export interface CommandResult {
  success: boolean;
  output: string;
  error?: string;
  timestamp: number;
}

export interface ShellPrompt {
  prompt: string;
  cwd: string;
  history: string[];
  ai: boolean;
}

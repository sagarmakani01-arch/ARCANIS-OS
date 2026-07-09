export type ThemeToken =
  | 'color.primary'
  | 'color.secondary'
  | 'color.accent'
  | 'color.background'
  | 'color.surface'
  | 'color.text'
  | 'color.textSecondary'
  | 'color.border'
  | 'color.success'
  | 'color.warning'
  | 'color.error'
  | 'color.info'
  | 'space.xs'
  | 'space.sm'
  | 'space.md'
  | 'space.lg'
  | 'space.xl'
  | 'space.2xl'
  | 'radius.sm'
  | 'radius.md'
  | 'radius.lg'
  | 'radius.full'
  | 'shadow.sm'
  | 'shadow.md'
  | 'shadow.lg'
  | 'font.family'
  | 'font.size.xs'
  | 'font.size.sm'
  | 'font.size.md'
  | 'font.size.lg'
  | 'font.size.xl'
  | 'font.weight.normal'
  | 'font.weight.medium'
  | 'font.weight.bold'
  | 'transition.fast'
  | 'transition.normal'
  | 'transition.slow'
  | 'zIndex.dropdown'
  | 'zIndex.modal'
  | 'zIndex.tooltip';

export type ThemeValues = Record<ThemeToken, string>;
export type ThemeMode = 'light' | 'dark' | 'system';
export type ThemeOverride = Partial<ThemeValues>;

export interface Theme {
  name: string;
  mode: ThemeMode;
  tokens: ThemeValues;
  override?: ThemeOverride;
}

export interface ThemeProvider {
  getTheme(): Theme;
  setTheme(theme: Partial<Theme>): void;
  getTokens(): ThemeValues;
  getToken(token: ThemeToken): string;
  onThemeChange(callback: (theme: Theme) => void): () => void;
}

import type { Theme, ThemeValues, ThemeToken, ThemeMode, ThemeOverride, ThemeProvider } from '../types/theme';

const lightTokens: ThemeValues = {
  'color.primary': '#6366f1',
  'color.secondary': '#8b5cf6',
  'color.accent': '#06b6d4',
  'color.background': '#ffffff',
  'color.surface': '#f8fafc',
  'color.text': '#0f172a',
  'color.textSecondary': '#64748b',
  'color.border': '#e2e8f0',
  'color.success': '#22c55e',
  'color.warning': '#f59e0b',
  'color.error': '#ef4444',
  'color.info': '#3b82f6',
  'space.xs': '4px',
  'space.sm': '8px',
  'space.md': '16px',
  'space.lg': '24px',
  'space.xl': '32px',
  'space.2xl': '48px',
  'radius.sm': '4px',
  'radius.md': '8px',
  'radius.lg': '12px',
  'radius.full': '9999px',
  'shadow.sm': '0 1px 2px rgba(0,0,0,0.05)',
  'shadow.md': '0 4px 6px -1px rgba(0,0,0,0.1)',
  'shadow.lg': '0 10px 15px -3px rgba(0,0,0,0.1)',
  'font.family': "'Inter', system-ui, -apple-system, sans-serif",
  'font.size.xs': '12px',
  'font.size.sm': '14px',
  'font.size.md': '16px',
  'font.size.lg': '18px',
  'font.size.xl': '20px',
  'font.weight.normal': '400',
  'font.weight.medium': '500',
  'font.weight.bold': '700',
  'transition.fast': '150ms ease',
  'transition.normal': '250ms ease',
  'transition.slow': '350ms ease',
  'zIndex.dropdown': '1000',
  'zIndex.modal': '1100',
  'zIndex.tooltip': '1200',
};

const darkTokens: ThemeValues = {
  'color.primary': '#818cf8',
  'color.secondary': '#a78bfa',
  'color.accent': '#22d3ee',
  'color.background': '#0f172a',
  'color.surface': '#1e293b',
  'color.text': '#f1f5f9',
  'color.textSecondary': '#94a3b8',
  'color.border': '#334155',
  'color.success': '#4ade80',
  'color.warning': '#fbbf24',
  'color.error': '#f87171',
  'color.info': '#60a5fa',
  'space.xs': '4px',
  'space.sm': '8px',
  'space.md': '16px',
  'space.lg': '24px',
  'space.xl': '32px',
  'space.2xl': '48px',
  'radius.sm': '4px',
  'radius.md': '8px',
  'radius.lg': '12px',
  'radius.full': '9999px',
  'shadow.sm': '0 1px 2px rgba(0,0,0,0.2)',
  'shadow.md': '0 4px 6px -1px rgba(0,0,0,0.3)',
  'shadow.lg': '0 10px 15px -3px rgba(0,0,0,0.4)',
  'font.family': "'Inter', system-ui, -apple-system, sans-serif",
  'font.size.xs': '12px',
  'font.size.sm': '14px',
  'font.size.md': '16px',
  'font.size.lg': '18px',
  'font.size.xl': '20px',
  'font.weight.normal': '400',
  'font.weight.medium': '500',
  'font.weight.bold': '700',
  'transition.fast': '150ms ease',
  'transition.normal': '250ms ease',
  'transition.slow': '350ms ease',
  'zIndex.dropdown': '1000',
  'zIndex.modal': '1100',
  'zIndex.tooltip': '1200',
};

export function createThemeProvider(initialOverride?: ThemeOverride): ThemeProvider {
  let currentMode: ThemeMode = 'system';
  let currentOverride: ThemeOverride = initialOverride || {};
  const listeners = new Set<(theme: Theme) => void>();

  function getSystemMode(): 'light' | 'dark' {
    if (typeof window === 'undefined') return 'light';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function resolveMode(): 'light' | 'dark' {
    return currentMode === 'system' ? getSystemMode() : currentMode;
  }

  function getResolvedTokens(): ThemeValues {
    const baseTokens = resolveMode() === 'dark' ? darkTokens : lightTokens;
    return { ...baseTokens, ...currentOverride };
  }

  function buildTheme(): Theme {
    return {
      name: 'arcanis',
      mode: currentMode,
      tokens: getResolvedTokens(),
      override: currentOverride,
    };
  }

  function notify(): void {
    const theme = buildTheme();
    listeners.forEach((cb) => cb(theme));
    if (typeof document !== 'undefined') {
      const root = document.documentElement;
      const tokens = theme.tokens;
      for (const [key, value] of Object.entries(tokens)) {
        root.style.setProperty(`--arcanis-${key}`, value);
      }
    }
  }

  if (typeof window !== 'undefined') {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (currentMode === 'system') notify();
    });
  }

  return {
    getTheme: buildTheme,
    setTheme(partial) {
      if (partial.mode !== undefined) currentMode = partial.mode;
      if (partial.override !== undefined) currentOverride = partial.override;
      notify();
    },
    getTokens: getResolvedTokens,
    getToken: (token) => getResolvedTokens()[token],
    onThemeChange(callback) {
      listeners.add(callback);
      return () => listeners.delete(callback);
    },
  };
}

export const defaultThemeProvider = createThemeProvider();

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createThemeProvider, defaultThemeProvider } from '../src/theme/ThemeProvider';

beforeEach(() => {
  vi.unstubAllGlobals();
});

describe('createThemeProvider', () => {
  it('creates a theme provider', () => {
    const provider = createThemeProvider();
    expect(provider).toHaveProperty('getTheme');
    expect(provider).toHaveProperty('setTheme');
    expect(provider).toHaveProperty('getTokens');
    expect(provider).toHaveProperty('getToken');
    expect(provider).toHaveProperty('onThemeChange');
  });

  it('getTheme returns theme object', () => {
    const provider = createThemeProvider();
    const theme = provider.getTheme();
    expect(theme.name).toBe('arcanis');
    expect(theme.mode).toBe('system');
    expect(theme.tokens).toBeDefined();
  });

  it('getTokens returns all tokens', () => {
    const provider = createThemeProvider();
    const tokens = provider.getTokens();
    expect(tokens['color.primary']).toBeDefined();
    expect(tokens['color.background']).toBeDefined();
    expect(tokens['space.md']).toBe('16px');
    expect(tokens['radius.md']).toBe('8px');
    expect(tokens['font.size.md']).toBe('16px');
  });

  it('getToken returns specific token', () => {
    const provider = createThemeProvider();
    expect(provider.getToken('space.md')).toBe('16px');
    expect(provider.getToken('radius.md')).toBe('8px');
    expect(provider.getToken('font.size.sm')).toBe('14px');
  });

  it('setTheme changes mode to light', () => {
    const provider = createThemeProvider();
    provider.setTheme({ mode: 'light' });
    const theme = provider.getTheme();
    expect(theme.mode).toBe('light');
    expect(theme.tokens['color.background']).toBe('#ffffff');
  });

  it('setTheme changes mode to dark', () => {
    const provider = createThemeProvider();
    provider.setTheme({ mode: 'dark' });
    const theme = provider.getTheme();
    expect(theme.mode).toBe('dark');
    expect(theme.tokens['color.background']).toBe('#0f172a');
  });

  it('setTheme applies override', () => {
    const provider = createThemeProvider();
    provider.setTheme({ override: { 'color.primary': '#ff0000' } });
    const theme = provider.getTheme();
    expect(theme.tokens['color.primary']).toBe('#ff0000');
    expect(theme.override).toEqual({ 'color.primary': '#ff0000' });
  });

  it('onThemeChange notifies on setTheme', () => {
    const provider = createThemeProvider();
    const callback = vi.fn();
    provider.onThemeChange(callback);
    provider.setTheme({ mode: 'dark' });
    expect(callback).toHaveBeenCalledTimes(1);
    const theme = callback.mock.calls[0][0];
    expect(theme.mode).toBe('dark');
  });

  it('onThemeChange returns unsubscribe function', () => {
    const provider = createThemeProvider();
    const callback = vi.fn();
    const unsub = provider.onThemeChange(callback);
    unsub();
    provider.setTheme({ mode: 'dark' });
    expect(callback).not.toHaveBeenCalled();
  });

  it('multiple listeners are notified', () => {
    const provider = createThemeProvider();
    const cb1 = vi.fn();
    const cb2 = vi.fn();
    provider.onThemeChange(cb1);
    provider.onThemeChange(cb2);
    provider.setTheme({ mode: 'dark' });
    expect(cb1).toHaveBeenCalledTimes(1);
    expect(cb2).toHaveBeenCalledTimes(1);
  });

  it('initial override is applied', () => {
    const provider = createThemeProvider({ 'color.primary': '#00ff00' });
    expect(provider.getToken('color.primary')).toBe('#00ff00');
  });

  it('tokens differ between light and dark', () => {
    const provider = createThemeProvider();
    provider.setTheme({ mode: 'light' });
    const lightBg = provider.getToken('color.background');
    provider.setTheme({ mode: 'dark' });
    const darkBg = provider.getToken('color.background');
    expect(lightBg).not.toBe(darkBg);
  });

  it('light theme has correct primary color', () => {
    const provider = createThemeProvider();
    provider.setTheme({ mode: 'light' });
    expect(provider.getToken('color.primary')).toBe('#6366f1');
  });

  it('dark theme has correct primary color', () => {
    const provider = createThemeProvider();
    provider.setTheme({ mode: 'dark' });
    expect(provider.getToken('color.primary')).toBe('#818cf8');
  });

  it('space tokens are consistent across modes', () => {
    const provider = createThemeProvider();
    provider.setTheme({ mode: 'light' });
    const lightSpace = provider.getToken('space.md');
    provider.setTheme({ mode: 'dark' });
    const darkSpace = provider.getToken('space.md');
    expect(lightSpace).toBe(darkSpace);
  });

  it('font tokens are consistent across modes', () => {
    const provider = createThemeProvider();
    provider.setTheme({ mode: 'light' });
    const lightFont = provider.getToken('font.size.md');
    provider.setTheme({ mode: 'dark' });
    const darkFont = provider.getToken('font.size.md');
    expect(lightFont).toBe(darkFont);
  });

  it('theme has override field when set', () => {
    const provider = createThemeProvider({ 'color.accent': '#123456' });
    const theme = provider.getTheme();
    expect(theme.override).toEqual({ 'color.accent': '#123456' });
  });

  it('theme override is empty by default', () => {
    const provider = createThemeProvider();
    const theme = provider.getTheme();
    expect(theme.override).toEqual({});
  });
});

describe('defaultThemeProvider', () => {
  it('is exported', () => {
    expect(defaultThemeProvider).toBeDefined();
  });

  it('has all methods', () => {
    expect(typeof defaultThemeProvider.getTheme).toBe('function');
    expect(typeof defaultThemeProvider.setTheme).toBe('function');
    expect(typeof defaultThemeProvider.getTokens).toBe('function');
    expect(typeof defaultThemeProvider.getToken).toBe('function');
    expect(typeof defaultThemeProvider.onThemeChange).toBe('function');
  });

  it('returns valid theme', () => {
    const theme = defaultThemeProvider.getTheme();
    expect(theme.name).toBe('arcanis');
    expect(theme.tokens).toBeDefined();
  });
});

describe('theme tokens completeness', () => {
  it('has all color tokens', () => {
    const provider = createThemeProvider();
    const tokens = provider.getTokens();
    const colorTokens = [
      'color.primary', 'color.secondary', 'color.accent', 'color.background',
      'color.surface', 'color.text', 'color.textSecondary', 'color.border',
      'color.success', 'color.warning', 'color.error', 'color.info',
    ];
    colorTokens.forEach((t) => {
      expect(tokens[t as keyof typeof tokens]).toBeDefined();
    });
  });

  it('has all space tokens', () => {
    const provider = createThemeProvider();
    const tokens = provider.getTokens();
    const spaceTokens = ['space.xs', 'space.sm', 'space.md', 'space.lg', 'space.xl', 'space.2xl'];
    spaceTokens.forEach((t) => {
      expect(tokens[t as keyof typeof tokens]).toBeDefined();
    });
  });

  it('has all radius tokens', () => {
    const provider = createThemeProvider();
    const tokens = provider.getTokens();
    const radiusTokens = ['radius.sm', 'radius.md', 'radius.lg', 'radius.full'];
    radiusTokens.forEach((t) => {
      expect(tokens[t as keyof typeof tokens]).toBeDefined();
    });
  });

  it('has all shadow tokens', () => {
    const provider = createThemeProvider();
    const tokens = provider.getTokens();
    const shadowTokens = ['shadow.sm', 'shadow.md', 'shadow.lg'];
    shadowTokens.forEach((t) => {
      expect(tokens[t as keyof typeof tokens]).toBeDefined();
    });
  });

  it('has all font tokens', () => {
    const provider = createThemeProvider();
    const tokens = provider.getTokens();
    const fontTokens = [
      'font.family', 'font.size.xs', 'font.size.sm', 'font.size.md',
      'font.size.lg', 'font.size.xl', 'font.weight.normal',
      'font.weight.medium', 'font.weight.bold',
    ];
    fontTokens.forEach((t) => {
      expect(tokens[t as keyof typeof tokens]).toBeDefined();
    });
  });

  it('has all transition tokens', () => {
    const provider = createThemeProvider();
    const tokens = provider.getTokens();
    const transTokens = ['transition.fast', 'transition.normal', 'transition.slow'];
    transTokens.forEach((t) => {
      expect(tokens[t as keyof typeof tokens]).toBeDefined();
    });
  });

  it('has all z-index tokens', () => {
    const provider = createThemeProvider();
    const tokens = provider.getTokens();
    const zTokens = ['zIndex.dropdown', 'zIndex.modal', 'zIndex.tooltip'];
    zTokens.forEach((t) => {
      expect(tokens[t as keyof typeof tokens]).toBeDefined();
    });
  });
});

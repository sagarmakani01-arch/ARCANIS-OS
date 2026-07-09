export interface ContextConfig {
  enabled: boolean;
  trackViewport: boolean;
  trackTime: boolean;
  trackUser: boolean;
  trackEnvironment: boolean;
}

export interface LayoutContext {
  viewport: ViewportContext;
  time: TimeContext;
  user: UserContext;
  environment: EnvironmentContext;
}

export interface ViewportContext {
  width: number;
  height: number;
  aspectRatio: number;
  orientation: 'portrait' | 'landscape';
  breakpoint: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  pixelRatio: number;
}

export interface TimeContext {
  hour: number;
  minute: number;
  period: 'morning' | 'afternoon' | 'evening' | 'night';
  dayOfWeek: number;
  isWeekend: boolean;
  season: 'spring' | 'summer' | 'autumn' | 'winter';
}

export interface UserContext {
  scrollPosition: number;
  scrollDirection: 'up' | 'down' | null;
  interactionSpeed: 'slow' | 'normal' | 'fast';
  sessionDuration: number;
  pagesVisited: number;
  lastAction: string | null;
}

export interface EnvironmentContext {
  isDarkMode: boolean;
  reducedMotion: boolean;
  highContrast: boolean;
  language: string;
  timezone: string;
  online: boolean;
}

export interface ContextEngine {
  getContext(): LayoutContext;
  onContextChange(callback: (context: LayoutContext) => void): () => void;
  update(): void;
  subscribe(key: string, callback: (value: unknown) => void): () => void;
}

const BREAKPOINTS = { xs: 0, sm: 640, md: 768, lg: 1024, xl: 1280, '2xl': 1536 } as const;

function getViewportContext(): ViewportContext {
  if (typeof window === 'undefined') {
    return { width: 0, height: 0, aspectRatio: 1, orientation: 'landscape', breakpoint: 'lg', pixelRatio: 1 };
  }

  const width = window.innerWidth;
  const height = window.innerHeight;
  const pixelRatio = window.devicePixelRatio || 1;

  let breakpoint: ViewportContext['breakpoint'] = 'xs';
  for (const [key, value] of Object.entries(BREAKPOINTS)) {
    if (width >= value) breakpoint = key as ViewportContext['breakpoint'];
  }

  return {
    width,
    height,
    aspectRatio: width / height,
    orientation: width > height ? 'landscape' : 'portrait',
    breakpoint,
    pixelRatio,
  };
}

function getTimeContext(): TimeContext {
  const now = new Date();
  const hour = now.getHours();
  const month = now.getMonth();

  let period: TimeContext['period'] = 'morning';
  if (hour >= 12 && hour < 17) period = 'afternoon';
  else if (hour >= 17 && hour < 21) period = 'evening';
  else if (hour >= 21 || hour < 5) period = 'night';

  let season: TimeContext['season'] = 'spring';
  if (month >= 2 && month <= 4) season = 'spring';
  else if (month >= 5 && month <= 7) season = 'summer';
  else if (month >= 8 && month <= 10) season = 'autumn';
  else season = 'winter';

  return {
    hour,
    minute: now.getMinutes(),
    period,
    dayOfWeek: now.getDay(),
    isWeekend: now.getDay() === 0 || now.getDay() === 6,
    season,
  };
}

function getUserContext(): UserContext {
  return {
    scrollPosition: typeof window !== 'undefined' ? window.scrollY : 0,
    scrollDirection: null,
    interactionSpeed: 'normal',
    sessionDuration: 0,
    pagesVisited: 1,
    lastAction: null,
  };
}

function getEnvironmentContext(): EnvironmentContext {
  if (typeof window === 'undefined') {
    return {
      isDarkMode: false,
      reducedMotion: false,
      highContrast: false,
      language: 'en',
      timezone: 'UTC',
      online: true,
    };
  }

  return {
    isDarkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
    reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    highContrast: window.matchMedia('(prefers-contrast: high)').matches,
    language: navigator.language,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    online: navigator.onLine,
  };
}

export function createContextEngine(config: ContextConfig): ContextEngine {
  const listeners = new Set<(context: LayoutContext) => void>();
  const subscriptions = new Map<string, Set<(value: unknown) => void>>();
  let cachedContext: LayoutContext | null = null;

  function buildContext(): LayoutContext {
    return {
      viewport: config.trackViewport ? getViewportContext() : (cachedContext?.viewport || getViewportContext()),
      time: config.trackTime ? getTimeContext() : (cachedContext?.time || getTimeContext()),
      user: config.trackUser ? getUserContext() : (cachedContext?.user || getUserContext()),
      environment: config.trackEnvironment ? getEnvironmentContext() : (cachedContext?.environment || getEnvironmentContext()),
    };
  }

  function notify(): void {
    const context = buildContext();
    cachedContext = context;
    listeners.forEach((cb) => cb(context));
    subscriptions.forEach((callbacks, key) => {
      const value = key.split('.').reduce((obj: unknown, k) => {
        if (obj && typeof obj === 'object') return (obj as Record<string, unknown>)[k];
        return undefined;
      }, context);
      callbacks.forEach((cb) => cb(value));
    });
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('resize', () => {
      if (config.trackViewport) notify();
    });

    window.addEventListener('scroll', () => {
      if (config.trackUser) {
        const ctx = cachedContext || buildContext();
        const prevScroll = ctx.user.scrollPosition;
        const currentScroll = window.scrollY;
        ctx.user.scrollPosition = currentScroll;
        ctx.user.scrollDirection = currentScroll > prevScroll ? 'down' : 'up';
        notify();
      }
    });

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (config.trackEnvironment) notify();
    });
  }

  return {
    getContext: () => cachedContext || buildContext(),
    onContextChange(callback) {
      listeners.add(callback);
      return () => listeners.delete(callback);
    },
    update: notify,
    subscribe(key, callback) {
      if (!subscriptions.has(key)) subscriptions.set(key, new Set());
      subscriptions.get(key)!.add(callback);
      return () => subscriptions.get(key)?.delete(callback);
    },
  };
}

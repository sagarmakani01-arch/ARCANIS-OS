export interface AdaptiveConfig {
  enabled: boolean;
  trackInteractions: boolean;
  analyzePatterns: boolean;
  autoAdjust: boolean;
}

export interface UserInteraction {
  type: 'click' | 'scroll' | 'hover' | 'focus' | 'input' | 'resize';
  target: string;
  timestamp: number;
  duration?: number;
  metadata?: Record<string, unknown>;
}

export interface LayoutSuggestion {
  type: 'spacing' | 'fontSize' | 'contrast' | 'density' | 'layout';
  property: string;
  value: string;
  confidence: number;
  reason: string;
}

export interface AdaptiveEngine {
  trackInteraction(interaction: Omit<UserInteraction, 'timestamp'>): void;
  getSuggestions(): LayoutSuggestion[];
  getInteractionHistory(): UserInteraction[];
  analyzeBehavior(): BehaviorAnalysis;
  applySuggestion(suggestion: LayoutSuggestion): void;
  reset(): void;
}

export interface BehaviorAnalysis {
  totalInteractions: number;
  averageSessionDuration: number;
  preferredDevice: 'mouse' | 'touch' | 'keyboard';
  frequentlyUsedFeatures: string[];
  timeOfDay: 'morning' | 'afternoon' | 'evening' | 'night';
  suggestions: LayoutSuggestion[];
}

export function createAdaptiveEngine(config: AdaptiveConfig = { enabled: true, trackInteractions: true, analyzePatterns: true, autoAdjust: false }): AdaptiveEngine {
  const interactions: UserInteraction[] = [];
  let suggestions: LayoutSuggestion[] = [];

  function trackInteraction(raw: Omit<UserInteraction, 'timestamp'>): void {
    if (!config.trackInteractions) return;
    interactions.push({ ...raw, timestamp: Date.now() });
    if (config.analyzePatterns) {
      analyzeAndSuggest();
    }
  }

  function analyzeAndSuggest(): void {
    suggestions = [];
    const recentInteractions = interactions.slice(-100);

    if (recentInteractions.length < 10) return;

    const clicks = recentInteractions.filter((i) => i.type === 'click');
    const scrollEvents = recentInteractions.filter((i) => i.type === 'scroll');
    const hoverEvents = recentInteractions.filter((i) => i.type === 'hover');

    if (clicks.length > 30) {
      suggestions.push({
        type: 'density',
        property: 'spacing',
        value: 'compact',
        confidence: 0.7,
        reason: 'High interaction frequency detected',
      });
    }

    const smallTargets = clicks.filter((c) => {
      if (c.metadata && typeof c.metadata === 'object') {
        const meta = c.metadata as Record<string, unknown>;
        if (typeof meta.width === 'number' && typeof meta.height === 'number') {
          return meta.width < 44 || meta.height < 44;
        }
      }
      return false;
    });

    if (smallTargets.length > clicks.length * 0.3) {
      suggestions.push({
        type: 'spacing',
        property: 'padding',
        value: 'increase',
        confidence: 0.8,
        reason: 'Multiple clicks on small targets detected',
      });
    }

    if (scrollEvents.length > 20) {
      suggestions.push({
        type: 'layout',
        property: 'scrollPosition',
        value: 'sticky',
        confidence: 0.6,
        reason: 'Frequent scrolling detected',
      });
    }
  }

  function getBehaviorAnalysis(): BehaviorAnalysis {
    const now = new Date();
    const hour = now.getHours();
    let timeOfDay: BehaviorAnalysis['timeOfDay'] = 'morning';
    if (hour >= 12 && hour < 17) timeOfDay = 'afternoon';
    else if (hour >= 17 && hour < 21) timeOfDay = 'evening';
    else if (hour >= 21 || hour < 5) timeOfDay = 'night';

    const deviceScores = { mouse: 0, touch: 0, keyboard: 0 };
    interactions.forEach((i) => {
      if (i.type === 'click') deviceScores.mouse++;
      if (i.type === 'hover') deviceScores.mouse++;
      if (i.type === 'input') deviceScores.keyboard++;
    });

    const preferredDevice = Object.entries(deviceScores).reduce((a, b) => a[1] > b[1] ? a : b)[0] as 'mouse' | 'touch' | 'keyboard';

    const featureCounts = new Map<string, number>();
    interactions.forEach((i) => {
      featureCounts.set(i.target, (featureCounts.get(i.target) || 0) + 1);
    });
    const frequentlyUsedFeatures = Array.from(featureCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([feature]) => feature);

    return {
      totalInteractions: interactions.length,
      averageSessionDuration: interactions.length > 1
        ? (interactions[interactions.length - 1].timestamp - interactions[0].timestamp) / 1000
        : 0,
      preferredDevice,
      frequentlyUsedFeatures,
      timeOfDay,
      suggestions,
    };
  }

  function applySuggestion(suggestion: LayoutSuggestion): void {
    if (!config.autoAdjust) return;

    const root = document.documentElement;
    if (suggestion.type === 'spacing') {
      root.style.setProperty(`--arcanis-adaptive-${suggestion.property}`, suggestion.value);
    } else if (suggestion.type === 'fontSize') {
      root.style.setProperty('--arcanis-adaptive-font-size', suggestion.value);
    } else if (suggestion.type === 'contrast') {
      root.style.setProperty('--arcanis-adaptive-contrast', suggestion.value);
    }
  }

  return {
    trackInteraction,
    getSuggestions: () => [...suggestions],
    getInteractionHistory: () => [...interactions],
    analyzeBehavior: getBehaviorAnalysis,
    applySuggestion,
    reset: () => { interactions.length = 0; suggestions = []; },
  };
}

export type EasingFunction = (t: number) => number;

export interface AnimationConfig {
  duration: number;
  delay?: number;
  easing?: EasingFunction | string;
  iterations?: number;
  direction?: 'normal' | 'reverse' | 'alternate' | 'alternate-reverse';
  fill?: 'none' | 'forwards' | 'backwards' | 'both';
  onStart?: () => void;
  onUpdate?: (progress: number) => void;
  onComplete?: () => void;
}

export interface Animation {
  play(): void;
  pause(): void;
  resume(): void;
  cancel(): void;
  reverse(): void;
  finished: Promise<void>;
  readonly currentTime: number;
  readonly progress: number;
  readonly isPlaying: boolean;
}

export const easings = {
  linear: (t: number) => t,
  easeIn: (t: number) => t * t * t,
  easeOut: (t: number) => 1 - Math.pow(1 - t, 3),
  easeInOut: (t: number) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  easeInQuad: (t: number) => t * t,
  easeOutQuad: (t: number) => t * (2 - t),
  easeInOutQuad: (t: number) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
  easeInBack: (t: number) => 2.70158 * t * t * t - 1.70158 * t * t,
  easeOutBack: (t: number) => {
    const c1 = 1.70158;
    const c3 = c1 + 1;
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
  },
  easeInOutBack: (t: number) => {
    const c1 = 1.70158;
    const c2 = c1 * 1.525;
    return t < 0.5
      ? (Math.pow(2 * t, 2) * ((c2 + 1) * 2 * t - c2)) / 2
      : (Math.pow(2 * t - 2, 2) * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2;
  },
  easeOutElastic: (t: number) => {
    const c4 = (2 * Math.PI) / 3;
    return t === 0 ? 0 : t === 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * c4) + 1;
  },
  easeOutBounce: (t: number) => {
    const n1 = 7.5625;
    const d1 = 2.75;
    if (t < 1 / d1) return n1 * t * t;
    if (t < 2 / d1) return n1 * (t -= 1.5 / d1) * t + 0.75;
    if (t < 2.5 / d1) return n1 * (t -= 2.25 / d1) * t + 0.9375;
    return n1 * (t -= 2.625 / d1) * t + 0.984375;
  },
} as const;

const runningAnimations = new Map<string, Animation>();

function parseEasing(easing: EasingFunction | string): EasingFunction {
  if (typeof easing === 'function') return easing;
  return easings[easing as keyof typeof easings] || easings.easeOut;
}

export function animate(element: Element, keyframes: Keyframe[], config: AnimationConfig): Animation {
  const id = `anim-${Math.random().toString(36).slice(2, 9)}`;
  let startTime = 0;
  let currentTime = 0;
  let isPlaying = false;
  let rafId: number | null = null;
  let direction = config.direction || 'normal';
  let iterations = config.iterations ?? 1;
  let iterationCount = 0;
  let resolveFinished: () => void;
  const finished = new Promise<void>((resolve) => { resolveFinished = resolve; });

  const easingFn = parseEasing(config.easing || easings.easeOut);
  const duration = config.duration;
  const delay = config.delay || 0;

  function interpolate(frame1: Keyframe, frame2: Keyframe, t: number): Record<string, string> {
    const result: Record<string, string> = {};
    for (const key in frame1) {
      if (key === 'offset') continue;
      const v1 = parseFloat(frame1[key] as string);
      const v2 = parseFloat(frame2[key] as string);
      if (!isNaN(v1) && !isNaN(v2)) {
        const unit = (frame1[key] as string).replace(/[\d.-]/g, '');
        result[key] = `${v1 + (v2 - v1) * t}${unit}`;
      } else {
        result[key] = t < 0.5 ? (frame1[key] as string) : (frame2[key] as string);
      }
    }
    return result;
  }

  function applyKeyframes(progress: number): void {
    if (!keyframes.length) return;

    let idx = 0;
    for (let i = 0; i < keyframes.length - 1; i++) {
      const offset = (keyframes[i + 1].offset ?? (i + 1) / (keyframes.length - 1));
      if (progress >= (keyframes[i].offset ?? i / (keyframes.length - 1))) {
        idx = i;
      }
    }

    const frame1 = keyframes[idx];
    const frame2 = keyframes[Math.min(idx + 1, keyframes.length - 1)];
    const frame1Offset = frame1.offset ?? idx / (keyframes.length - 1);
    const frame2Offset = frame2.offset ?? (idx + 1) / (keyframes.length - 1);
    const localProgress = frame2Offset > frame1Offset
      ? (progress - frame1Offset) / (frame2Offset - frame1Offset)
      : 1;

    const easedProgress = easingFn(Math.max(0, Math.min(1, localProgress)));
    const values = interpolate(frame1, frame2, easedProgress);

    if (element instanceof HTMLElement || element instanceof SVGElement) {
      for (const [prop, value] of Object.entries(values)) {
        if (prop === 'transform') {
          element.style.transform = value;
        } else if (prop === 'opacity') {
          element.style.opacity = value;
        } else {
          (element.style as unknown as Record<string, string>)[prop] = value;
        }
      }
    }
  }

  function tick(timestamp: number): void {
    if (!isPlaying) return;

    if (startTime === 0) startTime = timestamp;
    const elapsed = timestamp - startTime - delay;

    if (elapsed < 0) {
      rafId = requestAnimationFrame(tick);
      return;
    }

    const rawProgress = Math.min(elapsed / duration, 1);
    let progress = direction === 'reverse' ? 1 - rawProgress : rawProgress;

    if (direction === 'alternate' || direction === 'alternate-reverse') {
      progress = iterationCount % 2 === 0 ? progress : 1 - progress;
    }

    currentTime = elapsed;
    applyKeyframes(progress);
    config.onUpdate?.(progress);

    if (rawProgress >= 1) {
      iterationCount++;
      if (iterations === Infinity || iterationCount < iterations) {
        startTime = 0;
        rafId = requestAnimationFrame(tick);
      } else {
        isPlaying = false;
        config.onComplete?.();
        resolveFinished();
        runningAnimations.delete(id);
      }
    } else {
      rafId = requestAnimationFrame(tick);
    }
  }

  const animation: Animation = {
    play() {
      if (isPlaying) return;
      isPlaying = true;
      config.onStart?.();
      rafId = requestAnimationFrame(tick);
      runningAnimations.set(id, animation);
    },
    pause() {
      isPlaying = false;
      if (rafId !== null) cancelAnimationFrame(rafId);
    },
    resume() {
      if (isPlaying) return;
      isPlaying = true;
      rafId = requestAnimationFrame(tick);
    },
    cancel() {
      isPlaying = false;
      if (rafId !== null) cancelAnimationFrame(rafId);
      runningAnimations.delete(id);
      startTime = 0;
      currentTime = 0;
      iterationCount = 0;
    },
    reverse() {
      direction = direction === 'normal' ? 'reverse' : direction === 'reverse' ? 'normal' : direction;
    },
    get finished() { return finished; },
    get currentTime() { return currentTime; },
    get progress() { return duration > 0 ? currentTime / duration : 0; },
    get isPlaying() { return isPlaying; },
  };

  return animation;
}

export function animateValue(
  from: number,
  to: number,
  config: AnimationConfig
): { animation: Animation; onUpdate: (callback: (value: number) => void) => void } {
  const element = document.createElement('div');
  const keyframes = [
    { transform: `translateX(${from}px)`, offset: 0 },
    { transform: `translateX(${to}px)`, offset: 1 },
  ];

  let callback: ((value: number) => void) | null = null;
  const animation = animate(element, keyframes, {
    ...config,
    onUpdate(progress) {
      const value = from + (to - from) * progress;
      callback?.(value);
    },
  });

  return {
    animation,
    onUpdate(cb: (value: number) => void) {
      callback = cb;
    },
  };
}

export function stagger(
  elements: Element[],
  keyframes: Keyframe[],
  config: AnimationConfig & { staggerDelay?: number }
): Animation[] {
  const staggerDelay = config.staggerDelay || 50;
  return elements.map((el, i) => {
    const anim = animate(el, keyframes, { ...config, delay: (config.delay || 0) + i * staggerDelay });
    anim.play();
    return anim;
  });
}

export function spring(element: Element, config: Partial<AnimationConfig> & { stiffness?: number; damping?: number } = {}): Animation {
  const { stiffness = 100, damping = 10, ...rest } = config;
  const overshoot = stiffness / (stiffness + damping);

  return animate(element, [
    { transform: 'scale(0.8)', offset: 0 },
    { transform: `scale(${1 + overshoot * 0.1})`, offset: 0.6 },
    { transform: 'scale(1)', offset: 1 },
  ], { ...rest, duration: rest.duration || 600, easing: easings.easeOut });
}

export function fadeIn(element: Element, config: Partial<AnimationConfig> = {}): Animation {
  const anim = animate(element, [
    { opacity: '0', offset: 0 },
    { opacity: '1', offset: 1 },
  ], { duration: 300, ...config });
  anim.play();
  return anim;
}

export function fadeOut(element: Element, config: Partial<AnimationConfig> = {}): Animation {
  const anim = animate(element, [
    { opacity: '1', offset: 0 },
    { opacity: '0', offset: 1 },
  ], { duration: 300, ...config });
  anim.play();
  return anim;
}

export function slideIn(element: Element, direction: 'up' | 'down' | 'left' | 'right' = 'up', config: Partial<AnimationConfig> = {}): Animation {
  const transforms: Record<string, string> = {
    up: 'translateY(20px)',
    down: 'translateY(-20px)',
    left: 'translateX(20px)',
    right: 'translateX(-20px)',
  };

  const anim = animate(element, [
    { opacity: '0', transform: transforms[direction], offset: 0 },
    { opacity: '1', transform: 'translate(0)', offset: 1 },
  ], { duration: 300, easing: easings.easeOut, ...config });
  anim.play();
  return anim;
}

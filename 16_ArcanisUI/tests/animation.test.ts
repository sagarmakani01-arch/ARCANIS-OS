import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  easings,
  animate,
  animateValue,
  stagger,
  spring,
  fadeIn,
  fadeOut,
  slideIn,
} from '../src/animation/engine';

class MockHTMLElement {
  style: Record<string, string> = {};
}

class MockSVGElement {
  style: Record<string, string> = {};
}

let rafCallbacks: { cb: FrameRequestCallback; id: number }[] = [];
let rafIdCounter = 0;
let mockTime = 0;

beforeEach(() => {
  rafCallbacks = [];
  rafIdCounter = 0;
  mockTime = 1;
  vi.stubGlobal('HTMLElement', MockHTMLElement);
  vi.stubGlobal('SVGElement', MockSVGElement);
  vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => {
    const id = ++rafIdCounter;
    rafCallbacks.push({ cb, id });
    return id;
  });
  vi.stubGlobal('cancelAnimationFrame', (id: number) => {
    rafCallbacks = rafCallbacks.filter((r) => r.id !== id);
  });
  vi.stubGlobal('document', {
    createElement: vi.fn(() => new MockHTMLElement()),
  });
  vi.stubGlobal('performance', {
    now: () => mockTime,
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function flushRaf(ms = 50) {
  mockTime += ms;
  const callbacks = [...rafCallbacks];
  rafCallbacks = [];
  for (const { cb } of callbacks) {
    cb(mockTime);
  }
}

function createMockElement(): any {
  return new MockHTMLElement();
}

describe('easings', () => {
  it('linear returns t', () => {
    expect(easings.linear(0)).toBe(0);
    expect(easings.linear(0.5)).toBe(0.5);
    expect(easings.linear(1)).toBe(1);
  });

  it('easeIn is cubic', () => {
    expect(easings.easeIn(0)).toBe(0);
    expect(easings.easeIn(1)).toBe(1);
    expect(easings.easeIn(0.5)).toBeCloseTo(0.125, 5);
  });

  it('easeOut is inverse cubic', () => {
    expect(easings.easeOut(0)).toBe(0);
    expect(easings.easeOut(1)).toBe(1);
    expect(easings.easeOut(0.5)).toBeCloseTo(0.875, 5);
  });

  it('easeInOut transitions smoothly', () => {
    expect(easings.easeInOut(0)).toBe(0);
    expect(easings.easeInOut(1)).toBe(1);
    expect(easings.easeInOut(0.5)).toBeCloseTo(0.5, 5);
  });

  it('easeInQuad is quadratic', () => {
    expect(easings.easeInQuad(0)).toBe(0);
    expect(easings.easeInQuad(1)).toBe(1);
    expect(easings.easeInQuad(0.5)).toBeCloseTo(0.25, 5);
  });

  it('easeOutQuad', () => {
    expect(easings.easeOutQuad(0)).toBe(0);
    expect(easings.easeOutQuad(1)).toBe(1);
    expect(easings.easeOutQuad(0.5)).toBeCloseTo(0.75, 5);
  });

  it('easeInOutQuad', () => {
    expect(easings.easeInOutQuad(0)).toBe(0);
    expect(easings.easeInOutQuad(1)).toBe(1);
  });

  it('easeInBack', () => {
    expect(easings.easeInBack(0)).toBeCloseTo(0, 5);
    expect(easings.easeInBack(1)).toBeCloseTo(1, 5);
  });

  it('easeOutBack', () => {
    expect(easings.easeOutBack(0)).toBeCloseTo(0, 5);
    expect(easings.easeOutBack(1)).toBeCloseTo(1, 5);
  });

  it('easeInOutBack', () => {
    expect(easings.easeInOutBack(0)).toBeCloseTo(0, 5);
    expect(easings.easeInOutBack(1)).toBeCloseTo(1, 5);
  });

  it('easeOutElastic endpoints', () => {
    expect(easings.easeOutElastic(0)).toBe(0);
    expect(easings.easeOutElastic(1)).toBe(1);
  });

  it('easeOutBounce endpoints', () => {
    expect(easings.easeOutBounce(0)).toBe(0);
    expect(easings.easeOutBounce(1)).toBe(1);
  });
});

describe('animate', () => {
  it('creates an animation object', () => {
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 100 });
    expect(anim).toHaveProperty('play');
    expect(anim).toHaveProperty('pause');
    expect(anim).toHaveProperty('resume');
    expect(anim).toHaveProperty('cancel');
    expect(anim).toHaveProperty('reverse');
    expect(anim).toHaveProperty('finished');
    expect(anim).toHaveProperty('currentTime');
    expect(anim).toHaveProperty('progress');
    expect(anim).toHaveProperty('isPlaying');
  });

  it('starts not playing', () => {
    const el = createMockElement();
    const anim = animate(el, [], { duration: 100 });
    expect(anim.isPlaying).toBe(false);
  });

  it('play starts animation', () => {
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 100 });
    anim.play();
    expect(anim.isPlaying).toBe(true);
  });

  it('pause stops animation', () => {
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 100 });
    anim.play();
    anim.pause();
    expect(anim.isPlaying).toBe(false);
  });

  it('cancel resets animation', () => {
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 100 });
    anim.play();
    anim.cancel();
    expect(anim.isPlaying).toBe(false);
    expect(anim.currentTime).toBe(0);
  });

  it('calls onStart callback', () => {
    const onStart = vi.fn();
    const el = createMockElement();
    const anim = animate(el, [], { duration: 100, onStart });
    anim.play();
    expect(onStart).toHaveBeenCalled();
  });

  it('calls onComplete after duration', () => {
    const onComplete = vi.fn();
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 100, onComplete });
    anim.play();
    flushRaf(50);
    flushRaf(100);
    expect(onComplete).toHaveBeenCalled();
  });

  it('calls onUpdate with progress', () => {
    const onUpdate = vi.fn();
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 100, onUpdate });
    anim.play();
    flushRaf(50);
    expect(onUpdate).toHaveBeenCalled();
  });

  it('reverse toggles direction', () => {
    const el = createMockElement();
    const anim = animate(el, [], { duration: 100, direction: 'normal' });
    anim.reverse();
    anim.play();
    expect(anim.isPlaying).toBe(true);
  });

  it('initializes with delay', () => {
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 100, delay: 50 });
    anim.play();
    expect(anim.isPlaying).toBe(true);
  });

  it('supports iterations', () => {
    const onComplete = vi.fn();
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 50, iterations: 3, onComplete });
    anim.play();
    for (let i = 0; i < 15; i++) flushRaf(20);
    expect(onComplete).toHaveBeenCalled();
  });

  it('supports infinite iterations', () => {
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 50, iterations: Infinity });
    anim.play();
    for (let i = 0; i < 20; i++) flushRaf(20);
    expect(anim.isPlaying).toBe(true);
    anim.cancel();
  });

  it('supports string easing name', () => {
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 100, easing: 'easeIn' });
    anim.play();
    expect(anim.isPlaying).toBe(true);
  });

  it('supports custom easing function', () => {
    const custom = (t: number) => t;
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 100, easing: custom });
    anim.play();
    expect(anim.isPlaying).toBe(true);
  });

  it('progress is 0 at start', () => {
    const el = createMockElement();
    const anim = animate(el, [], { duration: 100 });
    expect(anim.progress).toBe(0);
  });

  it('finished returns a promise', () => {
    const el = createMockElement();
    const anim = animate(el, [], { duration: 100 });
    expect(anim.finished).toBeInstanceOf(Promise);
  });

  it('resume from paused state', () => {
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 100 });
    anim.play();
    anim.pause();
    anim.resume();
    expect(anim.isPlaying).toBe(true);
  });

  it('does not play if already playing', () => {
    const onStart = vi.fn();
    const el = createMockElement();
    const anim = animate(el, [], { duration: 100, onStart });
    anim.play();
    anim.play();
    expect(onStart).toHaveBeenCalledTimes(1);
  });

  it('does not resume if already playing', () => {
    const el = createMockElement();
    const anim = animate(el, [], { duration: 100 });
    anim.play();
    anim.resume();
    expect(anim.isPlaying).toBe(true);
  });

  it('supports alternate direction', () => {
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 50, direction: 'alternate', iterations: 2 });
    anim.play();
    for (let i = 0; i < 10; i++) flushRaf(20);
    expect(anim.isPlaying).toBe(false);
  });

  it('supports fill mode', () => {
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 100, fill: 'forwards' });
    anim.play();
    flushRaf(50);
    flushRaf(100);
    expect(anim.isPlaying).toBe(false);
  });

  it('supports reverse direction', () => {
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 100, direction: 'reverse' });
    anim.play();
    flushRaf(50);
    flushRaf(100);
    expect(anim.isPlaying).toBe(false);
  });

  it('supports alternate-reverse direction', () => {
    const el = createMockElement();
    const anim = animate(el, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 50, direction: 'alternate-reverse', iterations: 2 });
    anim.play();
    for (let i = 0; i < 10; i++) flushRaf(20);
    expect(anim.isPlaying).toBe(false);
  });

  it('supports non-numeric keyframe values', () => {
    const el = createMockElement();
    const anim = animate(el, [
      { color: 'red', offset: 0 },
      { color: 'blue', offset: 1 },
    ], { duration: 100 });
    anim.play();
    flushRaf(50);
    flushRaf(100);
    expect(anim.isPlaying).toBe(false);
  });
});

describe('animateValue', () => {
  it('creates animation with onUpdate', () => {
    const { animation, onUpdate } = animateValue(0, 100, { duration: 100 });
    const cb = vi.fn();
    onUpdate(cb);
    animation.play();
    flushRaf();
    expect(cb).toHaveBeenCalled();
  });

  it('interpolates values correctly', () => {
    const { animation, onUpdate } = animateValue(0, 100, { duration: 100 });
    let lastValue = 0;
    onUpdate((v) => { lastValue = v; });
    animation.play();
    flushRaf(50);
    flushRaf(100);
    expect(lastValue).toBeCloseTo(100, 0);
  });
});

describe('stagger', () => {
  it('creates animations for each element', () => {
    const elements = [
      createMockElement(),
      createMockElement(),
      createMockElement(),
    ];
    const animations = stagger(elements, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 100 });
    expect(animations).toHaveLength(3);
    animations.forEach((a) => a.cancel());
  });

  it('applies stagger delay', () => {
    const elements = [
      createMockElement(),
      createMockElement(),
    ];
    const animations = stagger(elements, [
      { opacity: '0', offset: 0 },
      { opacity: '1', offset: 1 },
    ], { duration: 100, staggerDelay: 50 });
    expect(animations).toHaveLength(2);
    animations.forEach((a) => a.cancel());
  });
});

describe('spring', () => {
  it('creates spring animation', () => {
    const el = createMockElement();
    const anim = spring(el, { duration: 600 });
    expect(anim).toHaveProperty('play');
    expect(anim).toHaveProperty('finished');
  });

  it('spring with custom stiffness and damping', () => {
    const el = createMockElement();
    const anim = spring(el, { stiffness: 200, damping: 15, duration: 400 });
    anim.play();
    expect(anim.isPlaying).toBe(true);
    anim.cancel();
  });

  it('spring with default config', () => {
    const el = createMockElement();
    const anim = spring(el);
    expect(anim).toHaveProperty('play');
  });
});

describe('fadeIn', () => {
  it('creates fade in animation and plays', () => {
    const el = createMockElement();
    const anim = fadeIn(el);
    expect(anim.isPlaying).toBe(true);
    anim.cancel();
  });

  it('fadeIn with custom config', () => {
    const el = createMockElement();
    const anim = fadeIn(el, { duration: 500 });
    expect(anim.isPlaying).toBe(true);
    anim.cancel();
  });
});

describe('fadeOut', () => {
  it('creates fade out animation and plays', () => {
    const el = createMockElement();
    const anim = fadeOut(el);
    expect(anim.isPlaying).toBe(true);
    anim.cancel();
  });

  it('fadeOut with custom config', () => {
    const el = createMockElement();
    const anim = fadeOut(el, { duration: 500 });
    expect(anim.isPlaying).toBe(true);
    anim.cancel();
  });
});

describe('slideIn', () => {
  it('slides in from up', () => {
    const el = createMockElement();
    const anim = slideIn(el, 'up');
    expect(anim.isPlaying).toBe(true);
    anim.cancel();
  });

  it('slides in from down', () => {
    const el = createMockElement();
    const anim = slideIn(el, 'down');
    expect(anim.isPlaying).toBe(true);
    anim.cancel();
  });

  it('slides in from left', () => {
    const el = createMockElement();
    const anim = slideIn(el, 'left');
    expect(anim.isPlaying).toBe(true);
    anim.cancel();
  });

  it('slides in from right', () => {
    const el = createMockElement();
    const anim = slideIn(el, 'right');
    expect(anim.isPlaying).toBe(true);
    anim.cancel();
  });

  it('slideIn with custom config', () => {
    const el = createMockElement();
    const anim = slideIn(el, 'up', { duration: 500 });
    expect(anim.isPlaying).toBe(true);
    anim.cancel();
  });

  it('slideIn default direction is up', () => {
    const el = createMockElement();
    const anim = slideIn(el);
    expect(anim.isPlaying).toBe(true);
    anim.cancel();
  });
});

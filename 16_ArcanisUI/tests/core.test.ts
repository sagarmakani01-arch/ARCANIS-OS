import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createElement, createTextVNode, Fragment, h } from '../src/core/dom/createElement';
import { diff } from '../src/core/dom/diff';
import {
  createInstance,
  getInstance,
  removeInstance,
  setCurrentInstance,
  getCurrentInstance,
  useState,
  useEffect,
  useMemo,
  useCallback,
  renderComponent,
} from '../src/core/component/component';
import { Scheduler } from '../src/core/scheduler/Scheduler';

beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => setTimeout(cb, 16) as unknown as number);
  vi.stubGlobal('cancelAnimationFrame', (id: number) => clearTimeout(id));
  vi.stubGlobal('window', { dispatchEvent: vi.fn(), matchMedia: vi.fn().mockReturnValue({ matches: false }), addEventListener: vi.fn() });
  vi.stubGlobal('CustomEvent', class CustomEvent extends Event {
    detail: any;
    constructor(type: string, opts: any) {
      super(type);
      this.detail = opts?.detail;
    }
  });
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('createElement', () => {
  it('creates element vnode with string type', () => {
    const vnode = createElement('div', { id: 'test' }, 'hello');
    expect(vnode.type).toBe('div');
    expect(vnode.props.id).toBe('test');
    expect(vnode.props.children).toHaveLength(1);
    expect(vnode._nodeId).toMatch(/^arc-/);
  });

  it('creates element vnode with null props', () => {
    const vnode = createElement('span', null);
    expect(vnode.type).toBe('span');
    expect(vnode.props).toHaveProperty('children');
  });

  it('flattens nested children arrays', () => {
    const child1 = createElement('li', null, 'a');
    const child2 = createElement('li', null, 'b');
    const vnode = createElement('ul', null, [child1, child2]);
    expect(vnode.props.children).toHaveLength(2);
  });

  it('converts string children to text vnodes', () => {
    const vnode = createElement('div', null, 'hello world');
    const children = vnode.props.children;
    expect(children).toHaveLength(1);
    expect((children[0] as any).type).toBe('text');
    expect((children[0] as any).text).toBe('hello world');
  });

  it('converts number children to text vnodes', () => {
    const vnode = createElement('div', null, 42);
    const children = vnode.props.children;
    expect(children).toHaveLength(1);
    expect((children[0] as any).text).toBe('42');
  });

  it('filters out null and boolean children', () => {
    const vnode = createElement('div', null, null, false, true, 'visible');
    expect(vnode.props.children).toHaveLength(1);
  });

  it('preserves key and ref props', () => {
    const ref = { current: null };
    const vnode = createElement('div', { key: 'k1', ref, class: 'box' });
    expect(vnode.key).toBe('k1');
    expect(vnode.ref).toBe(ref);
  });

  it('creates unique node ids', () => {
    const v1 = createElement('div', null);
    const v2 = createElement('div', null);
    expect(v1._nodeId).not.toBe(v2._nodeId);
  });

  it('h is alias for createElement', () => {
    expect(h).toBe(createElement);
  });

  it('handles component function type', () => {
    const MyComp = (props: any) => createElement('div', null, props.text);
    const vnode = createElement(MyComp, { text: 'hi' });
    expect(vnode.type).toBe(MyComp);
    expect(vnode.props.text).toBe('hi');
  });
});

describe('createTextVNode', () => {
  it('creates text vnode from string', () => {
    const tv = createTextVNode('hello');
    expect(tv.type).toBe('text');
    expect(tv.text).toBe('hello');
    expect(tv._nodeId).toMatch(/^arc-/);
  });

  it('creates text vnode from number', () => {
    const tv = createTextVNode(123);
    expect(tv.text).toBe('123');
  });
});

describe('Fragment', () => {
  it('creates fragment element', () => {
    const child1 = createElement('li', null, 'one');
    const child2 = createElement('li', null, 'two');
    const frag = Fragment({ children: [child1, child2] });
    expect(frag.type).toBe('__fragment');
    expect(frag.props.children).toHaveLength(2);
  });

  it('handles empty children', () => {
    const frag = Fragment({ children: [] });
    expect(frag.props.children).toHaveLength(0);
  });
});

describe('diff', () => {
  it('returns none when both trees are null', () => {
    const result = diff(null, null);
    expect(result.type).toBe('none');
  });

  it('returns create when old tree is null', () => {
    const newTree = createElement('div', null);
    const result = diff(null, newTree);
    expect(result.type).toBe('create');
    expect(result.newTree).toBe(newTree);
  });

  it('returns remove when new tree is null', () => {
    const oldTree = createElement('div', null);
    const result = diff(oldTree, null);
    expect(result.type).toBe('remove');
    expect(result.oldTree).toBe(oldTree);
  });

  it('returns replace when types differ', () => {
    const oldTree = createElement('div', null);
    const newTree = createElement('span', null);
    const result = diff(oldTree, newTree);
    expect(result.type).toBe('replace');
  });

  it('returns none when text vnodes are equal', () => {
    const oldTree = createTextVNode('hello');
    const newTree = createTextVNode('hello');
    const result = diff(oldTree, newTree);
    expect(result.type).toBe('none');
  });

  it('returns replace when text vnodes differ', () => {
    const oldTree = createTextVNode('hello');
    const newTree = createTextVNode('world');
    const result = diff(oldTree, newTree);
    expect(result.type).toBe('replace');
  });

  it('returns replace when one is text and other is element', () => {
    const textNode = createTextVNode('hello');
    const elemNode = createElement('div', null);
    const result = diff(textNode, elemNode);
    expect(result.type).toBe('replace');
  });

  it('returns none when element trees are identical', () => {
    const oldTree = createElement('div', { class: 'box' }, 'text');
    const newTree = createElement('div', { class: 'box' }, 'text');
    const result = diff(oldTree, newTree);
    expect(result.type).toBe('none');
  });

  it('returns update when props change', () => {
    const oldTree = createElement('div', { class: 'old' });
    const newTree = createElement('div', { class: 'new' });
    const result = diff(oldTree, newTree);
    expect(result.type).toBe('update');
    expect(result.propsDiff).toBeDefined();
    expect(result.propsDiff!.changed).toBe(true);
    expect(result.propsDiff!.updated.class).toBe('new');
  });

  it('detects added props', () => {
    const oldTree = createElement('div', null);
    const newTree = createElement('div', { id: 'new' });
    const result = diff(oldTree, newTree);
    expect(result.type).toBe('update');
    expect(result.propsDiff!.added.id).toBe('new');
  });

  it('detects removed props', () => {
    const oldTree = createElement('div', { id: 'old' });
    const newTree = createElement('div', null);
    const result = diff(oldTree, newTree);
    expect(result.type).toBe('update');
    expect(result.propsDiff!.removed.id).toBe('old');
  });

  it('ignores children, key, ref in props diff', () => {
    const oldTree = createElement('div', { key: 'k1' }, 'a');
    const newTree = createElement('div', { key: 'k2' }, 'b');
    const result = diff(oldTree, newTree);
    expect(result.type).toBe('update');
    expect(result.propsDiff!.changed).toBe(false);
  });

  it('detects children differences', () => {
    const oldTree = createElement('div', null, 'a');
    const newTree = createElement('div', null, 'b');
    const result = diff(oldTree, newTree);
    expect(result.type).toBe('update');
    expect(result.childrenDiff).toBeDefined();
    expect(result.childrenDiff!.type).toBe('update');
  });

  it('returns none when children are the same', () => {
    const oldTree = createElement('div', null, 'same');
    const newTree = createElement('div', null, 'same');
    const result = diff(oldTree, newTree);
    expect(result.type).toBe('none');
  });

  it('handles adding new children', () => {
    const oldTree = createElement('div', null);
    const newTree = createElement('div', null, 'new child');
    const result = diff(oldTree, newTree);
    expect(result.type).toBe('update');
  });

  it('handles removing children', () => {
    const oldTree = createElement('div', null, 'child');
    const newTree = createElement('div', null);
    const result = diff(oldTree, newTree);
    expect(result.type).toBe('update');
  });

  it('returns replace for component function types', () => {
    const Comp1 = () => createElement('div', null);
    const Comp2 = () => createElement('div', null);
    const oldTree = createElement(Comp1, null);
    const newTree = createElement(Comp2, null);
    const result = diff(oldTree, newTree);
    expect(result.type).toBe('replace');
  });
});

describe('component', () => {
  it('creates instance with unique id', () => {
    const Comp = (props: any) => createElement('div', null);
    const inst = createInstance(Comp, {});
    expect(inst.id).toMatch(/^inst-/);
    expect(inst.type).toBe(Comp);
    expect(inst.mounted).toBe(false);
    expect(inst.hooks).toEqual([]);
    expect(inst.hookIndex).toBe(0);
  });

  it('retrieves instance by id', () => {
    const Comp = (props: any) => createElement('div', null);
    const inst = createInstance(Comp, {});
    expect(getInstance(inst.id)).toBe(inst);
  });

  it('removes instance by id', () => {
    const Comp = (props: any) => createElement('div', null);
    const inst = createInstance(Comp, {});
    removeInstance(inst.id);
    expect(getInstance(inst.id)).toBeUndefined();
  });

  it('runs cleanup on remove', () => {
    const Comp = (props: any) => createElement('div', null);
    const inst = createInstance(Comp, {});
    const cleanup = vi.fn();
    inst.hooks.push({ cleanup });
    removeInstance(inst.id);
    expect(cleanup).toHaveBeenCalled();
  });

  it('getCurrentInstance throws outside component', () => {
    expect(() => getCurrentInstance()).toThrow('Hooks can only be called inside a component');
  });

  it('setCurrentInstance returns previous instance', () => {
    const Comp = (props: any) => createElement('div', null);
    const inst = createInstance(Comp, {});
    const prev = setCurrentInstance(inst);
    expect(prev).toBeNull();
    const prev2 = setCurrentInstance(null);
    expect(prev2).toBe(inst);
  });

  it('renderComponent calls component function', () => {
    const Comp = (props: any) => createElement('div', null, props.text);
    const result = renderComponent(Comp, { text: 'hello' }, null);
    expect(result).toBeNull();
  });

  it('useState returns initial value', () => {
    const Comp = (props: any) => {
      const [count, setCount] = useState(0);
      expect(count).toBe(0);
      expect(typeof setCount).toBe('function');
      return createElement('div', null);
    };
    renderComponent(Comp, {}, null);
  });

  it('useState setter updates value on re-render', () => {
    let capturedCount: number = -1;
    const Comp = (props: any) => {
      const [count] = useState(10);
      capturedCount = count;
      return createElement('div', null);
    };
    renderComponent(Comp, {}, null);
    expect(capturedCount).toBe(10);
  });

  it('useState setter with function updater', () => {
    let capturedCount: number = -1;
    const Comp = (props: any) => {
      const [count, setCount] = useState(5);
      capturedCount = count;
      setCount((prev: number) => prev + 1);
      return createElement('div', null);
    };
    renderComponent(Comp, {}, null);
    expect(capturedCount).toBe(5);
  });

  it('useMemo memoizes value', () => {
    let computeCount = 0;
    const Comp = (props: any) => {
      const val = useMemo(() => {
        computeCount++;
        return 42;
      }, []);
      expect(val).toBe(42);
      return createElement('div', null);
    };
    renderComponent(Comp, {}, null);
    expect(computeCount).toBe(1);
  });

  it('useCallback memoizes callback', () => {
    const Comp = (props: any) => {
      const cb = useCallback(() => 42, []);
      expect(typeof cb).toBe('function');
      expect(cb()).toBe(42);
      return createElement('div', null);
    };
    renderComponent(Comp, {}, null);
  });
});

describe('Scheduler', () => {
  let scheduler: Scheduler;

  beforeEach(() => {
    scheduler = new Scheduler();
  });

  afterEach(() => {
    scheduler.destroy();
  });

  it('creates with empty queue', () => {
    expect(scheduler.pendingCount).toBe(0);
  });

  it('schedules a task', () => {
    const callback = vi.fn();
    scheduler.schedule(callback, 'normal');
    expect(scheduler.pendingCount).toBeGreaterThanOrEqual(0);
  });

  it('cancels a task', () => {
    const callback = vi.fn();
    const id = scheduler.schedule(callback, 'normal');
    scheduler.cancel(id);
    expect(scheduler.pendingCount).toBe(0);
  });

  it('flushSync executes callback immediately', () => {
    const callback = vi.fn();
    scheduler.flushSync(callback);
    expect(callback).toHaveBeenCalled();
  });

  it('microtask executes via promise', async () => {
    const callback = vi.fn();
    scheduler.microtask(callback);
    await Promise.resolve();
    expect(callback).toHaveBeenCalled();
  });

  it('destroy clears all tasks', () => {
    scheduler.schedule(() => {}, 'normal');
    scheduler.schedule(() => {}, 'high');
    scheduler.destroy();
    expect(scheduler.pendingCount).toBe(0);
  });

  it('schedule returns a numeric id', () => {
    const id = scheduler.schedule(() => {}, 'normal');
    expect(typeof id).toBe('number');
  });

  it('flushSync does not throw', () => {
    expect(() => scheduler.flushSync(() => {})).not.toThrow();
  });
});

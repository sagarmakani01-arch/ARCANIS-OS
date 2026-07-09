import type { Props, VNode, ComponentInstance, HookState } from '../../types';
import { scheduler } from '../scheduler/Scheduler';

const instances = new Map<string, ComponentInstance>();
let currentInstance: ComponentInstance | null = null;

export function createInstance(type: (props: Props) => VNode, props: Props): ComponentInstance {
  const instance: ComponentInstance = {
    id: `inst-${Math.random().toString(36).slice(2, 9)}`,
    type,
    props,
    state: {},
    mounted: false,
    dom: null,
    children: [],
    hooks: [],
    hookIndex: 0,
  };
  instances.set(instance.id, instance);
  return instance;
}

export function getInstance(id: string): ComponentInstance | undefined {
  return instances.get(id);
}

export function removeInstance(id: string): void {
  const inst = instances.get(id);
  if (inst) {
    inst.hooks.forEach((hook) => {
      if (hook.cleanup) hook.cleanup();
    });
    instances.delete(id);
  }
}

export function setCurrentInstance(instance: ComponentInstance | null): ComponentInstance | null {
  const prev = currentInstance;
  currentInstance = instance;
  return prev;
}

export function getCurrentInstance(): ComponentInstance {
  if (!currentInstance) {
    throw new Error('Hooks can only be called inside a component');
  }
  return currentInstance;
}

export function useState<T>(initialValue: T): [T, (newValue: T | ((prev: T) => T)) => void] {
  const instance = getCurrentInstance();
  const hookIndex = instance.hookIndex++;

  if (hookIndex >= instance.hooks.length) {
    instance.hooks.push({ value: initialValue });
  }

  const hook = instance.hooks[hookIndex];
  const setState = (newValue: T | ((prev: T) => T)) => {
    const prevValue = hook.value as T;
    hook.value = typeof newValue === 'function' ? (newValue as (prev: T) => T)(prevValue) : newValue;
    if (prevValue !== hook.value) {
      scheduler.schedule(() => rerenderInstance(instance.id), 'high');
    }
  };

  return [hook.value as T, setState];
}

export function useEffect(callback: () => void | (() => void), deps?: unknown[]): void {
  const instance = getCurrentInstance();
  const hookIndex = instance.hookIndex++;

  if (hookIndex >= instance.hooks.length) {
    instance.hooks.push({ deps, value: undefined, cleanup: undefined });
  }

  const hook = instance.hooks[hookIndex];

  if (!deps || !hook.deps || hook.deps.length !== deps.length || hook.deps.some((d, i) => d !== deps[i])) {
    if (hook.cleanup) hook.cleanup();
    const cleanup = callback();
    hook.cleanup = typeof cleanup === 'function' ? cleanup : undefined;
    hook.deps = deps;
  }
}

export function useMemo<T>(factory: () => T, deps: unknown[]): T {
  const instance = getCurrentInstance();
  const hookIndex = instance.hookIndex++;

  if (hookIndex >= instance.hooks.length) {
    instance.hooks.push({ value: factory(), deps });
    return instance.hooks[hookIndex].value as T;
  }

  const hook = instance.hooks[hookIndex];
  if (!hook.deps || hook.deps.some((d, i) => d !== deps[i])) {
    hook.value = factory();
    hook.deps = deps;
  }

  return hook.value as T;
}

export function useCallback<T extends (...args: unknown[]) => unknown>(callback: T, deps: unknown[]): T {
  return useMemo(() => callback, deps);
}

function rerenderInstance(instanceId: string): void {
  const event = new CustomEvent('arcanis:rerender', { detail: { instanceId } });
  window.dispatchEvent(event);
}

export function renderComponent(
  type: (props: Props) => VNode,
  props: Props,
  dom: Node | null
): Node | null {
  const instance = createInstance(type, props);
  const prevInstance = currentInstance;

  setCurrentInstance(instance);
  instance.hookIndex = 0;

  const result = type(props);

  setCurrentInstance(prevInstance);
  instance.mounted = true;

  return dom;
}

export { instances };

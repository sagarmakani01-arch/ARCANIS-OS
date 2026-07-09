import type { VNode, RenderOptions, Props } from '../../types';
import { DOMRenderer } from '../renderer/DOMRenderer';
import { scheduler } from '../scheduler/Scheduler';
import { instances, setCurrentInstance, removeInstance, createInstance } from '../component/component';

export interface App {
  render(vnode: VNode): void;
  mount(container: Element): void;
  unmount(): void;
  update(newVNode: VNode): void;
}

export function createApp(rootComponent: (props: Props) => VNode, rootProps: Props = {}): App {
  const renderer = new DOMRenderer();
  let rootVNode: VNode | null = null;
  let container: Element | null = null;

  const app: App = {
    render(vnode: VNode) {
      rootVNode = vnode;
      if (container) {
        scheduler.schedule(() => {
          renderer.render(vnode, container!);
        }, 'high');
      }
    },

    mount(mountContainer: Element) {
      container = mountContainer;
      if (rootVNode) {
        renderer.render(rootVNode, container);
      } else {
        const vnode = rootComponent(rootProps);
        rootVNode = vnode;
        renderer.render(vnode, container);
      }
    },

    unmount() {
      if (container) {
        container.innerHTML = '';
        instances.forEach((_, id) => removeInstance(id));
        container = null;
        rootVNode = null;
      }
    },

    update(newVNode: VNode) {
      rootVNode = newVNode;
      if (container && rootVNode) {
        scheduler.schedule(() => {
          const firstChild = container!.firstChild;
          if (firstChild) {
            renderer.updateDOM(firstChild, newVNode);
          } else {
            renderer.render(newVNode, container!);
          }
        }, 'normal');
      }
    },
  };

  window.addEventListener('arcanis:rerender', ((e: CustomEvent) => {
    const { instanceId } = e.detail;
    const instance = instances.get(instanceId);
    if (instance) {
      const prevInstance = setCurrentInstance(instance);
      instance.hookIndex = 0;
      const newResult = (instance.type as (props: Props) => VNode)(instance.props);
      setCurrentInstance(prevInstance);
    }
  }) as EventListener);

  return app;
}

export function render(vnode: VNode, container: Element): void {
  const renderer = new DOMRenderer();
  scheduler.schedule(() => {
    renderer.render(vnode, container);
  }, 'high');
}

export function mount(container: Element): App {
  const noop = () => ({}) as VNode;
  return createApp(noop);
}

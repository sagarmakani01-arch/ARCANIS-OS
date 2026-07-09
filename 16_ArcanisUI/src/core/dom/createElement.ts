import type { VNode, TextVNode, Props, VNodeChild, ComponentFunction } from '../../types';

let nodeIdCounter = 0;
const nodeId = () => `arc-${++nodeIdCounter}`;

export function createElement(
  type: string | ComponentFunction,
  props: Props | null,
  ...children: VNodeChild[]
): VNode {
  const flatChildren = flattenChildren(children);
  const normalizedProps: Props = { ...props, children: flatChildren };
  return { type, props: normalizedProps, key: props?.key, ref: props?.ref, _nodeId: nodeId() };
}

export function createTextVNode(text: string | number): TextVNode {
  return { type: 'text', text: String(text), _nodeId: nodeId() };
}

function flattenChildren(children: VNodeChild[]): VNodeChild[] {
  const result: VNodeChild[] = [];
  for (const child of children) {
    if (Array.isArray(child)) {
      for (const item of child) {
        if (item != null && typeof item !== 'boolean') {
          if (typeof item === 'string' || typeof item === 'number') {
            result.push(createTextVNode(item));
          } else if (Array.isArray(item)) {
            result.push(...flattenChildren(item));
          } else {
            result.push(item);
          }
        }
      }
    } else if (child != null && typeof child !== 'boolean') {
      if (typeof child === 'string' || typeof child === 'number') {
        result.push(createTextVNode(child));
      } else {
        result.push(child);
      }
    }
  }
  return result;
}

export function Fragment({ children }: Props): VNode {
  return createElement('__fragment', null, ...((children as VNodeChild[]) || []));
}

export { createElement as h };

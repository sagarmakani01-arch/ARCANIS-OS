import type { VNode, TextVNode, Props, VNodeChild } from '../../types';

export class DOMRenderer {
  private eventDelegation: Map<string, Map<Element, (e: Event) => void>> = new Map();

  render(vnode: VNode | TextVNode, container: Element): Node {
    const dom = this.createDOM(vnode);
    container.appendChild(dom);
    return dom;
  }

  createDOM(vnode: VNode | TextVNode): Node {
    if (vnode.type === 'text') {
      return document.createTextNode((vnode as TextVNode).text);
    }

    const node = vnode as VNode;

    if (typeof node.type === 'function') {
      return document.createTextNode('');
    }

    const element = document.createElement(node.type);
    this.applyProps(element, node.props);
    this.bindEvents(element, node.props);

    const children = (node.props.children || []) as VNodeChild[];
    for (const child of children) {
      if (child != null && typeof child !== 'boolean') {
        if (typeof child === 'string' || typeof child === 'number') {
          element.appendChild(document.createTextNode(String(child)));
        } else {
          const childDom = this.createDOM(child as VNode | TextVNode);
          element.appendChild(childDom);
        }
      }
    }

    return element;
  }

  updateDOM(dom: Node, newVNode: VNode | TextVNode): Node {
    if (newVNode.type === 'text') {
      if (dom.nodeType === Node.TEXT_NODE) {
        dom.textContent = (newVNode as TextVNode).text;
        return dom;
      }
      const newDom = document.createTextNode((newVNode as TextVNode).text);
      dom.parentNode?.replaceChild(newDom, dom);
      return newDom;
    }

    const node = newVNode as VNode;

    if (typeof node.type === 'function') {
      return dom;
    }

    if (dom.nodeType !== Node.ELEMENT_NODE || (dom as Element).tagName.toLowerCase() !== node.type) {
      const newDom = this.createDOM(node);
      dom.parentNode?.replaceChild(newDom, dom);
      return newDom;
    }

    const element = dom as Element;
    this.applyProps(element, node.props);
    this.bindEvents(element, node.props);

    const children = (node.props.children || []) as VNodeChild[];
    this.updateChildren(element, children);

    return element;
  }

  private updateChildren(element: Element, newChildren: VNodeChild[]): void {
    const existingNodes = Array.from(element.childNodes);
    const maxLen = Math.max(existingNodes.length, newChildren.length);

    for (let i = 0; i < maxLen; i++) {
      const existing = existingNodes[i];
      const newChild = newChildren[i];

      if (newChild == null || typeof newChild === 'boolean') {
        if (existing) element.removeChild(existing);
        continue;
      }

      if (!existing) {
        if (typeof newChild === 'string' || typeof newChild === 'number') {
          element.appendChild(document.createTextNode(String(newChild)));
        } else {
          const newDom = this.createDOM(newChild as VNode | TextVNode);
          element.appendChild(newDom);
        }
        continue;
      }

      if (typeof newChild === 'string' || typeof newChild === 'number') {
        existing.textContent = String(newChild);
      } else {
        this.updateDOM(existing, newChild as VNode | TextVNode);
      }
    }
  }

  private applyProps(element: Element, props: Props): void {
    for (const [key, value] of Object.entries(props)) {
      if (key === 'children' || key === 'key' || key === 'ref' || key === 'className') continue;

      if (key === 'style' && typeof value === 'object' && value !== null) {
        Object.assign((element as HTMLElement).style, value);
      } else if (key.startsWith('on')) {
        continue;
      } else if (typeof value === 'boolean') {
        if (value) {
          element.setAttribute(key, '');
        } else {
          element.removeAttribute(key);
        }
      } else if (value != null && typeof value !== 'function') {
        element.setAttribute(key, String(value));
      }
    }

    if (props.className) {
      if (typeof props.className === 'string') {
        element.className = props.className;
      } else if (Array.isArray(props.className)) {
        element.className = props.className.filter(Boolean).join(' ');
      }
    }
  }

  private bindEvents(element: Element, props: Props): void {
    for (const [key, value] of Object.entries(props)) {
      if (key.startsWith('on') && typeof value === 'function') {
        const eventName = key.slice(2).toLowerCase();
        element.addEventListener(eventName, value as EventListener);
      }
    }
  }

  removeDOM(dom: Node): void {
    dom.parentNode?.removeChild(dom);
  }
}

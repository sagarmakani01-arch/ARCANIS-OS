export type NodeType = 'element' | 'text' | 'component' | 'fragment';

export type PropValue = string | number | boolean | null | undefined | ((e: Event) => void) | Record<string, unknown>;

export interface Props {
  children?: VNodeChild[];
  className?: string | string[];
  style?: string | Record<string, string>;
  key?: string | number;
  ref?: RefObject;
  [key: string]: unknown;
}

export interface VNode {
  type: string | ComponentFunction;
  props: Props;
  key?: string | number;
  ref?: RefObject;
  _nodeId?: string;
}

export interface TextVNode {
  type: 'text';
  text: string;
  _nodeId?: string;
}

export type VNodeChild = VNode | TextVNode | string | number | boolean | null | undefined | VNode[];

export type ComponentFunction<T extends Props = Props> = (props: T) => VNode;

export interface RefObject<T = unknown> {
  current: T | null;
}

export interface ComponentInstance {
  id: string;
  type: ComponentFunction;
  props: Props;
  state: Record<string, unknown>;
  mounted: boolean;
  dom: Node | null;
  children: ComponentInstance[];
  hooks: HookState[];
  hookIndex: number;
}

export interface HookState {
  deps?: unknown[];
  value?: unknown;
  cleanup?: () => void;
}

export interface RenderOptions {
  container: Element;
  hydrate?: boolean;
}

export interface reconcilerResult {
  created: Node[];
  updated: Node[];
  removed: Node[];
}

export type EventCallback = (event: Event) => void;

export interface EventBinding {
  event: string;
  callback: EventCallback;
  element: Element;
}

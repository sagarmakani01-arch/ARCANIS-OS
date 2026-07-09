import type { VNode, TextVNode, VNodeChild } from '../../types';

export function diff(oldTree: VNode | TextVNode | null, newTree: VNode | TextVNode | null): DiffResult {
  if (!oldTree && !newTree) return { type: 'none' };
  if (!oldTree) return { type: 'create', newTree };
  if (!newTree) return { type: 'remove', oldTree };

  const isOldText = oldTree.type === 'text';
  const isNewText = newTree.type === 'text';

  if (isOldText && isNewText) {
    if ((oldTree as TextVNode).text === (newTree as TextVNode).text) {
      return { type: 'none' };
    }
    return { type: 'replace', oldTree, newTree };
  }

  if (isOldText || isNewText) {
    return { type: 'replace', oldTree, newTree };
  }

  const oldVNode = oldTree as VNode;
  const newVNode = newTree as VNode;

  if (oldVNode.type !== newVNode.type) {
    return { type: 'replace', oldTree, newTree };
  }

  if (typeof oldVNode.type === 'string' && typeof newVNode.type === 'string') {
    const propsDiff = diffProps(oldVNode.props, newVNode.props);
    const childrenDiff = diffChildren(
      (oldVNode.props.children || []) as VNodeChild[],
      (newVNode.props.children || []) as VNodeChild[]
    );

    if (!propsDiff.changed && childrenDiff.type === 'none') {
      return { type: 'none' };
    }

    return {
      type: 'update',
      oldTree,
      newTree,
      propsDiff,
      childrenDiff,
    };
  }

  return { type: 'replace', oldTree, newTree };
}

function diffProps(
  oldProps: Record<string, unknown>,
  newProps: Record<string, unknown>
): PropsDiffResult {
  const result: PropsDiffResult = { changed: false, added: {}, removed: {}, updated: {} };

  for (const key in oldProps) {
    if (key === 'children' || key === 'key' || key === 'ref') continue;
    if (!(key in newProps)) {
      result.removed[key] = oldProps[key];
      result.changed = true;
    } else if (oldProps[key] !== newProps[key]) {
      result.updated[key] = newProps[key];
      result.changed = true;
    }
  }

  for (const key in newProps) {
    if (key === 'children' || key === 'key' || key === 'ref') continue;
    if (!(key in oldProps)) {
      result.added[key] = newProps[key];
      result.changed = true;
    }
  }

  return result;
}

function diffChildren(
  oldChildren: VNodeChild[],
  newChildren: VNodeChild[]
): ChildrenDiffResult {
  const maxLen = Math.max(oldChildren.length, newChildren.length);
  const patches: DiffResult[] = [];
  let changed = false;

  for (let i = 0; i < maxLen; i++) {
    const oldChild = oldChildren[i] ?? null;
    const newChild = newChildren[i] ?? null;
    const patch = diff(oldChild as VNode | TextVNode | null, newChild as VNode | TextVNode | null);
    patches.push(patch);
    if (patch.type !== 'none') changed = true;
  }

  return { type: changed ? 'update' : 'none', patches };
}

export interface DiffResult {
  type: 'none' | 'create' | 'remove' | 'replace' | 'update';
  oldTree?: VNode | TextVNode;
  newTree?: VNode | TextVNode;
  propsDiff?: PropsDiffResult;
  childrenDiff?: ChildrenDiffResult;
}

interface PropsDiffResult {
  changed: boolean;
  added: Record<string, unknown>;
  removed: Record<string, unknown>;
  updated: Record<string, unknown>;
}

interface ChildrenDiffResult {
  type: 'none' | 'update';
  patches: DiffResult[];
}

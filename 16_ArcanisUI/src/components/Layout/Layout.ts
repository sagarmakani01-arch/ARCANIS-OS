import type { VNode } from '../../types';
import { createElement as h } from '../../core/dom/createElement';

export type StackDirection = 'horizontal' | 'vertical';
export type StackAlign = 'start' | 'center' | 'end' | 'stretch' | 'baseline';
export type StackJustify = 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly';
export type StackGap = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';

export interface StackProps {
  direction?: StackDirection;
  align?: StackAlign;
  justify?: StackJustify;
  gap?: StackGap;
  wrap?: boolean;
  className?: string;
  children?: VNode | VNode[];
}

const gapStyles: Record<StackGap, string> = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  '2xl': '48px',
};

const alignStyles: Record<StackAlign, string> = {
  start: 'flex-start',
  center: 'center',
  end: 'flex-end',
  stretch: 'stretch',
  baseline: 'baseline',
};

const justifyStyles: Record<StackJustify, string> = {
  start: 'flex-start',
  center: 'center',
  end: 'flex-end',
  between: 'space-between',
  around: 'space-around',
  evenly: 'space-evenly',
};

export function Stack(props: StackProps): VNode {
  const {
    direction = 'vertical',
    align = 'stretch',
    justify = 'start',
    gap = 'md',
    wrap = false,
    className = '',
    children,
  } = props;

  const style = `display:flex;flex-direction:${direction === 'horizontal' ? 'row' : 'column'};align-items:${alignStyles[align]};justify-content:${justifyStyles[justify]};gap:${gapStyles[gap]};${wrap ? 'flex-wrap:wrap;' : ''}`;

  return h('div', {
    className: `arcanis-stack arcanis-stack--${direction} ${className}`.trim(),
    style,
  }, children);
}

export function Flex(props: StackProps & { inline?: boolean }): VNode {
  const {
    align = 'stretch',
    justify = 'start',
    gap = 'md',
    wrap = false,
    inline = false,
    className = '',
    children,
  } = props;

  const style = `display:${inline ? 'inline-flex' : 'flex'};align-items:${alignStyles[align]};justify-content:${justifyStyles[justify]};gap:${gapStyles[gap]};${wrap ? 'flex-wrap:wrap;' : ''}`;

  return h('div', {
    className: `arcanis-flex ${className}`.trim(),
    style,
  }, children);
}

export function Grid(props: {
  columns?: number;
  rows?: number;
  gap?: StackGap;
  className?: string;
  children?: VNode | VNode[];
}): VNode {
  const {
    columns = 1,
    rows,
    gap = 'md',
    className = '',
    children,
  } = props;

  const style = `display:grid;grid-template-columns:repeat(${columns},1fr);${rows ? `grid-template-rows:repeat(${rows},1fr);` : ''}gap:${gapStyles[gap]};`;

  return h('div', {
    className: `arcanis-grid ${className}`.trim(),
    style,
  }, children);
}

export function Center(props: { className?: string; children?: VNode | VNode[] }): VNode {
  const { className = '', children } = props;
  return h('div', {
    className: `arcanis-center ${className}`.trim(),
    style: 'display:flex;align-items:center;justify-content:center;',
  }, children);
}

export function Spacer(props: { size?: StackGap; className?: string }): VNode {
  const { size = 'md', className = '' } = props;
  return h('div', {
    className: `arcanis-spacer ${className}`.trim(),
    style: `width:${gapStyles[size]};height:${gapStyles[size]};`,
  });
}

export function Divider(props: { orientation?: 'horizontal' | 'vertical'; className?: string }): VNode {
  const { orientation = 'horizontal', className = '' } = props;
  const style = orientation === 'horizontal'
    ? 'width:100%;height:1px;background:var(--arcanis-color-border);'
    : 'width:1px;height:100%;background:var(--arcanis-color-border);';

  return h('div', {
    className: `arcanis-divider arcanis-divider--${orientation} ${className}`.trim(),
    style,
    role: 'separator',
  });
}

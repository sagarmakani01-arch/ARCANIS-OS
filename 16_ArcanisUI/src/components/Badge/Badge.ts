import type { VNode } from '../../types';
import { createElement as h } from '../../core/dom/createElement';

export type BadgeVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'outline';
export type BadgeSize = 'sm' | 'md' | 'lg';

export interface BadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  className?: string;
  children?: VNode | VNode[] | string;
}

const variantStyles: Record<BadgeVariant, string> = {
  primary: 'background:var(--arcanis-color-primary);color:white;',
  secondary: 'background:var(--arcanis-color-secondary);color:white;',
  success: 'background:var(--arcanis-color-success);color:white;',
  warning: 'background:var(--arcanis-color-warning);color:white;',
  error: 'background:var(--arcanis-color-error);color:white;',
  info: 'background:var(--arcanis-color-info);color:white;',
  outline: 'background:transparent;border:1px solid var(--arcanis-color-border);color:var(--arcanis-color-text);',
};

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'padding:2px 6px;font-size:10px;',
  md: 'padding:3px 8px;font-size:12px;',
  lg: 'padding:4px 10px;font-size:14px;',
};

export function Badge(props: BadgeProps): VNode {
  const { variant = 'primary', size = 'md', dot = false, className = '', children } = props;

  const style = `display:inline-flex;align-items:center;gap:4px;border-radius:var(--arcanis-radius-full);font-weight:var(--arcanis-font-weight-medium);line-height:1;${variantStyles[variant]}${sizeStyles[size]}`;

  const dotEl = dot ? h('span', {
    style: 'width:6px;height:6px;border-radius:50%;background:currentColor;',
    className: 'arcanis-badge-dot',
  }) : null;

  return h('span', {
    className: `arcanis-badge arcanis-badge--${variant} ${className}`.trim(),
    style,
  }, dotEl, children);
}

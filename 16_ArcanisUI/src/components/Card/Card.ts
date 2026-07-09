import type { VNode } from '../../types';
import { createElement as h } from '../../core/dom/createElement';

export type CardVariant = 'elevated' | 'outlined' | 'filled';
export type CardPadding = 'none' | 'sm' | 'md' | 'lg';

export interface CardProps {
  variant?: CardVariant;
  padding?: CardPadding;
  hoverable?: boolean;
  selected?: boolean;
  onClick?: (event: MouseEvent) => void;
  className?: string;
  children?: VNode | VNode[];
}

const variantStyles: Record<CardVariant, string> = {
  elevated: 'background:var(--arcanis-color-surface);box-shadow:var(--arcanis-shadow-md);border:none;',
  outlined: 'background:var(--arcanis-color-surface);box-shadow:none;border:1px solid var(--arcanis-color-border);',
  filled: 'background:var(--arcanis-color-background);box-shadow:none;border:none;',
};

const paddingStyles: Record<CardPadding, string> = {
  none: 'padding:0;',
  sm: 'padding:12px;',
  md: 'padding:16px;',
  lg: 'padding:24px;',
};

export function Card(props: CardProps): VNode {
  const {
    variant = 'elevated',
    padding = 'md',
    hoverable = false,
    selected = false,
    onClick,
    className = '',
    children,
  } = props;

  const baseStyle = 'border-radius:var(--arcanis-radius-lg);transition:all var(--arcanis-transition-fast);';

  const hoverStyle = hoverable
    ? 'cursor:pointer;'
    : '';

  const selectedStyle = selected
    ? 'border-color:var(--arcanis-color-primary);box-shadow:0 0 0 2px var(--arcanis-color-primary);'
    : '';

  const interactiveStyle = (hoverable || onClick)
    ? 'cursor:pointer;'
    : '';

  const style = baseStyle + variantStyles[variant] + paddingStyles[padding] + hoverStyle + selectedStyle + interactiveStyle;

  return h('div', {
    className: `arcanis-card arcanis-card--${variant} ${selected ? 'arcanis-card--selected' : ''} ${className}`.trim(),
    style,
    onClick,
    role: onClick ? 'button' : undefined,
    tabIndex: onClick ? 0 : undefined,
    'aria-pressed': selected !== undefined ? selected : undefined,
  }, children);
}

export interface CardHeaderProps {
  title: string;
  subtitle?: string;
  action?: VNode;
  className?: string;
}

export function CardHeader(props: CardHeaderProps): VNode {
  const { title, subtitle, action, className = '' } = props;

  const headerStyle = 'display:flex;align-items:flex-start;justify-content:space-between;gap:12px;';

  const titleStyle = 'margin:0;font-size:var(--arcanis-font-size-md);font-weight:var(--arcanis-font-weight-bold);color:var(--arcanis-color-text);';

  const subtitleStyle = 'margin:4px 0 0;font-size:var(--arcanis-font-size-sm);color:var(--arcanis-color-textSecondary);';

  return h('div', {
    className: `arcanis-card-header ${className}`.trim(),
    style: headerStyle,
  },
    h('div', {},
      h('h3', { style: titleStyle }, title),
      subtitle ? h('p', { style: subtitleStyle }, subtitle) : null,
    ),
    action || null,
  );
}

export interface CardBodyProps {
  className?: string;
  children?: VNode | VNode[];
}

export function CardBody(props: CardBodyProps): VNode {
  const { className = '', children } = props;
  return h('div', {
    className: `arcanis-card-body ${className}`.trim(),
    style: 'margin-top:12px;',
  }, children);
}

export interface CardFooterProps {
  className?: string;
  children?: VNode | VNode[];
}

export function CardFooter(props: CardFooterProps): VNode {
  const { className = '', children } = props;
  return h('div', {
    className: `arcanis-card-footer ${className}`.trim(),
    style: 'display:flex;align-items:center;justify-content:flex-end;gap:8px;margin-top:16px;padding-top:12px;border-top:1px solid var(--arcanis-color-border);',
  }, children);
}

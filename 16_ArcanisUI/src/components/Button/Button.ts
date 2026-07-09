import type { VNode } from '../../types';
import { createElement as h } from '../../core/dom/createElement';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline' | 'link';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  leftIcon?: VNode;
  rightIcon?: VNode;
  onClick?: (event: MouseEvent) => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
  children?: VNode | VNode[] | string;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'background:var(--arcanis-color-primary);color:white;border:none;cursor:pointer;',
  secondary: 'background:var(--arcanis-color-secondary);color:white;border:none;cursor:pointer;',
  ghost: 'background:transparent;color:var(--arcanis-color-text);border:none;cursor:pointer;',
  danger: 'background:var(--arcanis-color-error);color:white;border:none;cursor:pointer;',
  outline: 'background:transparent;color:var(--arcanis-color-primary);border:1px solid var(--arcanis-color-primary);cursor:pointer;',
  link: 'background:transparent;color:var(--arcanis-color-primary);border:none;cursor:pointer;text-decoration:underline;',
};

const sizeStyles: Record<ButtonSize, string> = {
  xs: 'padding:4px 8px;font-size:12px;border-radius:var(--arcanis-radius-sm);',
  sm: 'padding:6px 12px;font-size:14px;border-radius:var(--arcanis-radius-sm);',
  md: 'padding:8px 16px;font-size:14px;border-radius:var(--arcanis-radius-md);',
  lg: 'padding:12px 24px;font-size:16px;border-radius:var(--arcanis-radius-md);',
  xl: 'padding:16px 32px;font-size:18px;border-radius:var(--arcanis-radius-lg);',
};

export function Button(props: ButtonProps): VNode {
  const {
    variant = 'primary',
    size = 'md',
    disabled = false,
    loading = false,
    fullWidth = false,
    leftIcon,
    rightIcon,
    onClick,
    type = 'button',
    className = '',
    children,
  } = props;

  const baseStyles = 'display:inline-flex;align-items:center;justify-content:center;gap:8px;font-family:var(--arcanis-font-family);font-weight:var(--arcanis-font-weight-medium);transition:all var(--arcanis-transition-fast);';

  const widthStyle = fullWidth ? 'width:100%;' : '';
  const disabledStyle = disabled || loading ? 'opacity:0.5;cursor:not-allowed;pointer-events:none;' : '';

  const style = baseStyles + variantStyles[variant] + sizeStyles[size] + widthStyle + disabledStyle;

  const ariaLabel = loading ? 'Loading...' : undefined;

  return h('button', {
    type,
    className: `arcanis-button arcanis-button--${variant} arcanis-button--${size} ${className}`.trim(),
    style,
    disabled,
    'aria-disabled': disabled || loading,
    'aria-busy': loading,
    'aria-label': ariaLabel,
    onClick: disabled || loading ? undefined : onClick,
  }, leftIcon, ...(Array.isArray(children) ? children : [children]), rightIcon);
}

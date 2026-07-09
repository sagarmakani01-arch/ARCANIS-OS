import type { VNode } from '../../types';
import { createElement as h } from '../../core/dom/createElement';

export type InputSize = 'sm' | 'md' | 'lg';

export interface InputProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search' | 'date';
  size?: InputSize;
  placeholder?: string;
  value?: string;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  error?: boolean;
  errorMessage?: string;
  label?: string;
  helperText?: string;
  leftAddon?: string | VNode;
  rightAddon?: string | VNode;
  onChange?: (event: Event) => void;
  onFocus?: (event: FocusEvent) => void;
  onBlur?: (event: FocusEvent) => void;
  className?: string;
  id?: string;
  name?: string;
  autoComplete?: string;
  autoFocus?: boolean;
  maxLength?: number;
  minLength?: number;
  pattern?: string;
  step?: number;
}

const sizeStyles: Record<InputSize, string> = {
  sm: 'padding:6px 10px;font-size:12px;height:32px;',
  md: 'padding:8px 12px;font-size:14px;height:40px;',
  lg: 'padding:10px 14px;font-size:16px;height:48px;',
};

export function Input(props: InputProps): VNode {
  const {
    type = 'text',
    size = 'md',
    placeholder,
    value,
    disabled = false,
    readOnly = false,
    required = false,
    error = false,
    errorMessage,
    label,
    helperText,
    leftAddon,
    rightAddon,
    onChange,
    onFocus,
    onBlur,
    className = '',
    id,
    name,
    autoComplete,
    autoFocus,
    maxLength,
    minLength,
    pattern,
    step,
  } = props;

  const inputId = id || `arcanis-input-${Math.random().toString(36).slice(2, 9)}`;
  const errorId = error ? `${inputId}-error` : undefined;
  const helperId = helperText ? `${inputId}-helper` : undefined;

  const baseInputStyles = `width:100%;box-sizing:border-box;font-family:var(--arcanis-font-family);background:var(--arcanis-color-surface);color:var(--arcanis-color-text);border:1px solid var(--arcanis-color-border);border-radius:var(--arcanis-radius-md);transition:border-color var(--arcanis-transition-fast);outline:none;`;

  const errorStyles = error ? 'border-color:var(--arcanis-color-error);' : '';
  const disabledStyles = disabled ? 'opacity:0.5;cursor:not-allowed;background:var(--arcanis-color-background);' : '';
  const readOnlyStyles = readOnly ? 'cursor:default;' : '';

  const inputStyle = baseInputStyles + sizeStyles[size] + errorStyles + disabledStyles + readOnlyStyles;

  const input = h('input', {
    id: inputId,
    type,
    placeholder,
    value,
    disabled,
    readOnly,
    required,
    name,
    autoComplete,
    autoFocus,
    maxLength,
    minLength,
    pattern,
    step,
    className: `arcanis-input ${className}`.trim(),
    style: inputStyle,
    'aria-invalid': error || undefined,
    'aria-describedby': [errorId, helperId].filter(Boolean).join(' ') || undefined,
    onChange,
    onFocus,
    onBlur,
  });

  const labelEl = label ? h('label', {
    htmlFor: inputId,
    style: 'display:block;margin-bottom:4px;font-size:14px;font-weight:var(--arcanis-font-weight-medium);color:var(--arcanis-color-text);',
    className: 'arcanis-input-label',
  }, label) : null;

  const errorEl = error && errorMessage ? h('div', {
    id: errorId,
    role: 'alert',
    style: 'color:var(--arcanis-color-error);font-size:12px;margin-top:4px;',
    className: 'arcanis-input-error',
  }, errorMessage) : null;

  const helperEl = helperText ? h('div', {
    id: helperId,
    style: 'color:var(--arcanis-color-textSecondary);font-size:12px;margin-top:4px;',
    className: 'arcanis-input-helper',
  }, helperText) : null;

  if (leftAddon || rightAddon) {
    const wrapperStyle = `display:flex;align-items:center;gap:0;width:100%;`;

    const leftEl = leftAddon ? h('span', {
      style: 'display:flex;align-items:center;padding:0 10px;background:var(--arcanis-color-background);border:1px solid var(--arcanis-color-border);border-right:none;border-radius:var(--arcanis-radius-md) 0 0 var(--arcanis-radius-md);height:100%;',
      className: 'arcanis-input-left-addon',
    }, leftAddon) : null;

    const rightEl = rightAddon ? h('span', {
      style: 'display:flex;align-items:center;padding:0 10px;background:var(--arcanis-color-background);border:1px solid var(--arcanis-color-border);border-left:none;border-radius:0 var(--arcanis-radius-md) var(--arcanis-radius-md) 0;height:100%;',
      className: 'arcanis-input-right-addon',
    }, rightAddon) : null;

    return h('div', { className: 'arcanis-input-wrapper' },
      labelEl,
      h('div', { style: wrapperStyle, className: 'arcanis-input-group' }, leftEl, input, rightEl),
      errorEl,
      helperEl,
    );
  }

  return h('div', { className: 'arcanis-input-wrapper' },
    labelEl,
    input,
    errorEl,
    helperEl,
  );
}

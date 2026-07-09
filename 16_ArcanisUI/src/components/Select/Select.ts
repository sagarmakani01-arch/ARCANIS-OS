import type { VNode } from '../../types';
import { createElement as h } from '../../core/dom/createElement';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps {
  options: SelectOption[];
  value?: string;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  error?: boolean;
  errorMessage?: string;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  onChange?: (value: string) => void;
  className?: string;
}

const sizeStyles: Record<string, string> = {
  sm: 'padding:6px 10px;font-size:12px;height:32px;',
  md: 'padding:8px 12px;font-size:14px;height:40px;',
  lg: 'padding:10px 14px;font-size:16px;height:48px;',
};

export function Select(props: SelectProps): VNode {
  const {
    options,
    value,
    placeholder,
    disabled = false,
    required = false,
    error = false,
    errorMessage,
    label,
    size = 'md',
    onChange,
    className = '',
  } = props;

  const selectId = `arcanis-select-${Math.random().toString(36).slice(2, 9)}`;

  const selectStyle = `width:100%;box-sizing:border-box;font-family:var(--arcanis-font-family);background:var(--arcanis-color-surface);color:var(--arcanis-color-text);border:1px solid ${error ? 'var(--arcanis-color-error)' : 'var(--arcanis-color-border)'};border-radius:var(--arcanis-radius-md);cursor:pointer;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2364748b' d='M2 4l4 4 4-4'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center;padding-right:32px;${sizeStyles[size]}${disabled ? 'opacity:0.5;cursor:not-allowed;' : ''}`;

  const optionsList = [
    ...(placeholder ? [{ value: '', label: placeholder, disabled: true }] : []),
    ...options,
  ];

  const selectEl = h('select', {
    id: selectId,
    className: `arcanis-select ${className}`.trim(),
    style: selectStyle,
    disabled,
    required,
    value,
    onChange: onChange ? ((e: Event) => onChange((e.target as HTMLSelectElement).value)) as unknown as string : undefined,
  }, ...optionsList.map((opt) =>
    h('option', { value: opt.value, disabled: opt.disabled }, opt.label)
  ));

  const labelEl = label ? h('label', {
    htmlFor: selectId,
    style: 'display:block;margin-bottom:4px;font-size:14px;font-weight:var(--arcanis-font-weight-medium);color:var(--arcanis-color-text);',
    className: 'arcanis-select-label',
  }, label) : null;

  const errorEl = error && errorMessage ? h('div', {
    role: 'alert',
    style: 'color:var(--arcanis-color-error);font-size:12px;margin-top:4px;',
    className: 'arcanis-select-error',
  }, errorMessage) : null;

  return h('div', { className: 'arcanis-select-wrapper' },
    labelEl,
    selectEl,
    errorEl,
  );
}

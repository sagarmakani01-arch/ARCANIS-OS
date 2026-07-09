import type { VNode } from '../../types';
import { createElement as h } from '../../core/dom/createElement';

export interface CheckboxProps {
  checked?: boolean;
  indeterminate?: boolean;
  disabled?: boolean;
  label?: string;
  onChange?: (checked: boolean) => void;
  className?: string;
}

export function Checkbox(props: CheckboxProps): VNode {
  const {
    checked = false,
    indeterminate = false,
    disabled = false,
    label,
    onChange,
    className = '',
  } = props;

  const checkboxId = `arcanis-checkbox-${Math.random().toString(36).slice(2, 9)}`;

  const boxStyle = `width:18px;height:18px;border:2px solid ${checked || indeterminate ? 'var(--arcanis-color-primary)' : 'var(--arcanis-color-border)'};border-radius:var(--arcanis-radius-sm);background:${checked || indeterminate ? 'var(--arcanis-color-primary)' : 'transparent'};cursor:${disabled ? 'not-allowed' : 'pointer'};transition:all var(--arcanis-transition-fast);display:flex;align-items:center;justify-content:center;${disabled ? 'opacity:0.5;' : ''}`;

  const checkmark = checked ? h('svg', { width: '12', height: '12', viewBox: '0 0 12 12', fill: 'none' },
    h('path', { d: 'M10 3L4.5 8.5L2 6', stroke: 'white', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
  ) : null;

  const indeterminateMark = indeterminate && !checked ? h('svg', { width: '12', height: '12', viewBox: '0 0 12 12', fill: 'none' },
    h('path', { d: 'M2 6H10', stroke: 'white', 'stroke-width': '2', 'stroke-linecap': 'round' })
  ) : null;

  const checkbox = h('div', {
    className: `arcanis-checkbox ${className}`.trim(),
    style: boxStyle,
    role: 'checkbox',
    'aria-checked': indeterminate ? 'mixed' : String(checked),
    'aria-disabled': disabled,
    tabIndex: disabled ? -1 : 0,
    onClick: disabled ? undefined : () => onChange?.(!checked),
    onKeyDown: disabled ? undefined : ((e: KeyboardEvent) => {
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        onChange?.(!checked);
      }
    }) as unknown as string,
  }, checkmark, indeterminateMark);

  const labelEl = label ? h('label', {
    htmlFor: checkboxId,
    style: `margin-left:8px;font-size:14px;color:var(--arcanis-color-text);${disabled ? 'opacity:0.5;cursor:not-allowed;' : 'cursor:pointer;'}`,
    className: 'arcanis-checkbox-label',
  }, label) : null;

  return h('div', {
    className: 'arcanis-checkbox-wrapper',
    style: 'display:flex;align-items:center;',
  }, checkbox, labelEl);
}

export interface RadioProps {
  checked?: boolean;
  disabled?: boolean;
  label?: string;
  onChange?: () => void;
  className?: string;
}

export function Radio(props: RadioProps): VNode {
  const {
    checked = false,
    disabled = false,
    label,
    onChange,
    className = '',
  } = props;

  const radioId = `arcanis-radio-${Math.random().toString(36).slice(2, 9)}`;

  const outerStyle = `width:18px;height:18px;border:2px solid ${checked ? 'var(--arcanis-color-primary)' : 'var(--arcanis-color-border)'};border-radius:50%;background:transparent;cursor:${disabled ? 'not-allowed' : 'pointer'};transition:all var(--arcanis-transition-fast);display:flex;align-items:center;justify-content:center;${disabled ? 'opacity:0.5;' : ''}`;

  const innerDot = checked ? h('div', {
    style: 'width:8px;height:8px;border-radius:50%;background:var(--arcanis-color-primary);',
  }) : null;

  const radio = h('div', {
    className: `arcanis-radio ${className}`.trim(),
    style: outerStyle,
    role: 'radio',
    'aria-checked': String(checked),
    'aria-disabled': disabled,
    tabIndex: disabled ? -1 : 0,
    onClick: disabled ? undefined : () => onChange?.(),
  }, innerDot);

  const labelEl = label ? h('label', {
    style: `margin-left:8px;font-size:14px;color:var(--arcanis-color-text);${disabled ? 'opacity:0.5;cursor:not-allowed;' : 'cursor:pointer;'}`,
    className: 'arcanis-radio-label',
  }, label) : null;

  return h('div', {
    className: 'arcanis-radio-wrapper',
    style: 'display:flex;align-items:center;',
  }, radio, labelEl);
}

export interface SwitchProps {
  checked?: boolean;
  disabled?: boolean;
  label?: string;
  onChange?: (checked: boolean) => void;
  className?: string;
}

export function Switch(props: SwitchProps): VNode {
  const {
    checked = false,
    disabled = false,
    label,
    onChange,
    className = '',
  } = props;

  const trackStyle = `width:40px;height:22px;border-radius:11px;background:${checked ? 'var(--arcanis-color-primary)' : 'var(--arcanis-color-border)'};cursor:${disabled ? 'not-allowed' : 'pointer'};transition:background var(--arcanis-transition-fast);position:relative;${disabled ? 'opacity:0.5;' : ''}`;

  const thumbStyle = `width:18px;height:18px;border-radius:50%;background:white;position:absolute;top:2px;left:${checked ? '20px' : '2px'};transition:left var(--arcanis-transition-fast);box-shadow:var(--arcanis-shadow-sm);`;

  const switchEl = h('div', {
    className: `arcanis-switch ${className}`.trim(),
    style: trackStyle,
    role: 'switch',
    'aria-checked': String(checked),
    'aria-disabled': disabled,
    tabIndex: disabled ? -1 : 0,
    onClick: disabled ? undefined : () => onChange?.(!checked),
  }, h('div', { style: thumbStyle }));

  const labelEl = label ? h('label', {
    style: `margin-left:8px;font-size:14px;color:var(--arcanis-color-text);${disabled ? 'opacity:0.5;cursor:not-allowed;' : 'cursor:pointer;'}`,
    className: 'arcanis-switch-label',
  }, label) : null;

  return h('div', {
    className: 'arcanis-switch-wrapper',
    style: 'display:flex;align-items:center;',
  }, switchEl, labelEl);
}

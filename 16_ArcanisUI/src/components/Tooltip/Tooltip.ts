import type { VNode } from '../../types';
import { createElement as h } from '../../core/dom/createElement';

export type TooltipPlacement = 'top' | 'bottom' | 'left' | 'right';

export interface TooltipProps {
  content: string;
  placement?: TooltipPlacement;
  delay?: number;
  children: VNode;
  className?: string;
}

const placementStyles: Record<TooltipPlacement, string> = {
  top: 'bottom:calc(100% + 8px);left:50%;transform:translateX(-50%);',
  bottom: 'top:calc(100% + 8px);left:50%;transform:translateX(-50%);',
  left: 'right:calc(100% + 8px);top:50%;transform:translateY(-50%);',
  right: 'left:calc(100% + 8px);top:50%;transform:translateY(-50%);',
};

export function Tooltip(props: TooltipProps): VNode {
  const { content, placement = 'top', delay = 200, className = '' } = props;

  const wrapperStyle = 'position:relative;display:inline-block;';

  const tooltipStyle = `position:absolute;${placementStyles[placement]}background:var(--arcanis-color-text);color:var(--arcanis-color-surface);padding:6px 10px;border-radius:var(--arcanis-radius-sm);font-size:12px;white-space:nowrap;pointer-events:none;opacity:0;transition:opacity 150ms ease;z-index:var(--arcanis-zIndex-tooltip);box-shadow:var(--arcanis-shadow-md);`;

  return h('div', {
    className: `arcanis-tooltip-wrapper ${className}`.trim(),
    style: wrapperStyle,
    onMouseEnter: `this.querySelector('.arcanis-tooltip').style.opacity='1'`,
    onMouseLeave: `this.querySelector('.arcanis-tooltip').style.opacity='0'`,
  },
    props.children,
    h('div', {
      className: 'arcanis-tooltip',
      style: tooltipStyle,
      role: 'tooltip',
    }, content),
  );
}

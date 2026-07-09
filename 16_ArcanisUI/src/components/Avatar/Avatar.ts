import type { VNode } from '../../types';
import { createElement as h } from '../../core/dom/createElement';

export interface AvatarProps {
  src?: string;
  alt?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  shape?: 'circle' | 'square';
  name?: string;
  className?: string;
}

const sizeMap: Record<string, number> = { xs: 24, sm: 32, md: 40, lg: 56, xl: 72 };

export function Avatar(props: AvatarProps): VNode {
  const { src, alt, size = 'md', shape = 'circle', name, className = '' } = props;
  const px = sizeMap[size];

  const containerStyle = `width:${px}px;height:${px}px;border-radius:${shape === 'circle' ? '50%' : 'var(--arcanis-radius-md)'};overflow:hidden;display:flex;align-items:center;justify-content:center;background:var(--arcanis-color-primary);color:white;font-weight:var(--arcanis-font-weight-medium);font-size:${px * 0.4}px;flex-shrink:0;`;

  const initials = name ? name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase() : '?';

  if (src) {
    return h('img', {
      src,
      alt: alt || name || '',
      className: `arcanis-avatar ${className}`.trim(),
      style: containerStyle,
      onError: `this.style.display='none';this.nextElementSibling.style.display='flex'`,
    });
  }

  return h('div', {
    className: `arcanis-avatar ${className}`.trim(),
    style: containerStyle,
    'aria-label': alt || name,
  }, initials);
}

export interface AvatarGroupProps {
  max?: number;
  className?: string;
  children?: VNode[];
}

export function AvatarGroup(props: AvatarGroupProps): VNode {
  const { max = 4, className = '' } = props;
  const children = (props.children || []) as VNode[];
  const visible = children.slice(0, max);
  const remaining = children.length - max;

  const groupStyle = 'display:flex;flex-direction:row-reverse;justify-content:flex-end;align-items:center;';

  const hiddenGroup = remaining > 0
    ? h('div', {
        style: 'width:32px;height:32px;border-radius:50%;background:var(--arcanis-color-surface);border:2px solid var(--arcanis-color-background);display:flex;align-items:center;justify-content:center;font-size:12px;color:var(--arcanis-color-textSecondary);margin-left:-8px;',
        className: 'arcanis-avatar-group-more',
      }, `+${remaining}`)
    : null;

  return h('div', {
    className: `arcanis-avatar-group ${className}`.trim(),
    style: groupStyle,
    role: 'group',
  }, ...visible.map((child, i) =>
    h('div', { style: `margin-left:${i === 0 ? 0 : '-8px'};` }, child)
  ), hiddenGroup);
}

import type { VNode } from '../../types';
import { createElement as h } from '../../core/dom/createElement';
import { useState, useEffect } from '../../core/component/component';
import { announce } from '../../accessibility';

export type TabItem = {
  id: string;
  label: string;
  icon?: VNode;
  disabled?: boolean;
  content: VNode | VNode[];
};

export interface TabsProps {
  tabs: TabItem[];
  activeId?: string;
  onChange?: (tabId: string) => void;
  variant?: 'line' | 'enclosed' | 'pills';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const variantStyles: Record<string, string> = {
  line: 'border-bottom:1px solid var(--arcanis-color-border);',
  enclosed: 'background:var(--arcanis-color-background);border-radius:var(--arcanis-radius-md);padding:4px;',
  pills: 'background:var(--arcanis-color-background);border-radius:var(--arcanis-radius-full);padding:4px;',
};

const sizeStyles: Record<string, string> = {
  sm: 'font-size:12px;padding:6px 12px;',
  md: 'font-size:14px;padding:8px 16px;',
  lg: 'font-size:16px;padding:10px 20px;',
};

export function Tabs(props: TabsProps): VNode {
  const {
    tabs,
    activeId,
    onChange,
    variant = 'line',
    size = 'md',
    className = '',
  } = props;

  const [selectedTab, setSelectedTab] = useState(activeId || tabs[0]?.id || '');

  const handleTabClick = (tabId: string) => {
    const tab = tabs.find((t) => t.id === tabId);
    if (tab?.disabled) return;
    setSelectedTab(tabId);
    onChange?.(tabId);
    announce(`Selected ${tab?.label} tab`);
  };

  const tabListStyle = `display:flex;gap:2px;${variantStyles[variant]}`;

  const tabButtonStyle = (isActive: boolean, isDisabled: boolean) => `
    display:inline-flex;align-items:center;gap:6px;
    font-family:var(--arcanis-font-family);
    font-weight:${isActive ? 'var(--arcanis-font-weight-medium)' : 'var(--arcanis-font-weight-normal)'};
    color:${isActive ? 'var(--arcanis-color-primary)' : 'var(--arcanis-color-textSecondary)'};
    background:${isActive && variant !== 'line' ? 'var(--arcanis-color-surface)' : 'transparent'};
    border:none;cursor:${isDisabled ? 'not-allowed' : 'pointer'};
    opacity:${isDisabled ? '0.5' : '1'};
    transition:all var(--arcanis-transition-fast);
    border-radius:${variant === 'pills' ? 'var(--arcanis-radius-full)' : variant === 'enclosed' ? 'var(--arcanis-radius-md)' : '0'};
    ${variant === 'line' ? `border-bottom:2px solid ${isActive ? 'var(--arcanis-color-primary)' : 'transparent'};` : ''}
    ${sizeStyles[size]};
  `.replace(/\n/g, ' ').trim();

  const tabList = h('div', {
    role: 'tablist',
    className: `arcanis-tabs-list arcanis-tabs--${variant}`.trim(),
    style: tabListStyle,
    'aria-orientation': 'horizontal',
  },
    ...tabs.map((tab) => {
      const isActive = tab.id === selectedTab;
      return h('button', {
        role: 'tab',
        id: `tab-${tab.id}`,
        'aria-selected': String(isActive),
        'aria-controls': `tabpanel-${tab.id}`,
        'aria-disabled': String(tab.disabled),
        tabIndex: isActive ? 0 : -1,
        className: `arcanis-tab ${isActive ? 'arcanis-tab--active' : ''}`,
        style: tabButtonStyle(isActive, !!tab.disabled),
        onClick: () => handleTabClick(tab.id),
      }, tab.icon || null, tab.label);
    }),
  );

  const activeContent = tabs.find((t) => t.id === selectedTab)?.content;

  const tabPanel = h('div', {
    role: 'tabpanel',
    id: `tabpanel-${selectedTab}`,
    'aria-labelledby': `tab-${selectedTab}`,
    tabIndex: 0,
    className: 'arcanis-tab-panel',
    style: 'padding:var(--arcanis-space-md) 0;',
  }, activeContent);

  return h('div', {
    className: `arcanis-tabs ${className}`.trim(),
  }, tabList, tabPanel);
}

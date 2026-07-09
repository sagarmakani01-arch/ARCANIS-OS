import type { VNode } from '../../types';
import { createElement as h } from '../../core/dom/createElement';
import { createFocusTrap, announce, getA11yProps } from '../../accessibility';

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnOverlayClick?: boolean;
  closeOnEsc?: boolean;
  showClose?: boolean;
  children?: VNode | VNode[];
  footer?: VNode | VNode[];
  initialFocus?: string;
  className?: string;
}

const sizeStyles: Record<string, string> = {
  sm: 'max-width:400px;',
  md: 'max-width:560px;',
  lg: 'max-width:720px;',
  xl: 'max-width:900px;',
  full: 'max-width:calc(100vw - 48px);',
};

export function Modal(props: ModalProps): VNode {
  const {
    open,
    onClose,
    title,
    description,
    size = 'md',
    closeOnOverlayClick = true,
    closeOnEsc = true,
    showClose = true,
    children,
    footer,
    className = '',
  } = props;

  if (!open) return h('div', {});

  const overlayStyle = 'position:fixed;inset:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:var(--arcanis-zIndex-modal);padding:24px;backdrop-filter:blur(4px);';

  const modalStyle = `background:var(--arcanis-color-surface);border-radius:var(--arcanis-radius-lg);box-shadow:var(--arcanis-shadow-lg);width:100%;${sizeStyles[size]}display:flex;flex-direction:column;max-height:calc(100vh - 48px);overflow:hidden;`;

  const headerStyle = 'display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid var(--arcanis-color-border);';

  const bodyStyle = 'padding:20px;overflow-y:auto;flex:1;';

  const footerStyle = 'display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:16px 20px;border-top:1px solid var(--arcanis-color-border);';

  const titleEl = title ? h('h2', {
    style: 'margin:0;font-size:var(--arcanis-font-size-lg);font-weight:var(--arcanis-font-weight-bold);color:var(--arcanis-color-text);',
    id: 'arcanis-modal-title',
  }, title) : null;

  const descriptionEl = description ? h('p', {
    style: 'margin:4px 0 0;font-size:var(--arcanis-font-size-sm);color:var(--arcanis-color-textSecondary);',
    id: 'arcanis-modal-description',
  }, description) : null;

  const closeButton = showClose ? h('button', {
    onClick: onClose,
    style: 'background:none;border:none;cursor:pointer;padding:4px;border-radius:var(--arcanis-radius-sm);color:var(--arcanis-color-textSecondary);display:flex;align-items:center;justify-content:center;',
    'aria-label': 'Close modal',
    className: 'arcanis-modal-close',
  }, '\u2715') : null;

  const headerContent = (titleEl || descriptionEl || closeButton)
    ? h('div', { style: headerStyle, className: 'arcanis-modal-header' },
        h('div', {}, titleEl, descriptionEl),
        closeButton,
      )
    : null;

  const bodyEl = children ? h('div', { style: bodyStyle, className: 'arcanis-modal-body' }, children) : null;

  const footerEl = footer ? h('div', { style: footerStyle, className: 'arcanis-modal-footer' }, footer) : null;

  const handleOverlayClick = (e: MouseEvent) => {
    if (closeOnOverlayClick && (e.target as Element).classList.contains('arcanis-modal-overlay')) {
      onClose();
    }
  };

  const handleKeydown = (e: KeyboardEvent) => {
    if (closeOnEsc && e.key === 'Escape') {
      onClose();
    }
  };

  return h('div', {
    className: `arcanis-modal-overlay ${className}`.trim(),
    style: overlayStyle,
    onClick: handleOverlayClick,
    onKeyDown: handleKeydown,
    ...getA11yProps({
      role: 'dialog',
      labelledBy: title ? 'arcanis-modal-title' : undefined,
      describedBy: description ? 'arcanis-modal-description' : undefined,
    }),
  },
    h('div', {
      className: 'arcanis-modal',
      style: modalStyle,
      role: 'document',
    }, headerContent, bodyEl, footerEl),
  );
}

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createElement as h } from '../src/core/dom/createElement';
import { Button } from '../src/components/Button/Button';
import { Badge } from '../src/components/Badge/Badge';
import { Modal } from '../src/components/Modal/Modal';
import { Input } from '../src/components/Input/Input';
import { Card, CardHeader, CardBody, CardFooter } from '../src/components/Card/Card';
import { Select } from '../src/components/Select/Select';
import { Checkbox, Radio, Switch } from '../src/components/Toggle/Toggle';
import { Tooltip } from '../src/components/Tooltip/Tooltip';
import { Avatar, AvatarGroup } from '../src/components/Avatar/Avatar';
import { Stack, Flex, Grid, Center, Spacer, Divider } from '../src/components/Layout/Layout';
import { renderComponent } from '../src/core/component/component';

beforeEach(() => {
  vi.stubGlobal('window', { dispatchEvent: vi.fn(), matchMedia: vi.fn().mockReturnValue({ matches: false }), addEventListener: vi.fn() });
  vi.stubGlobal('CustomEvent', class CustomEvent extends Event {
    detail: any;
    constructor(type: string, opts: any) {
      super(type);
      this.detail = opts?.detail;
    }
  });
  vi.stubGlobal('document', {
    getElementById: vi.fn().mockReturnValue(null),
    createElement: vi.fn().mockReturnValue({ style: {} }),
    body: { appendChild: vi.fn(), innerHTML: '' },
    querySelector: vi.fn().mockReturnValue(null),
    documentElement: { style: { setProperty: vi.fn() } },
  });
});

function getProps(vnode: any) {
  return vnode.props;
}

function getClassName(vnode: any) {
  return vnode.props.className;
}

function hasChild(vnode: any, predicate: (child: any) => boolean): boolean {
  return (vnode.props.children || []).some(predicate);
}

function findChild(vnode: any, predicate: (child: any) => boolean): any {
  return (vnode.props.children || []).find(predicate);
}

describe('Button', () => {
  it('renders with default props', () => {
    const vnode = Button({ children: 'Click me' });
    expect(vnode.type).toBe('button');
    expect(getProps(vnode).type).toBe('button');
    expect(getClassName(vnode)).toContain('arcanis-button--primary');
    expect(getClassName(vnode)).toContain('arcanis-button--md');
  });

  it('renders with variant', () => {
    const vnode = Button({ variant: 'secondary', children: 'Test' });
    expect(getClassName(vnode)).toContain('arcanis-button--secondary');
  });

  it('renders with size', () => {
    const vnode = Button({ size: 'lg', children: 'Test' });
    expect(getClassName(vnode)).toContain('arcanis-button--lg');
  });

  it('renders disabled state', () => {
    const vnode = Button({ disabled: true, children: 'Test' });
    expect(getProps(vnode).disabled).toBe(true);
    expect(getProps(vnode)['aria-disabled']).toBe(true);
  });

  it('renders loading state', () => {
    const vnode = Button({ loading: true, children: 'Test' });
    expect(getProps(vnode)['aria-busy']).toBe(true);
    expect(getProps(vnode)['aria-label']).toBe('Loading...');
  });

  it('renders fullWidth', () => {
    const vnode = Button({ fullWidth: true, children: 'Test' });
    expect(getProps(vnode).style).toContain('width:100%');
  });

  it('renders with custom type', () => {
    const vnode = Button({ type: 'submit', children: 'Submit' });
    expect(getProps(vnode).type).toBe('submit');
  });

  it('renders with onClick', () => {
    const onClick = () => {};
    const vnode = Button({ onClick, children: 'Test' });
    expect(getProps(vnode).onClick).toBe(onClick);
  });

  it('disables onClick when loading', () => {
    const onClick = () => {};
    const vnode = Button({ loading: true, onClick, children: 'Test' });
    expect(getProps(vnode).onClick).toBeUndefined();
  });

  it('disables onClick when disabled', () => {
    const onClick = () => {};
    const vnode = Button({ disabled: true, onClick, children: 'Test' });
    expect(getProps(vnode).onClick).toBeUndefined();
  });

  it('renders all variants', () => {
    const variants = ['primary', 'secondary', 'ghost', 'danger', 'outline', 'link'] as const;
    variants.forEach((v) => {
      const vnode = Button({ variant: v, children: 'Test' });
      expect(getClassName(vnode)).toContain(`arcanis-button--${v}`);
    });
  });

  it('renders all sizes', () => {
    const sizes = ['xs', 'sm', 'md', 'lg', 'xl'] as const;
    sizes.forEach((s) => {
      const vnode = Button({ size: s, children: 'Test' });
      expect(getClassName(vnode)).toContain(`arcanis-button--${s}`);
    });
  });
});

describe('Badge', () => {
  it('renders with default props', () => {
    const vnode = Badge({ children: 'Badge' });
    expect(vnode.type).toBe('span');
    expect(getClassName(vnode)).toContain('arcanis-badge--primary');
  });

  it('renders with variant', () => {
    const vnode = Badge({ variant: 'success', children: 'OK' });
    expect(getClassName(vnode)).toContain('arcanis-badge--success');
  });

  it('renders with size lg', () => {
    const vnode = Badge({ size: 'lg', children: 'Big' });
    expect(getProps(vnode).style).toContain('font-size:14px');
  });

  it('renders with size sm', () => {
    const vnode = Badge({ size: 'sm', children: 'Small' });
    expect(getProps(vnode).style).toContain('font-size:10px');
  });

  it('renders dot indicator', () => {
    const vnode = Badge({ dot: true, children: 'With dot' });
    expect(hasChild(vnode, (c: any) => c?.props?.className === 'arcanis-badge-dot')).toBe(true);
  });

  it('does not render dot by default', () => {
    const vnode = Badge({ children: 'No dot' });
    expect(hasChild(vnode, (c: any) => c?.props?.className === 'arcanis-badge-dot')).toBe(false);
  });

  it('renders all variants', () => {
    const variants = ['primary', 'secondary', 'success', 'warning', 'error', 'info', 'outline'] as const;
    variants.forEach((v) => {
      const vnode = Badge({ variant: v, children: 'Test' });
      expect(getClassName(vnode)).toContain(`arcanis-badge--${v}`);
    });
  });
});

describe('Modal', () => {
  it('renders nothing when closed', () => {
    const vnode = Modal({ open: false, onClose: () => {}, children: 'Content' });
    expect(vnode.type).toBe('div');
    expect(vnode.props.className).toBeUndefined();
  });

  it('renders overlay when open', () => {
    const vnode = Modal({ open: true, onClose: () => {}, children: 'Content' });
    expect(getClassName(vnode)).toContain('arcanis-modal-overlay');
  });

  it('renders with title', () => {
    const vnode = Modal({ open: true, onClose: () => {}, title: 'My Title', children: 'Content' });
    const modal = findChild(vnode, (c: any) => c?.props?.className === 'arcanis-modal');
    expect(modal).toBeDefined();
  });

  it('renders with description', () => {
    const vnode = Modal({
      open: true,
      onClose: () => {},
      title: 'Title',
      description: 'Desc',
      children: 'Content',
    });
    expect(vnode.type).toBe('div');
  });

  it('renders with size sm', () => {
    const vnode = Modal({ open: true, onClose: () => {}, size: 'sm', children: 'Content' });
    expect(vnode.type).toBe('div');
  });

  it('renders with size lg', () => {
    const vnode = Modal({ open: true, onClose: () => {}, size: 'lg', children: 'Content' });
    expect(vnode.type).toBe('div');
  });

  it('renders close button by default', () => {
    const vnode = Modal({ open: true, onClose: () => {}, title: 'T', children: 'Content' });
    const modal = findChild(vnode, (c: any) => c?.props?.className === 'arcanis-modal');
    expect(modal).toBeDefined();
  });

  it('hides close button when showClose is false', () => {
    const vnode = Modal({
      open: true,
      onClose: () => {},
      showClose: false,
      title: 'T',
      children: 'Content',
    });
    expect(vnode.type).toBe('div');
  });

  it('renders footer', () => {
    const footer = h('div', null, 'Footer');
    const vnode = Modal({ open: true, onClose: () => {}, footer, children: 'Content' });
    const modal = findChild(vnode, (c: any) => c?.props?.className === 'arcanis-modal');
    expect(modal).toBeDefined();
  });

  it('applies a11y role dialog', () => {
    const vnode = Modal({ open: true, onClose: () => {}, title: 'T', children: 'Content' });
    expect(getProps(vnode).role).toBe('dialog');
  });

  it('all sizes render', () => {
    const sizes = ['sm', 'md', 'lg', 'xl', 'full'] as const;
    sizes.forEach((s) => {
      const vnode = Modal({ open: true, onClose: () => {}, size: s, children: 'Content' });
      expect(vnode.type).toBe('div');
    });
  });
});

describe('Input', () => {
  it('renders with default props', () => {
    const vnode = Input({});
    expect(vnode.type).toBe('div');
    expect(getClassName(vnode)).toContain('arcanis-input-wrapper');
  });

  it('renders input element inside', () => {
    const vnode = Input({ placeholder: 'Type here' });
    expect(hasChild(vnode, (c: any) => c?.type === 'input')).toBe(true);
  });

  it('renders with type email', () => {
    const vnode = Input({ type: 'email' });
    expect(hasChild(vnode, (c: any) => c?.type === 'input' && c?.props?.type === 'email')).toBe(true);
  });

  it('renders with type password', () => {
    const vnode = Input({ type: 'password' });
    expect(hasChild(vnode, (c: any) => c?.type === 'input' && c?.props?.type === 'password')).toBe(true);
  });

  it('renders with label', () => {
    const vnode = Input({ label: 'Email' });
    expect(hasChild(vnode, (c: any) => c?.type === 'label')).toBe(true);
  });

  it('renders with error', () => {
    const vnode = Input({ error: true, errorMessage: 'Required' });
    expect(hasChild(vnode, (c: any) => c?.props?.className === 'arcanis-input-error')).toBe(true);
  });

  it('renders with helper text', () => {
    const vnode = Input({ helperText: 'Help me' });
    expect(hasChild(vnode, (c: any) => c?.props?.className === 'arcanis-input-helper')).toBe(true);
  });

  it('renders with addons', () => {
    const vnode = Input({ leftAddon: '$', rightAddon: '.00' });
    expect(hasChild(vnode, (c: any) => c?.props?.className === 'arcanis-input-group')).toBe(true);
  });

  it('renders disabled', () => {
    const vnode = Input({ disabled: true });
    expect(hasChild(vnode, (c: any) => c?.type === 'input' && c?.props?.disabled === true)).toBe(true);
  });

  it('renders readOnly', () => {
    const vnode = Input({ readOnly: true });
    expect(hasChild(vnode, (c: any) => c?.type === 'input' && c?.props?.readOnly === true)).toBe(true);
  });

  it('renders required', () => {
    const vnode = Input({ required: true });
    expect(hasChild(vnode, (c: any) => c?.type === 'input' && c?.props?.required === true)).toBe(true);
  });

  it('applies aria-invalid on error', () => {
    const vnode = Input({ error: true, errorMessage: 'Bad' });
    expect(hasChild(vnode, (c: any) => c?.props?.['aria-invalid'] === true)).toBe(true);
  });

  it('renders all sizes', () => {
    const sizes = ['sm', 'md', 'lg'] as const;
    sizes.forEach((s) => {
      const vnode = Input({ size: s });
      expect(vnode.type).toBe('div');
    });
  });

  it('renders with name', () => {
    const vnode = Input({ name: 'email' });
    expect(hasChild(vnode, (c: any) => c?.type === 'input' && c?.props?.name === 'email')).toBe(true);
  });

  it('renders with id', () => {
    const vnode = Input({ id: 'my-input' });
    expect(hasChild(vnode, (c: any) => c?.type === 'input' && c?.props?.id === 'my-input')).toBe(true);
  });
});

describe('Card', () => {
  it('renders with default props', () => {
    const vnode = Card({ children: 'Content' });
    expect(vnode.type).toBe('div');
    expect(getClassName(vnode)).toContain('arcanis-card--elevated');
  });

  it('renders with variant outlined', () => {
    const vnode = Card({ variant: 'outlined', children: 'Content' });
    expect(getClassName(vnode)).toContain('arcanis-card--outlined');
  });

  it('renders with variant filled', () => {
    const vnode = Card({ variant: 'filled', children: 'Content' });
    expect(getClassName(vnode)).toContain('arcanis-card--filled');
  });

  it('renders selected state', () => {
    const vnode = Card({ selected: true, children: 'Content' });
    expect(getClassName(vnode)).toContain('arcanis-card--selected');
    expect(getProps(vnode)['aria-pressed']).toBe(true);
  });

  it('renders clickable card', () => {
    const onClick = () => {};
    const vnode = Card({ onClick, children: 'Content' });
    expect(getProps(vnode).role).toBe('button');
    expect(getProps(vnode).tabIndex).toBe(0);
  });

  it('CardHeader renders title', () => {
    const vnode = CardHeader({ title: 'My Title' });
    expect(vnode.type).toBe('div');
    expect(getClassName(vnode)).toContain('arcanis-card-header');
  });

  it('CardHeader renders subtitle', () => {
    const vnode = CardHeader({ title: 'Title', subtitle: 'Sub' });
    expect(vnode.type).toBe('div');
  });

  it('CardHeader renders action', () => {
    const action = h('button', null, 'Action');
    const vnode = CardHeader({ title: 'Title', action });
    expect(vnode.type).toBe('div');
  });

  it('CardBody renders children', () => {
    const vnode = CardBody({ children: 'Body content' });
    expect(getClassName(vnode)).toContain('arcanis-card-body');
  });

  it('CardFooter renders children', () => {
    const vnode = CardFooter({ children: 'Footer content' });
    expect(getClassName(vnode)).toContain('arcanis-card-footer');
  });

  it('all variants render', () => {
    const variants = ['elevated', 'outlined', 'filled'] as const;
    variants.forEach((v) => {
      const vnode = Card({ variant: v, children: 'Test' });
      expect(getClassName(vnode)).toContain(`arcanis-card--${v}`);
    });
  });

  it('all paddings render', () => {
    const paddings = ['none', 'sm', 'md', 'lg'] as const;
    paddings.forEach((p) => {
      const vnode = Card({ padding: p, children: 'Test' });
      expect(vnode.type).toBe('div');
    });
  });
});

describe('Select', () => {
  it('renders with options', () => {
    const options = [
      { value: 'a', label: 'A' },
      { value: 'b', label: 'B' },
    ];
    const vnode = Select({ options });
    expect(vnode.type).toBe('div');
    expect(getClassName(vnode)).toContain('arcanis-select-wrapper');
  });

  it('renders select element', () => {
    const options = [{ value: 'a', label: 'A' }];
    const vnode = Select({ options });
    expect(hasChild(vnode, (c: any) => c?.type === 'select')).toBe(true);
  });

  it('renders with label', () => {
    const options = [{ value: 'a', label: 'A' }];
    const vnode = Select({ options, label: 'Pick one' });
    expect(hasChild(vnode, (c: any) => c?.type === 'label')).toBe(true);
  });

  it('renders with placeholder', () => {
    const options = [{ value: 'a', label: 'A' }];
    const vnode = Select({ options, placeholder: 'Select...' });
    expect(vnode.type).toBe('div');
  });

  it('renders disabled', () => {
    const options = [{ value: 'a', label: 'A' }];
    const vnode = Select({ options, disabled: true });
    expect(hasChild(vnode, (c: any) => c?.type === 'select' && c?.props?.disabled === true)).toBe(true);
  });

  it('renders error state', () => {
    const options = [{ value: 'a', label: 'A' }];
    const vnode = Select({ options, error: true, errorMessage: 'Required' });
    expect(hasChild(vnode, (c: any) => c?.props?.className === 'arcanis-select-error')).toBe(true);
  });

  it('renders disabled options', () => {
    const options = [{ value: 'a', label: 'A', disabled: true }];
    const vnode = Select({ options });
    expect(vnode.type).toBe('div');
  });

  it('renders required', () => {
    const options = [{ value: 'a', label: 'A' }];
    const vnode = Select({ options, required: true });
    expect(hasChild(vnode, (c: any) => c?.type === 'select' && c?.props?.required === true)).toBe(true);
  });
});

describe('Checkbox', () => {
  it('renders unchecked', () => {
    const vnode = Checkbox({});
    expect(vnode.type).toBe('div');
    expect(getClassName(vnode)).toContain('arcanis-checkbox-wrapper');
  });

  it('renders checked', () => {
    const vnode = Checkbox({ checked: true });
    expect(hasChild(vnode, (c: any) => c?.props?.role === 'checkbox')).toBe(true);
  });

  it('renders indeterminate', () => {
    const vnode = Checkbox({ indeterminate: true });
    expect(vnode.type).toBe('div');
  });

  it('renders disabled', () => {
    const vnode = Checkbox({ disabled: true });
    expect(vnode.type).toBe('div');
  });

  it('renders with label', () => {
    const vnode = Checkbox({ label: 'Accept terms' });
    expect(hasChild(vnode, (c: any) => c?.props?.className === 'arcanis-checkbox-label')).toBe(true);
  });

  it('sets aria-checked to mixed for indeterminate', () => {
    const vnode = Checkbox({ indeterminate: true });
    const checkbox = findChild(vnode, (c: any) => c?.props?.role === 'checkbox');
    expect(checkbox?.props?.['aria-checked']).toBe('mixed');
  });

  it('sets aria-checked true when checked', () => {
    const vnode = Checkbox({ checked: true });
    const checkbox = findChild(vnode, (c: any) => c?.props?.role === 'checkbox');
    expect(checkbox?.props?.['aria-checked']).toBe('true');
  });

  it('sets aria-checked false when unchecked', () => {
    const vnode = Checkbox({ checked: false });
    const checkbox = findChild(vnode, (c: any) => c?.props?.role === 'checkbox');
    expect(checkbox?.props?.['aria-checked']).toBe('false');
  });
});

describe('Radio', () => {
  it('renders unchecked', () => {
    const vnode = Radio({});
    expect(vnode.type).toBe('div');
    expect(getClassName(vnode)).toContain('arcanis-radio-wrapper');
  });

  it('renders checked', () => {
    const vnode = Radio({ checked: true });
    expect(hasChild(vnode, (c: any) => c?.props?.role === 'radio')).toBe(true);
  });

  it('renders disabled', () => {
    const vnode = Radio({ disabled: true });
    expect(vnode.type).toBe('div');
  });

  it('renders with label', () => {
    const vnode = Radio({ label: 'Option A' });
    expect(hasChild(vnode, (c: any) => c?.props?.className === 'arcanis-radio-label')).toBe(true);
  });

  it('sets aria-checked correctly', () => {
    const onVnode = Radio({ checked: true });
    const radio = findChild(onVnode, (c: any) => c?.props?.role === 'radio');
    expect(radio?.props?.['aria-checked']).toBe('true');

    const offVnode = Radio({ checked: false });
    const offRadio = findChild(offVnode, (c: any) => c?.props?.role === 'radio');
    expect(offRadio?.props?.['aria-checked']).toBe('false');
  });
});

describe('Switch', () => {
  it('renders off', () => {
    const vnode = Switch({});
    expect(vnode.type).toBe('div');
    expect(getClassName(vnode)).toContain('arcanis-switch-wrapper');
  });

  it('renders on', () => {
    const vnode = Switch({ checked: true });
    expect(hasChild(vnode, (c: any) => c?.props?.role === 'switch')).toBe(true);
  });

  it('renders disabled', () => {
    const vnode = Switch({ disabled: true });
    expect(vnode.type).toBe('div');
  });

  it('renders with label', () => {
    const vnode = Switch({ label: 'Enable feature' });
    expect(hasChild(vnode, (c: any) => c?.props?.className === 'arcanis-switch-label')).toBe(true);
  });

  it('sets aria-checked correctly', () => {
    const onVnode = Switch({ checked: true });
    const switchEl = findChild(onVnode, (c: any) => c?.props?.role === 'switch');
    expect(switchEl?.props?.['aria-checked']).toBe('true');

    const offVnode = Switch({ checked: false });
    const offSwitch = findChild(offVnode, (c: any) => c?.props?.role === 'switch');
    expect(offSwitch?.props?.['aria-checked']).toBe('false');
  });
});

describe('Tabs', () => {
  const tabs = [
    { id: 'tab1', label: 'Tab 1', content: 'Content 1' },
    { id: 'tab2', label: 'Tab 2', content: 'Content 2' },
  ];

  it('can be imported', async () => {
    const mod = await import('../src/components/Tabs/Tabs');
    expect(mod.Tabs).toBeDefined();
  });
});

describe('Tooltip', () => {
  it('renders wrapper with tooltip', () => {
    const child = h('button', null, 'Hover me');
    const vnode = Tooltip({ content: 'Tip', children: child });
    expect(vnode.type).toBe('div');
    expect(getClassName(vnode)).toContain('arcanis-tooltip-wrapper');
  });

  it('renders tooltip element with role', () => {
    const child = h('button', null, 'Hover me');
    const vnode = Tooltip({ content: 'Tip', children: child });
    expect(hasChild(vnode, (c: any) => c?.props?.role === 'tooltip')).toBe(true);
  });

  it('renders with placement top', () => {
    const child = h('button', null, 'X');
    const vnode = Tooltip({ content: 'Tip', placement: 'top', children: child });
    expect(vnode.type).toBe('div');
  });

  it('renders with placement bottom', () => {
    const child = h('button', null, 'X');
    const vnode = Tooltip({ content: 'Tip', placement: 'bottom', children: child });
    expect(vnode.type).toBe('div');
  });

  it('renders with placement left', () => {
    const child = h('button', null, 'X');
    const vnode = Tooltip({ content: 'Tip', placement: 'left', children: child });
    expect(vnode.type).toBe('div');
  });

  it('renders with placement right', () => {
    const child = h('button', null, 'X');
    const vnode = Tooltip({ content: 'Tip', placement: 'right', children: child });
    expect(vnode.type).toBe('div');
  });

  it('renders content text in tooltip', () => {
    const child = h('span', null, 'S');
    const vnode = Tooltip({ content: 'My tooltip', children: child });
    const tooltip = findChild(vnode, (c: any) => c?.props?.role === 'tooltip');
    const textChild = tooltip?.props?.children?.[0];
    expect(textChild?.text).toBe('My tooltip');
  });

  it('renders with custom className', () => {
    const child = h('span', null, 'X');
    const vnode = Tooltip({ content: 'T', className: 'custom', children: child });
    expect(getClassName(vnode)).toContain('custom');
  });
});

describe('Avatar', () => {
  it('renders image when src provided', () => {
    const vnode = Avatar({ src: 'pic.jpg', alt: 'User' });
    expect(vnode.type).toBe('img');
    expect(getProps(vnode).src).toBe('pic.jpg');
  });

  it('renders initials when no src', () => {
    const vnode = Avatar({ name: 'John Doe' });
    expect(vnode.type).toBe('div');
    const textChild = vnode.props.children?.[0];
    expect(textChild?.text).toBe('JD');
  });

  it('renders question mark for no name', () => {
    const vnode = Avatar({});
    expect(vnode.type).toBe('div');
    const textChild = vnode.props.children?.[0];
    expect(textChild?.text).toBe('?');
  });

  it('renders with size xs', () => {
    const vnode = Avatar({ size: 'xs' });
    expect(getProps(vnode).style).toContain('width:24px');
  });

  it('renders with size sm', () => {
    const vnode = Avatar({ size: 'sm' });
    expect(getProps(vnode).style).toContain('width:32px');
  });

  it('renders with size md', () => {
    const vnode = Avatar({ size: 'md' });
    expect(getProps(vnode).style).toContain('width:40px');
  });

  it('renders with size lg', () => {
    const vnode = Avatar({ size: 'lg' });
    expect(getProps(vnode).style).toContain('width:56px');
  });

  it('renders with size xl', () => {
    const vnode = Avatar({ size: 'xl' });
    expect(getProps(vnode).style).toContain('width:72px');
  });

  it('renders with shape circle', () => {
    const vnode = Avatar({ shape: 'circle' });
    expect(getProps(vnode).style).toContain('border-radius:50%');
  });

  it('renders with shape square', () => {
    const vnode = Avatar({ shape: 'square' });
    expect(getProps(vnode).style).toContain('border-radius:var(--arcanis-radius-md)');
  });

  it('AvatarGroup renders children', () => {
    const child1 = Avatar({ name: 'A' });
    const child2 = Avatar({ name: 'B' });
    const vnode = AvatarGroup({ children: [child1, child2] });
    expect(getClassName(vnode)).toContain('arcanis-avatar-group');
  });

  it('AvatarGroup limits visible children', () => {
    const children = Array.from({ length: 6 }, (_, i) => Avatar({ name: `User ${i}` }));
    const vnode = AvatarGroup({ max: 3, children });
    expect(vnode.type).toBe('div');
  });

  it('AvatarGroup shows overflow count', () => {
    const children = Array.from({ length: 5 }, (_, i) => Avatar({ name: `U${i}` }));
    const vnode = AvatarGroup({ max: 2, children });
    expect(hasChild(vnode, (c: any) => c?.props?.className === 'arcanis-avatar-group-more')).toBe(true);
  });

  it('AvatarGroup does not show overflow when within max', () => {
    const children = Array.from({ length: 2 }, (_, i) => Avatar({ name: `U${i}` }));
    const vnode = AvatarGroup({ max: 4, children });
    expect(hasChild(vnode, (c: any) => c?.props?.className === 'arcanis-avatar-group-more')).toBe(false);
  });

  it('single name gets one-letter initial', () => {
    const vnode = Avatar({ name: 'Alice' });
    const textChild = vnode.props.children?.[0];
    expect(textChild?.text).toBe('A');
  });
});

describe('Layout', () => {
  it('Stack renders vertical by default', () => {
    const vnode = Stack({ children: 'Content' });
    expect(getClassName(vnode)).toContain('arcanis-stack--vertical');
    expect(getProps(vnode).style).toContain('flex-direction:column');
  });

  it('Stack renders horizontal', () => {
    const vnode = Stack({ direction: 'horizontal', children: 'Content' });
    expect(getProps(vnode).style).toContain('flex-direction:row');
  });

  it('Stack with gap xs', () => {
    const vnode = Stack({ gap: 'xs', children: 'Content' });
    expect(getProps(vnode).style).toContain('gap:4px');
  });

  it('Stack with gap sm', () => {
    const vnode = Stack({ gap: 'sm', children: 'Content' });
    expect(getProps(vnode).style).toContain('gap:8px');
  });

  it('Stack with gap md', () => {
    const vnode = Stack({ gap: 'md', children: 'Content' });
    expect(getProps(vnode).style).toContain('gap:16px');
  });

  it('Stack with gap lg', () => {
    const vnode = Stack({ gap: 'lg', children: 'Content' });
    expect(getProps(vnode).style).toContain('gap:24px');
  });

  it('Stack with gap xl', () => {
    const vnode = Stack({ gap: 'xl', children: 'Content' });
    expect(getProps(vnode).style).toContain('gap:32px');
  });

  it('Stack with gap 2xl', () => {
    const vnode = Stack({ gap: '2xl', children: 'Content' });
    expect(getProps(vnode).style).toContain('gap:48px');
  });

  it('Stack with wrap', () => {
    const vnode = Stack({ wrap: true, children: 'Content' });
    expect(getProps(vnode).style).toContain('flex-wrap:wrap');
  });

  it('Stack all directions', () => {
    const dirs = ['horizontal', 'vertical'] as const;
    dirs.forEach((d) => {
      const vnode = Stack({ direction: d, children: 'C' });
      expect(vnode.type).toBe('div');
    });
  });

  it('Stack all alignments', () => {
    const aligns = ['start', 'center', 'end', 'stretch', 'baseline'] as const;
    aligns.forEach((a) => {
      const vnode = Stack({ align: a, children: 'C' });
      expect(vnode.type).toBe('div');
    });
  });

  it('Stack all justifies', () => {
    const justifies = ['start', 'center', 'end', 'between', 'around', 'evenly'] as const;
    justifies.forEach((j) => {
      const vnode = Stack({ justify: j, children: 'C' });
      expect(vnode.type).toBe('div');
    });
  });

  it('Flex renders', () => {
    const vnode = Flex({ children: 'Content' });
    expect(getClassName(vnode)).toContain('arcanis-flex');
  });

  it('Flex inline', () => {
    const vnode = Flex({ inline: true, children: 'Content' });
    expect(getProps(vnode).style).toContain('display:inline-flex');
  });

  it('Flex not inline by default', () => {
    const vnode = Flex({ children: 'Content' });
    expect(getProps(vnode).style).toContain('display:flex');
  });

  it('Grid renders', () => {
    const vnode = Grid({ columns: 3, children: 'Content' });
    expect(getClassName(vnode)).toContain('arcanis-grid');
    expect(getProps(vnode).style).toContain('grid-template-columns:repeat(3,1fr)');
  });

  it('Grid with rows', () => {
    const vnode = Grid({ columns: 2, rows: 3, children: 'Content' });
    expect(getProps(vnode).style).toContain('grid-template-rows:repeat(3,1fr)');
  });

  it('Grid default column', () => {
    const vnode = Grid({ children: 'Content' });
    expect(getProps(vnode).style).toContain('grid-template-columns:repeat(1,1fr)');
  });

  it('Center renders', () => {
    const vnode = Center({ children: 'Centered' });
    expect(getClassName(vnode)).toContain('arcanis-center');
    expect(getProps(vnode).style).toContain('align-items:center');
    expect(getProps(vnode).style).toContain('justify-content:center');
  });

  it('Spacer renders with size md', () => {
    const vnode = Spacer({ size: 'md' });
    expect(getClassName(vnode)).toContain('arcanis-spacer');
    expect(getProps(vnode).style).toContain('width:16px');
    expect(getProps(vnode).style).toContain('height:16px');
  });

  it('Spacer default size', () => {
    const vnode = Spacer({});
    expect(getProps(vnode).style).toContain('width:16px');
  });

  it('Divider horizontal', () => {
    const vnode = Divider({ orientation: 'horizontal' });
    expect(getClassName(vnode)).toContain('arcanis-divider--horizontal');
    expect(getProps(vnode).role).toBe('separator');
  });

  it('Divider vertical', () => {
    const vnode = Divider({ orientation: 'vertical' });
    expect(getClassName(vnode)).toContain('arcanis-divider--vertical');
  });

  it('Divider default horizontal', () => {
    const vnode = Divider({});
    expect(getClassName(vnode)).toContain('arcanis-divider--horizontal');
  });
});

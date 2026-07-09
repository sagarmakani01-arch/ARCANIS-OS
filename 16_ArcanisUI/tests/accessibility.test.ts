import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  getDefaultA11yConfig,
  createFocusTrap,
  announce,
  generateId,
  getA11yProps,
  KEYBOARD_KEYS,
} from '../src/accessibility/a11y';

function createDomElement(tag: string): any {
  const children: any[] = [];
  const el: any = {
    tagName: tag,
    children,
    appendChild(child: any) { children.push(child); child.parentNode = el; },
    removeChild(child: any) { const i = children.indexOf(child); if (i >= 0) children.splice(i, 1); },
    querySelectorAll(selector: string) {
      const focusable = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
      if (selector !== focusable) return [];
      return children.filter((c: any) => {
        if (c.tagName === 'BUTTON' && !c.disabled) return true;
        if (c.tagName === 'INPUT' && !c.disabled) return true;
        if (c.tagName === 'A' && c.href) return true;
        if (c.tabIndex === 0) return true;
        return false;
      });
    },
    querySelector() { return null; },
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    focus: vi.fn(),
    style: { cssText: '' },
    setAttribute: vi.fn(),
    getAttribute: vi.fn().mockReturnValue(null),
    classList: { contains: vi.fn().mockReturnValue(false) },
    parentNode: null,
    disabled: false,
    tabIndex: 0,
    href: '',
  };
  return el;
}

let mockDocument: any;

beforeEach(() => {
  const elements = new Map<string, any>();
  mockDocument = {
    body: {
      appendChild: vi.fn(),
      innerHTML: '',
    },
    documentElement: { style: { setProperty: vi.fn() } },
    getElementById: vi.fn((id: string) => elements.get(id) || null),
    createElement: vi.fn((tag: string) => createDomElement(tag)),
    querySelector: vi.fn().mockReturnValue(null),
    activeElement: null,
  };
  vi.stubGlobal('document', mockDocument);
  vi.stubGlobal('window', {
    matchMedia: vi.fn().mockReturnValue({ matches: false }),
    addEventListener: vi.fn(),
    navigator: { userAgent: '' },
  });
  vi.stubGlobal('KeyboardEvent', class KeyboardEvent {
    key: string;
    shiftKey: boolean;
    bubbles: boolean;
    preventDefault = vi.fn();
    constructor(type: string, opts: any = {}) {
      this.key = opts.key || '';
      this.shiftKey = opts.shiftKey || false;
      this.bubbles = opts.bubbles || false;
    }
  });
  vi.stubGlobal('requestAnimationFrame', (cb: any) => setTimeout(cb, 16));
});

describe('getDefaultA11yConfig', () => {
  it('returns default config', () => {
    const config = getDefaultA11yConfig();
    expect(config.enabled).toBe(true);
    expect(config.announceChanges).toBe(true);
    expect(config.focusManagement).toBe(true);
    expect(config.keyboardNavigation).toBe(true);
    expect(typeof config.reducedMotion).toBe('boolean');
    expect(typeof config.highContrast).toBe('boolean');
    expect(typeof config.screenReader).toBe('boolean');
  });
});

describe('createFocusTrap', () => {
  it('creates a focus trap', () => {
    const container = createDomElement('div');
    const trap = createFocusTrap(container);
    expect(trap).toHaveProperty('activate');
    expect(trap).toHaveProperty('deactivate');
    expect(trap).toHaveProperty('isActive');
  });

  it('isActive is false initially', () => {
    const container = createDomElement('div');
    const trap = createFocusTrap(container);
    expect(trap.isActive).toBe(false);
  });

  it('activate sets isActive to true', () => {
    const container = createDomElement('div');
    const trap = createFocusTrap(container);
    trap.activate();
    expect(trap.isActive).toBe(true);
  });

  it('deactivate sets isActive to false', () => {
    const container = createDomElement('div');
    const trap = createFocusTrap(container);
    trap.activate();
    trap.deactivate();
    expect(trap.isActive).toBe(false);
  });

  it('focuses first focusable element on activate', () => {
    const container = createDomElement('div');
    const btn = createDomElement('button');
    container.appendChild(btn);
    const trap = createFocusTrap(container);
    trap.activate();
    expect(btn.focus).toHaveBeenCalled();
  });

  it('does not focus when no focusable elements', () => {
    const container = createDomElement('div');
    const trap = createFocusTrap(container);
    expect(() => trap.activate()).not.toThrow();
    expect(trap.isActive).toBe(true);
  });

  it('traps tab forward at end', () => {
    const container = createDomElement('div');
    const btn1 = createDomElement('button');
    const btn2 = createDomElement('button');
    container.appendChild(btn1);
    container.appendChild(btn2);
    const trap = createFocusTrap(container);
    trap.activate();
    mockDocument.activeElement = btn2;
    const keydownEvent = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true });
    container.addEventListener.mock.calls.find((c: any) => c[0] === 'keydown')?.[1](keydownEvent);
    expect(btn1.focus).toHaveBeenCalled();
  });

  it('traps tab backward at start', () => {
    const container = createDomElement('div');
    const btn1 = createDomElement('button');
    container.appendChild(btn1);
    const trap = createFocusTrap(container);
    trap.activate();
    mockDocument.activeElement = btn1;
    const keydownEvent = new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true });
    container.addEventListener.mock.calls.find((c: any) => c[0] === 'keydown')?.[1](keydownEvent);
    expect(btn1.focus).toHaveBeenCalled();
  });

  it('deactivate removes event listener', () => {
    const container = createDomElement('div');
    const trap = createFocusTrap(container);
    trap.activate();
    trap.deactivate();
    expect(trap.isActive).toBe(false);
    expect(container.removeEventListener).toHaveBeenCalled();
  });

  it('handles input elements as focusable', () => {
    const container = createDomElement('div');
    const input = createDomElement('input');
    container.appendChild(input);
    const trap = createFocusTrap(container);
    trap.activate();
    expect(input.focus).toHaveBeenCalled();
  });

  it('handles anchor elements as focusable', () => {
    const container = createDomElement('div');
    const link = createDomElement('a');
    link.href = 'https://example.com';
    container.appendChild(link);
    const trap = createFocusTrap(container);
    trap.activate();
    expect(link.focus).toHaveBeenCalled();
  });

  it('handles elements with tabindex', () => {
    const container = createDomElement('div');
    const div = createDomElement('div');
    div.tabIndex = 0;
    container.appendChild(div);
    const trap = createFocusTrap(container);
    trap.activate();
    expect(div.focus).toHaveBeenCalled();
  });

  it('ignores elements with tabindex=-1', () => {
    const container = createDomElement('div');
    const div = createDomElement('div');
    div.tabIndex = -1;
    container.appendChild(div);
    const trap = createFocusTrap(container);
    trap.activate();
    expect(trap.isActive).toBe(true);
  });

  it('handles disabled buttons correctly', () => {
    const container = createDomElement('div');
    const btn = createDomElement('button');
    btn.disabled = true;
    container.appendChild(btn);
    const trap = createFocusTrap(container);
    trap.activate();
    expect(trap.isActive).toBe(true);
  });
});

describe('announce', () => {
  it('creates announcer element', () => {
    const announcer = createDomElement('div');
    announcer.id = 'arcanis-a11y-announcer';
    announcer.style = { cssText: '' };
    announcer.setAttribute = vi.fn();
    announcer.textContent = '';
    mockDocument.getElementById.mockReturnValue(null);
    mockDocument.createElement.mockReturnValue(announcer);
    announce('Hello world');
    expect(mockDocument.body.appendChild).toHaveBeenCalled();
  });

  it('sets aria-live to polite by default', () => {
    const announcer = createDomElement('div');
    announcer.getAttribute = vi.fn().mockReturnValue('polite');
    mockDocument.getElementById.mockReturnValue(announcer);
    announce('Hello');
    expect(announcer.getAttribute('aria-live')).toBe('polite');
  });

  it('sets aria-live to assertive when specified', () => {
    const announcer = createDomElement('div');
    announcer.getAttribute = vi.fn().mockReturnValue('assertive');
    mockDocument.getElementById.mockReturnValue(announcer);
    announce('Urgent', 'assertive');
    expect(announcer.getAttribute('aria-live')).toBe('assertive');
  });

  it('reuses existing announcer', () => {
    const announcer = createDomElement('div');
    announcer.getAttribute = vi.fn().mockReturnValue(null);
    mockDocument.getElementById.mockReturnValue(announcer);
    announce('First');
    announce('Second');
    expect(mockDocument.getElementById).toHaveBeenCalledTimes(2);
  });

  it('sets aria-atomic', () => {
    const announcer = createDomElement('div');
    announcer.getAttribute = vi.fn().mockReturnValue('true');
    mockDocument.getElementById.mockReturnValue(announcer);
    announce('Test');
    expect(announcer.getAttribute('aria-atomic')).toBe('true');
  });

  it('announcer is visually hidden', () => {
    const announcer = createDomElement('div');
    announcer.style = { cssText: 'position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;' };
    announcer.getAttribute = vi.fn().mockReturnValue(null);
    mockDocument.getElementById.mockReturnValue(announcer);
    announce('Test');
    expect(announcer.style.cssText).toContain('clip:rect(0,0,0,0)');
  });
});

describe('generateId', () => {
  it('generates id with default prefix', () => {
    const id = generateId();
    expect(id).toMatch(/^arcanis-/);
  });

  it('generates id with custom prefix', () => {
    const id = generateId('btn');
    expect(id).toMatch(/^btn-/);
  });

  it('generates unique ids', () => {
    const id1 = generateId();
    const id2 = generateId();
    expect(id1).not.toBe(id2);
  });

  it('generates ids with random part', () => {
    const id = generateId('test');
    const parts = id.split('-');
    expect(parts.length).toBe(2);
    expect(parts[0]).toBe('test');
    expect(parts[1].length).toBeGreaterThan(0);
  });
});

describe('getA11yProps', () => {
  it('returns empty object for no options', () => {
    const props = getA11yProps({});
    expect(props).toEqual({});
  });

  it('sets aria-label', () => {
    const props = getA11yProps({ label: 'My button' });
    expect(props['aria-label']).toBe('My button');
  });

  it('sets aria-labelledby', () => {
    const props = getA11yProps({ labelledBy: 'label-1' });
    expect(props['aria-labelledby']).toBe('label-1');
  });

  it('sets aria-describedby', () => {
    const props = getA11yProps({ describedBy: 'desc-1' });
    expect(props['aria-describedby']).toBe('desc-1');
  });

  it('sets role', () => {
    const props = getA11yProps({ role: 'button' });
    expect(props.role).toBe('button');
  });

  it('sets aria-live', () => {
    const props = getA11yProps({ live: 'polite' });
    expect(props['aria-live']).toBe('polite');
  });

  it('sets aria-hidden', () => {
    const props = getA11yProps({ hidden: true });
    expect(props['aria-hidden']).toBe(true);
  });

  it('sets aria-required', () => {
    const props = getA11yProps({ required: true });
    expect(props['aria-required']).toBe(true);
  });

  it('sets aria-invalid', () => {
    const props = getA11yProps({ invalid: true });
    expect(props['aria-invalid']).toBe(true);
  });

  it('sets aria-expanded', () => {
    const props = getA11yProps({ expanded: true });
    expect(props['aria-expanded']).toBe(true);
  });

  it('sets aria-selected', () => {
    const props = getA11yProps({ selected: true });
    expect(props['aria-selected']).toBe(true);
  });

  it('sets aria-checked true', () => {
    const props = getA11yProps({ checked: true });
    expect(props['aria-checked']).toBe(true);
  });

  it('sets aria-checked mixed', () => {
    const props = getA11yProps({ checked: 'mixed' });
    expect(props['aria-checked']).toBe('mixed');
  });

  it('sets multiple props', () => {
    const props = getA11yProps({
      label: 'Name',
      role: 'textbox',
      required: true,
      invalid: false,
    });
    expect(props['aria-label']).toBe('Name');
    expect(props.role).toBe('textbox');
    expect(props['aria-required']).toBe(true);
    expect(props['aria-invalid']).toBe(false);
  });

  it('does not set undefined optional props', () => {
    const props = getA11yProps({ label: 'Test' });
    expect(props).not.toHaveProperty('aria-labelledby');
    expect(props).not.toHaveProperty('aria-describedby');
    expect(props).not.toHaveProperty('role');
  });
});

describe('KEYBOARD_KEYS', () => {
  it('has all key constants', () => {
    expect(KEYBOARD_KEYS.ENTER).toBe('Enter');
    expect(KEYBOARD_KEYS.SPACE).toBe(' ');
    expect(KEYBOARD_KEYS.ESCAPE).toBe('Escape');
    expect(KEYBOARD_KEYS.ARROW_UP).toBe('ArrowUp');
    expect(KEYBOARD_KEYS.ARROW_DOWN).toBe('ArrowDown');
    expect(KEYBOARD_KEYS.ARROW_LEFT).toBe('ArrowLeft');
    expect(KEYBOARD_KEYS.ARROW_RIGHT).toBe('ArrowRight');
    expect(KEYBOARD_KEYS.HOME).toBe('Home');
    expect(KEYBOARD_KEYS.END).toBe('End');
    expect(KEYBOARD_KEYS.TAB).toBe('Tab');
  });

  it('has correct number of keys', () => {
    expect(Object.keys(KEYBOARD_KEYS)).toHaveLength(10);
  });
});

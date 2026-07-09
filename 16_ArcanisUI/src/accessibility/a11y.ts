export interface A11yConfig {
  enabled: boolean;
  announceChanges: boolean;
  focusManagement: boolean;
  keyboardNavigation: boolean;
  reducedMotion: boolean;
  highContrast: boolean;
  screenReader: boolean;
}

export interface FocusTrap {
  activate(): void;
  deactivate(): void;
  readonly isActive: boolean;
}

export function getDefaultA11yConfig(): A11yConfig {
  return {
    enabled: true,
    announceChanges: true,
    focusManagement: true,
    keyboardNavigation: true,
    reducedMotion: prefersReducedMotion(),
    highContrast: prefersHighContrast(),
    screenReader: hasScreenReader(),
  };
}

function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function prefersHighContrast(): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-contrast: high)').matches;
}

function hasScreenReader(): boolean {
  if (typeof window === 'undefined') return false;
  return !!(
    window.navigator.userAgent.includes('NVDA') ||
    window.navigator.userAgent.includes('JAWS') ||
    window.navigator.userAgent.includes('VoiceOver') ||
    document.querySelector('[aria-live]') !== null
  );
}

export function createFocusTrap(container: Element): FocusTrap {
  let isActive = false;
  const focusableSelectors = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

  function getFocusableElements(): HTMLElement[] {
    return Array.from(container.querySelectorAll(focusableSelectors)) as HTMLElement[];
  }

  function handleKeydown(e: KeyboardEvent): void {
    if (e.key !== 'Tab') return;

    const focusable = getFocusableElements();
    if (focusable.length === 0) return;

    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault();
        last.focus();
      }
    } else {
      if (document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  }

  return {
    activate() {
      isActive = true;
      container.addEventListener('keydown', handleKeydown);
      const focusable = getFocusableElements();
      if (focusable.length > 0) {
        focusable[0].focus();
      }
    },
    deactivate() {
      isActive = false;
      container.removeEventListener('keydown', handleKeydown);
    },
    get isActive() { return isActive; },
  };
}

export function announce(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
  if (typeof document === 'undefined') return;

  let announcer = document.getElementById('arcanis-a11y-announcer');
  if (!announcer) {
    announcer = document.createElement('div');
    announcer.id = 'arcanis-a11y-announcer';
    announcer.setAttribute('aria-live', priority);
    announcer.setAttribute('aria-atomic', 'true');
    announcer.style.cssText = 'position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;';
    document.body.appendChild(announcer);
  }

  announcer.setAttribute('aria-live', priority);
  announcer.textContent = '';
  requestAnimationFrame(() => {
    announcer!.textContent = message;
  });
}

export function generateId(prefix = 'arcanis'): string {
  return `${prefix}-${Math.random().toString(36).slice(2, 9)}`;
}

export function getA11yProps(options: {
  label?: string;
  labelledBy?: string;
  describedBy?: string;
  role?: string;
  live?: 'polite' | 'assertive' | 'off';
  hidden?: boolean;
  required?: boolean;
  invalid?: boolean;
  expanded?: boolean;
  selected?: boolean;
  checked?: boolean | 'mixed';
}): Record<string, string | boolean | undefined> {
  const props: Record<string, string | boolean | undefined> = {};

  if (options.label) props['aria-label'] = options.label;
  if (options.labelledBy) props['aria-labelledby'] = options.labelledBy;
  if (options.describedBy) props['aria-describedby'] = options.describedBy;
  if (options.role) props['role'] = options.role;
  if (options.live) props['aria-live'] = options.live;
  if (options.hidden) props['aria-hidden'] = true;
  if (options.required !== undefined) props['aria-required'] = options.required;
  if (options.invalid !== undefined) props['aria-invalid'] = options.invalid;
  if (options.expanded !== undefined) props['aria-expanded'] = options.expanded;
  if (options.selected !== undefined) props['aria-selected'] = options.selected;
  if (options.checked !== undefined) props['aria-checked'] = options.checked;

  return props;
}

export const KEYBOARD_KEYS = {
  ENTER: 'Enter',
  SPACE: ' ',
  ESCAPE: 'Escape',
  ARROW_UP: 'ArrowUp',
  ARROW_DOWN: 'ArrowDown',
  ARROW_LEFT: 'ArrowLeft',
  ARROW_RIGHT: 'ArrowRight',
  HOME: 'Home',
  END: 'End',
  TAB: 'Tab',
} as const;

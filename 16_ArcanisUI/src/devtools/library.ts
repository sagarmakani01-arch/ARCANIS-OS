export interface ComponentMeta {
  name: string;
  category: string;
  description: string;
  props: PropMeta[];
  examples: string;
  tags: string[];
}

export interface PropMeta {
  name: string;
  type: string;
  defaultValue?: string;
  required?: boolean;
  description: string;
}

const registry: Map<string, ComponentMeta> = new Map();

export function registerComponent(meta: ComponentMeta): void {
  registry.set(meta.name, meta);
}

export function getComponent(name: string): ComponentMeta | undefined {
  return registry.get(name);
}

export function getAllComponents(): ComponentMeta[] {
  return Array.from(registry.values());
}

export function getComponentsByCategory(category: string): ComponentMeta[] {
  return getAllComponents().filter((c) => c.category === category);
}

export function searchComponents(query: string): ComponentMeta[] {
  const lower = query.toLowerCase();
  return getAllComponents().filter(
    (c) =>
      c.name.toLowerCase().includes(lower) ||
      c.description.toLowerCase().includes(lower) ||
      c.tags.some((t) => t.toLowerCase().includes(lower))
  );
}

export function getCategories(): string[] {
  const categories = new Set<string>();
  registry.forEach((meta) => categories.add(meta.category));
  return Array.from(categories).sort();
}

export function initComponentLibrary(): void {
  registerComponent({
    name: 'Button',
    category: 'Forms',
    description: 'Interactive button component with multiple variants, sizes, and states.',
    props: [
      { name: 'variant', type: "'primary' | 'secondary' | 'ghost' | 'danger' | 'outline' | 'link'", defaultValue: 'primary', description: 'Visual style variant' },
      { name: 'size', type: "'xs' | 'sm' | 'md' | 'lg' | 'xl'", defaultValue: 'md', description: 'Button size' },
      { name: 'disabled', type: 'boolean', defaultValue: 'false', description: 'Whether the button is disabled' },
      { name: 'loading', type: 'boolean', defaultValue: 'false', description: 'Shows loading spinner' },
      { name: 'fullWidth', type: 'boolean', defaultValue: 'false', description: 'Expands to full width' },
      { name: 'onClick', type: '(event: MouseEvent) => void', description: 'Click handler' },
    ],
    examples: `Button({ variant: 'primary', size: 'md', children: 'Click Me' })`,
    tags: ['form', 'interactive', 'click'],
  });

  registerComponent({
    name: 'Input',
    category: 'Forms',
    description: 'Text input component with labels, validation, and addons.',
    props: [
      { name: 'type', type: "'text' | 'email' | 'password' | 'number'", defaultValue: 'text', description: 'Input type' },
      { name: 'size', type: "'sm' | 'md' | 'lg'", defaultValue: 'md', description: 'Input size' },
      { name: 'placeholder', type: 'string', description: 'Placeholder text' },
      { name: 'value', type: 'string', description: 'Controlled value' },
      { name: 'disabled', type: 'boolean', defaultValue: 'false', description: 'Disabled state' },
      { name: 'error', type: 'boolean', defaultValue: 'false', description: 'Error state' },
      { name: 'label', type: 'string', description: 'Input label' },
    ],
    examples: `Input({ label: 'Email', type: 'email', placeholder: 'you@example.com' })`,
    tags: ['form', 'text', 'input'],
  });

  registerComponent({
    name: 'Modal',
    category: 'Layout',
    description: 'Dialog overlay component for important content or actions.',
    props: [
      { name: 'open', type: 'boolean', required: true, description: 'Whether modal is visible' },
      { name: 'onClose', type: '() => void', required: true, description: 'Close handler' },
      { name: 'title', type: 'string', description: 'Modal title' },
      { name: 'size', type: "'sm' | 'md' | 'lg' | 'xl' | 'full'", defaultValue: 'md', description: 'Modal size' },
      { name: 'closeOnOverlayClick', type: 'boolean', defaultValue: 'true', description: 'Close on overlay click' },
    ],
    examples: `Modal({ open: true, title: 'Confirm', children: content })`,
    tags: ['layout', 'dialog', 'overlay'],
  });

  registerComponent({
    name: 'Card',
    category: 'Layout',
    description: 'Container component for grouping related content.',
    props: [
      { name: 'variant', type: "'elevated' | 'outlined' | 'filled'", defaultValue: 'elevated', description: 'Visual variant' },
      { name: 'padding', type: "'none' | 'sm' | 'md' | 'lg'", defaultValue: 'md', description: 'Inner padding' },
      { name: 'hoverable', type: 'boolean', defaultValue: 'false', description: 'Hover effect' },
      { name: 'selected', type: 'boolean', description: 'Selected state' },
    ],
    examples: `Card({ variant: 'elevated' }, CardHeader({ title: 'Title' }))`,
    tags: ['layout', 'container'],
  });

  registerComponent({
    name: 'Select',
    category: 'Forms',
    description: 'Dropdown select component for choosing from options.',
    props: [
      { name: 'options', type: 'SelectOption[]', required: true, description: 'Available options' },
      { name: 'value', type: 'string', description: 'Selected value' },
      { name: 'placeholder', type: 'string', description: 'Placeholder text' },
      { name: 'label', type: 'string', description: 'Select label' },
    ],
    examples: `Select({ options: [{ value: 'a', label: 'Option A' }] })`,
    tags: ['form', 'dropdown', 'select'],
  });

  registerComponent({
    name: 'Badge',
    category: 'Data Display',
    description: 'Status indicator and label component.',
    props: [
      { name: 'variant', type: "'primary' | 'success' | 'warning' | 'error'", defaultValue: 'primary', description: 'Color variant' },
      { name: 'size', type: "'sm' | 'md' | 'lg'", defaultValue: 'md', description: 'Badge size' },
      { name: 'dot', type: 'boolean', defaultValue: 'false', description: 'Shows dot indicator' },
    ],
    examples: `Badge({ variant: 'success', children: 'Active' })`,
    tags: ['display', 'status', 'label'],
  });

  registerComponent({
    name: 'Tabs',
    category: 'Navigation',
    description: 'Tabbed navigation component for switching between views.',
    props: [
      { name: 'tabs', type: 'TabItem[]', required: true, description: 'Tab definitions' },
      { name: 'activeId', type: 'string', description: 'Active tab ID' },
      { name: 'variant', type: "'line' | 'enclosed' | 'pills'", defaultValue: 'line', description: 'Tab style' },
    ],
    examples: `Tabs({ tabs: [{ id: '1', label: 'Tab 1', content: ... }] })`,
    tags: ['navigation', 'tabs'],
  });
}

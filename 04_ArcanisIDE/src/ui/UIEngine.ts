import { EventBus } from '../core/EventBus';
import { Configuration } from '../core/Configuration';
import { ThemeManager, Theme } from './themes/ThemeManager';

export interface UIComponent {
  id: string;
  render(): string;
  onMount?(): void;
  onUnmount?(): void;
  update(props: Record<string, unknown>): void;
}

export type NotificationType = 'info' | 'warning' | 'error' | 'success';

export interface InputBoxOptions {
  title?: string;
  prompt?: string;
  value?: string;
  placeholder?: string;
  validateInput?: (value: string) => string | undefined;
}

export interface QuickPickItem<T = unknown> {
  label: string;
  description?: string;
  detail?: string;
  value: T;
  icon?: string;
}

export interface QuickPickOptions {
  placeholder?: string;
  canPickMany?: boolean;
  matchOnDescription?: boolean;
}

export interface MessageBoxOptions {
  title?: string;
  message: string;
  detail?: string;
  buttons: string[];
  defaultButton?: number;
  cancelButton?: number;
}

export interface MessageBoxResult {
  button: number;
  checkboxChecked?: boolean;
}

export class UIEngine {
  private components: Map<string, UIComponent> = new Map();
  private themeManager: ThemeManager;
  private visiblePanels: Set<string> = new Set();
  private initialized = false;

  constructor(
    private eventBus: EventBus,
    private configuration: Configuration,
  ) {
    this.themeManager = new ThemeManager(eventBus, configuration);
  }

  async initialize(): Promise<void> {
    if (this.initialized) return;

    this.themeManager = new ThemeManager(this.eventBus, this.configuration);

    this.initialized = true;
    this.eventBus.emit('ui:initialized', { timestamp: Date.now() });
  }

  render(): void {
    if (!this.initialized) {
      console.warn('[UIEngine] Cannot render before initialization');
      return;
    }

    const theme = this.themeManager.getTheme();
    const html = this.renderLayout(theme);
    const globalObj = globalThis as { document?: { getElementById: (id: string) => { innerHTML: string } | null } };
    const rootEl = globalObj.document?.getElementById('app') ?? null;
    if (rootEl) {
      rootEl.innerHTML = html;
    } else {
      console.log('[UIEngine] Render output (no DOM):', html.substring(0, 100) + '...');
    }
  }

  private renderLayout(theme: Theme): string {
    return `
      <div class="arcanis-shell" style="background:${theme.colors['editor.background']};color:${theme.colors['editor.foreground']};">
        <div class="arcanis-menu-bar" style="background:${theme.colors['sidebar.background']};">
          <!-- menu bar content -->
        </div>
        <div class="arcanis-body" style="display:flex;flex:1;overflow:hidden;">
          <div class="arcanis-sidebar" style="width:260px;background:${theme.colors['sidebar.background']};color:${theme.colors['sidebar.foreground']};">
            ${this.renderComponent('project-explorer')}
          </div>
          <div class="arcanis-main" style="flex:1;display:flex;flex-direction:column;overflow:hidden;">
            <div class="arcanis-editor-area" style="flex:1;overflow:hidden;">
              ${this.renderComponent('editor-view')}
            </div>
            <div class="arcanis-panel" style="background:${theme.colors['panel.background']};color:${theme.colors['panel.foreground']};">
              ${this.renderComponent('panel')}
            </div>
          </div>
        </div>
        <div class="arcanis-status-bar" style="background:${theme.colors['statusBar.background']};color:${theme.colors['statusBar.foreground']};">
          ${this.renderComponent('status-bar')}
        </div>
      </div>
    `;
  }

  private renderComponent(id: string): string {
    const component = this.components.get(id);
    if (component) {
      return component.render();
    }
    return `<div class="component-${id}"></div>`;
  }

  getComponent<T extends UIComponent>(id: string): T | undefined {
    return this.components.get(id) as T | undefined;
  }

  registerComponent(id: string, component: UIComponent): void {
    this.components.set(id, component);
    this.eventBus.emit('ui:componentRegistered', { id, component });
  }

  showPanel(panelId: string): void {
    this.visiblePanels.add(panelId);
    this.eventBus.emit('ui:panelShown', { panelId });
  }

  hidePanel(panelId: string): void {
    this.visiblePanels.delete(panelId);
    this.eventBus.emit('ui:panelHidden', { panelId });
  }

  togglePanel(panelId: string): void {
    if (this.visiblePanels.has(panelId)) {
      this.hidePanel(panelId);
    } else {
      this.showPanel(panelId);
    }
  }

  getThemeManager(): ThemeManager {
    return this.themeManager;
  }

  showNotification(message: string, type: NotificationType): void {
    this.eventBus.emit('ui:notification', { message, type, timestamp: Date.now() });
  }

  showInputBox(options: InputBoxOptions): Promise<string | undefined> {
    return new Promise((resolve) => {
      this.eventBus.emit('ui:showInputBox', { options, resolve });
    });
  }

  showQuickPick<T>(items: QuickPickItem<T>[], options?: QuickPickOptions): Promise<T | undefined> {
    return new Promise((resolve) => {
      this.eventBus.emit('ui:showQuickPick', { items, options, resolve });
    });
  }

  showMessageBox(options: MessageBoxOptions): Promise<MessageBoxResult> {
    return new Promise((resolve) => {
      this.eventBus.emit('ui:showMessageBox', { options, resolve });
    });
  }
}

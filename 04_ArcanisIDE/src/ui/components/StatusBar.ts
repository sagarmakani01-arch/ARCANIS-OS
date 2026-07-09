import { IDisposable } from '../../api/types';
import { EventBus } from '../../core/EventBus';
import { UIComponent } from '../UIEngine';

export interface StatusBarItem {
  id: string;
  text: string;
  tooltip?: string;
  command?: string;
  priority?: number;
}

export class StatusBar implements UIComponent {
  id = 'status-bar';
  private leftText = '';
  private rightText = '';
  private message: { text: string; type: string; until: number } | null = null;
  private languageId = 'Plain Text';
  private cursorLine = 1;
  private cursorColumn = 1;
  private encoding = 'UTF-8';
  private tabSize = 4;
  private insertSpaces = true;
  private branch = 'main';
  private buildMode = 'debug';
  private leftItems: StatusBarItem[] = [];
  private rightItems: StatusBarItem[] = [];
  private disposables: IDisposable[] = [];

  constructor(private eventBus: EventBus) {}

  render(): string {
    const leftHtml = this.renderLeftItems();
    const rightHtml = this.renderRightItems();

    const messageHtml = this.message
      ? `<span class="status-bar-message status-${this.message.type}">${this.escapeHtml(this.message.text)}</span>`
      : '';

    const leftSide = this.leftText || leftHtml || messageHtml;
    const rightSide = [
      this.branch ? `<span class="status-bar-item" title="Git branch">$(branch) ${this.escapeHtml(this.branch)}</span>` : '',
      `<span class="status-bar-item" title="Build Mode">${this.escapeHtml(this.buildMode)}</span>`,
      `<span class="status-bar-item" title="Encoding">${this.escapeHtml(this.encoding)}</span>`,
      `<span class="status-bar-item" title="Indentation">${this.insertSpaces ? 'Spaces' : 'Tabs'}: ${this.tabSize}</span>`,
      `<span class="status-bar-item" title="Cursor Position">Ln ${this.cursorLine}, Col ${this.cursorColumn}</span>`,
      `<span class="status-bar-item" title="Language">${this.escapeHtml(this.languageId)}</span>`,
      rightHtml,
    ].filter(Boolean).join('<span class="status-bar-separator">|</span>');

    return `<div class="status-bar-inner">
      <div class="status-bar-left">${leftSide}</div>
      <div class="status-bar-right">${rightSide}</div>
    </div>`;
  }

  private renderLeftItems(): string {
    const sorted = [...this.leftItems].sort((a, b) => (b.priority || 0) - (a.priority || 0));
    return sorted
      .map(
        (item) =>
          `<span class="status-bar-item" data-command="${item.command || ''}" title="${this.escapeHtml(item.tooltip || item.text)}">${this.escapeHtml(item.text)}</span>`,
      )
      .join('');
  }

  private renderRightItems(): string {
    const sorted = [...this.rightItems].sort((a, b) => (b.priority || 0) - (a.priority || 0));
    return sorted
      .map(
        (item) =>
          `<span class="status-bar-item" data-command="${item.command || ''}" title="${this.escapeHtml(item.tooltip || item.text)}">${this.escapeHtml(item.text)}</span>`,
      )
      .join('');
  }

  private escapeHtml(text: string): string {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  onMount(): void {
    const sub = this.eventBus.on<{ text: string; type: 'info' | 'warning' | 'error' }>(
      'statusBar:message',
      (payload) => this.showMessage(payload.text, payload.type),
    );
    this.disposables.push(sub);
  }

  onUnmount(): void {
    for (const d of this.disposables) {
      d.dispose();
    }
    this.disposables = [];
  }

  update(props: Record<string, unknown>): void {
    if (props.leftText) this.leftText = props.leftText as string;
    if (props.rightText) this.rightText = props.rightText as string;
    if (props.languageId) this.languageId = props.languageId as string;
    if (props.cursorLine !== undefined) this.cursorLine = props.cursorLine as number;
    if (props.cursorColumn !== undefined) this.cursorColumn = props.cursorColumn as number;
  }

  setText(left: string, right?: string): void {
    this.leftText = left;
    if (right !== undefined) {
      this.rightText = right;
    }
  }

  showMessage(text: string, type?: 'info' | 'warning' | 'error', duration?: number): void {
    this.message = {
      text,
      type: type || 'info',
      until: Date.now() + (duration || 5000),
    };
    setTimeout(() => {
      if (this.message && this.message.until <= Date.now()) {
        this.message = null;
      }
    }, duration || 5000);
  }

  setLanguage(languageId: string): void {
    this.languageId = languageId;
  }

  setCursorPosition(line: number, column: number): void {
    this.cursorLine = line;
    this.cursorColumn = column;
    this.eventBus.emit('statusBar:cursorChanged', { line, column });
  }

  setEncoding(encoding: string): void {
    this.encoding = encoding;
  }

  setIndentation(tabSize: number, insertSpaces: boolean): void {
    this.tabSize = tabSize;
    this.insertSpaces = insertSpaces;
  }

  setBranch(branch: string): void {
    this.branch = branch;
  }

  setBuildMode(mode: string): void {
    this.buildMode = mode;
  }

  addLeftItem(item: StatusBarItem): IDisposable {
    this.leftItems.push(item);
    return {
      dispose: () => {
        const idx = this.leftItems.indexOf(item);
        if (idx >= 0) this.leftItems.splice(idx, 1);
      },
    };
  }

  addRightItem(item: StatusBarItem): IDisposable {
    this.rightItems.push(item);
    return {
      dispose: () => {
        const idx = this.rightItems.indexOf(item);
        if (idx >= 0) this.rightItems.splice(idx, 1);
      },
    };
  }
}

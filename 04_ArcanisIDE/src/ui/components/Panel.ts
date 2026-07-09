import { DiagnosticSeverity, Diagnostic } from '../../api/types';
import { EventBus } from '../../core/EventBus';
import { UIComponent } from '../UIEngine';

interface PanelTab {
  id: string;
  title: string;
  content: string;
  outputLines: string[];
}

export class Panel implements UIComponent {
  id = 'panel';
  private tabs: Map<string, PanelTab> = new Map();
  private activeTabId = 'OUTPUT';
  private visible = true;
  private panelHeight = 200;
  private diagnostics: Diagnostic[] = [];
  private subscriptions: { dispose: () => void }[] = [];

  constructor(private eventBus: EventBus) {
    this.initializeDefaultTabs();
  }

  private initializeDefaultTabs(): void {
    this.tabs.set('OUTPUT', { id: 'OUTPUT', title: 'OUTPUT', content: '', outputLines: [] });
    this.tabs.set('PROBLEMS', { id: 'PROBLEMS', title: 'PROBLEMS', content: '', outputLines: [] });
    this.tabs.set('DEBUG CONSOLE', { id: 'DEBUG CONSOLE', title: 'DEBUG CONSOLE', content: '', outputLines: [] });
    this.tabs.set('TERMINAL', { id: 'TERMINAL', title: 'TERMINAL', content: '', outputLines: [] });
  }

  render(): string {
    if (!this.visible) {
      return '<div class="panel-hidden"></div>';
    }

    const tabsHtml = this.renderTabs();
    const activeContent = this.renderActiveContent();

    return `<div class="panel-container" style="height:${this.panelHeight}px;">
      <div class="panel-tabs">${tabsHtml}</div>
      <div class="panel-content">${activeContent}</div>
      <div class="panel-resize-handle"></div>
    </div>`;
  }

  private renderTabs(): string {
    return Array.from(this.tabs.values())
      .map((tab) => {
        const isActive = tab.id === this.activeTabId;
        return `<div class="panel-tab ${isActive ? 'active' : ''}" data-tab-id="${tab.id}">
          <span class="panel-tab-title">${tab.title}</span>
          <button class="panel-tab-close" data-tab-id="${tab.id}">×</button>
        </div>`;
      })
      .join('');
  }

  private renderActiveContent(): string {
    if (this.activeTabId === 'PROBLEMS') {
      return this.renderProblems();
    }

    const tab = this.tabs.get(this.activeTabId);
    if (!tab) return '';

    const linesHtml = tab.outputLines
      .map((line) => `<div class="panel-output-line">${this.escapeHtml(line)}</div>`)
      .join('');

    return `<div class="panel-output">${linesHtml}</div>`;
  }

  private renderProblems(): string {
    if (this.diagnostics.length === 0) {
      return '<div class="panel-problems-empty">No problems detected</div>';
    }

    const groups = new Map<string, Diagnostic[]>();
    for (const d of this.diagnostics) {
      const source = d.source || 'unknown';
      if (!groups.has(source)) groups.set(source, []);
      groups.get(source)!.push(d);
    }

    let html = '';
    for (const [source, diags] of groups) {
      html += `<div class="panel-problem-group">
        <div class="panel-problem-source">${this.escapeHtml(source)}</div>
        ${diags
          .map((d) => {
            const severityClass = DiagnosticSeverity[d.severity].toLowerCase();
            const icon = this.getSeverityIcon(d.severity);
            const line = d.range.start.line + 1;
            const col = d.range.start.column + 1;
            return `<div class="panel-problem-item ${severityClass}">
              <span class="panel-problem-icon">${icon}</span>
              <span class="panel-problem-message">${this.escapeHtml(d.message)}</span>
              <span class="panel-problem-location">[Ln ${line}, Col ${col}]</span>
            </div>`;
          })
          .join('')}
      </div>`;
    }

    return `<div class="panel-problems">${html}</div>`;
  }

  private getSeverityIcon(severity: DiagnosticSeverity): string {
    switch (severity) {
      case DiagnosticSeverity.Error:
        return '✖';
      case DiagnosticSeverity.Warning:
        return '⚠';
      case DiagnosticSeverity.Information:
        return 'ℹ';
      case DiagnosticSeverity.Hint:
        return '💡';
      default:
        return '?';
    }
  }

  private escapeHtml(text: string): string {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  onMount(): void {
    const disposable = this.eventBus.on<{ diagnostics: Diagnostic[] }>(
      'panel:diagnosticsUpdated',
      (payload) => {
        this.diagnostics = payload.diagnostics;
      },
    );
    this.subscriptions.push(disposable);
  }

  onUnmount(): void {
    // cleanup if needed
  }

  update(props: Record<string, unknown>): void {
    if (props.visible !== undefined) this.visible = props.visible as boolean;
    if (props.height !== undefined) this.panelHeight = props.height as number;
    if (props.diagnostics) this.diagnostics = props.diagnostics as Diagnostic[];
  }

  openTab(tabId: string, title: string): void {
    if (!this.tabs.has(tabId)) {
      this.tabs.set(tabId, { id: tabId, title, content: '', outputLines: [] });
    }
    this.activeTabId = tabId;
  }

  closeTab(tabId: string): void {
    const defaultTabs = ['OUTPUT', 'PROBLEMS', 'DEBUG CONSOLE', 'TERMINAL'];
    if (defaultTabs.includes(tabId)) return;

    this.tabs.delete(tabId);
    if (this.activeTabId === tabId) {
      this.activeTabId = 'OUTPUT';
    }
  }

  setActiveTab(tabId: string): void {
    if (this.tabs.has(tabId)) {
      this.activeTabId = tabId;
    }
  }

  appendOutput(tabId: string, text: string): void {
    const tab = this.tabs.get(tabId);
    if (!tab) return;

    const lines = text.split('\n');
    for (const line of lines) {
      tab.outputLines.push(line);
    }
    tab.content += text;

    if (tab.outputLines.length > 10000) {
      tab.outputLines.splice(0, tab.outputLines.length - 10000);
    }
  }

  clearOutput(tabId: string): void {
    const tab = this.tabs.get(tabId);
    if (tab) {
      tab.content = '';
      tab.outputLines = [];
    }
  }

  show(): void {
    this.visible = true;
  }

  hide(): void {
    this.visible = false;
  }

  toggle(): void {
    this.visible = !this.visible;
  }

  resize(height: number): void {
    this.panelHeight = Math.max(50, Math.min(800, height));
  }

  setDiagnostics(diagnostics: Diagnostic[]): void {
    this.diagnostics = diagnostics;
  }

  isVisible(): boolean {
    return this.visible;
  }

  getActiveTab(): string {
    return this.activeTabId;
  }
}

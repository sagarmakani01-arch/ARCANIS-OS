import { IDisposable, Diagnostic, DiagnosticSeverity } from '../../api/types';
import { EventBus } from '../../core/EventBus';
import { UIComponent } from '../UIEngine';

interface EditorTab {
  uri: string;
  title: string;
  dirty: boolean;
  content: string;
}

export class EditorView implements UIComponent {
  id = 'editor-view';
  private tabs: EditorTab[] = [];
  private activeUri: string | undefined;
  private diagnostics: Map<string, Diagnostic[]> = new Map();
  private disposables: IDisposable[] = [];

  constructor(private eventBus: EventBus) {}

  render(): string {
    if (this.tabs.length === 0) {
      return `<div class="editor-empty">
        <div class="editor-welcome">
          <h2>Arcanis IDE</h2>
          <p>Open a file to start editing</p>
        </div>
      </div>`;
    }

    const tabsHtml = this.renderTabs();
    const activeDoc = this.getActiveDocument();
    const contentHtml = activeDoc ? this.renderEditorContent(activeDoc) : '';

    return `<div class="editor-container">
      <div class="editor-tabs">${tabsHtml}</div>
      <div class="editor-body">
        <div class="editor-content">${contentHtml}</div>
      </div>
    </div>`;
  }

  private renderTabs(): string {
    return this.tabs.map((tab) => {
      const isActive = tab.uri === this.activeUri;
      const dirtyIndicator = tab.dirty ? '<span class="editor-tab-dirty">●</span>' : '';
      return `<div class="editor-tab ${isActive ? 'active' : ''}" data-uri="${tab.uri}">
        ${dirtyIndicator}
        <span class="editor-tab-title">${this.escapeHtml(tab.title)}</span>
        <button class="editor-tab-close" data-uri="${tab.uri}">×</button>
      </div>`;
    }).join('');
  }

  private renderEditorContent(uri: string): string {
    const tab = this.tabs.find((t) => t.uri === uri);
    if (!tab) return '';

    const lines = tab.content.split('\n');
    const lineCount = lines.length;
    const lineNumWidth = String(lineCount).length;

    const lineNumbers = lines.map((_, i) => {
      const lineNum = i + 1;
      return `<span class="editor-line-number" style="min-width:${lineNumWidth}ch;">${String(lineNum).padStart(lineNumWidth)}</span>`;
    }).join('\n');

    const codeLines = lines.map((text, i) => {
      const diags = this.getDiagnosticsForLine(uri, i + 1);
      const squiggles = diags.map((d) => {
        const severityClass = DiagnosticSeverity[d.severity].toLowerCase();
        return `<span class="editor-squiggle ${severityClass}" title="${this.escapeHtml(d.message)}"></span>`;
      }).join('');
      return `<div class="editor-line" data-line="${i + 1}">
        <span class="editor-line-text">${this.escapeHtml(text)}</span>${squiggles}
      </div>`;
    }).join('\n');

    return `<div class="editor-scrollable">
      <div class="editor-lines">
        <div class="editor-line-numbers">${lineNumbers}</div>
        <div class="editor-code-lines">${codeLines}</div>
      </div>
    </div>`;
  }

  private getDiagnosticsForLine(uri: string, line: number): Diagnostic[] {
    const fileDiags = this.diagnostics.get(uri) || [];
    return fileDiags.filter(
      (d) => d.range.start.line <= line && d.range.end.line >= line,
    );
  }

  private escapeHtml(text: string): string {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  onMount(): void {
    const sub = this.eventBus.on<{ uri: string; diagnostics: Diagnostic[] }>(
      'editor:diagnosticsUpdated',
      (payload) => {
        this.diagnostics.set(payload.uri, payload.diagnostics);
      },
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
    if (props.activeUri) {
      this.activeUri = props.activeUri as string;
    }
    if (props.diagnostics) {
      this.diagnostics = props.diagnostics as Map<string, Diagnostic[]>;
    }
  }

  openDocument(uri: string, content?: string): void {
    const existing = this.tabs.find((t) => t.uri === uri);
    if (existing) {
      this.activeUri = uri;
      if (content !== undefined) {
        existing.content = content;
      }
      this.eventBus.emit('editorView:activeDocumentChanged', { uri });
      return;
    }

    const fileName = uri.split('/').pop() || uri.split('\\').pop() || uri;
    this.tabs.push({
      uri,
      title: fileName,
      dirty: false,
      content: content || '',
    });
    this.activeUri = uri;
    this.eventBus.emit('editorView:documentOpened', { uri });
    this.eventBus.emit('editorView:activeDocumentChanged', { uri });
  }

  closeDocument(uri: string): void {
    const index = this.tabs.findIndex((t) => t.uri === uri);
    if (index < 0) return;

    this.tabs.splice(index, 1);

    if (this.activeUri === uri) {
      if (this.tabs.length > 0) {
        const newIndex = Math.min(index, this.tabs.length - 1);
        this.activeUri = this.tabs[newIndex].uri;
      } else {
        this.activeUri = undefined;
      }
    }

    this.eventBus.emit('editorView:documentClosed', { uri });
    if (this.activeUri) {
      this.eventBus.emit('editorView:activeDocumentChanged', { uri: this.activeUri });
    }
  }

  setActiveDocument(uri: string): void {
    const tab = this.tabs.find((t) => t.uri === uri);
    if (!tab) return;
    this.activeUri = uri;
    this.eventBus.emit('editorView:activeDocumentChanged', { uri });
  }

  getOpenDocuments(): string[] {
    return this.tabs.map((t) => t.uri);
  }

  getActiveDocument(): string | undefined {
    return this.activeUri;
  }

  setDiagnostics(uri: string, diagnostics: Diagnostic[]): void {
    this.diagnostics.set(uri, diagnostics);
  }

  markDirty(uri: string, dirty: boolean): void {
    const tab = this.tabs.find((t) => t.uri === uri);
    if (tab) {
      tab.dirty = dirty;
    }
  }

  updateContent(uri: string, content: string): void {
    const tab = this.tabs.find((t) => t.uri === uri);
    if (tab) {
      tab.content = content;
    }
  }
}

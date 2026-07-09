import { TextDocument, IDisposable, Position, Range, CompletionContext, CodeActionContext } from '../api/types';
import { EventBus, EventHandler } from '../core/EventBus';
import { SyntaxHighlighter } from './SyntaxHighlighter';
import { CompletionProvider } from './CompletionProvider';
import { DiagnosticEngine } from './DiagnosticEngine';
import { RefactoringEngine } from './RefactoringEngine';
import { LanguageService } from './languages/LanguageService';

export class EditorEngine {
  private documents = new Map<string, TextDocument>();
  private activeDocumentUri: string | undefined;
  private documentVersions = new Map<string, number>();
  private highlighter: SyntaxHighlighter;
  private completionProvider: CompletionProvider;
  private diagnosticEngine: DiagnosticEngine;
  private refactoringEngine: RefactoringEngine;
  private eventBus = new EventBus();

  constructor() {
    this.highlighter = new SyntaxHighlighter();
    this.completionProvider = new CompletionProvider();
    this.diagnosticEngine = new DiagnosticEngine();
    this.refactoringEngine = new RefactoringEngine();
  }

  async openDocument(uri: string): Promise<TextDocument> {
    const existing = this.documents.get(uri);
    if (existing) {
      this.setActiveDocument(uri);
      return existing;
    }

    const version = 1;
    const document = await this.loadDocument(uri, version);
    this.documents.set(uri, document);
    this.documentVersions.set(uri, version);
    this.setActiveDocument(uri);
    this.eventBus.emit('document:opened', { uri, document });
    return document;
  }

  closeDocument(uri: string): void {
    this.documents.delete(uri);
    this.documentVersions.delete(uri);

    if (this.activeDocumentUri === uri) {
      const remaining = Array.from(this.documents.keys());
      this.activeDocumentUri = remaining.length > 0 ? remaining[remaining.length - 1] : undefined;
      if (this.activeDocumentUri) {
        this.eventBus.emit('editor:activeDocumentChanged', { uri: this.activeDocumentUri });
      }
    }

    this.highlighter.invalidate(uri);
    this.eventBus.emit('document:closed', { uri });
  }

  getDocument(uri: string): TextDocument | undefined {
    return this.documents.get(uri);
  }

  getActiveDocument(): TextDocument | undefined {
    if (this.activeDocumentUri) {
      return this.documents.get(this.activeDocumentUri);
    }
    return undefined;
  }

  setActiveDocument(uri: string): void {
    if (this.documents.has(uri)) {
      this.activeDocumentUri = uri;
      this.eventBus.emit('editor:activeDocumentChanged', { uri });
    }
  }

  updateDocument(uri: string, text: string): void {
    const existing = this.documents.get(uri);
    if (!existing) return;

    const version = (this.documentVersions.get(uri) ?? 0) + 1;
    this.documentVersions.set(uri, version);

    const updated = this.createUpdatedDocument(existing, text, version);
    this.documents.set(uri, updated);
    this.highlighter.invalidate(uri);
    this.eventBus.emit('document:changed', { uri, document: updated, version });
  }

  getHighlighter(): SyntaxHighlighter {
    return this.highlighter;
  }

  getCompletionProvider(): CompletionProvider {
    return this.completionProvider;
  }

  getDiagnosticEngine(): DiagnosticEngine {
    return this.diagnosticEngine;
  }

  getRefactoringEngine(): RefactoringEngine {
    return this.refactoringEngine;
  }

  registerLanguageService(languageService: LanguageService): void {
    this.highlighter.registerLanguage(languageService);
    this.refactoringEngine.registerLanguageService(languageService);
    this.completionProvider.registerProvider(
      languageService.languageId,
      (doc, pos, ctx) => languageService.provideCompletions(doc, pos, ctx),
    );
    this.diagnosticEngine.registerProvider(
      languageService.languageId,
      (doc) => languageService.provideDiagnostics(doc),
    );
  }

  onDocumentOpened(handler: EventHandler<{ uri: string; document: TextDocument }>): IDisposable {
    return this.eventBus.on('document:opened', handler);
  }

  onDocumentClosed(handler: EventHandler<{ uri: string }>): IDisposable {
    return this.eventBus.on('document:closed', handler);
  }

  onDocumentChanged(handler: EventHandler<{ uri: string; document: TextDocument; version: number }>): IDisposable {
    return this.eventBus.on('document:changed', handler);
  }

  onActiveDocumentChanged(handler: EventHandler<{ uri: string }>): IDisposable {
    return this.eventBus.on('editor:activeDocumentChanged', handler);
  }

  private async loadDocument(uri: string, version: number): Promise<TextDocument> {
    const fileName = uri.split('/').pop() ?? uri;
    const ext = fileName.includes('.') ? fileName.split('.').pop()!.toLowerCase() : '';
    const languageId = this.guessLanguageId(ext, fileName);

    return this.createTextDocument(uri, fileName, languageId, version, '');
  }

  private guessLanguageId(ext: string, fileName: string): string {
    const extMap: Record<string, string> = {
      arc: 'arcanis',
      arcanis: 'arcanis',
      ts: 'typescript',
      js: 'javascript',
      json: 'json',
      md: 'markdown',
      html: 'html',
      css: 'css',
      py: 'python',
      rs: 'rust',
    };
    return extMap[ext] ?? 'plaintext';
  }

  private createTextDocument(
    uri: string,
    fileName: string,
    languageId: string,
    version: number,
    content: string,
  ): TextDocument {
    const lines = content.split('\n');
    return {
      uri,
      fileName,
      languageId,
      version,
      getText: (range?: Range) => {
        if (!range) return content;
        const startLine = range.start.line;
        const endLine = range.end.line;
        if (startLine === endLine) {
          return lines[startLine].substring(range.start.column, range.end.column);
        }
        const parts: string[] = [];
        parts.push(lines[startLine].substring(range.start.column));
        for (let i = startLine + 1; i < endLine; i++) {
          parts.push(lines[i]);
        }
        parts.push(lines[endLine].substring(0, range.end.column));
        return parts.join('\n');
      },
      lineAt: (line: number) => {
        const lineText = lines[line] ?? '';
        return {
          lineNumber: line,
          text: lineText,
          range: {
            start: { line, column: 0 },
            end: { line, column: lineText.length },
          },
          firstNonWhitespaceCharacterIndex: lineText.search(/\S/),
          isEmptyOrWhitespace: lineText.trim().length === 0,
        };
      },
      lineCount: lines.length,
    };
  }

  private createUpdatedDocument(existing: TextDocument, text: string, version: number): TextDocument {
    const lines = text.split('\n');
    return {
      uri: existing.uri,
      fileName: existing.fileName,
      languageId: existing.languageId,
      version,
      getText: (range?: Range) => {
        if (!range) return text;
        const startLine = range.start.line;
        const endLine = range.end.line;
        if (startLine === endLine) {
          return lines[startLine].substring(range.start.column, range.end.column);
        }
        const parts: string[] = [];
        parts.push(lines[startLine].substring(range.start.column));
        for (let i = startLine + 1; i < endLine; i++) {
          parts.push(lines[i]);
        }
        parts.push(lines[endLine].substring(0, range.end.column));
        return parts.join('\n');
      },
      lineAt: (line: number) => {
        const lineText = lines[line] ?? '';
        return {
          lineNumber: line,
          text: lineText,
          range: {
            start: { line, column: 0 },
            end: { line, column: lineText.length },
          },
          firstNonWhitespaceCharacterIndex: lineText.search(/\S/),
          isEmptyOrWhitespace: lineText.trim().length === 0,
        };
      },
      lineCount: lines.length,
    };
  }
}

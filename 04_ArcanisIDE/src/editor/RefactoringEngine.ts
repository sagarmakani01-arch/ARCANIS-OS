import {
  TextDocument, Range, Position, CodeAction, CodeActionContext,
  CodeActionKind, WorkspaceEdit, TextEdit, Diagnostic,
} from '../api/types';
import { LanguageService } from './languages/LanguageService';

export type CodeActionProviderFn = (
  document: TextDocument,
  range: Range,
  context: CodeActionContext,
) => CodeAction[];

export type RenameProviderFn = (
  document: TextDocument,
  position: Position,
  newName: string,
) => WorkspaceEdit | undefined;

export class RefactoringEngine {
  private languages = new Map<string, LanguageService>();
  private codeActionProviders = new Map<string, CodeActionProviderFn[]>();
  private renameProviders = new Map<string, RenameProviderFn[]>();

  provideCodeActions(
    document: TextDocument,
    range: Range,
    context: CodeActionContext,
  ): CodeAction[] {
    const actions: CodeAction[] = [];

    const langService = this.languages.get(document.languageId);
    if (langService) {
      actions.push(...langService.provideCodeActions(document, range, context));
    }

    const providers = this.codeActionProviders.get(document.languageId) ?? [];
    for (const provider of providers) {
      actions.push(...provider(document, range, context));
    }

    const diagBasedActions = this.generateDiagnosticActions(context.diagnostics);
    actions.push(...diagBasedActions);

    return actions;
  }

  renameSymbol(
    document: TextDocument,
    position: Position,
    newName: string,
  ): WorkspaceEdit | undefined {
    const langService = this.languages.get(document.languageId);
    if (langService) {
      const result = langService.provideRename(document, position, newName);
      if (result) return result;
    }

    const providers = this.renameProviders.get(document.languageId) ?? [];
    for (const provider of providers) {
      const result = provider(document, position, newName);
      if (result) return result;
    }

    return undefined;
  }

  extractFunction(
    document: TextDocument,
    range: Range,
    name: string,
  ): WorkspaceEdit | undefined {
    const selectedText = document.getText(range);
    if (!selectedText || selectedText.trim().length === 0) return undefined;

    const edits: TextEdit[] = [];

    const functionText = `fn ${name}() {\n${selectedText}\n}`;
    const insertPosition: Position = { line: 0, column: 0 };

    edits.push({
      range: { start: insertPosition, end: insertPosition },
      newText: functionText + '\n\n',
    });

    edits.push({
      range,
      newText: `${name}()`,
    });

    return { changes: { [document.uri]: edits } };
  }

  organizeImports(document: TextDocument): TextEdit[] {
    const text = document.getText();
    const lines = text.split('\n');
    const importLines: { index: number; text: string; lineText: string }[] = [];

    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();
      if (trimmed.startsWith('import ') || trimmed.startsWith('use ') || trimmed.startsWith('from ')) {
        importLines.push({ index: i, text: trimmed, lineText: lines[i] });
      }
    }

    if (importLines.length === 0) return [];

    const sorted = [...importLines].sort((a, b) => a.text.localeCompare(b.text));

    const range: Range = {
      start: { line: importLines[0].index, column: 0 },
      end: { line: importLines[importLines.length - 1].index, column: lines[importLines[importLines.length - 1].index].length },
    };

    const newText = sorted.map((s) => s.lineText).join('\n') + '\n';

    return [{ range, newText }];
  }

  registerLanguageService(languageService: LanguageService): void {
    this.languages.set(languageService.languageId, languageService);
  }

  registerCodeActionProvider(languageId: string, provider: CodeActionProviderFn): void {
    if (!this.codeActionProviders.has(languageId)) {
      this.codeActionProviders.set(languageId, []);
    }
    this.codeActionProviders.get(languageId)!.push(provider);
  }

  registerRenameProvider(languageId: string, provider: RenameProviderFn): void {
    if (!this.renameProviders.has(languageId)) {
      this.renameProviders.set(languageId, []);
    }
    this.renameProviders.get(languageId)!.push(provider);
  }

  private generateDiagnosticActions(diagnostics: Diagnostic[]): CodeAction[] {
    const actions: CodeAction[] = [];
    for (const diagnostic of diagnostics) {
      actions.push({
        title: `Fix: ${diagnostic.message}`,
        kind: CodeActionKind.QuickFix,
        diagnostics: [diagnostic],
      });
    }
    return actions;
  }
}

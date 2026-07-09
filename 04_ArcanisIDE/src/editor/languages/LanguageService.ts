import {
  LanguageService as ILanguageService,
  TextDocument,
  Token,
  Position,
  CompletionItem,
  CompletionContext,
  Diagnostic,
  CodeAction,
  Range,
  CodeActionContext,
  SignatureHelp,
  FormattingOptions,
  TextEdit,
  Location,
  WorkspaceEdit,
} from '../../api/types';

export abstract class LanguageService implements ILanguageService {
  readonly languageId: string;

  constructor(languageId: string) {
    this.languageId = languageId;
  }

  provideTokens(document: TextDocument): Token[] {
    return [];
  }

  provideCompletions(document: TextDocument, position: Position, context?: CompletionContext): CompletionItem[] {
    return [];
  }

  provideDiagnostics(document: TextDocument): Diagnostic[] {
    return [];
  }

  provideCodeActions(document: TextDocument, range: Range, context: CodeActionContext): CodeAction[] {
    return [];
  }

  provideHover(document: TextDocument, position: Position): string | undefined {
    return undefined;
  }

  provideSignatureHelp(document: TextDocument, position: Position): SignatureHelp | undefined {
    return undefined;
  }

  provideDocumentFormatting(document: TextDocument, options: FormattingOptions): TextEdit[] {
    return [];
  }

  provideDefinition(document: TextDocument, position: Position): Location | undefined {
    return undefined;
  }

  provideReferences(document: TextDocument, position: Position): Location[] {
    return [];
  }

  provideRename(document: TextDocument, position: Position, newName: string): WorkspaceEdit | undefined {
    return undefined;
  }
}

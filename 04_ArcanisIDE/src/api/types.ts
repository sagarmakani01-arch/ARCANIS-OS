export interface IDisposable {
  dispose(): void;
}

export interface Position {
  line: number;
  column: number;
}

export interface Range {
  start: Position;
  end: Position;
}

export interface TextDocument {
  uri: string;
  fileName: string;
  languageId: string;
  version: number;
  getText(): string;
  getText(range: Range): string;
  lineAt(line: number): TextLine;
  lineCount: number;
}

export interface TextLine {
  lineNumber: number;
  text: string;
  range: Range;
  firstNonWhitespaceCharacterIndex: number;
  isEmptyOrWhitespace: boolean;
}

export interface EditorConfig {
  fontSize: number;
  fontFamily: string;
  tabSize: number;
  insertSpaces: boolean;
  wordWrap: 'off' | 'on' | 'wordWrapColumn';
  wordWrapColumn: number;
  lineNumbers: 'on' | 'off' | 'relative';
  minimap: boolean;
  bracketPairColorization: boolean;
  autoClosingBrackets: boolean;
  autoClosingQuotes: boolean;
  formatOnPaste: boolean;
  formatOnSave: boolean;
  suggestOnTriggerCharacters: boolean;
}

export interface Diagnostic {
  range: Range;
  severity: DiagnosticSeverity;
  message: string;
  source: string;
  code: string | number;
  relatedInformation?: DiagnosticRelatedInfo[];
}

export interface DiagnosticRelatedInfo {
  location: Location;
  message: string;
}

export interface Location {
  uri: string;
  range: Range;
}

export enum DiagnosticSeverity {
  Error = 0,
  Warning = 1,
  Information = 2,
  Hint = 3,
}

export interface CompletionItem {
  label: string;
  kind: CompletionItemKind;
  detail?: string;
  documentation?: string;
  insertText?: string;
  filterText?: string;
  sortText?: string;
  range?: Range;
  commitCharacters?: string[];
}

export enum CompletionItemKind {
  Method = 0,
  Function = 1,
  Constructor = 2,
  Field = 3,
  Variable = 4,
  Class = 5,
  Struct = 6,
  Interface = 7,
  Module = 8,
  Property = 9,
  Event = 10,
  Operator = 11,
  Unit = 12,
  Value = 13,
  Constant = 14,
  Enum = 15,
  EnumMember = 16,
  Keyword = 17,
  Snippet = 18,
  Color = 19,
  File = 20,
  Reference = 21,
  Folder = 22,
  TypeParameter = 23,
}

export interface Token {
  type: TokenType;
  value: string;
  range: Range;
}

export enum TokenType {
  Keyword = 'keyword',
  Type = 'type',
  Function = 'function',
  String = 'string',
  Number = 'number',
  Comment = 'comment',
  Operator = 'operator',
  Variable = 'variable',
  Parameter = 'parameter',
  Property = 'property',
  Decorator = 'decorator',
  Punctuation = 'punctuation',
  Whitespace = 'whitespace',
  Identifier = 'identifier',
  Unknown = 'unknown',
}

export interface CodeAction {
  title: string;
  kind: CodeActionKind;
  diagnostics?: Diagnostic[];
  edit?: WorkspaceEdit;
  command?: Command;
}

export enum CodeActionKind {
  QuickFix = 'quickfix',
  Refactor = 'refactor',
  RefactorExtract = 'refactor.extract',
  RefactorInline = 'refactor.inline',
  RefactorRewrite = 'refactor.rewrite',
  Source = 'source',
  SourceOrganizeImports = 'source.organizeImports',
}

export interface WorkspaceEdit {
  changes: { [uri: string]: TextEdit[] };
}

export interface TextEdit {
  range: Range;
  newText: string;
}

export interface Command {
  id: string;
  title: string;
  arguments?: unknown[];
}

export interface FileItem {
  name: string;
  path: string;
  isDirectory: boolean;
  children?: FileItem[];
  size?: number;
  modifiedAt?: Date;
}

export interface WorkspaceFolder {
  uri: string;
  name: string;
  path: string;
}

export interface Breakpoint {
  id: string;
  uri: string;
  line: number;
  column?: number;
  enabled: boolean;
  condition?: string;
  hitCondition?: string;
  logMessage?: string;
}

export interface StackFrame {
  id: number;
  name: string;
  source?: string;
  line: number;
  column: number;
  scopes?: Scope[];
}

export interface Scope {
  name: string;
  variables: Variable[];
}

export interface Variable {
  name: string;
  value: string;
  type: string;
  reference?: number;
  children?: Variable[];
}

export interface Thread {
  id: number;
  name: string;
  stopped: boolean;
  stackFrames: StackFrame[];
}

export interface BuildConfig {
  target: string;
  mode: 'debug' | 'release';
  optimize: boolean;
  outputDir: string;
  sourceDir: string;
  compilerFlags: string[];
}

export interface GitStatus {
  branch: string;
  changes: GitChange[];
  ahead: number;
  behind: number;
  staged: number;
  modified: number;
  untracked: number;
  conflicts: number;
}

export interface GitChange {
  path: string;
  status: 'added' | 'modified' | 'deleted' | 'renamed' | 'untracked' | 'conflict';
}

export interface AISuggestion {
  id: string;
  type: 'improvement' | 'bug' | 'performance' | 'security' | 'style' | 'documentation';
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  range?: Range;
  code?: string;
  explanation: string;
}

export interface AICompletionContext {
  document: TextDocument;
  position: Position;
  prefix: string;
  suffix: string;
  language: string;
  recentFiles: string[];
  projectStructure: string[];
}

export interface AICompletionResult {
  completions: AICompletion[];
  requestId: string;
}

export interface AICompletion {
  text: string;
  confidence: number;
  explanation?: string;
}

export interface PluginManifest {
  name: string;
  version: string;
  description: string;
  author: string;
  license?: string;
  main: string;
  contributes?: {
    commands?: CommandDefinition[];
    languages?: LanguageContribution[];
    themes?: ThemeContribution[];
    menuItems?: MenuContribution[];
    keybindings?: KeybindingContribution[];
  };
  activationEvents?: string[];
  dependencies?: string[];
}

export interface CommandDefinition {
  id: string;
  title: string;
  category?: string;
  icon?: string;
  keybinding?: string;
}

export interface LanguageContribution {
  id: string;
  extensions: string[];
  aliases?: string[];
  filenamePatterns?: string[];
  configuration?: string;
}

export interface ThemeContribution {
  id: string;
  label: string;
  type: 'dark' | 'light' | 'highContrast';
  path: string;
}

export interface MenuContribution {
  id: string;
  label: string;
  command: string;
  group?: string;
  order?: number;
  when?: string;
}

export interface KeybindingContribution {
  command: string;
  key: string;
  when?: string;
  mac?: string;
  linux?: string;
  win?: string;
}

export interface PluginContext {
  subscriptions: IDisposable[];
  extensionPath: string;
  workspaceState: Memento;
  globalState: Memento;
  log: (message: string) => void;
}

export interface Memento {
  get<T>(key: string): T | undefined;
  set<T>(key: string, value: T): void;
  delete(key: string): void;
  keys(): string[];
}

export interface LanguageService {
  languageId: string;
  provideTokens(document: TextDocument): Token[];
  provideCompletions(document: TextDocument, position: Position, context?: CompletionContext): CompletionItem[];
  provideDiagnostics(document: TextDocument): Diagnostic[];
  provideCodeActions(document: TextDocument, range: Range, context: CodeActionContext): CodeAction[];
  provideHover(document: TextDocument, position: Position): string | undefined;
  provideSignatureHelp(document: TextDocument, position: Position): SignatureHelp | undefined;
  provideDocumentFormatting(document: TextDocument, options: FormattingOptions): TextEdit[];
  provideDefinition(document: TextDocument, position: Position): Location | undefined;
  provideReferences(document: TextDocument, position: Position): Location[];
  provideRename(document: TextDocument, position: Position, newName: string): WorkspaceEdit | undefined;
}

export interface CompletionContext {
  triggerKind: CompletionTriggerKind;
  triggerCharacter?: string;
}

export enum CompletionTriggerKind {
  Invoke = 0,
  TriggerCharacter = 1,
  TriggerForIncompleteCompletions = 2,
}

export interface CodeActionContext {
  diagnostics: Diagnostic[];
  only?: CodeActionKind;
}

export interface SignatureHelp {
  signatures: SignatureInformation[];
  activeSignature: number;
  activeParameter: number;
}

export interface SignatureInformation {
  label: string;
  documentation?: string;
  parameters: ParameterInformation[];
}

export interface ParameterInformation {
  label: string;
  documentation?: string;
}

export interface FormattingOptions {
  tabSize: number;
  insertSpaces: boolean;
}

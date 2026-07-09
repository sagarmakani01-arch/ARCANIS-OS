import { IDisposable, EditorConfig } from '../api/types';
import { EventBus, EventHandler } from './EventBus';

export interface IConfiguration {
  get<T>(key: string, defaultValue?: T): T;
  set<T>(key: string, value: T): void;
  has(key: string): boolean;
  delete(key: string): void;
  getAll(): Record<string, unknown>;
  onDidChange(key: string, handler: EventHandler<unknown>): IDisposable;
  getEditorConfig(): EditorConfig;
  resetToDefaults(): void;
}

export class Configuration implements IConfiguration {
  private config: Record<string, unknown> = {};
  private eventBus = new EventBus();

  private static readonly DEFAULTS: Record<string, unknown> = {
    'editor.fontSize': 14,
    'editor.fontFamily': 'Cascadia Code, Fira Code, Consolas, monospace',
    'editor.tabSize': 4,
    'editor.insertSpaces': true,
    'editor.wordWrap': 'off',
    'editor.wordWrapColumn': 120,
    'editor.lineNumbers': 'on',
    'editor.minimap': true,
    'editor.bracketPairColorization': true,
    'editor.autoClosingBrackets': true,
    'editor.autoClosingQuotes': true,
    'editor.formatOnPaste': false,
    'editor.formatOnSave': true,
    'editor.suggestOnTriggerCharacters': true,
    'ai.enabled': true,
    'ai.model': 'arcanis-coder',
    'ai.maxTokens': 2048,
    'ai.temperature': 0.2,
    'ai.suggestionsEnabled': true,
    'ai.bugDetectionEnabled': true,
    'ai.docGenerationEnabled': true,
    'build.defaultTarget': 'wasm32',
    'build.defaultMode': 'debug',
    'terminal.shell': 'powershell',
    'terminal.fontSize': 13,
    'git.enabled': true,
    'git.autoFetch': true,
    'plugin.developmentMode': false,
    'theme': 'arcanis-dark',
  };

  constructor() {
    this.resetToDefaults();
  }

  get<T>(key: string, defaultValue?: T): T {
    return (this.config[key] as T) ?? (Configuration.DEFAULTS[key] as T) ?? (defaultValue as T);
  }

  set<T>(key: string, value: T): void {
    const oldValue = this.config[key];
    this.config[key] = value;
    this.eventBus.emit(`config:changed:${key}`, value);
    this.eventBus.emit('config:changed', { key, value, oldValue });
  }

  has(key: string): boolean {
    return key in this.config || key in Configuration.DEFAULTS;
  }

  delete(key: string): void {
    if (key in this.config) {
      const oldValue = this.config[key];
      delete this.config[key];
      this.eventBus.emit(`config:changed:${key}`, undefined);
      this.eventBus.emit('config:changed', { key, value: undefined, oldValue });
    }
  }

  getAll(): Record<string, unknown> {
    return { ...Configuration.DEFAULTS, ...this.config };
  }

  onDidChange(key: string, handler: EventHandler<unknown>): IDisposable {
    return this.eventBus.on(`config:changed:${key}`, handler);
  }

  getEditorConfig(): EditorConfig {
    return {
      fontSize: this.get<number>('editor.fontSize', 14),
      fontFamily: this.get<string>('editor.fontFamily', 'Consolas, monospace'),
      tabSize: this.get<number>('editor.tabSize', 4),
      insertSpaces: this.get<boolean>('editor.insertSpaces', true),
      wordWrap: this.get<'off' | 'on' | 'wordWrapColumn'>('editor.wordWrap', 'off'),
      wordWrapColumn: this.get<number>('editor.wordWrapColumn', 120),
      lineNumbers: this.get<'on' | 'off' | 'relative'>('editor.lineNumbers', 'on'),
      minimap: this.get<boolean>('editor.minimap', true),
      bracketPairColorization: this.get<boolean>('editor.bracketPairColorization', true),
      autoClosingBrackets: this.get<boolean>('editor.autoClosingBrackets', true),
      autoClosingQuotes: this.get<boolean>('editor.autoClosingQuotes', true),
      formatOnPaste: this.get<boolean>('editor.formatOnPaste', false),
      formatOnSave: this.get<boolean>('editor.formatOnSave', true),
      suggestOnTriggerCharacters: this.get<boolean>('editor.suggestOnTriggerCharacters', true),
    };
  }

  resetToDefaults(): void {
    this.config = { ...Configuration.DEFAULTS };
  }
}

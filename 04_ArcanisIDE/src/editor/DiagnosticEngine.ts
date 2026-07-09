import { TextDocument, Diagnostic, IDisposable } from '../api/types';
import { EventBus, EventHandler } from '../core/EventBus';

export type DiagnosticProviderFn = (document: TextDocument) => Diagnostic[];

export class DiagnosticEngine {
  private providers = new Map<string, DiagnosticProviderFn[]>();
  private eventBus = new EventBus();

  runDiagnostics(document: TextDocument): Diagnostic[] {
    const all: Diagnostic[] = [];
    const providers = this.providers.get(document.languageId) ?? [];

    for (const provider of providers) {
      const results = provider(document);
      all.push(...results);
    }

    const deduplicated = this.deduplicate(all);
    this.eventBus.emit('diagnostics:updated', { uri: document.uri, diagnostics: deduplicated });

    return deduplicated;
  }

  registerProvider(languageId: string, provider: DiagnosticProviderFn): void {
    if (!this.providers.has(languageId)) {
      this.providers.set(languageId, []);
    }
    this.providers.get(languageId)!.push(provider);
  }

  onDiagnosticsUpdated(handler: EventHandler<{ uri: string; diagnostics: Diagnostic[] }>): IDisposable {
    return this.eventBus.on('diagnostics:updated', handler);
  }

  private deduplicate(diagnostics: Diagnostic[]): Diagnostic[] {
    const seen = new Set<string>();
    return diagnostics.filter((d) => {
      const key = `${d.range.start.line}:${d.range.start.column}-${d.range.end.line}:${d.range.end.column}:${d.message}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }
}

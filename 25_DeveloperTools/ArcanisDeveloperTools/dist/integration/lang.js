"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanisLangIntegration = void 0;
class ArcanisLangIntegration {
    name = '@arcanis/developer-tools-lang';
    version = '0.1.0';
    async provideCompletions(context) {
        console.log(`[Lang] Providing completions for ${context.file}:${context.line}`);
        return [];
    }
    async provideDiagnostics(source, filePath) {
        console.log(`[Lang] Diagnosing ${filePath}`);
        return [];
    }
    async provideHover(context) {
        console.log(`[Lang] Hover info for ${context.file}:${context.line}`);
        return null;
    }
    async provideDefinition(context) {
        console.log(`[Lang] Definition lookup for ${context.file}:${context.line}`);
        return null;
    }
    getLanguageFeatures() {
        return ['completions', 'diagnostics', 'hover', 'goToDefinition'];
    }
}
exports.ArcanisLangIntegration = ArcanisLangIntegration;
//# sourceMappingURL=lang.js.map
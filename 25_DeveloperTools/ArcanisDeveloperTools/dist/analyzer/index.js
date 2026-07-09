"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CodeAnalyzer = exports.analyzeComplexity = exports.defaultRules = void 0;
const lint_js_1 = require("./lint.js");
Object.defineProperty(exports, "defaultRules", { enumerable: true, get: function () { return lint_js_1.defaultRules; } });
const complexity_js_1 = require("./complexity.js");
Object.defineProperty(exports, "analyzeComplexity", { enumerable: true, get: function () { return complexity_js_1.analyzeComplexity; } });
class CodeAnalyzer {
    rules;
    constructor(rules) {
        this.rules = rules ?? lint_js_1.defaultRules;
    }
    async analyzeFile(filePath, source) {
        const issues = [];
        for (const rule of this.rules) {
            try {
                const ruleIssues = rule.check(source);
                issues.push(...ruleIssues);
            }
            catch (err) {
                console.error(`[Analyzer] Rule '${rule.name}' failed:`, err);
            }
        }
        const complexity = (0, complexity_js_1.analyzeComplexity)(source);
        const dependencies = this.extractDependencies(source);
        return { file: filePath, issues, complexity, dependencies };
    }
    extractDependencies(source) {
        const deps = [];
        const importRegex = /(?:import\s+(?:\w+\s*,?\s*)?(?:\{[^}]*\})?\s*from\s+['"]|require\s*\(\s*['"])([^'"]+)/g;
        let m;
        while ((m = importRegex.exec(source)) !== null) {
            deps.push(m[1]);
        }
        return deps;
    }
}
exports.CodeAnalyzer = CodeAnalyzer;
//# sourceMappingURL=index.js.map
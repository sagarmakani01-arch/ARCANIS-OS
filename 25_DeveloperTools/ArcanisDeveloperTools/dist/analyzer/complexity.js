"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.analyzeComplexity = analyzeComplexity;
function analyzeComplexity(source) {
    const lines = source.split('\n');
    const linesOfCode = lines.filter(l => l.trim().length > 0 && !l.trim().startsWith('//')).length;
    const cyclomaticComplexity = computeCyclomaticComplexity(source);
    const cognitiveComplexity = computeCognitiveComplexity(source);
    const funcRegex = /(?:function\s+\w+|=>\s*\{|\(.*?\)\s*=>)/g;
    const numberOfFunctions = (source.match(funcRegex) || []).length;
    const classRegex = /class\s+\w+/g;
    const numberOfClasses = (source.match(classRegex) || []).length;
    const maxDepth = computeMaxDepth(source);
    return { cyclomaticComplexity, cognitiveComplexity, linesOfCode, numberOfFunctions, numberOfClasses, maxDepth };
}
function computeCyclomaticComplexity(source) {
    const decisionPoints = [
        /\bif\s*\(/g, /\belse\s+if\s*\(/g, /\bwhile\s*\(/g,
        /\bfor\s*\(/g, /\bcase\s+/g, /\bcatch\s*\(/g,
        /\b\?\s*/g, /\b\|\|\s*/g, /\b&&\s*/g,
    ];
    let count = 1;
    for (const pattern of decisionPoints) {
        const matches = source.match(pattern);
        if (matches)
            count += matches.length;
    }
    return count;
}
function computeCognitiveComplexity(source) {
    let score = 0;
    const nestingPatterns = [
        /\bif\s*\(/g, /\bfor\s*\(/g, /\bwhile\s*\(/g,
        /\bcatch\s*\(/g, /\bcase\s+/g,
    ];
    for (const pattern of nestingPatterns) {
        const matches = source.match(pattern);
        if (matches)
            score += matches.length;
    }
    return score;
}
function computeMaxDepth(source) {
    let depth = 0;
    let maxDepth = 0;
    for (const char of source) {
        if (char === '{') {
            depth++;
            maxDepth = Math.max(maxDepth, depth);
        }
        else if (char === '}') {
            depth--;
        }
    }
    return maxDepth;
}
//# sourceMappingURL=complexity.js.map
import { Token, TokenType, Position, Range } from '../../api/types';

export interface TokenRule {
  pattern: RegExp;
  type: TokenType;
}

export class Tokenizer {
  private rules: TokenRule[];
  readonly languageId: string;

  constructor(languageId: string, rules: TokenRule[]) {
    this.languageId = languageId;
    this.rules = rules;
  }

  addRule(rule: TokenRule): void {
    this.rules.push(rule);
  }

  setRules(rules: TokenRule[]): void {
    this.rules = rules;
  }

  tokenize(text: string): Token[] {
    const tokens: Token[] = [];
    const lines = text.split('\n');

    let inBlockComment = false;
    let blockCommentStartLine = 0;
    let blockCommentStartColumn = 0;

    for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
      const line = lines[lineIndex];

      if (inBlockComment) {
        const endIndex = line.indexOf('*/');
        if (endIndex !== -1) {
          const start: Position = { line: blockCommentStartLine, column: blockCommentStartColumn };
          const end: Position = { line: lineIndex, column: endIndex + 2 };
          tokens.push({
            type: TokenType.Comment,
            value: lines.slice(blockCommentStartLine, lineIndex + 1).join('\n').substring(
              blockCommentStartColumn,
              lineIndex === blockCommentStartLine
                ? endIndex + 2
                : lines[lineIndex].length
            ),
            range: { start, end },
          });
          inBlockComment = false;
          let remaining = line.substring(endIndex + 2);
          if (remaining.length > 0) {
            const lineTokens = this.tokenizeLine(remaining, lineIndex, endIndex + 2);
            tokens.push(...lineTokens);
          }
        }
        continue;
      }

      const lineTokens = this.tokenizeLine(line, lineIndex, 0);

      for (const token of lineTokens) {
        if (token.type === TokenType.Comment && token.value.startsWith('/*')) {
          const endIndex = line.indexOf('*/', token.range.start.column + 2);
          if (endIndex === -1) {
            inBlockComment = true;
            blockCommentStartLine = lineIndex;
            blockCommentStartColumn = token.range.start.column;
            tokens.push(token);
            break;
          }
        }
        tokens.push(token);
      }
    }

    if (inBlockComment) {
      const start: Position = { line: blockCommentStartLine, column: blockCommentStartColumn };
      const end: Position = { line: lines.length - 1, column: lines[lines.length - 1].length };
      tokens.push({
        type: TokenType.Comment,
        value: lines.slice(blockCommentStartLine).join('\n'),
        range: { start, end },
      });
    }

    return tokens;
  }

  private tokenizeLine(line: string, lineIndex: number, startOffset: number): Token[] {
    const tokens: Token[] = [];
    let remaining = line.substring(startOffset);
    let currentOffset = startOffset;

    while (remaining.length > 0) {
      let matched = false;

      for (const rule of this.rules) {
        const match = remaining.match(rule.pattern);
        if (match && match.index === 0) {
          const value = match[0];
          const start: Position = { line: lineIndex, column: currentOffset };
          const end: Position = { line: lineIndex, column: currentOffset + value.length };
          tokens.push({ type: rule.type, value, range: { start, end } });
          currentOffset += value.length;
          remaining = remaining.substring(value.length);
          matched = true;
          break;
        }
      }

      if (!matched) {
        const start: Position = { line: lineIndex, column: currentOffset };
        const end: Position = { line: lineIndex, column: currentOffset + 1 };
        tokens.push({ type: TokenType.Unknown, value: remaining[0], range: { start, end } });
        currentOffset += 1;
        remaining = remaining.substring(1);
      }
    }

    return tokens;
  }
}

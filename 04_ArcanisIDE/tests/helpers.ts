import { TextDocument } from '../src/api/types';

export function makeDocument(
  text: string,
  languageId: string,
  fileName: string,
  version = 1,
): TextDocument {
  const lines = text.split('\n');
  return {
    uri: `file:///${fileName}`,
    fileName,
    languageId,
    version,
    getText: (range?: { start: { line: number; column: number }; end: { line: number; column: number } }) => {
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
        range: { start: { line, column: 0 }, end: { line, column: lineText.length } },
        firstNonWhitespaceCharacterIndex: lineText.search(/\S/),
        isEmptyOrWhitespace: lineText.trim().length === 0,
      };
    },
    lineCount: lines.length,
  };
}

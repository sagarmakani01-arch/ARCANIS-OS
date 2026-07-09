export interface DocComment {
  description: string;
  tags: DocTag[];
  line: number;
}

export interface DocTag {
  name: string;
  value: string;
  type?: string;
}

export interface DocumentedSymbol {
  name: string;
  type: 'function' | 'class' | 'interface' | 'type' | 'variable' | 'module';
  comment: DocComment | null;
  signature: string;
  line: number;
  children: DocumentedSymbol[];
}

export interface DocumentationPage {
  title: string;
  description: string;
  symbols: DocumentedSymbol[];
  format: 'markdown' | 'html';
}

export interface DocGenConfig {
  outputDir: string;
  format: 'markdown' | 'html';
  includePrivate: boolean;
  title: string;
}

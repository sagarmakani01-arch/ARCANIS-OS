import { LanguageDefinition } from "./types";

export class ArcanisLang {
  private languages: Map<string, LanguageDefinition> = new Map();

  constructor() {
    this.registerBuiltin();
  }

  private registerBuiltin(): void {
    this.register({
      name: "arcanis-script",
      version: "1.0",
      extensions: [".arc", ".arcs"],
      keywords: ["agent", "brain", "learn", "think", "remember", "act", "observe", "infer"],
      operators: ["->", "=>", "::", "|>", "<|"],
      types: ["intent", "memory", "thought", "action", "entity", "model"],
    });
    this.register({
      name: "typescript",
      version: "5.3",
      extensions: [".ts", ".tsx"],
      keywords: ["interface", "type", "enum", "class", "async", "await", "export", "import"],
      operators: ["=>", "|", "&", "as", "is", "keyof", "typeof"],
      types: ["string", "number", "boolean", "any", "void", "never", "unknown"],
    });
    this.register({
      name: "python",
      version: "3.12",
      extensions: [".py"],
      keywords: ["def", "class", "async", "await", "with", "as", "lambda", "yield"],
      operators: ["->", ":", "**", "//", "@", ":="],
      types: ["int", "str", "float", "bool", "list", "dict", "tuple", "set"],
    });
  }

  register(def: LanguageDefinition): void {
    this.languages.set(def.name, def);
  }

  get(name: string): LanguageDefinition | undefined {
    return this.languages.get(name);
  }

  detect(filename: string): LanguageDefinition | undefined {
    for (const [, lang] of this.languages) {
      if (lang.extensions.some(ext => filename.endsWith(ext))) {
        return lang;
      }
    }
    return undefined;
  }

  list(): LanguageDefinition[] {
    return Array.from(this.languages.values());
  }
}

import { CommandResult } from "./types";

export class ArcanisShell {
  private history: string[] = [];
  private cwd: string = "/home/user";
  private aliases: Map<string, string> = new Map();
  private aiMode: boolean = false;

  constructor() {
    this.aliases.set("ll", "ls -la");
    this.aliases.set("cls", "clear");
  }

  async execute(input: string): Promise<CommandResult> {
    const trimmed = input.trim();
    if (!trimmed) {
      return { success: true, output: "", timestamp: Date.now() };
    }

    this.history.push(trimmed);

    if (trimmed.toLowerCase() === "exit") {
      this.aiMode = false;
      return { success: true, output: "AI mode disabled.", timestamp: Date.now() };
    }

    if (this.aiMode) {
      return this.executeAICmd(trimmed);
    }

    const resolved = this.aliases.get(trimmed.split(/\s+/)[0])
      ? trimmed.replace(/^\S+/, this.aliases.get(trimmed.split(/\s+/)[0])!)
      : trimmed;

    try {
      const parts = resolved.split(/\s+/);
      const cmd = parts[0].toLowerCase();
      const args = parts.slice(1);

      switch (cmd) {
        case "help":
          return this.cmdHelp(args);
        case "echo":
          return { success: true, output: args.join(" "), timestamp: Date.now() };
        case "pwd":
          return { success: true, output: this.cwd, timestamp: Date.now() };
        case "clear":
          this.history = [];
          return { success: true, output: "", timestamp: Date.now() };
        case "date":
          return { success: true, output: new Date().toString(), timestamp: Date.now() };
        case "ai":
          this.aiMode = true;
          return { success: true, output: "AI mode enabled. Type natural language commands.", timestamp: Date.now() };
        case "exit":
          this.aiMode = false;
          return { success: true, output: "AI mode disabled.", timestamp: Date.now() };
        case "history":
          return { success: true, output: this.history.map((h, i) => `  ${i + 1}  ${h}`).join("\n"), timestamp: Date.now() };
        default:
          return { success: false, output: "", error: `Unknown command: ${cmd}`, timestamp: Date.now() };
      }
    } catch (error) {
      return { success: false, output: "", error: String(error), timestamp: Date.now() };
    }
  }

  private async executeAICmd(input: string): Promise<CommandResult> {
    return {
      success: true,
      output: `[AI] Processing: "${input}"\n[AI] This would be interpreted by ArcanisBrain.`,
      timestamp: Date.now(),
    };
  }

  private cmdHelp(args: string[]): CommandResult {
    const commands = [
      "  help      Show this help message",
      "  echo      Echo text",
      "  pwd       Print working directory",
      "  clear     Clear terminal",
      "  date      Show current date/time",
      "  ai        Enter AI command mode",
      "  exit      Exit AI mode",
      "  history   Show command history",
    ];
    const topic = args[0];
    if (topic) {
      return { success: true, output: `Help for '${topic}':\n  Use '${topic}' with appropriate arguments.`, timestamp: Date.now() };
    }
    return { success: true, output: `ArcanisShell v1.0\nAvailable commands:\n${commands.join("\n")}`, timestamp: Date.now() };
  }

  getPrompt(): string {
    const mode = this.aiMode ? "🤖 " : "";
    return `${mode}arcanis@os:${this.cwd}$ `;
  }

  getHistory(): string[] {
    return [...this.history];
  }

  isAIMode(): boolean {
    return this.aiMode;
  }

  setCwd(path: string): void {
    this.cwd = path;
  }
}

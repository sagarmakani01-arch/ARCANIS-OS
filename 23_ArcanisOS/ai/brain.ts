import { v4 as uuid } from "uuid";
import { ArcanisMemory } from "./memory";
import { Intent, Thought } from "./types";

export class ArcanisBrain {
  public readonly memory: ArcanisMemory;
  private thoughts: Thought[] = [];
  private processing: boolean = false;

  constructor() {
    this.memory = new ArcanisMemory();
  }

  async think(input: string): Promise<Thought> {
    this.processing = true;
    const thought: Thought = {
      id: uuid(),
      content: input,
      confidence: 0,
      timestamp: Date.now(),
      source: "brain",
    };
    this.thoughts.push(thought);
    this.processing = false;
    return thought;
  }

  async understand(input: string): Promise<Intent> {
    const normalized = input.toLowerCase().trim();
    const tokens = normalized.split(/\s+/);
    const action = tokens[0] || "unknown";
    return {
      action,
      entities: { tokens: tokens.slice(1), raw: input },
      confidence: 0.5,
      raw: input,
    };
  }

  async learn(input: string, output: string, feedback: number = 0): Promise<void> {
    this.memory.store(
      `learn:${input}`,
      { input, output, feedback },
      1,
      null,
      { feedback }
    );
  }

  async reason(premises: string[]): Promise<string> {
    const result: string[] = [];
    for (const premise of premises) {
      const memories = this.memory.recall(premise);
      if (memories.length > 0) {
        const val = memories[0].value;
        const str = typeof val === "object" ? (val as Record<string, unknown>).output || JSON.stringify(val) : String(val);
        result.push(`From memory: ${str}`);
      }
    }
    return result.join("\n") || "No relevant knowledge found.";
  }

  getRecentThoughts(count: number = 10): Thought[] {
    return this.thoughts.slice(-count);
  }

  isProcessing(): boolean {
    return this.processing;
  }
}

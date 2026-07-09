import { ArcanisDesktop } from "./desktop";
import { ArcanisShell } from "./shell";
import { CommandResult } from "./types";

export class ArcanisUI {
  public readonly desktop: ArcanisDesktop;
  public readonly shell: ArcanisShell;
  private listeners: Array<(event: string, data: unknown) => void> = [];

  constructor() {
    this.desktop = new ArcanisDesktop();
    this.shell = new ArcanisShell();

    this.desktop.onEvent((event, data) => {
      this.emit(`desktop:${event}`, data);
    });
  }

  async processCommand(input: string): Promise<CommandResult> {
    this.emit("command:executing", input);
    const result = await this.shell.execute(input);
    this.emit("command:executed", result);
    return result;
  }

  updateTheme(theme: Record<string, unknown>): void {
    this.desktop.setTheme(theme as Parameters<ArcanisDesktop["setTheme"]>[0]);
  }

  onEvent(callback: (event: string, data: unknown) => void): void {
    this.listeners.push(callback);
  }

  private emit(event: string, data: unknown): void {
    for (const listener of this.listeners) {
      listener(event, data);
    }
  }
}

import { IDisposable, Command } from '../api/types';

export interface CommandHandler {
  (...args: unknown[]): unknown | Promise<unknown>;
}

export interface ICommandRegistry {
  registerCommand(id: string, handler: CommandHandler, context?: string): IDisposable;
  executeCommand(id: string, ...args: unknown[]): Promise<unknown>;
  getCommand(id: string): CommandDescriptor | undefined;
  getCommands(context?: string): CommandDescriptor[];
  hasCommand(id: string): boolean;
}

export interface CommandDescriptor {
  id: string;
  context?: string;
}

export class CommandRegistry implements ICommandRegistry {
  private commands = new Map<string, { handler: CommandHandler; context?: string }>();

  registerCommand(id: string, handler: CommandHandler, context?: string): IDisposable {
    if (this.commands.has(id)) {
      console.warn(`[CommandRegistry] Command "${id}" is being overridden.`);
    }
    this.commands.set(id, { handler, context });
    return {
      dispose: () => this.commands.delete(id),
    };
  }

  async executeCommand(id: string, ...args: unknown[]): Promise<unknown> {
    const entry = this.commands.get(id);
    if (!entry) {
      throw new Error(`Command "${id}" not found.`);
    }
    try {
      return await entry.handler(...args);
    } catch (err) {
      console.error(`[CommandRegistry] Error executing "${id}":`, err);
      throw err;
    }
  }

  getCommand(id: string): CommandDescriptor | undefined {
    const entry = this.commands.get(id);
    if (!entry) return undefined;
    return { id, context: entry.context };
  }

  getCommands(context?: string): CommandDescriptor[] {
    const result: CommandDescriptor[] = [];
    for (const [id, entry] of this.commands) {
      if (!context || entry.context === context) {
        result.push({ id, context: entry.context });
      }
    }
    return result;
  }

  hasCommand(id: string): boolean {
    return this.commands.has(id);
  }
}

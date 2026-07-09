import { spawn, ChildProcess } from 'child_process';
import { IDisposable } from '../api/types';
import { EventBus } from '../core/EventBus';

export interface TerminalOptions {
  title?: string;
  shellPath?: string;
  shellArgs?: string[];
  cwd?: string;
  env?: Record<string, string>;
}

export interface TerminalInstance {
  id: number;
  title: string;
  process?: string;
  cols: number;
  rows: number;
  buffer: string[];
}

interface ManagedTerminal extends TerminalInstance {
  proc: ChildProcess | null;
  dataHandlers: Set<(data: string) => void>;
  exitHandlers: Set<(code: number | null) => void>;
}

export class Terminal {
  private terminals = new Map<number, ManagedTerminal>();
  private nextId = 1;

  constructor(private eventBus: EventBus) {}

  async open(options?: TerminalOptions): Promise<number> {
    const id = this.nextId++;
    const shellPath = options?.shellPath || this.getDefaultShell();
    const shellArgs = options?.shellArgs || [];

    const proc = spawn(shellPath, shellArgs, {
      cwd: options?.cwd || process.cwd(),
      env: { ...process.env, ...options?.env } as NodeJS.ProcessEnv,
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    const instance: ManagedTerminal = {
      id,
      title: options?.title || `Terminal ${id}`,
      process: shellPath,
      cols: 80,
      rows: 24,
      buffer: [],
      proc,
      dataHandlers: new Set(),
      exitHandlers: new Set(),
    };

    proc.stdout?.on('data', (data: Buffer) => {
      const text = data.toString();
      instance.buffer.push(text);
      for (const handler of instance.dataHandlers) {
        handler(text);
      }
    });

    proc.stderr?.on('data', (data: Buffer) => {
      const text = data.toString();
      instance.buffer.push(text);
      for (const handler of instance.dataHandlers) {
        handler(text);
      }
    });

    proc.on('exit', (code) => {
      for (const handler of instance.exitHandlers) {
        handler(code);
      }
      this.terminals.delete(id);
      this.eventBus.emit('terminal:closed', { id, code });
    });

    this.terminals.set(id, instance);
    this.eventBus.emit('terminal:opened', instance);

    return id;
  }

  close(terminalId: number): void {
    const instance = this.terminals.get(terminalId);
    if (!instance) return;

    if (instance.proc && !instance.proc.killed) {
      instance.proc.kill('SIGTERM');
      setTimeout(() => {
        if (instance.proc && !instance.proc.killed) {
          instance.proc.kill('SIGKILL');
        }
      }, 2000);
    }

    this.terminals.delete(terminalId);
    this.eventBus.emit('terminal:closed', { id: terminalId });
  }

  write(terminalId: number, data: string): void {
    const instance = this.terminals.get(terminalId);
    if (!instance || !instance.proc || !instance.proc.stdin) return;

    instance.proc.stdin.write(data);
    this.eventBus.emit('terminal:data', { id: terminalId, data });
  }

  onData(terminalId: number, handler: (data: string) => void): IDisposable {
    const instance = this.terminals.get(terminalId);
    if (!instance) {
      throw new Error(`Terminal ${terminalId} not found`);
    }

    instance.dataHandlers.add(handler);

    return {
      dispose: () => {
        instance.dataHandlers.delete(handler);
      },
    };
  }

  onExit(terminalId: number, handler: (code: number | null) => void): IDisposable {
    const instance = this.terminals.get(terminalId);
    if (!instance) {
      throw new Error(`Terminal ${terminalId} not found`);
    }

    instance.exitHandlers.add(handler);

    return {
      dispose: () => {
        instance.exitHandlers.delete(handler);
      },
    };
  }

  resize(terminalId: number, cols: number, rows: number): void {
    const instance = this.terminals.get(terminalId);
    if (!instance) return;

    instance.cols = cols;
    instance.rows = rows;
  }

  clear(terminalId: number): void {
    const instance = this.terminals.get(terminalId);
    if (!instance) return;

    instance.buffer = [];
  }

  getTerminals(): TerminalInstance[] {
    return Array.from(this.terminals.values()).map(({ proc, dataHandlers, exitHandlers, ...rest }) => rest);
  }

  private getDefaultShell(): string {
    if (process.platform === 'win32') {
      return process.env.COMSPEC || 'cmd.exe';
    }
    return process.env.SHELL || '/bin/sh';
  }
}

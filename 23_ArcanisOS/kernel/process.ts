import { v4 as uuid } from "uuid";
import {
  ProcessInfo,
  ProcessState,
  Priority,
} from "./types";

export class Process {
  public readonly pid: string;
  public readonly createdAt: number;
  public state: ProcessState;
  public priority: Priority;
  public cpuUsage: number;
  public memoryUsage: number;
  public metadata: Record<string, unknown>;

  constructor(
    public readonly name: string,
    public readonly parentPid: string | null = null,
    priority: Priority = Priority.Normal,
    public readonly executable?: () => Promise<void>
  ) {
    this.pid = uuid();
    this.createdAt = Date.now();
    this.state = ProcessState.Created;
    this.priority = priority;
    this.cpuUsage = 0;
    this.memoryUsage = 0;
    this.metadata = {};
  }

  get info(): ProcessInfo {
    return {
      pid: this.pid,
      name: this.name,
      state: this.state,
      priority: this.priority,
      parentPid: this.parentPid,
      createdAt: this.createdAt,
      cpuUsage: this.cpuUsage,
      memoryUsage: this.memoryUsage,
      metadata: { ...this.metadata },
    };
  }

  async start(): Promise<void> {
    this.state = ProcessState.Running;
    if (this.executable) {
      try {
        await this.executable();
      } catch (error) {
        this.state = ProcessState.Terminated;
        throw error;
      }
    }
  }

  suspend(): void {
    if (this.state === ProcessState.Running) {
      this.state = ProcessState.Suspended;
    }
  }

  resume(): void {
    if (this.state === ProcessState.Suspended) {
      this.state = ProcessState.Running;
    }
  }

  terminate(): void {
    this.state = ProcessState.Terminated;
  }

  block(): void {
    if (this.state === ProcessState.Running) {
      this.state = ProcessState.Blocked;
    }
  }

  unblock(): void {
    if (this.state === ProcessState.Blocked) {
      this.state = ProcessState.Running;
    }
  }
}

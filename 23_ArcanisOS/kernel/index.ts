import { Process } from "./process";
import { Scheduler } from "./scheduler";
import { ModuleManager } from "./module";
import {
  KernelConfig,
  KernelFeatures,
  Priority,
  ProcessState,
  SecurityLevel,
  SystemStats,
} from "./types";

export const DEFAULT_CONFIG: KernelConfig = {
  version: "1.0.0-alpha",
  maxProcesses: 1024,
  defaultPriority: Priority.Normal,
  schedulerTickMs: 100,
  securityLevel: SecurityLevel.High,
  features: {
    aiAcceleration: true,
    voiceControl: true,
    memoryManagement: true,
    processIsolation: true,
  },
};

export class ArcanisKernel {
  public readonly config: KernelConfig;
  public readonly scheduler: Scheduler;
  public readonly moduleManager: ModuleManager;
  private processes: Map<string, Process> = new Map();
  private startedAt: number = 0;
  private running: boolean = false;

  constructor(config: Partial<KernelConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.scheduler = new Scheduler(this.config.schedulerTickMs);
    this.moduleManager = new ModuleManager(this);
  }

  async boot(): Promise<void> {
    this.startedAt = Date.now();
    this.running = true;
    this.scheduler.start();
  }

  async shutdown(): Promise<void> {
    this.running = false;
    this.scheduler.stop();
    await this.moduleManager.shutdownAll();
    for (const [, process] of this.processes) {
      process.terminate();
    }
    this.processes.clear();
  }

  async createProcess(
    name: string,
    executable?: () => Promise<void>,
    priority: Priority = Priority.Normal,
    parentPid: string | null = null
  ): Promise<Process> {
    if (this.processes.size >= this.config.maxProcesses) {
      throw new Error("Max process limit reached");
    }
    const process = new Process(name, parentPid, priority, executable);
    this.processes.set(process.pid, process);
    this.scheduler.enqueue(process);
    return process;
  }

  getProcess(pid: string): Process | undefined {
    return this.processes.get(pid);
  }

  killProcess(pid: string): boolean {
    const process = this.processes.get(pid);
    if (!process) return false;
    process.terminate();
    this.scheduler.dequeue(process);
    this.processes.delete(pid);
    return true;
  }

  listProcesses(includeTerminated: boolean = false): Process[] {
    const all = Array.from(this.processes.values());
    return includeTerminated
      ? all
      : all.filter(p => p.state !== ProcessState.Terminated);
  }

  getStats(): SystemStats {
    const allProcesses = this.listProcesses();
    const activeProcesses = allProcesses.filter(
      p => p.state === ProcessState.Running
    );

    return {
      uptime: this.running ? Date.now() - this.startedAt : 0,
      totalProcesses: allProcesses.length,
      activeProcesses: activeProcesses.length,
      cpuLoad: this.calculateCpuLoad(),
      memoryUsed: allProcesses.reduce((sum, p) => sum + p.memoryUsage, 0),
      memoryTotal: 16 * 1024 * 1024 * 1024,
    };
  }

  isRunning(): boolean {
    return this.running;
  }

  get uptime(): number {
    return this.running ? Date.now() - this.startedAt : 0;
  }

  private calculateCpuLoad(): number {
    const running = this.listProcesses().filter(
      p => p.state === ProcessState.Running
    );
    if (running.length === 0) return 0;
    const totalCpu = running.reduce((sum, p) => sum + p.cpuUsage, 0);
    return Math.min(totalCpu / running.length, 100);
  }
}

export { Process, Scheduler, ModuleManager };
export * from "./types";

import { describe, it, expect, beforeEach } from "vitest";
import { ArcanisKernel, Process, Priority, ProcessState } from "../kernel";

describe("ArcanisKernel", () => {
  let kernel: ArcanisKernel;

  beforeEach(() => {
    kernel = new ArcanisKernel();
  });

  it("should boot and shutdown", async () => {
    await kernel.boot();
    expect(kernel.isRunning()).toBe(true);
    await kernel.shutdown();
    expect(kernel.isRunning()).toBe(false);
  });

  it("should create processes", async () => {
    await kernel.boot();
    const proc = await kernel.createProcess("test-process");
    expect(proc).toBeInstanceOf(Process);
    expect(proc.state).toBe(ProcessState.Created);
    await kernel.shutdown();
  });

  it("should enforce max process limit", async () => {
    const limited = new ArcanisKernel({ maxProcesses: 1 });
    await limited.boot();
    await limited.createProcess("proc1");
    await expect(limited.createProcess("proc2")).rejects.toThrow("Max process limit");
    await limited.shutdown();
  });

  it("should kill processes", async () => {
    await kernel.boot();
    const proc = await kernel.createProcess("to-kill");
    const killed = kernel.killProcess(proc.pid);
    expect(killed).toBe(true);
    expect(kernel.getProcess(proc.pid)).toBeUndefined();
    await kernel.shutdown();
  });

  it("should return system stats", async () => {
    await kernel.boot();
    const stats = kernel.getStats();
    expect(stats).toHaveProperty("uptime");
    expect(stats).toHaveProperty("totalProcesses");
    expect(stats).toHaveProperty("activeProcesses");
    await kernel.shutdown();
  });
});

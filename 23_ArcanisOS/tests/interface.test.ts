import { describe, it, expect, beforeEach } from "vitest";
import { ArcanisDesktop, ArcanisShell, ArcanisUI } from "../interface";

describe("ArcanisDesktop", () => {
  let desktop: ArcanisDesktop;

  beforeEach(() => {
    desktop = new ArcanisDesktop();
  });

  it("should have default config", () => {
    expect(desktop.config.theme.mode).toBe("dark");
    expect(desktop.config.theme.primaryColor).toBe("#6366f1");
  });

  it("should update theme", () => {
    desktop.setTheme({ mode: "light", primaryColor: "#ff0000" });
    expect(desktop.config.theme.mode).toBe("light");
    expect(desktop.config.theme.primaryColor).toBe("#ff0000");
  });

  it("should manage shortcuts", () => {
    desktop.addShortcut({ id: "1", name: "Terminal", icon: "terminal", command: "terminal", category: "system" });
    expect(desktop.config.dock).toHaveLength(1);
    desktop.removeShortcut("1");
    expect(desktop.config.dock).toHaveLength(0);
  });
});

describe("ArcanisShell", () => {
  let shell: ArcanisShell;

  beforeEach(() => {
    shell = new ArcanisShell();
  });

  it("should echo commands", async () => {
    const result = await shell.execute("echo hello world");
    expect(result.success).toBe(true);
    expect(result.output).toBe("hello world");
  });

  it("should handle pwd", async () => {
    const result = await shell.execute("pwd");
    expect(result.success).toBe(true);
    expect(result.output).toBeTruthy();
  });

  it("should handle unknown commands", async () => {
    const result = await shell.execute("nonexistent");
    expect(result.success).toBe(false);
    expect(result.error).toContain("Unknown command");
  });

  it("should toggle AI mode", async () => {
    let result = await shell.execute("ai");
    expect(result.success).toBe(true);
    expect(shell.isAIMode()).toBe(true);
    result = await shell.execute("exit");
    expect(shell.isAIMode()).toBe(false);
  });
});

describe("ArcanisUI", () => {
  it("should integrate desktop and shell", async () => {
    const ui = new ArcanisUI();
    const result = await ui.processCommand("echo integration test");
    expect(result.success).toBe(true);
    expect(result.output).toBe("integration test");
  });
});

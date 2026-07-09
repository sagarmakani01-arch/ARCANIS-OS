import { describe, it, expect, beforeEach } from "vitest";
import { ArcanisLang, ArcanisBuild, ArcanisPackageManager } from "../development";

describe("ArcanisLang", () => {
  let lang: ArcanisLang;

  beforeEach(() => {
    lang = new ArcanisLang();
  });

  it("should detect languages by extension", () => {
    expect(lang.detect("file.ts")?.name).toBe("typescript");
    expect(lang.detect("file.py")?.name).toBe("python");
    expect(lang.detect("file.arc")?.name).toBe("arcanis-script");
  });

  it("should list registered languages", () => {
    expect(lang.list().length).toBeGreaterThanOrEqual(3);
  });

  it("should register custom languages", () => {
    lang.register({
      name: "custom", version: "1.0", extensions: [".cust"],
      keywords: [], operators: [], types: [],
    });
    expect(lang.get("custom")).toBeDefined();
  });
});

describe("ArcanisBuild", () => {
  let build: ArcanisBuild;

  beforeEach(() => {
    build = new ArcanisBuild();
  });

  it("should fail on missing entry", async () => {
    await expect(build.build({ entry: "nonexistent.ts", output: "dist", target: "js", optimize: false, minify: false, sourceMaps: false })).rejects.toThrow();
  });
});

describe("ArcanisPackageManager", () => {
  let pm: ArcanisPackageManager;

  beforeEach(() => {
    pm = new ArcanisPackageManager("https://registry.arcanis.io", "./test-apps");
  });

  it("should install packages", async () => {
    const pkg = await pm.install("test-pkg");
    expect(pkg.name).toBe("test-pkg");
    expect(pm.list()).toHaveLength(1);
  });

  it("should uninstall packages", async () => {
    await pm.install("to-remove");
    expect(pm.uninstall("to-remove")).toBe(true);
    expect(pm.list()).toHaveLength(0);
  });
});

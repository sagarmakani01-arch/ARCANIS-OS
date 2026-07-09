import { existsSync, mkdirSync, copyFileSync, writeFileSync, readdirSync, statSync } from "fs";
import { join, relative, resolve } from "path";

interface InstallerOptions {
  prefix: string;
  components: string[];
  withExamples: boolean;
  withDocs: boolean;
}

export class ArcanisInstaller {
  private sourceRoot: string;
  private options: InstallerOptions;

  constructor(sourceRoot: string, options: Partial<InstallerOptions> = {}) {
    this.sourceRoot = sourceRoot;
    this.options = {
      prefix: options.prefix || "/opt/arcanis-os",
      components: options.components || ["kernel", "ai", "interface", "development", "security"],
      withExamples: options.withExamples ?? true,
      withDocs: options.withDocs ?? true,
    };
  }

  async install(): Promise<{ success: boolean; path: string; components: string[] }> {
    const targetDir = resolve(this.options.prefix);
    if (!existsSync(targetDir)) {
      mkdirSync(targetDir, { recursive: true });
    }

    const installed: string[] = [];
    for (const component of this.options.components) {
      const srcPath = join(this.sourceRoot, component);
      if (existsSync(srcPath)) {
        const destPath = join(targetDir, component);
        this.copyRecursive(srcPath, destPath);
        installed.push(component);
      }
    }

    const configSrc = join(this.sourceRoot, "config", "default.json");
    if (existsSync(configSrc)) {
      const configDest = join(targetDir, "config");
      if (!existsSync(configDest)) mkdirSync(configDest, { recursive: true });
      copyFileSync(configSrc, join(configDest, "config.json"));
    }

    writeFileSync(join(targetDir, "arcanis.conf"), this.generateConfig());
    writeFileSync(join(targetDir, ".arcanis-version"), "1.0.0-alpha");

    return { success: true, path: targetDir, components: installed };
  }

  private copyRecursive(src: string, dest: string): void {
    if (!existsSync(dest)) mkdirSync(dest, { recursive: true });
    const entries = readdirSync(src, { withFileTypes: true });
    for (const entry of entries) {
      const srcPath = join(src, entry.name);
      const destPath = join(dest, entry.name);
      if (entry.isDirectory()) {
        this.copyRecursive(srcPath, destPath);
      } else {
        copyFileSync(srcPath, destPath);
      }
    }
  }

  private generateConfig(): string {
    return `# ArcanisOS Configuration
INSTALL_PATH=${this.options.prefix}
COMPONENTS=${this.options.components.join(",")}
AI_ENABLED=true
VOICE_CONTROL=true
SECURITY_LEVEL=high
AUTO_UPDATE=true
`;
  }

  async verify(): Promise<{ complete: boolean; missing: string[] }> {
    const missing: string[] = [];
    for (const component of this.options.components) {
      const path = join(this.options.prefix, component);
      if (!existsSync(path)) missing.push(component);
    }
    return { complete: missing.length === 0, missing };
  }

  async uninstall(): Promise<void> {
    const targetDir = resolve(this.options.prefix);
    if (existsSync(targetDir)) {
      const { rmSync } = await import("fs");
      rmSync(targetDir, { recursive: true, force: true });
    }
  }
}

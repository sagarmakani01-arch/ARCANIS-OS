import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";
import { PackageManifest } from "./types";

export class ArcanisPackageManager {
  private packages: Map<string, PackageManifest> = new Map();
  private registry: string;
  private installPath: string;

  constructor(registry: string = "https://registry.arcanis.io", installPath: string = "./apps") {
    this.registry = registry;
    this.installPath = installPath;
  }

  async install(name: string, version: string = "latest"): Promise<PackageManifest> {
    const pkg = await this.resolve(name, version);
    this.packages.set(`${name}@${pkg.version}`, pkg);
    const fullPath = join(this.installPath, name);
    if (!existsSync(fullPath)) {
      mkdirSync(fullPath, { recursive: true });
    }
    writeFileSync(join(fullPath, "manifest.json"), JSON.stringify(pkg, null, 2));
    return pkg;
  }

  uninstall(name: string): boolean {
    for (const [key] of this.packages) {
      if (key.startsWith(`${name}@`)) {
        this.packages.delete(key);
        return true;
      }
    }
    return false;
  }

  list(): PackageManifest[] {
    return Array.from(this.packages.values());
  }

  get(name: string): PackageManifest | undefined {
    for (const [, pkg] of this.packages) {
      if (pkg.name === name) return pkg;
    }
    return undefined;
  }

  private async resolve(name: string, version: string): Promise<PackageManifest> {
    return {
      name,
      version: version === "latest" ? "1.0.0" : version,
      description: `${name} package`,
      author: "ArcanisOS",
      dependencies: {},
      entry: `index.js`,
      type: "app",
    };
  }

  async updateAll(): Promise<void> {
    for (const [, pkg] of this.packages) {
      const updated = await this.resolve(pkg.name, "latest");
      this.packages.set(`${pkg.name}@${updated.version}`, updated);
    }
  }
}

import { createHash } from "crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { join, dirname, relative } from "path";
import { BuildConfig, BuildArtifact } from "./types";

export class ArcanisBuild {
  private artifacts: BuildArtifact[] = [];

  async build(config: BuildConfig): Promise<BuildArtifact[]> {
    this.artifacts = [];
    const entryPath = join(process.cwd(), config.entry);
    if (!existsSync(entryPath)) {
      throw new Error(`Entry file not found: ${entryPath}`);
    }

    const outputDir = join(process.cwd(), config.output);
    if (!existsSync(outputDir)) {
      mkdirSync(outputDir, { recursive: true });
    }

    const source = readFileSync(entryPath, "utf-8");
    const result = this.transpile(source, config);
    const outputPath = join(outputDir, this.getOutputName(config));

    writeFileSync(outputPath, result);
    const hash = createHash("sha256").update(result).digest("hex");

    const artifact: BuildArtifact = {
      name: config.entry.split("/").pop() || "output",
      path: outputPath,
      size: Buffer.byteLength(result),
      hash,
      type: "bundle",
    };
    this.artifacts.push(artifact);
    return this.artifacts;
  }

  private transpile(source: string, config: BuildConfig): string {
    let result = source;
    if (config.optimize) {
      result = result.replace(/\/\/.*$/gm, "").replace(/\/\*[\s\S]*?\*\//g, "");
      result = result.replace(/\s+/g, " ").trim();
    }
    return result;
  }

  private getOutputName(config: BuildConfig): string {
    const base = config.entry.split("/").pop()?.split(".")[0] || "output";
    return `${base}.${config.target || "js"}`;
  }

  getArtifacts(): BuildArtifact[] {
    return [...this.artifacts];
  }

  clear(): void {
    this.artifacts = [];
  }
}

import { existsSync, readFileSync, readdirSync } from "fs";
import { join, extname } from "path";
import { ArcanisLang } from "./lang";
import { IDEProject, FileBuffer } from "./types";

export class ArcanisIDE {
  public readonly lang: ArcanisLang;
  private projects: Map<string, IDEProject> = new Map();
  private openBuffers: Map<string, FileBuffer> = new Map();
  private activeProject: IDEProject | null = null;

  constructor() {
    this.lang = new ArcanisLang();
  }

  openProject(root: string): IDEProject {
    const name = root.split(/[/\\]/).pop() || "project";
    const files = this.scanFiles(root);
    const project: IDEProject = {
      name,
      root,
      language: "typescript",
      files,
      buildConfig: {
        entry: files[0] || "index.ts",
        output: "dist",
        target: "js",
        optimize: true,
        minify: false,
        sourceMaps: true,
      },
      openFiles: [],
    };
    this.projects.set(root, project);
    this.activeProject = project;
    return project;
  }

  openFile(path: string): FileBuffer {
    if (this.openBuffers.has(path)) {
      return this.openBuffers.get(path)!;
    }
    const content = existsSync(path) ? readFileSync(path, "utf-8") : "";
    const lang = this.lang.detect(path);
    const buffer: FileBuffer = {
      path,
      content,
      language: lang?.name || "unknown",
      dirty: false,
      cursor: 0,
    };
    this.openBuffers.set(path, buffer);
    if (this.activeProject && !this.activeProject.openFiles.includes(path)) {
      this.activeProject.openFiles.push(path);
    }
    return buffer;
  }

  closeFile(path: string): void {
    this.openBuffers.delete(path);
    if (this.activeProject) {
      this.activeProject.openFiles = this.activeProject.openFiles.filter(f => f !== path);
    }
  }

  private scanFiles(root: string): string[] {
    try {
      const files: string[] = [];
      const entries = readdirSync(root, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.isFile()) {
          files.push(entry.name);
        }
      }
      return files;
    } catch {
      return [];
    }
  }

  getActiveProject(): IDEProject | null {
    return this.activeProject;
  }

  getOpenBuffers(): FileBuffer[] {
    return Array.from(this.openBuffers.values());
  }
}

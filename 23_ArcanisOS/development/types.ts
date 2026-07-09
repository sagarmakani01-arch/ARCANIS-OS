export interface LanguageDefinition {
  name: string;
  version: string;
  extensions: string[];
  keywords: string[];
  operators: string[];
  types: string[];
}

export interface BuildConfig {
  entry: string;
  output: string;
  target: string;
  optimize: boolean;
  minify: boolean;
  sourceMaps: boolean;
}

export interface BuildArtifact {
  name: string;
  path: string;
  size: number;
  hash: string;
  type: "binary" | "source" | "asset" | "bundle";
}

export interface PackageManifest {
  name: string;
  version: string;
  description: string;
  author: string;
  dependencies: Record<string, string>;
  entry: string;
  type: "app" | "library" | "theme" | "extension";
}

export interface IDEProject {
  name: string;
  root: string;
  language: string;
  files: string[];
  buildConfig: BuildConfig;
  openFiles: string[];
}

export interface FileBuffer {
  path: string;
  content: string;
  language: string;
  dirty: boolean;
  cursor: number;
}

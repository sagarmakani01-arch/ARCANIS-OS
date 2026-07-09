export interface Intent {
  action: string;
  entities: Record<string, unknown>;
  confidence: number;
  raw: string;
}

export interface MemoryEntry {
  id: string;
  key: string;
  value: unknown;
  type: MemoryType;
  timestamp: number;
  ttl: number | null;
  metadata: Record<string, unknown>;
}

export enum MemoryType {
  Episodic = "episodic",
  Semantic = "semantic",
  Procedural = "procedural",
  Working = "working",
}

export interface AgentConfig {
  name: string;
  role: string;
  model: string;
  capabilities: string[];
  temperature: number;
  maxTokens: number;
}

export interface Thought {
  id: string;
  content: string;
  confidence: number;
  timestamp: number;
  source: string;
}

export interface LearningExample {
  input: string;
  output: string;
  feedback: number;
  timestamp: number;
}

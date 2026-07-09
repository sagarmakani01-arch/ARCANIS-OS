import { describe, it, expect, beforeEach } from "vitest";
import { ArcanisBrain, ArcanisMemory, ArcanisAgents, ArcanisAgent } from "../ai";
import { MemoryType } from "../ai/types";

describe("ArcanisBrain", () => {
  let brain: ArcanisBrain;

  beforeEach(() => {
    brain = new ArcanisBrain();
  });

  it("should think", async () => {
    const thought = await brain.think("Hello world");
    expect(thought).toHaveProperty("id");
    expect(thought).toHaveProperty("content");
    expect(thought.content).toBe("Hello world");
  });

  it("should understand intents", async () => {
    const intent = await brain.understand("open calculator");
    expect(intent).toHaveProperty("action");
    expect(intent).toHaveProperty("confidence");
    expect(intent.action).toBe("open");
  });

  it("should learn and recall", async () => {
    await brain.learn("What is AI?", "Artificial Intelligence");
    const result = await brain.reason(["AI"]);
    expect(result).toContain("Artificial Intelligence");
  });
});

describe("ArcanisMemory", () => {
  let memory: ArcanisMemory;

  beforeEach(() => {
    memory = new ArcanisMemory(100);
  });

  it("should store and recall entries", () => {
    memory.store("user_name", "Alice", MemoryType.Semantic);
    const results = memory.recall("user_name");
    expect(results).toHaveLength(1);
    expect(results[0].value).toBe("Alice");
  });

  it("should forget entries", () => {
    const entry = memory.store("temp", "value", MemoryType.Working, 1000);
    const forgot = memory.forget(entry.id);
    expect(forgot).toBe(true);
    expect(memory.recall("temp")).toHaveLength(0);
  });

  it("should clear by type", () => {
    memory.store("k1", "v1", MemoryType.Semantic);
    memory.store("k2", "v2", MemoryType.Episodic);
    memory.clear(MemoryType.Semantic);
    expect(memory.stats().total).toBe(1);
  });
});

describe("ArcanisAgents", () => {
  let brain: ArcanisBrain;
  let agents: ArcanisAgents;

  beforeEach(() => {
    brain = new ArcanisBrain();
    agents = new ArcanisAgents(brain);
  });

  it("should create agents", () => {
    const agent = agents.createAgent({
      name: "Helper",
      role: "assistant",
      model: "arcanis-v1",
      capabilities: ["chat", "search"],
      temperature: 0.7,
      maxTokens: 1024,
    });
    expect(agent).toBeInstanceOf(ArcanisAgent);
    expect(agent.config.name).toBe("Helper");
  });

  it("should list agents", () => {
    agents.createAgent({ name: "A1", role: "r", model: "m", capabilities: [], temperature: 0.5, maxTokens: 512 });
    agents.createAgent({ name: "A2", role: "r", model: "m", capabilities: [], temperature: 0.5, maxTokens: 512 });
    expect(agents.listAgents()).toHaveLength(2);
  });
});

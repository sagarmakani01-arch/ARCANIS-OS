import { v4 as uuid } from "uuid";
import { ArcanisBrain } from "./brain";
import { AgentConfig, Intent } from "./types";

export class ArcanisAgent {
  public readonly id: string;
  public readonly config: AgentConfig;
  private brain: ArcanisBrain;
  private active: boolean = false;
  private taskQueue: string[] = [];

  constructor(config: AgentConfig, brain: ArcanisBrain) {
    this.id = uuid();
    this.config = config;
    this.brain = brain;
  }

  async start(): Promise<void> {
    this.active = true;
    this.processQueue();
  }

  async stop(): Promise<void> {
    this.active = false;
  }

  async assignTask(task: string): Promise<void> {
    this.taskQueue.push(task);
    if (this.active) {
      this.processQueue();
    }
  }

  private async processQueue(): Promise<void> {
    while (this.active && this.taskQueue.length > 0) {
      const task = this.taskQueue.shift()!;
      await this.executeTask(task);
    }
  }

  private async executeTask(task: string): Promise<void> {
    const intent = await this.brain.understand(task);
    this.brain.memory.store(
      `agent:${this.config.name}:task`,
      { task, intent },
      1,
      3600000,
      { agentId: this.id }
    );
  }

  get status(): { id: string; name: string; active: boolean; queueLength: number } {
    return {
      id: this.id,
      name: this.config.name,
      active: this.active,
      queueLength: this.taskQueue.length,
    };
  }
}

export class ArcanisAgents {
  private agents: Map<string, ArcanisAgent> = new Map();
  private brain: ArcanisBrain;

  constructor(brain: ArcanisBrain) {
    this.brain = brain;
  }

  createAgent(config: AgentConfig): ArcanisAgent {
    const agent = new ArcanisAgent(config, this.brain);
    this.agents.set(agent.id, agent);
    return agent;
  }

  getAgent(id: string): ArcanisAgent | undefined {
    return this.agents.get(id);
  }

  removeAgent(id: string): void {
    const agent = this.agents.get(id);
    if (agent) {
      agent.stop();
      this.agents.delete(id);
    }
  }

  listAgents(): ArcanisAgent[] {
    return Array.from(this.agents.values());
  }

  async broadcastTask(task: string): Promise<void> {
    for (const [, agent] of this.agents) {
      await agent.assignTask(task);
    }
  }
}

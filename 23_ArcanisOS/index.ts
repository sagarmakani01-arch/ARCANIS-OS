import { ArcanisKernel } from "./kernel";
import { ArcanisBrain, ArcanisAgents } from "./ai";
import { ArcanisUI } from "./interface";
import { ArcanisLang, ArcanisIDE, ArcanisBuild, ArcanisPackageManager } from "./development";
import { EventBus, ApiGateway } from "./integration";
import { SecurityManager } from "./security";

export class ArcanisOS {
  public readonly kernel: ArcanisKernel;
  public readonly brain: ArcanisBrain;
  public readonly agents: ArcanisAgents;
  public readonly ui: ArcanisUI;
  public readonly lang: ArcanisLang;
  public readonly ide: ArcanisIDE;
  public readonly build: ArcanisBuild;
  public readonly packageManager: ArcanisPackageManager;
  public readonly eventBus: EventBus;
  public readonly api: ApiGateway;
  public readonly security: SecurityManager;

  private initialized: boolean = false;

  constructor() {
    this.kernel = new ArcanisKernel();
    this.brain = new ArcanisBrain();
    this.agents = new ArcanisAgents(this.brain);
    this.ui = new ArcanisUI();
    this.lang = new ArcanisLang();
    this.ide = new ArcanisIDE();
    this.build = new ArcanisBuild();
    this.packageManager = new ArcanisPackageManager();
    this.eventBus = new EventBus();
    this.api = new ApiGateway();
    this.security = new SecurityManager();
  }

  async boot(): Promise<void> {
    if (this.initialized) return;
    await this.kernel.boot();
    this.registerAPIs();
    this.setupEventBus();
    this.initialized = true;
    this.eventBus.emit("system:boot", "arcanis-os", { time: Date.now() });
  }

  async shutdown(): Promise<void> {
    await this.kernel.shutdown();
    this.initialized = false;
  }

  async executeCommand(input: string): Promise<string> {
    const intent = await this.brain.understand(input);
    if (intent.confidence > 0.3) {
      const result = await this.ui.processCommand(input);
      return result.output || result.error || "Command executed.";
    }
    const thought = await this.brain.think(input);
    return `[AI] ${thought.content}`;
  }

  private registerAPIs(): void {
    this.api.register({
      method: "GET", path: "/system/status",
      handler: async () => ({ status: 200, data: this.kernel.getStats() }),
    });
    this.api.register({
      method: "GET", path: "/system/processes",
      handler: async () => ({ status: 200, data: this.kernel.listProcesses().map(p => p.info) }),
    });
    this.api.register({
      method: "POST", path: "/ai/think",
      handler: async (params) => {
        const thought = await this.brain.think(String(params.input || ""));
        return { status: 200, data: thought };
      },
    });
    this.api.register({
      method: "POST", path: "/ai/learn",
      handler: async (params) => {
        await this.brain.learn(String(params.input || ""), String(params.output || ""));
        return { status: 200, data: { learned: true } };
      },
    });
  }

  private setupEventBus(): void {
    this.eventBus.on("system:shutdown", () => { this.shutdown(); });
    this.eventBus.on("command:exec", (event) => {
      const data = event.data as { input: string };
      this.executeCommand(data.input);
    });
    this.ui.onEvent((event, data) => {
      this.eventBus.emit(event, "ui", data);
    });
  }

  get version(): string {
    return "1.0.0-alpha";
  }

  get status(): string {
    return this.initialized ? "running" : "stopped";
  }
}

export default ArcanisOS;

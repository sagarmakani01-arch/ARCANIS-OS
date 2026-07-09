import { Kernel } from "./index";

export interface KernelModule {
  name: string;
  version: string;
  init(kernel: Kernel): Promise<void>;
  shutdown(): Promise<void>;
}

export class ModuleManager {
  private modules: Map<string, KernelModule> = new Map();

  constructor(private kernel: Kernel) {}

  async register(module: KernelModule): Promise<void> {
    if (this.modules.has(module.name)) {
      throw new Error(`Module '${module.name}' is already registered`);
    }
    await module.init(this.kernel);
    this.modules.set(module.name, module);
  }

  async unregister(name: string): Promise<void> {
    const module = this.modules.get(name);
    if (!module) {
      throw new Error(`Module '${name}' not found`);
    }
    await module.shutdown();
    this.modules.delete(name);
  }

  get(name: string): KernelModule | undefined {
    return this.modules.get(name);
  }

  list(): KernelModule[] {
    return Array.from(this.modules.values());
  }

  async shutdownAll(): Promise<void> {
    for (const [, module] of this.modules) {
      await module.shutdown();
    }
    this.modules.clear();
  }
}

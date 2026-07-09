import { ArcanisKernelIntegration } from "./kernel";
import { ArcanisSecurityIntegration } from "./security";
import { ArcanisBrainIntegration } from "./brain";

export { ArcanisKernelIntegration } from "./kernel";
export { ArcanisSecurityIntegration } from "./security";
export { ArcanisBrainIntegration } from "./brain";

export class IntegrationManager {
  public readonly kernel: ArcanisKernelIntegration;
  public readonly security: ArcanisSecurityIntegration;
  public readonly brain: ArcanisBrainIntegration;

  constructor() {
    this.kernel = new ArcanisKernelIntegration();
    this.security = new ArcanisSecurityIntegration();
    this.brain = new ArcanisBrainIntegration();
  }

  initialize(): void {
    this.setupEventForwarding();
  }

  private setupEventForwarding(): void {
    this.kernel.on("packet:received", (packet) => {
      this.brain.learn("kernel:packets", packet);
    });
    this.security.on("security:event", (event) => {
      this.brain.processSecurityEvent(event);
    });
  }

  connectToKernel(kernel: unknown): void {
    this.kernel.setKernelReference(kernel);
  }

  connectToSecurity(security: unknown): void {
    this.security.setSecurityReference(security);
  }

  connectToBrain(brain: unknown): void {
    this.brain.setBrainReference(brain);
  }

  getStats(): {
    kernel: ReturnType<ArcanisKernelIntegration["getStats"]>;
    security: ReturnType<ArcanisSecurityIntegration["getStats"]>;
    brain: ReturnType<ArcanisBrainIntegration["getStats"]>;
  } {
    return {
      kernel: this.kernel.getStats(),
      security: this.security.getStats(),
      brain: this.brain.getStats(),
    };
  }
}

import { EventEmitter } from "events";
import { CoreNetworking } from "./core";
import { DataTransfer, StreamManager, PacketBuilder, NetworkBuffer, RingBuffer } from "./transfer";
import { NetworkSecurity, TlsManager, Firewall, NetworkEncryption } from "./security";
import { DeviceManager, MDNSDiscovery, UPnPDiscovery } from "./discovery";
import { LocalNetworkServices, DnsResolver, DhcpServer } from "./services";
import { CloudConnectivity, CloudConnector, DataSync } from "./cloud";
import { NetworkOptimizer, ConnectionMonitor, SecurityAnalyzer } from "./ai";
import { IntegrationManager, ArcanisKernelIntegration, ArcanisSecurityIntegration, ArcanisBrainIntegration } from "./integration";
import { NetworkMetricsCollector, NetworkLogger, PacketTracer } from "./monitoring";
import {
  NetworkConfig,
  DEFAULT_NETWORK_CONFIG,
  NetworkStats,
  NetworkEvent,
  SecurityEvent,
  NetworkPacket,
  ConnectionInfo,
  Protocol,
  NetworkAddress,
} from "./types";

export class ArcanisNetwork extends EventEmitter {
  public readonly core: CoreNetworking;
  public readonly transfer: DataTransfer;
  public readonly streams: StreamManager;
  public readonly security: NetworkSecurity;
  public readonly discovery: DeviceManager;
  public readonly services: LocalNetworkServices;
  public readonly cloud: CloudConnectivity;
  public readonly optimizer: NetworkOptimizer;
  public readonly connectionMonitor: ConnectionMonitor;
  public readonly securityAnalyzer: SecurityAnalyzer;
  public readonly integration: IntegrationManager;
  public readonly metrics: NetworkMetricsCollector;
  public readonly logger: NetworkLogger;
  public readonly tracer: PacketTracer;
  private config: NetworkConfig;
  private initialized: boolean = false;

  constructor(config: Partial<NetworkConfig> = {}) {
    super();
    this.config = { ...DEFAULT_NETWORK_CONFIG, ...config };
    this.core = new CoreNetworking(this.config);
    this.transfer = new DataTransfer();
    this.streams = new StreamManager();
    this.security = new NetworkSecurity();
    this.discovery = new DeviceManager();
    this.services = new LocalNetworkServices();
    this.cloud = new CloudConnectivity();
    this.optimizer = new NetworkOptimizer();
    this.connectionMonitor = new ConnectionMonitor();
    this.securityAnalyzer = new SecurityAnalyzer();
    this.integration = new IntegrationManager();
    this.metrics = new NetworkMetricsCollector();
    this.logger = new NetworkLogger();
    this.tracer = new PacketTracer();
    this.setupEventForwarding();
  }

  private setupEventForwarding(): void {
    this.core.stack.on("packet:received", (event: NetworkEvent) => {
      this.logger.info("network", "Packet received", event.data);
      this.integration.brain.processNetworkEvent(event);
    });
    this.core.stack.on("packet:sent", (event: NetworkEvent) => {
      this.logger.debug("network", "Packet sent", event.data);
    });
    this.security.on("security:event", (event: SecurityEvent) => {
      this.securityAnalyzer.analyzeEvent(event);
      this.integration.brain.processSecurityEvent(event);
    });
    this.core.connectionManager.on("connection:established", (info: ConnectionInfo) => {
      this.connectionMonitor.trackConnection(info);
      this.logger.info("connection", "Connection established", { id: info.id });
    });
    this.core.connectionManager.on("connection:error", (data: { connection: ConnectionInfo; error: Error }) => {
      this.logger.error("connection", "Connection error", { id: data.connection.id, error: data.error.message });
    });
  }

  async initialize(): Promise<void> {
    if (this.initialized) return;
    this.logger.info("system", "Initializing ArcanisNetwork");
    await this.core.initialize();
    this.services.initialize();
    this.cloud.initialize();
    this.integration.initialize();
    this.metrics.startCollection(5000);
    this.initialized = true;
    this.emit("network:initialized");
    this.logger.info("system", "ArcanisNetwork initialized successfully");
  }

  async shutdown(): Promise<void> {
    if (!this.initialized) return;
    this.logger.info("system", "Shutting down ArcanisNetwork");
    this.metrics.stopCollection();
    await this.core.shutdown();
    this.initialized = false;
    this.emit("network:shutdown");
    this.logger.info("system", "ArcanisNetwork shut down successfully");
  }

  async connect(remoteAddress: NetworkAddress, protocol: Protocol = Protocol.TCP): Promise<ConnectionInfo | null> {
    if (!this.initialized) return null;
    const localAddress: NetworkAddress = { ip: "0.0.0.0", port: Math.floor(Math.random() * 65535) };
    const connection = this.core.connectionManager.createConnection(localAddress, remoteAddress, protocol);
    await connection.connect();
    this.logger.info("connection", "Connecting to remote", { remote: remoteAddress });
    return connection.info;
  }

  async disconnect(connectionId: string): Promise<void> {
    const connection = this.core.connectionManager.getConnection(connectionId);
    if (connection) {
      await connection.disconnect();
      this.logger.info("connection", "Disconnected", { id: connectionId });
    }
  }

  async sendData(connectionId: string, data: Buffer): Promise<boolean> {
    const connection = this.core.connectionManager.getConnection(connectionId);
    if (!connection) return false;
    return connection.send(data);
  }

  getNetworkStats(): {
    core: ReturnType<CoreNetworking["getStats"]>;
    transfer: ReturnType<DataTransfer["getStats"]>;
    streams: ReturnType<StreamManager["getStats"]>;
    security: ReturnType<NetworkSecurity["getStats"]>;
    discovery: ReturnType<DeviceManager["getStats"]>;
    services: ReturnType<LocalNetworkServices["getStats"]>;
    cloud: ReturnType<CloudConnectivity["getStats"]>;
    optimizer: ReturnType<NetworkOptimizer["getStats"]>;
    metrics: ReturnType<NetworkMetricsCollector["getStats"]>;
    logger: ReturnType<NetworkLogger["getStats"]>;
    tracer: ReturnType<PacketTracer["getStats"]>;
  } {
    return {
      core: this.core.getStats(),
      transfer: this.transfer.getStats(),
      streams: this.streams.getStats(),
      security: this.security.getStats(),
      discovery: this.discovery.getStats(),
      services: this.services.getStats(),
      cloud: this.cloud.getStats(),
      optimizer: this.optimizer.getStats(),
      metrics: this.metrics.getStats(),
      logger: this.logger.getStats(),
      tracer: this.tracer.getStats(),
    };
  }

  getConfig(): NetworkConfig {
    return { ...this.config };
  }

  isInitialized(): boolean {
    return this.initialized;
  }
}

export { CoreNetworking } from "./core";
export { DataTransfer, StreamManager, PacketBuilder, NetworkBuffer, RingBuffer } from "./transfer";
export { NetworkSecurity, TlsManager, Firewall, NetworkEncryption } from "./security";
export { DeviceManager, MDNSDiscovery, UPnPDiscovery } from "./discovery";
export { LocalNetworkServices, DnsResolver, DhcpServer } from "./services";
export { CloudConnectivity, CloudConnector, DataSync } from "./cloud";
export { NetworkOptimizer, ConnectionMonitor, SecurityAnalyzer } from "./ai";
export { IntegrationManager, ArcanisKernelIntegration, ArcanisSecurityIntegration, ArcanisBrainIntegration } from "./integration";
export { NetworkMetricsCollector, NetworkLogger, PacketTracer } from "./monitoring";
export * from "./types";

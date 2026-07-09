import { NetworkStack } from "./stack";
import { ConnectionManager } from "./connection";
import { TcpServer, TcpSocket } from "./tcp";
import { UdpServer, UdpSocket, BroadcastManager } from "./udp";
import { IpLayer } from "./ip";
import {
  NetworkConfig,
  DEFAULT_NETWORK_CONFIG,
  Protocol,
  NetworkAddress,
} from "../types";

export class CoreNetworking {
  public readonly stack: NetworkStack;
  public readonly connectionManager: ConnectionManager;
  public readonly ipLayer: IpLayer;
  public readonly udpServer: UdpServer;
  public readonly broadcastManager: BroadcastManager;
  private tcpServers: Map<number, TcpServer> = new Map();
  private config: NetworkConfig;

  constructor(config: Partial<NetworkConfig> = {}) {
    this.config = { ...DEFAULT_NETWORK_CONFIG, ...config };
    this.stack = new NetworkStack(this.config);
    this.connectionManager = new ConnectionManager(this.config);
    this.ipLayer = new IpLayer(this.stack);
    this.udpServer = new UdpServer(this.config);
    this.broadcastManager = new BroadcastManager();
  }

  async initialize(): Promise<void> {
    await this.stack.initialize();
    await this.broadcastManager.startListening();
  }

  async shutdown(): Promise<void> {
    for (const server of this.tcpServers.values()) {
      await server.stop();
    }
    this.tcpServers.clear();
    await this.udpServer.closeAll();
    await this.broadcastManager.stop();
    await this.connectionManager.closeAll();
    await this.stack.shutdown();
  }

  createTcpServer(port: number): TcpServer {
    if (this.tcpServers.has(port)) {
      throw new Error(`TCP server already exists on port ${port}`);
    }
    const server = new TcpServer(port, this.config);
    this.tcpServers.set(port, server);
    return server;
  }

  getTcpServer(port: number): TcpServer | undefined {
    return this.tcpServers.get(port);
  }

  removeTcpServer(port: number): boolean {
    const server = this.tcpServers.get(port);
    if (!server) return false;
    server.stop();
    this.tcpServers.delete(port);
    return true;
  }

  async createTcpConnection(
    remoteAddress: NetworkAddress,
    localPort?: number
  ): Promise<TcpSocket> {
    const socket = new TcpSocket(this.config);
    await socket.connect(remoteAddress);
    return socket;
  }

  async createUdpSocket(port?: number): Promise<UdpSocket> {
    const socket = this.udpServer.createSocket();
    if (port) {
      await socket.bind(port);
    }
    return socket;
  }

  getStats(): {
    stack: ReturnType<NetworkStack["getStats"]>;
    connections: ReturnType<ConnectionManager["getStats"]>;
    tcpServers: number;
    udp: ReturnType<UdpServer["getStats"]>;
  } {
    return {
      stack: this.stack.getStats(),
      connections: this.connectionManager.getStats(),
      tcpServers: this.tcpServers.size,
      udp: this.udpServer.getStats(),
    };
  }
}

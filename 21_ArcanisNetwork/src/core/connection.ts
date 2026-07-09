import { EventEmitter } from "events";
import {
  ConnectionInfo,
  ConnectionState,
  Protocol,
  NetworkAddress,
  NetworkPacket,
  NetworkConfig,
  DEFAULT_NETWORK_CONFIG,
  PacketFlags,
} from "../types";
import { v4 as uuidv4 } from "uuid";

export class Connection extends EventEmitter {
  public readonly id: string;
  public info: ConnectionInfo;
  private config: NetworkConfig;
  private keepAliveTimer: NodeJS.Timeout | null = null;
  private timeoutTimer: NodeJS.Timeout | null = null;

  constructor(
    localAddress: NetworkAddress,
    remoteAddress: NetworkAddress,
    protocol: Protocol,
    config: Partial<NetworkConfig> = {}
  ) {
    super();
    this.id = uuidv4();
    this.config = { ...DEFAULT_NETWORK_CONFIG, ...config };
    this.info = {
      id: this.id,
      localAddress,
      remoteAddress,
      protocol,
      state: ConnectionState.Created,
      createdAt: Date.now(),
      lastActivity: Date.now(),
      bytesSent: 0,
      bytesReceived: 0,
      latency: 0,
      isActive: false,
    };
  }

  async connect(): Promise<boolean> {
    if (this.info.state !== ConnectionState.Created) return false;
    this.info.state = ConnectionState.Connecting;
    this.emit("connecting", this.info);
    this.startTimeout();
    return true;
  }

  onConnected(): void {
    this.info.state = ConnectionState.Connected;
    this.info.isActive = true;
    this.clearTimeout();
    this.startKeepAlive();
    this.emit("connected", this.info);
  }

  async disconnect(): Promise<void> {
    if (this.info.state === ConnectionState.Disconnected) return;
    this.stopKeepAlive();
    this.clearTimeout();
    this.info.state = ConnectionState.Disconnected;
    this.info.isActive = false;
    this.emit("disconnected", this.info);
  }

  onError(error: Error): void {
    this.info.state = ConnectionState.Error;
    this.info.isActive = false;
    this.clearTimeout();
    this.stopKeepAlive();
    this.emit("error", error);
  }

  send(data: Buffer): boolean {
    if (this.info.state !== ConnectionState.Connected) return false;
    this.info.bytesSent += data.length;
    this.info.lastActivity = Date.now();
    this.emit("data:out", data);
    return true;
  }

  receive(data: Buffer): void {
    if (this.info.state !== ConnectionState.Connected) return;
    this.info.bytesReceived += data.length;
    this.info.lastActivity = Date.now();
    this.emit("data:in", data);
  }

  updateLatency(latency: number): void {
    this.info.latency = latency;
  }

  isActive(): boolean {
    return this.info.isActive && this.info.state === ConnectionState.Connected;
  }

  getDuration(): number {
    return Date.now() - this.info.createdAt;
  }

  private startKeepAlive(): void {
    this.stopKeepAlive();
    this.keepAliveTimer = setInterval(() => {
      if (this.isActive()) {
        this.emit("keepalive", this.info);
      }
    }, this.config.keepAliveInterval);
  }

  private stopKeepAlive(): void {
    if (this.keepAliveTimer) {
      clearInterval(this.keepAliveTimer);
      this.keepAliveTimer = null;
    }
  }

  private startTimeout(): void {
    this.clearTimeout();
    this.timeoutTimer = setTimeout(() => {
      if (this.info.state === ConnectionState.Connecting) {
        this.onError(new Error("Connection timeout"));
      }
    }, this.config.connectionTimeout);
  }

  private clearTimeout(): void {
    if (this.timeoutTimer) {
      clearTimeout(this.timeoutTimer);
      this.timeoutTimer = null;
    }
  }
}

export class ConnectionManager extends EventEmitter {
  private connections: Map<string, Connection> = new Map();
  private config: NetworkConfig;

  constructor(config: Partial<NetworkConfig> = {}) {
    super();
    this.config = { ...DEFAULT_NETWORK_CONFIG, ...config };
  }

  createConnection(
    localAddress: NetworkAddress,
    remoteAddress: NetworkAddress,
    protocol: Protocol
  ): Connection {
    const connection = new Connection(localAddress, remoteAddress, protocol, this.config);
    this.connections.set(connection.id, connection);
    connection.on("connected", () => this.emit("connection:established", connection.info));
    connection.on("disconnected", () => {
      this.emit("connection:closed", connection.info);
    });
    connection.on("error", (error) => this.emit("connection:error", { connection: connection.info, error }));
    this.emit("connection:created", connection.info);
    return connection;
  }

  getConnection(id: string): Connection | undefined {
    return this.connections.get(id);
  }

  removeConnection(id: string): boolean {
    const connection = this.connections.get(id);
    if (!connection) return false;
    connection.disconnect();
    this.connections.delete(id);
    return true;
  }

  getConnectionsByState(state: ConnectionState): Connection[] {
    return Array.from(this.connections.values()).filter((c) => c.info.state === state);
  }

  getActiveConnections(): Connection[] {
    return this.getConnectionsByState(ConnectionState.Connected);
  }

  listConnections(): ConnectionInfo[] {
    return Array.from(this.connections.values()).map((c) => ({ ...c.info }));
  }

  getStats(): {
    total: number;
    active: number;
    connecting: number;
    disconnected: number;
    errors: number;
  } {
    const all = Array.from(this.connections.values());
    return {
      total: all.length,
      active: all.filter((c) => c.info.state === ConnectionState.Connected).length,
      connecting: all.filter((c) => c.info.state === ConnectionState.Connecting).length,
      disconnected: all.filter((c) => c.info.state === ConnectionState.Disconnected).length,
      errors: all.filter((c) => c.info.state === ConnectionState.Error).length,
    };
  }

  async closeAll(): Promise<void> {
    for (const connection of this.connections.values()) {
      await connection.disconnect();
    }
    this.connections.clear();
  }
}

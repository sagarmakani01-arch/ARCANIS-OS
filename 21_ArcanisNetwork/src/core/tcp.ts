import { EventEmitter } from "events";
import {
  Connection,
  ConnectionManager,
} from "./connection";
import {
  NetworkAddress,
  Protocol,
  ConnectionState,
  NetworkConfig,
  PacketFlags,
  DEFAULT_NETWORK_CONFIG,
} from "../types";
import { PacketBuilder } from "../transfer/packet";
import { v4 as uuidv4 } from "uuid";

export enum TcpState {
  Closed = "closed",
  Listen = "listen",
  SynSent = "syn_sent",
  SynReceived = "syn_received",
  Established = "established",
  CloseWait = "close_wait",
  Closing = "closing",
  LastAck = "last_ack",
  TimeWait = "time_wait",
}

export interface TcpSegment {
  sequence: number;
  acknowledgment: number;
  flags: PacketFlags;
  window: number;
  data: Buffer;
}

export class TcpSocket extends EventEmitter {
  public readonly id: string;
  public state: TcpState = TcpState.Closed;
  private connection: Connection | null = null;
  private sequenceNumber: number = 0;
  private acknowledgmentNumber: number = 0;
  private windowSize: number = 65535;
  private sendBuffer: Buffer[] = [];
  private receiveBuffer: Buffer[] = [];
  private config: NetworkConfig;

  constructor(config: Partial<NetworkConfig> = {}) {
    super();
    this.id = uuidv4();
    this.config = { ...DEFAULT_NETWORK_CONFIG, ...config };
  }

  async connect(remoteAddress: NetworkAddress): Promise<boolean> {
    if (this.state !== TcpState.Closed) return false;
    const localAddress: NetworkAddress = {
      ip: "0.0.0.0",
      port: Math.floor(Math.random() * 65535),
    };
    this.connection = new Connection(localAddress, remoteAddress, Protocol.TCP, this.config);
    this.connection.on("data:in", (data: Buffer) => this.handleIncomingData(data));
    this.state = TcpState.SynSent;
    this.sequenceNumber = Math.floor(Math.random() * 4294967296);
    const synPacket = PacketBuilder.createTcpSyn(localAddress, remoteAddress, this.sequenceNumber);
    await this.connection.connect();
    this.emit("connecting", { local: localAddress, remote: remoteAddress });
    return true;
  }

  async listen(port: number): Promise<void> {
    this.state = TcpState.Listen;
    this.emit("listening", { port });
  }

  async accept(): Promise<TcpSocket | null> {
    if (this.state !== TcpState.Listen) return null;
    return new TcpSocket(this.config);
  }

  async send(data: Buffer): Promise<boolean> {
    if (this.state !== TcpState.Established || !this.connection) return false;
    this.sendBuffer.push(data);
    this.acknowledgmentNumber += data.length;
    const packet = PacketBuilder.createTcpAck(
      this.connection.info.localAddress,
      this.connection.info.remoteAddress,
      this.sequenceNumber,
      this.acknowledgmentNumber
    );
    return this.connection.send(packet.data);
  }

  async receive(): Promise<Buffer | null> {
    if (this.receiveBuffer.length === 0) return null;
    return this.receiveBuffer.shift() || null;
  }

  async close(): Promise<void> {
    if (this.state === TcpState.Established) {
      this.state = TcpState.Closing;
      if (this.connection) {
        const finPacket = PacketBuilder.createTcpFin(
          this.connection.info.localAddress,
          this.connection.info.remoteAddress,
          this.sequenceNumber,
          this.acknowledgmentNumber
        );
        await this.connection.send(finPacket.data);
      }
    }
    if (this.connection) {
      await this.connection.disconnect();
    }
    this.state = TcpState.Closed;
    this.emit("closed");
  }

  private handleIncomingData(data: Buffer): void {
    if (this.state === TcpState.SynSent) {
      this.state = TcpState.Established;
      this.emit("connected");
    } else if (this.state === TcpState.Established) {
      this.receiveBuffer.push(data);
      this.emit("data", data);
    }
  }

  getStats(): {
    state: TcpState;
    bytesSent: number;
    bytesReceived: number;
    latency: number;
  } {
    return {
      state: this.state,
      bytesSent: this.connection?.info.bytesSent || 0,
      bytesReceived: this.connection?.info.bytesReceived || 0,
      latency: this.connection?.info.latency || 0,
    };
  }
}

export class TcpServer extends EventEmitter {
  private sockets: Map<string, TcpSocket> = new Map();
  private port: number;
  private config: NetworkConfig;
  private listening: boolean = false;

  constructor(port: number, config: Partial<NetworkConfig> = {}) {
    super();
    this.port = port;
    this.config = { ...DEFAULT_NETWORK_CONFIG, ...config };
  }

  async start(): Promise<void> {
    this.listening = true;
    this.emit("listening", { port: this.port });
  }

  async stop(): Promise<void> {
    this.listening = false;
    for (const socket of this.sockets.values()) {
      await socket.close();
    }
    this.sockets.clear();
    this.emit("closed");
  }

  handleConnection(socket: TcpSocket): void {
    this.sockets.set(socket.id, socket);
    socket.on("data", (data: Buffer) => {
      this.emit("data", { socket: socket.id, data });
    });
    socket.on("closed", () => {
      this.sockets.delete(socket.id);
    });
    this.emit("connection", socket);
  }

  getSockets(): TcpSocket[] {
    return Array.from(this.sockets.values());
  }

  getStats(): {
    listening: boolean;
    port: number;
    connections: number;
  } {
    return {
      listening: this.listening,
      port: this.port,
      connections: this.sockets.size,
    };
  }
}

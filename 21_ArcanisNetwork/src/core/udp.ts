import { EventEmitter } from "events";
import {
  NetworkAddress,
  Protocol,
  NetworkConfig,
  DEFAULT_NETWORK_CONFIG,
} from "../types";
import { PacketBuilder } from "../transfer/packet";
import { v4 as uuidv4 } from "uuid";

export interface UdpMessage {
  id: string;
  source: NetworkAddress;
  destination: NetworkAddress;
  data: Buffer;
  timestamp: number;
}

export class UdpSocket extends EventEmitter {
  public readonly id: string;
  private bound: boolean = false;
  private localAddress: NetworkAddress | null = null;
  private config: NetworkConfig;

  constructor(config: Partial<NetworkConfig> = {}) {
    super();
    this.id = uuidv4();
    this.config = { ...DEFAULT_NETWORK_CONFIG, ...config };
  }

  async bind(port: number, address: string = "0.0.0.0"): Promise<void> {
    this.localAddress = { ip: address, port };
    this.bound = true;
    this.emit("bound", { address, port });
  }

  async send(data: Buffer, destination: NetworkAddress): Promise<boolean> {
    if (!this.bound || !this.localAddress) return false;
    const packet = PacketBuilder.createUdpPacket(this.localAddress, destination, data);
    this.emit("sent", { destination, size: data.length });
    return true;
  }

  async receive(): Promise<UdpMessage | null> {
    return new Promise((resolve) => {
      const handler = (message: UdpMessage) => {
        this.removeListener("message", handler);
        resolve(message);
      };
      this.on("message", handler);
      setTimeout(() => {
        this.removeListener("message", handler);
        resolve(null);
      }, this.config.connectionTimeout);
    });
  }

  handleMessage(source: NetworkAddress, data: Buffer): void {
    const message: UdpMessage = {
      id: uuidv4(),
      source,
      destination: this.localAddress!,
      data,
      timestamp: Date.now(),
    };
    this.emit("message", message);
  }

  async close(): Promise<void> {
    this.bound = false;
    this.localAddress = null;
    this.emit("closed");
  }

  isBound(): boolean {
    return this.bound;
  }

  getLocalAddress(): NetworkAddress | null {
    return this.localAddress;
  }
}

export class UdpServer extends EventEmitter {
  private sockets: Map<string, UdpSocket> = new Map();
  private config: NetworkConfig;

  constructor(config: Partial<NetworkConfig> = {}) {
    super();
    this.config = { ...DEFAULT_NETWORK_CONFIG, ...config };
  }

  createSocket(): UdpSocket {
    const socket = new UdpSocket(this.config);
    this.sockets.set(socket.id, socket);
    socket.on("message", (message: UdpMessage) => {
      this.emit("message", message);
    });
    socket.on("closed", () => {
      this.sockets.delete(socket.id);
    });
    return socket;
  }

  removeSocket(id: string): boolean {
    const socket = this.sockets.get(id);
    if (!socket) return false;
    socket.close();
    this.sockets.delete(id);
    return true;
  }

  async closeAll(): Promise<void> {
    for (const socket of this.sockets.values()) {
      await socket.close();
    }
    this.sockets.clear();
  }

  getStats(): {
    sockets: number;
    bound: number;
  } {
    const all = Array.from(this.sockets.values());
    return {
      sockets: all.length,
      bound: all.filter((s) => s.isBound()).length,
    };
  }
}

export class BroadcastManager extends EventEmitter {
  private port: number;
  private sockets: UdpSocket[] = [];

  constructor(port: number = 9999) {
    super();
    this.port = port;
  }

  async startListening(): Promise<void> {
    const socket = new UdpSocket();
    await socket.bind(this.port);
    socket.on("message", (message: UdpMessage) => {
      this.emit("broadcast", message);
    });
    this.sockets.push(socket);
  }

  async broadcast(data: Buffer, address: string = "255.255.255.255"): Promise<void> {
    for (const socket of this.sockets) {
      if (socket.isBound()) {
        await socket.send(data, { ip: address, port: this.port });
      }
    }
  }

  async stop(): Promise<void> {
    for (const socket of this.sockets) {
      await socket.close();
    }
    this.sockets = [];
  }
}

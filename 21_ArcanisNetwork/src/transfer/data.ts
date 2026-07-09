import { NetworkStream, StreamManager, StreamChunk } from "./stream";
import { PacketBuilder } from "./packet";
import { NetworkBuffer, RingBuffer } from "./buffer";
import {
  NetworkPacket,
  NetworkAddress,
  Protocol,
  NetworkConfig,
  DEFAULT_NETWORK_CONFIG,
} from "../types";
import { EventEmitter } from "events";
import { v4 as uuidv4 } from "uuid";

export interface DataTransferOptions {
  chunkSize: number;
  maxRetries: number;
  timeout: number;
  enableCompression: boolean;
  enableChecksum: boolean;
}

export const DEFAULT_TRANSFER_OPTIONS: DataTransferOptions = {
  chunkSize: 8192,
  maxRetries: 3,
  timeout: 30000,
  enableCompression: false,
  enableChecksum: true,
};

export class DataTransfer extends EventEmitter {
  private streamManager: StreamManager;
  private options: DataTransferOptions;
  private transfers: Map<string, TransferSession> = new Map();

  constructor(options: Partial<DataTransferOptions> = {}) {
    super();
    this.streamManager = new StreamManager();
    this.options = { ...DEFAULT_TRANSFER_OPTIONS, ...options };
  }

  async sendFile(
    source: NetworkAddress,
    destination: NetworkAddress,
    fileName: string,
    data: Buffer
  ): Promise<string> {
    const transferId = uuidv4();
    const session = new TransferSession(transferId, source, destination, this.options);
    this.transfers.set(transferId, session);
    const chunks = this.chunkData(data);
    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      const streamChunk = session.createChunk(chunk, i === chunks.length - 1);
      this.emit("chunk:sent", { transferId, chunk: streamChunk });
    }
    session.complete();
    this.emit("transfer:complete", { transferId, fileName, size: data.length });
    return transferId;
  }

  async receiveFile(transferId: string): Promise<Buffer | null> {
    const session = this.transfers.get(transferId);
    if (!session) return null;
    return session.getData();
  }

  private chunkData(data: Buffer): Buffer[] {
    const chunks: Buffer[] = [];
    for (let i = 0; i < data.length; i += this.options.chunkSize) {
      chunks.push(data.slice(i, Math.min(i + this.options.chunkSize, data.length)));
    }
    return chunks;
  }

  getTransfer(id: string): TransferSession | undefined {
    return this.transfers.get(id);
  }

  getStats(): {
    activeTransfers: number;
    totalTransfers: number;
    totalBytesTransferred: number;
  } {
    const sessions = Array.from(this.transfers.values());
    return {
      activeTransfers: sessions.filter((s) => !s.isComplete()).length,
      totalTransfers: sessions.length,
      totalBytesTransferred: sessions.reduce((sum, s) => sum + s.getSize(), 0),
    };
  }
}

export class TransferSession {
  public readonly id: string;
  public readonly source: NetworkAddress;
  public readonly destination: NetworkAddress;
  private stream: NetworkStream;
  private options: DataTransferOptions;
  private chunks: StreamChunk[] = [];
  private completed: boolean = false;
  private startedAt: number;
  private completedAt: number = 0;

  constructor(
    id: string,
    source: NetworkAddress,
    destination: NetworkAddress,
    options: DataTransferOptions
  ) {
    this.id = id;
    this.source = source;
    this.destination = destination;
    this.options = options;
    this.stream = new NetworkStream();
    this.startedAt = Date.now();
  }

  createChunk(data: Buffer, isLast: boolean): StreamChunk {
    const chunk = this.stream.createChunk(data, isLast);
    this.chunks.push(chunk);
    return chunk;
  }

  processChunk(chunk: StreamChunk): void {
    this.stream.processChunk(chunk);
  }

  complete(): void {
    this.completed = true;
    this.completedAt = Date.now();
  }

  isComplete(): boolean {
    return this.completed;
  }

  getData(): Buffer {
    return this.stream.read(this.stream.getAvailableData());
  }

  getSize(): number {
    return this.chunks.reduce((sum, c) => sum + c.data.length, 0);
  }

  getDuration(): number {
    return (this.completedAt || Date.now()) - this.startedAt;
  }

  getStats(): {
    id: string;
    chunks: number;
    size: number;
    duration: number;
    complete: boolean;
  } {
    return {
      id: this.id,
      chunks: this.chunks.length,
      size: this.getSize(),
      duration: this.getDuration(),
      complete: this.completed,
    };
  }
}

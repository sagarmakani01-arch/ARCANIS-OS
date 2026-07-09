import { NetworkBuffer, RingBuffer } from "./buffer";
import { PacketBuilder } from "./packet";
import {
  NetworkPacket,
  NetworkAddress,
  Protocol,
  NetworkConfig,
  DEFAULT_NETWORK_CONFIG,
} from "../types";
import { v4 as uuidv4 } from "uuid";

export interface StreamChunk {
  id: string;
  sequence: number;
  data: Buffer;
  timestamp: number;
  isLast: boolean;
}

export class NetworkStream {
  public readonly id: string;
  private sendBuffer: NetworkBuffer;
  private receiveBuffer: NetworkBuffer;
  private chunkBuffer: RingBuffer<StreamChunk>;
  private sequenceNumber: number = 0;
  private config: NetworkConfig;

  constructor(config: Partial<NetworkConfig> = {}) {
    this.id = uuidv4();
    this.config = { ...DEFAULT_NETWORK_CONFIG, ...config };
    this.sendBuffer = new NetworkBuffer(this.config.bufferSize);
    this.receiveBuffer = new NetworkBuffer(this.config.bufferSize * 4);
    this.chunkBuffer = new RingBuffer<StreamChunk>(1024);
  }

  write(data: Buffer): boolean {
    const written = this.sendBuffer.write(data);
    if (written < data.length) {
      this.sendBuffer.grow(this.sendBuffer["capacity"] * 2);
      return this.sendBuffer.write(data) === data.length;
    }
    return true;
  }

  read(length: number): Buffer {
    return this.receiveBuffer.read(length);
  }

  peek(length: number): Buffer {
    return this.receiveBuffer.peek(length);
  }

  createChunk(data: Buffer, isLast: boolean = false): StreamChunk {
    const chunk: StreamChunk = {
      id: uuidv4(),
      sequence: this.sequenceNumber++,
      data,
      timestamp: Date.now(),
      isLast,
    };
    this.chunkBuffer.push(chunk);
    return chunk;
  }

  processChunk(chunk: StreamChunk): void {
    this.receiveBuffer.write(chunk.data);
  }

  getAvailableData(): number {
    return this.receiveBuffer.length;
  }

  clear(): void {
    this.sendBuffer.clear();
    this.receiveBuffer.clear();
    this.chunkBuffer.clear();
  }

  getStats(): {
    sendBufferSize: number;
    receiveBufferSize: number;
    pendingChunks: number;
    sequenceNumber: number;
  } {
    return {
      sendBufferSize: this.sendBuffer.length,
      receiveBufferSize: this.receiveBuffer.length,
      pendingChunks: this.chunkBuffer.size,
      sequenceNumber: this.sequenceNumber,
    };
  }
}

export class StreamManager {
  private streams: Map<string, NetworkStream> = new Map();

  createStream(): NetworkStream {
    const stream = new NetworkStream();
    this.streams.set(stream.id, stream);
    return stream;
  }

  getStream(id: string): NetworkStream | undefined {
    return this.streams.get(id);
  }

  removeStream(id: string): boolean {
    const stream = this.streams.get(id);
    if (!stream) return false;
    stream.clear();
    this.streams.delete(id);
    return true;
  }

  listStreams(): NetworkStream[] {
    return Array.from(this.streams.values());
  }

  getStats(): {
    totalStreams: number;
    totalBufferData: number;
  } {
    const streams = this.listStreams();
    return {
      totalStreams: streams.length,
      totalBufferData: streams.reduce(
        (sum, s) => sum + s.getStats().receiveBufferSize,
        0
      ),
    };
  }
}

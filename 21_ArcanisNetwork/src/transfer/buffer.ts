export class NetworkBuffer {
  private buffer: Buffer;
  private readOffset: number = 0;
  private writeOffset: number = 0;
  private capacity: number;

  constructor(capacity: number) {
    this.capacity = capacity;
    this.buffer = Buffer.alloc(capacity);
  }

  get availableRead(): number {
    return this.writeOffset - this.readOffset;
  }

  get availableWrite(): number {
    return this.capacity - this.writeOffset;
  }

  get length(): number {
    return this.availableRead;
  }

  write(data: Buffer): number {
    const bytesToWrite = Math.min(data.length, this.availableWrite);
    if (bytesToWrite === 0) return 0;
    data.copy(this.buffer, this.writeOffset, 0, bytesToWrite);
    this.writeOffset += bytesToWrite;
    return bytesToWrite;
  }

  read(length: number): Buffer {
    const bytesToRead = Math.min(length, this.availableRead);
    if (bytesToRead === 0) return Buffer.alloc(0);
    const result = this.buffer.slice(this.readOffset, this.readOffset + bytesToRead);
    this.readOffset += bytesToRead;
    this.compact();
    return result;
  }

  peek(length: number): Buffer {
    const bytesToRead = Math.min(length, this.availableRead);
    if (bytesToRead === 0) return Buffer.alloc(0);
    return this.buffer.slice(this.readOffset, this.readOffset + bytesToRead);
  }

  skip(bytes: number): number {
    const bytesToSkip = Math.min(bytes, this.availableRead);
    this.readOffset += bytesToSkip;
    this.compact();
    return bytesToSkip;
  }

  clear(): void {
    this.readOffset = 0;
    this.writeOffset = 0;
    this.buffer.fill(0);
  }

  private compact(): void {
    if (this.readOffset === 0) return;
    const remaining = this.availableRead;
    if (remaining > 0) {
      this.buffer.copy(this.buffer, 0, this.readOffset, this.writeOffset);
    }
    this.readOffset = 0;
    this.writeOffset = remaining;
  }

  grow(newCapacity: number): void {
    if (newCapacity <= this.capacity) return;
    const newBuffer = Buffer.alloc(newCapacity);
    this.buffer.copy(newBuffer, 0, 0, this.writeOffset);
    this.buffer = newBuffer;
    this.capacity = newCapacity;
  }

  getBuffer(): Buffer {
    return this.buffer.slice(this.readOffset, this.writeOffset);
  }
}

export class RingBuffer<T> {
  private buffer: (T | undefined)[];
  private head: number = 0;
  private tail: number = 0;
  private count: number = 0;
  private capacity: number;

  constructor(capacity: number) {
    this.capacity = capacity;
    this.buffer = new Array(capacity);
  }

  get size(): number {
    return this.count;
  }

  get isFull(): boolean {
    return this.count === this.capacity;
  }

  get isEmpty(): boolean {
    return this.count === 0;
  }

  push(item: T): boolean {
    if (this.isFull) return false;
    this.buffer[this.tail] = item;
    this.tail = (this.tail + 1) % this.capacity;
    this.count++;
    return true;
  }

  pop(): T | undefined {
    if (this.isEmpty) return undefined;
    const item = this.buffer[this.head];
    this.buffer[this.head] = undefined;
    this.head = (this.head + 1) % this.capacity;
    this.count--;
    return item;
  }

  peek(): T | undefined {
    if (this.isEmpty) return undefined;
    return this.buffer[this.head];
  }

  clear(): void {
    this.buffer = new Array(this.capacity);
    this.head = 0;
    this.tail = 0;
    this.count = 0;
  }

  toArray(): T[] {
    const result: T[] = [];
    let current = this.head;
    for (let i = 0; i < this.count; i++) {
      result.push(this.buffer[current]!);
      current = (current + 1) % this.capacity;
    }
    return result;
  }
}

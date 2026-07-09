type EventHandler = (event: BusEvent) => void;

export interface BusEvent {
  type: string;
  source: string;
  data: unknown;
  timestamp: number;
  id: string;
}

export class EventBus {
  private handlers: Map<string, Set<EventHandler>> = new Map();
  private history: BusEvent[] = [];
  private maxHistory: number;

  constructor(maxHistory: number = 1000) {
    this.maxHistory = maxHistory;
  }

  emit(type: string, source: string, data: unknown): void {
    const event: BusEvent = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      type,
      source,
      data,
      timestamp: Date.now(),
    };
    this.history.push(event);
    if (this.history.length > this.maxHistory) {
      this.history.shift();
    }
    const handlers = this.handlers.get(type);
    if (handlers) {
      for (const handler of handlers) {
        try {
          handler(event);
        } catch {
        }
      }
    }
  }

  on(type: string, handler: EventHandler): void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);
  }

  off(type: string, handler: EventHandler): void {
    const handlers = this.handlers.get(type);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.handlers.delete(type);
      }
    }
  }

  once(type: string, handler: EventHandler): void {
    const wrapper = (event: BusEvent) => {
      handler(event);
      this.off(type, wrapper);
    };
    this.on(type, wrapper);
  }

  getHistory(type?: string): BusEvent[] {
    if (type) {
      return this.history.filter(e => e.type === type);
    }
    return [...this.history];
  }

  clear(): void {
    this.handlers.clear();
    this.history = [];
  }
}

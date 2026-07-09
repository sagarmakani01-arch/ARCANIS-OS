import { IDisposable } from '../api/types';

export type EventHandler<T = unknown> = (event: T) => void;

export interface IEventBus {
  on<T>(event: string, handler: EventHandler<T>): IDisposable;
  once<T>(event: string, handler: EventHandler<T>): IDisposable;
  emit<T>(event: string, payload: T): void;
  off<T>(event: string, handler: EventHandler<T>): void;
  clear(): void;
  listenerCount(event: string): number;
}

export class EventBus implements IEventBus {
  private listeners = new Map<string, Set<EventHandler>>();
  private onceListeners = new Map<string, Set<EventHandler>>();

  on<T>(event: string, handler: EventHandler<T>): IDisposable {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(handler as EventHandler);
    return {
      dispose: () => this.off(event, handler as EventHandler),
    };
  }

  once<T>(event: string, handler: EventHandler<T>): IDisposable {
    if (!this.onceListeners.has(event)) {
      this.onceListeners.set(event, new Set());
    }
    this.onceListeners.get(event)!.add(handler as EventHandler);
    return {
      dispose: () => {
        const handlers = this.onceListeners.get(event);
        if (handlers) {
          handlers.delete(handler as EventHandler);
        }
      },
    };
  }

  emit<T>(event: string, payload: T): void {
    const handlers = this.listeners.get(event);
    if (handlers) {
      for (const handler of handlers) {
        try {
          handler(payload);
        } catch (err) {
          console.error(`[EventBus] Error in handler for "${event}":`, err);
        }
      }
    }

    const onceHandlers = this.onceListeners.get(event);
    if (onceHandlers) {
      for (const handler of onceHandlers) {
        try {
          handler(payload);
        } catch (err) {
          console.error(`[EventBus] Error in once-handler for "${event}":`, err);
        }
      }
      this.onceListeners.delete(event);
    }
  }

  off<T>(event: string, handler: EventHandler<T>): void {
    const handlers = this.listeners.get(event);
    if (handlers) {
      handlers.delete(handler as EventHandler);
      if (handlers.size === 0) {
        this.listeners.delete(event);
      }
    }
  }

  clear(): void {
    this.listeners.clear();
    this.onceListeners.clear();
  }

  listenerCount(event: string): number {
    const permanent = this.listeners.get(event)?.size || 0;
    const once = this.onceListeners.get(event)?.size || 0;
    return permanent + once;
  }
}

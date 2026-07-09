import { EventBus } from '../../src/core/EventBus';

describe('EventBus', () => {
  let bus: EventBus;

  beforeEach(() => {
    bus = new EventBus();
  });

  describe('on and emit', () => {
    it('should register a handler and emit events to it', () => {
      const handler = jest.fn();
      bus.on('test:event', handler);
      bus.emit('test:event', 'payload');
      expect(handler).toHaveBeenCalledWith('payload');
    });

    it('should emit to multiple handlers for the same event', () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();
      bus.on('test:event', handler1);
      bus.on('test:event', handler2);
      bus.emit('test:event', { data: 42 });
      expect(handler1).toHaveBeenCalledWith({ data: 42 });
      expect(handler2).toHaveBeenCalledWith({ data: 42 });
    });

    it('should do nothing when emitting an event with no handlers', () => {
      expect(() => bus.emit('nonexistent', 'data')).not.toThrow();
    });

    it('should pass payload of any type', () => {
      const handler = jest.fn();
      bus.on('test', handler);
      bus.emit('test', 123);
      expect(handler).toHaveBeenCalledWith(123);

      bus.emit('test', { nested: true });
      expect(handler).toHaveBeenCalledWith({ nested: true });

      bus.emit('test', null);
      expect(handler).toHaveBeenCalledWith(null);
    });
  });

  describe('once', () => {
    it('should handle the event only once', () => {
      const handler = jest.fn();
      bus.once('test:once', handler);
      bus.emit('test:once', 1);
      bus.emit('test:once', 2);
      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler).toHaveBeenCalledWith(1);
    });

    it('should return a disposable that removes the listener', () => {
      const handler = jest.fn();
      const disposable = bus.once('test:once', handler);
      disposable.dispose();
      bus.emit('test:once', 'data');
      expect(handler).not.toHaveBeenCalled();
    });
  });

  describe('off', () => {
    it('should remove a specific handler', () => {
      const handler = jest.fn();
      bus.on('test:event', handler);
      bus.off('test:event', handler);
      bus.emit('test:event', 'data');
      expect(handler).not.toHaveBeenCalled();
    });

    it('should not affect other handlers when removing one', () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();
      bus.on('test:event', handler1);
      bus.on('test:event', handler2);
      bus.off('test:event', handler1);
      bus.emit('test:event', 'data');
      expect(handler1).not.toHaveBeenCalled();
      expect(handler2).toHaveBeenCalledWith('data');
    });

    it('should do nothing when removing a handler that was never registered', () => {
      expect(() => bus.off('test:event', jest.fn())).not.toThrow();
    });
  });

  describe('clear', () => {
    it('should remove all permanent listeners', () => {
      const handler = jest.fn();
      bus.on('test:a', handler);
      bus.on('test:b', handler);
      bus.clear();
      bus.emit('test:a', 'data');
      bus.emit('test:b', 'data');
      expect(handler).not.toHaveBeenCalled();
    });

    it('should remove all once listeners', () => {
      const handler = jest.fn();
      bus.once('test:once', handler);
      bus.clear();
      bus.emit('test:once', 'data');
      expect(handler).not.toHaveBeenCalled();
    });
  });

  describe('listenerCount', () => {
    it('should return 0 for an event with no listeners', () => {
      expect(bus.listenerCount('test')).toBe(0);
    });

    it('should count permanent listeners', () => {
      bus.on('test', jest.fn());
      bus.on('test', jest.fn());
      expect(bus.listenerCount('test')).toBe(2);
    });

    it('should count once listeners', () => {
      bus.once('test', jest.fn());
      bus.once('test', jest.fn());
      expect(bus.listenerCount('test')).toBe(2);
    });

    it('should count both permanent and once listeners', () => {
      bus.on('test', jest.fn());
      bus.once('test', jest.fn());
      expect(bus.listenerCount('test')).toBe(2);
    });

    it('should decrease after removing a listener via off', () => {
      const handler = jest.fn();
      bus.on('test', handler);
      expect(bus.listenerCount('test')).toBe(1);
      bus.off('test', handler);
      expect(bus.listenerCount('test')).toBe(0);
    });

    it('should decrease after once listener fires', () => {
      const handler = jest.fn();
      bus.once('test', handler);
      expect(bus.listenerCount('test')).toBe(1);
      bus.emit('test', 'data');
      expect(bus.listenerCount('test')).toBe(0);
    });
  });

  describe('error handling', () => {
    it('should not throw when a handler throws', () => {
      const throwingHandler = jest.fn().mockImplementation(() => {
        throw new Error('handler error');
      });
      const safeHandler = jest.fn();

      bus.on('test:event', throwingHandler);
      bus.on('test:event', safeHandler);

      expect(() => bus.emit('test:event', 'data')).not.toThrow();
      expect(safeHandler).toHaveBeenCalledWith('data');
    });

    it('should continue calling remaining handlers after one throws', () => {
      const order: number[] = [];
      bus.on('test', () => { order.push(1); });
      bus.on('test', () => { order.push(2); throw new Error('fail'); });
      bus.on('test', () => { order.push(3); });

      bus.emit('test', null);
      expect(order).toEqual([1, 2, 3]);
    });

    it('should not throw when a once-handler throws', () => {
      bus.once('test', () => { throw new Error('once error'); });
      expect(() => bus.emit('test', 'data')).not.toThrow();
    });
  });

  describe('disposable from on', () => {
    it('should remove the listener when disposed', () => {
      const handler = jest.fn();
      const disposable = bus.on('test', handler);
      disposable.dispose();
      bus.emit('test', 'data');
      expect(handler).not.toHaveBeenCalled();
    });
  });
});

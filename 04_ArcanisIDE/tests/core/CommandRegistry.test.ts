import { CommandRegistry } from '../../src/core/CommandRegistry';

describe('CommandRegistry', () => {
  let registry: CommandRegistry;

  beforeEach(() => {
    registry = new CommandRegistry();
  });

  describe('registerCommand and executeCommand', () => {
    it('should register and execute a command', async () => {
      const handler = jest.fn().mockReturnValue('result');
      registry.registerCommand('test.command', handler);
      const result = await registry.executeCommand('test.command');
      expect(handler).toHaveBeenCalled();
      expect(result).toBe('result');
    });

    it('should execute a command with arguments', async () => {
      const handler = jest.fn().mockReturnValue('done');
      registry.registerCommand('test.command', handler);
      await registry.executeCommand('test.command', 'arg1', 42, { key: 'val' });
      expect(handler).toHaveBeenCalledWith('arg1', 42, { key: 'val' });
    });

    it('should support async handlers', async () => {
      const handler = jest.fn().mockResolvedValue('async-result');
      registry.registerCommand('async.command', handler);
      const result = await registry.executeCommand('async.command');
      expect(result).toBe('async-result');
    });

    it('should throw for unknown command', async () => {
      await expect(registry.executeCommand('unknown')).rejects.toThrow(
        'Command "unknown" not found.',
      );
    });
  });

  describe('registerCommand override warning', () => {
    it('should allow overriding a command and use the new handler', async () => {
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
      const handler1 = jest.fn().mockReturnValue('first');
      const handler2 = jest.fn().mockReturnValue('second');

      registry.registerCommand('test.command', handler1);
      registry.registerCommand('test.command', handler2);

      expect(warnSpy).toHaveBeenCalledWith(
        expect.stringContaining('test.command'),
      );

      const result = await registry.executeCommand('test.command');
      expect(result).toBe('second');
      expect(handler1).not.toHaveBeenCalled();

      warnSpy.mockRestore();
    });
  });

  describe('getCommand', () => {
    it('should return command descriptor for registered command', () => {
      registry.registerCommand('test.command', jest.fn(), 'test-context');
      const desc = registry.getCommand('test.command');
      expect(desc).toEqual({ id: 'test.command', context: 'test-context' });
    });

    it('should return undefined for unknown command', () => {
      expect(registry.getCommand('unknown')).toBeUndefined();
    });
  });

  describe('getCommands', () => {
    it('should return all registered commands', () => {
      registry.registerCommand('cmd1', jest.fn());
      registry.registerCommand('cmd2', jest.fn());
      const commands = registry.getCommands();
      expect(commands).toHaveLength(2);
      expect(commands.map((c) => c.id)).toEqual(expect.arrayContaining(['cmd1', 'cmd2']));
    });

    it('should filter commands by context', () => {
      registry.registerCommand('cmd1', jest.fn(), 'ctx-a');
      registry.registerCommand('cmd2', jest.fn(), 'ctx-b');
      registry.registerCommand('cmd3', jest.fn());

      const ctxACommands = registry.getCommands('ctx-a');
      expect(ctxACommands).toHaveLength(1);
      expect(ctxACommands[0].id).toBe('cmd1');

      const noCtxCommands = registry.getCommands(undefined);
      expect(noCtxCommands).toHaveLength(3);
    });

    it('should return empty array when no commands match context', () => {
      expect(registry.getCommands('nonexistent')).toEqual([]);
    });
  });

  describe('hasCommand', () => {
    it('should return true for registered command', () => {
      registry.registerCommand('test.command', jest.fn());
      expect(registry.hasCommand('test.command')).toBe(true);
    });

    it('should return false for unknown command', () => {
      expect(registry.hasCommand('unknown')).toBe(false);
    });
  });

  describe('disposable returned by registerCommand', () => {
    it('should unregister the command when disposed', async () => {
      const handler = jest.fn();
      const disposable = registry.registerCommand('temp.command', handler);
      disposable.dispose();

      expect(registry.hasCommand('temp.command')).toBe(false);
      await expect(registry.executeCommand('temp.command')).rejects.toThrow(
        'Command "temp.command" not found.',
      );
    });
  });

  describe('executeCommand error handling', () => {
    it('should re-throw errors from handler', async () => {
      const handler = jest.fn().mockImplementation(() => {
        throw new Error('handler failure');
      });
      const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      registry.registerCommand('failing.command', handler);

      await expect(registry.executeCommand('failing.command')).rejects.toThrow(
        'handler failure',
      );

      errorSpy.mockRestore();
    });
  });
});

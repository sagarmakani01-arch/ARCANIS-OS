import { Configuration } from '../../src/core/Configuration';

describe('Configuration', () => {
  let config: Configuration;

  beforeEach(() => {
    config = new Configuration();
  });

  describe('default values', () => {
    it('should provide default values for known keys', () => {
      expect(config.get<number>('editor.fontSize')).toBe(14);
      expect(config.get<string>('editor.fontFamily')).toBe('Cascadia Code, Fira Code, Consolas, monospace');
      expect(config.get<number>('editor.tabSize')).toBe(4);
      expect(config.get<boolean>('editor.insertSpaces')).toBe(true);
      expect(config.get<string>('editor.wordWrap')).toBe('off');
      expect(config.get<boolean>('editor.minimap')).toBe(true);
    });

    it('should return undefined for unknown keys without default', () => {
      expect(config.get('nonexistent.key')).toBeUndefined();
    });

    it('should return the provided default value for unknown keys', () => {
      expect(config.get('nonexistent', 'fallback')).toBe('fallback');
    });
  });

  describe('get and set', () => {
    it('should set and get a value', () => {
      config.set('editor.fontSize', 20);
      expect(config.get<number>('editor.fontSize')).toBe(20);
    });

    it('should overwrite default with set value', () => {
      expect(config.get<string>('theme')).toBe('arcanis-dark');
      config.set('theme', 'custom-dark');
      expect(config.get<string>('theme')).toBe('custom-dark');
    });

    it('should store values of different types', () => {
      config.set('test.string', 'hello');
      config.set('test.number', 42);
      config.set('test.boolean', true);
      config.set('test.object', { nested: true });

      expect(config.get('test.string')).toBe('hello');
      expect(config.get('test.number')).toBe(42);
      expect(config.get('test.boolean')).toBe(true);
      expect(config.get('test.object')).toEqual({ nested: true });
    });
  });

  describe('has', () => {
    it('should return true for default keys', () => {
      expect(config.has('editor.fontSize')).toBe(true);
    });

    it('should return true for set keys', () => {
      config.set('custom.key', 'value');
      expect(config.has('custom.key')).toBe(true);
    });

    it('should return false for unknown keys', () => {
      expect(config.has('completely.random.key')).toBe(false);
    });
  });

  describe('delete', () => {
    it('should remove a custom-set value', () => {
      config.set('editor.fontSize', 24);
      config.delete('editor.fontSize');
      expect(config.get<number>('editor.fontSize')).toBe(14);
    });

    it('should do nothing when deleting a non-existent key', () => {
      expect(() => config.delete('nonexistent')).not.toThrow();
    });
  });

  describe('getAll', () => {
    it('should return merged defaults and custom values', () => {
      config.set('editor.fontSize', 18);
      const all = config.getAll();
      expect(all['editor.fontSize']).toBe(18);
      expect(all['editor.tabSize']).toBe(4);
    });
  });

  describe('getEditorConfig', () => {
    it('should return an EditorConfig object with correct defaults', () => {
      const editorConfig = config.getEditorConfig();
      expect(editorConfig.fontSize).toBe(14);
      expect(editorConfig.tabSize).toBe(4);
      expect(editorConfig.insertSpaces).toBe(true);
      expect(editorConfig.wordWrap).toBe('off');
      expect(editorConfig.lineNumbers).toBe('on');
      expect(editorConfig.minimap).toBe(true);
      expect(editorConfig.bracketPairColorization).toBe(true);
      expect(editorConfig.autoClosingBrackets).toBe(true);
      expect(editorConfig.autoClosingQuotes).toBe(true);
      expect(editorConfig.formatOnPaste).toBe(false);
      expect(editorConfig.formatOnSave).toBe(true);
    });

    it('should reflect changes made to config values', () => {
      config.set('editor.fontSize', 22);
      config.set('editor.tabSize', 2);
      config.set('editor.wordWrap', 'on');

      const editorConfig = config.getEditorConfig();
      expect(editorConfig.fontSize).toBe(22);
      expect(editorConfig.tabSize).toBe(2);
      expect(editorConfig.wordWrap).toBe('on');
    });
  });

  describe('onDidChange', () => {
    it('should fire when a config value changes', () => {
      const handler = jest.fn();
      config.onDidChange('editor.fontSize', handler);
      config.set('editor.fontSize', 16);
      expect(handler).toHaveBeenCalledWith(16);
    });

    it('should not fire for unrelated keys', () => {
      const handler = jest.fn();
      config.onDidChange('editor.fontSize', handler);
      config.set('editor.tabSize', 8);
      expect(handler).not.toHaveBeenCalled();
    });

    it('should return a disposable that stops notifications', () => {
      const handler = jest.fn();
      const disposable = config.onDidChange('editor.fontSize', handler);
      disposable.dispose();
      config.set('editor.fontSize', 16);
      expect(handler).not.toHaveBeenCalled();
    });

    it('should fire when a value is deleted', () => {
      config.set('custom.key', 'value');
      const handler = jest.fn();
      config.onDidChange('custom.key', handler);
      config.delete('custom.key');
      expect(handler).toHaveBeenCalledWith(undefined);
    });
  });

  describe('resetToDefaults', () => {
    it('should reset all custom values to defaults', () => {
      config.set('editor.fontSize', 100);
      config.set('editor.tabSize', 100);
      config.set('custom.value', 'should be removed');
      config.resetToDefaults();

      expect(config.get<number>('editor.fontSize')).toBe(14);
      expect(config.get<number>('editor.tabSize')).toBe(4);
      expect(config.has('custom.value')).toBe(false);
    });
  });
});

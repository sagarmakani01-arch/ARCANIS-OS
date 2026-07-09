const { ManifestValidator, ManifestValidationError } = require('../src/core/ManifestValidator');

describe('ManifestValidator', () => {
  let validator;

  beforeEach(() => {
    validator = new ManifestValidator();
  });

  describe('validate', () => {
    test('throws on null manifest', () => {
      expect(() => validator.validate(null)).toThrow(ManifestValidationError);
    });

    test('throws on non-object manifest', () => {
      expect(() => validator.validate('string')).toThrow(ManifestValidationError);
    });

    test('returns errors for missing required fields', () => {
      const result = validator.validate({});
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing required field: name');
      expect(result.errors).toContain('Missing required field: version');
      expect(result.errors).toContain('Missing required field: description');
    });

    test('passes with valid minimal manifest', () => {
      const result = validator.validate({
        name: 'my-package',
        version: '1.0.0',
        description: 'A test package'
      });
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    test('validates scoped package names', () => {
      const result = validator.validate({
        name: '@scope/my-package',
        version: '1.0.0',
        description: 'Scoped package'
      });
      expect(result.valid).toBe(true);
    });

    test('rejects invalid package names', () => {
      const result = validator.validate({
        name: 'My_Package!',
        version: '1.0.0',
        description: 'Bad name'
      });
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Package name must be lowercase, hyphen-separated, optionally scoped (@scope/name)');
    });

    test('rejects invalid semver', () => {
      const result = validator.validate({
        name: 'my-package',
        version: '1.0',
        description: 'Bad version'
      });
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Version must follow semver format (x.y.z)');
    });

    test('validates dependencies object', () => {
      const result = validator.validate({
        name: 'my-package',
        version: '1.0.0',
        description: 'Test',
        dependencies: { 'dep-a': '^1.0.0' }
      });
      expect(result.valid).toBe(true);
    });

    test('rejects non-string dependency versions', () => {
      const result = validator.validate({
        name: 'my-package',
        version: '1.0.0',
        description: 'Test',
        dependencies: { 'dep-a': 123 }
      });
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Invalid version constraint for dependency "dep-a"');
    });

    test('rejects non-object dependencies', () => {
      const result = validator.validate({
        name: 'my-package',
        version: '1.0.0',
        description: 'Test',
        dependencies: 'not-an-object'
      });
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('dependencies must be an object');
    });

    test('validates permissions array', () => {
      const result = validator.validate({
        name: 'my-package',
        version: '1.0.0',
        description: 'Test',
        permissions: ['network', 'filesystem']
      });
      expect(result.valid).toBe(true);
    });

    test('warns on unknown permissions', () => {
      const result = validator.validate({
        name: 'my-package',
        version: '1.0.0',
        description: 'Test',
        permissions: ['network', 'unknown-perm']
      });
      expect(result.warnings).toContain('Unknown permission "unknown-perm"');
    });

    test('rejects non-array permissions', () => {
      const result = validator.validate({
        name: 'my-package',
        version: '1.0.0',
        description: 'Test',
        permissions: 'network'
      });
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('permissions must be an array');
    });
  });

  describe('sanitize', () => {
    test('strips unknown fields', () => {
      const clean = validator.sanitize({
        name: 'test',
        version: '1.0.0',
        description: 'Test',
        customField: 'should be removed',
        another: 123
      });
      expect(clean.name).toBe('test');
      expect(clean.version).toBe('1.0.0');
      expect(clean.description).toBe('Test');
      expect(clean.customField).toBeUndefined();
      expect(clean.another).toBeUndefined();
    });

    test('preserves optional fields', () => {
      const clean = validator.sanitize({
        name: 'test',
        version: '1.0.0',
        description: 'Test',
        author: 'Sagar',
        license: 'MIT',
        main: 'index.js',
        dependencies: { a: '^1.0.0' }
      });
      expect(clean.author).toBe('Sagar');
      expect(clean.license).toBe('MIT');
      expect(clean.main).toBe('index.js');
      expect(clean.dependencies).toEqual({ a: '^1.0.0' });
    });
  });
});

'use strict';

class ManifestValidationError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = 'ManifestValidationError';
    this.details = details;
  }
}

class ManifestValidator {
  constructor() {
    this.requiredFields = ['name', 'version', 'description'];
    this.optionalFields = [
      'author', 'license', 'main', 'dependencies',
      'devDependencies', 'arcanis', 'scripts', 'permissions',
      'repository', 'keywords', 'type', 'engines'
    ];
  }

  validate(manifest) {
    const errors = [];
    const warnings = [];

    if (!manifest || typeof manifest !== 'object') {
      throw new ManifestValidationError('Manifest must be a non-null object');
    }

    for (const field of this.requiredFields) {
      if (!manifest[field]) {
        errors.push(`Missing required field: ${field}`);
      }
    }

    if (manifest.name) {
      if (!/^(@[a-z0-9-]+\/)?[a-z0-9-]+$/.test(manifest.name)) {
        errors.push('Package name must be lowercase, hyphen-separated, optionally scoped (@scope/name)');
      }
    }

    if (manifest.version) {
      if (!/^\d+\.\d+\.\d+/.test(manifest.version)) {
        errors.push('Version must follow semver format (x.y.z)');
      }
    }

    if (manifest.dependencies) {
      if (typeof manifest.dependencies !== 'object') {
        errors.push('dependencies must be an object');
      } else {
        for (const [dep, ver] of Object.entries(manifest.dependencies)) {
          if (typeof ver !== 'string') {
            errors.push(`Invalid version constraint for dependency "${dep}"`);
          }
        }
      }
    }

    if (manifest.permissions) {
      if (!Array.isArray(manifest.permissions)) {
        errors.push('permissions must be an array');
      } else {
        const validPerms = ['network', 'filesystem', 'process', 'env', 'device'];
        for (const perm of manifest.permissions) {
          if (!validPerms.includes(perm)) {
            warnings.push(`Unknown permission "${perm}"`);
          }
        }
      }
    }

    return { valid: errors.length === 0, errors, warnings };
  }

  sanitize(manifest) {
    const clean = {};
    for (const field of [...this.requiredFields, ...this.optionalFields]) {
      if (manifest[field] !== undefined) {
        clean[field] = manifest[field];
      }
    }
    return clean;
  }
}

module.exports = { ManifestValidator, ManifestValidationError };

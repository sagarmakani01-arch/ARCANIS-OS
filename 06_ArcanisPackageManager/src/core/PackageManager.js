'use strict';

const path = require('path');
const fs = require('fs');
const { DependencyResolver } = require('./DependencyResolver');
const { RegistryClient } = require('./RegistryClient');
const { PackageInstaller } = require('./PackageInstaller');
const { ManifestValidator } = require('./ManifestValidator');
const { PackageVerifier } = require('../security/PackageVerifier');
const { MalwareScanner } = require('../security/MalwareScanner');
const { PermissionManager } = require('../security/PermissionManager');
const { TrustedSourceManager } = require('../security/TrustedSourceManager');

class PackageManager {
  constructor(options = {}) {
    this.projectRoot = options.projectRoot || process.cwd();
    this.config = this.loadConfig(options.config);

    this.registry = new RegistryClient({
      defaultRegistry: this.config.registry?.default,
      fallbackRegistries: this.config.registry?.fallback || []
    });

    this.resolver = new DependencyResolver(this.registry);
    this.installer = new PackageInstaller({
      installRoot: this.projectRoot,
      modulesDir: this.config.cache?.directory || '.arcanis/modules',
      cacheDir: path.join(this.projectRoot, '.arcanis', 'cache')
    });

    this.validator = new ManifestValidator();
    this.verifier = new PackageVerifier();
    this.scanner = new MalwareScanner();
    this.permissions = new PermissionManager(this.config.permissions);
    this.trustedSources = new TrustedSourceManager(this.config.trustedSources);
  }

  loadConfig(config) {
    const defaultConfig = {
      registry: { default: 'https://registry.arcanis.dev/v1', fallback: [] },
      trustedSources: ['https://registry.arcanis.dev'],
      permissions: { defaultPolicy: 'ask', allowedScopes: [] },
      cache: { directory: '.arcanis/modules', maxAge: 86400000 },
      security: { verifySignatures: true, scanOnInstall: true, strictMode: false }
    };

    const configPath = path.join(this.projectRoot, '.arcanis', 'config.json');
    try {
      const userConfig = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
      return this.mergeConfig(defaultConfig, userConfig);
    } catch {
      return defaultConfig;
    }
  }

  mergeConfig(base, override) {
    const result = { ...base };
    for (const [key, val] of Object.entries(override || {})) {
      if (val && typeof val === 'object' && !Array.isArray(val)) {
        result[key] = this.mergeConfig(result[key] || {}, val);
      } else {
        result[key] = val;
      }
    }
    return result;
  }

  async install(packageName, constraint = '*', options = {}) {
    const source = options.source || this.config.registry?.default;

    if (this.config.security?.verifySignatures) {
      const trusted = await this.trustedSources.isTrusted(source);
      if (!trusted) {
        const allowed = await this.permissions.requestPermission(
          'install', `Install from untrusted source: ${source}`
        );
        if (!allowed) {
          return { success: false, error: `Source not trusted: ${source}` };
        }
      }
    }

    const tree = await this.resolver.resolve(packageName, constraint, source);

    if (this.config.security?.scanOnInstall) {
      const scanResult = await this.scanner.scan(tree);
      if (scanResult.malicious && this.config.security?.strictMode) {
        return { success: false, error: 'Package flagged as malicious', scanResult };
      }
    }

    const result = await this.installer.install(tree, options);
    const manifest = await this.generateLockFile(tree);

    return { success: true, tree, installed: result, lockFile: manifest };
  }

  async remove(packageName) {
    return this.installer.remove(packageName);
  }

  async update(packageName, constraint = '*', options = {}) {
    const lockPath = path.join(this.projectRoot, '.arcanis', 'lock.json');
    try {
      const lock = JSON.parse(fs.readFileSync(lockPath, 'utf-8'));
      const entry = lock.dependencies?.[packageName];
      if (entry) {
        constraint = constraint === '*' ? `^${entry.version}` : constraint;
      }
    } catch {}

    return this.install(packageName, constraint, { ...options, force: true });
  }

  async list() {
    return this.installer.listInstalled();
  }

  async publish(packageDir, options = {}) {
    const manifestPath = path.join(packageDir, 'arcanis.json');
    let manifest;
    try {
      manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
    } catch {
      return { success: false, error: 'Invalid arcanis.json manifest' };
    }

    const validation = this.validator.validate(manifest);
    if (!validation.valid) {
      return { success: false, error: 'Manifest validation failed', details: validation.errors };
    }

    const source = options.source || this.config.registry?.default;
    const trusted = await this.trustedSources.isTrusted(source);
    if (!trusted) {
      return { success: false, error: 'Cannot publish to untrusted registry' };
    }

    const packageData = this.preparePackageData(manifest, packageDir);
    return this.registry.publishPackage(packageData, source);
  }

  preparePackageData(manifest, packageDir) {
    const data = { ...manifest, files: {} };
    const mainFile = manifest.main || 'index.js';
    const mainPath = path.join(packageDir, mainFile);
    try {
      data.files[mainFile] = fs.readFileSync(mainPath, 'utf-8');
    } catch {}

    const distDir = path.join(packageDir, 'dist');
    if (fs.existsSync(distDir)) {
      const entries = fs.readdirSync(distDir, { recursive: true });
      for (const entry of entries) {
        const fullPath = path.join(distDir, entry);
        if (fs.statSync(fullPath).isFile()) {
          data.files[`dist/${entry}`] = fs.readFileSync(fullPath, 'utf-8');
        }
      }
    }

    return data;
  }

  async search(query) {
    return this.registry.searchPackages(query);
  }

  async generateLockFile(resolvedTree) {
    const flat = this.resolver.flatten(resolvedTree);
    const lock = {
      version: 1,
      createdAt: new Date().toISOString(),
      dependencies: {}
    };
    for (const pkg of flat) {
      lock.dependencies[`${pkg.name}@${pkg.version}`] = {
        name: pkg.name,
        version: pkg.version,
        resolved: true
      };
    }

    const lockPath = path.join(this.projectRoot, '.arcanis', 'lock.json');
    fs.writeFileSync(lockPath, JSON.stringify(lock, null, 2), 'utf-8');
    return lock;
  }

  async verify(packageName) {
    const pkg = await this.installer.listInstalled().then(list =>
      list.find(p => p.name === packageName)
    );
    if (!pkg) return { valid: false, error: 'Package not installed' };

    const installPath = this.installer.getInstallPath(packageName);
    return this.verifier.verify(installPath);
  }

  listPermissions() {
    return this.permissions.listPermissions();
  }

  addTrustedSource(source) {
    return this.trustedSources.addSource(source);
  }

  removeTrustedSource(source) {
    return this.trustedSources.removeSource(source);
  }
}

module.exports = { PackageManager };

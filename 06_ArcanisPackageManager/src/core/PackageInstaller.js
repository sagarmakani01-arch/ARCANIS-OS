'use strict';

const fs = require('fs');
const path = require('path');

class InstallationError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = 'InstallationError';
    this.details = details;
  }
}

class PackageInstaller {
  constructor(options = {}) {
    this.installRoot = options.installRoot || process.cwd();
    this.modulesDir = options.modulesDir || '.arcanis/modules';
    this.cacheDir = options.cacheDir || '.arcanis/cache';
  }

  getInstallPath(packageName) {
    return path.join(this.installRoot, this.modulesDir, packageName);
  }

  async install(resolvedTree, options = {}) {
    const flatList = [];
    const seen = new Set();
    const walk = (node) => {
      const key = `${node.name}@${node.version}`;
      if (!seen.has(key)) {
        seen.add(key);
        flatList.push(node);
      }
      if (node.dependencies) {
        for (const dep of Object.values(node.dependencies)) {
          walk(dep);
        }
      }
    };
    walk(resolvedTree);

    const results = [];
    for (const pkg of flatList) {
      results.push(await this.installPackage(pkg, options));
    }
    return results;
  }

  async installPackage(pkg, options = {}) {
    const installPath = this.getInstallPath(pkg.name);
    const pkgDir = path.dirname(installPath);

    if (!fs.existsSync(pkgDir)) {
      fs.mkdirSync(pkgDir, { recursive: true });
    }

    const manifestPath = path.join(installPath, 'arcanis.json');
    if (fs.existsSync(manifestPath) && !options.force) {
      return { name: pkg.name, version: pkg.version, status: 'already-installed' };
    }

    if (fs.existsSync(installPath)) {
      this.removeDirectorySync(installPath);
    }

    fs.mkdirSync(installPath, { recursive: true });

    const manifest = {
      name: pkg.name,
      version: pkg.version,
      description: pkg.manifest?.description || '',
      dependencies: pkg.dependencies ? this.summarizeDeps(pkg.dependencies) : {},
      installedAt: new Date().toISOString()
    };

    const files = pkg.manifest?.files || {};
    for (const [filePath, content] of Object.entries(files)) {
      const fullPath = path.join(installPath, filePath);
      const fileDir = path.dirname(fullPath);
      if (!fs.existsSync(fileDir)) {
        fs.mkdirSync(fileDir, { recursive: true });
      }

      if (typeof content === 'string' && content.startsWith('base64:')) {
        fs.writeFileSync(fullPath, Buffer.from(content.slice(7), 'base64'));
      } else if (typeof content === 'string') {
        fs.writeFileSync(fullPath, content, 'utf-8');
      } else if (Buffer.isBuffer(content)) {
        fs.writeFileSync(fullPath, content);
      }
    }

    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf-8');

    return { name: pkg.name, version: pkg.version, status: 'installed', path: installPath };
  }

  summarizeDeps(deps) {
    const result = {};
    for (const [name, dep] of Object.entries(deps)) {
      result[name] = dep.version;
    }
    return result;
  }

  async remove(packageName) {
    const installPath = this.getInstallPath(packageName);
    if (!fs.existsSync(installPath)) {
      return { name: packageName, status: 'not-found' };
    }
    this.removeDirectorySync(installPath);
    return { name: packageName, status: 'removed' };
  }

  async listInstalled() {
    const modulesPath = path.join(this.installRoot, this.modulesDir);
    if (!fs.existsSync(modulesPath)) return [];

    const packages = [];
    const entries = fs.readdirSync(modulesPath, { withFileTypes: true });

    for (const entry of entries) {
      if (entry.isDirectory()) {
        const scopePath = path.join(modulesPath, entry.name);
        if (entry.name.startsWith('@')) {
          const scopedEntries = fs.readdirSync(scopePath, { withFileTypes: true });
          for (const se of scopedEntries) {
            if (se.isDirectory()) {
              packages.push(this.readPackageManifest(path.join(scopePath, se.name)));
            }
          }
        } else {
          packages.push(this.readPackageManifest(scopePath));
        }
      }
    }
    return packages.filter(Boolean);
  }

  readPackageManifest(dir) {
    const manifestPath = path.join(dir, 'arcanis.json');
    try {
      return JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
    } catch {
      return null;
    }
  }

  removeDirectorySync(dirPath) {
    if (!fs.existsSync(dirPath)) return;
    for (const entry of fs.readdirSync(dirPath, { withFileTypes: true })) {
      const fullPath = path.join(dirPath, entry.name);
      if (entry.isDirectory()) {
        this.removeDirectorySync(fullPath);
      } else {
        fs.unlinkSync(fullPath);
      }
    }
    fs.rmdirSync(dirPath);
  }
}

module.exports = { PackageInstaller, InstallationError };

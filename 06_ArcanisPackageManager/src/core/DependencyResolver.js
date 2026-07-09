'use strict';

class ResolverError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = 'ResolverError';
    this.details = details;
  }
}

class DependencyResolver {
  constructor(registry) {
    this.registry = registry;
    this.resolved = new Map();
    this.visited = new Set();
  }

  parseConstraint(constraint) {
    const range = constraint.trim();
    if (range === '*') return { type: 'any', value: '*' };
    if (/^\d+\.\d+\.\d+$/.test(range)) return { type: 'exact', value: range };
    const match = range.match(/^([~^><=]*)\s*(\d+\.\d+\.\d+)$/);
    if (match) return { type: match[1] || 'exact', value: match[2] };
    throw new ResolverError(`Unrecognized version constraint: ${constraint}`);
  }

  satisfies(version, constraint) {
    if (constraint === '*') return true;
    const v = version.split('.').map(Number);
    const c = this.parseConstraint(constraint);
    const cv = c.value.split('.').map(Number);

    switch (c.type) {
      case 'exact': return version === c.value;
      case '~': return v[0] === cv[0] && v[1] === cv[1];
      case '^': return v[0] === cv[0] && (v[1] >= cv[1] || v[0] > cv[0]);
      case '>=': return this.compareVersions(version, c.value) >= 0;
      case '<=': return this.compareVersions(version, c.value) <= 0;
      case '>': return this.compareVersions(version, c.value) > 0;
      case '<': return this.compareVersions(version, c.value) < 0;
      case 'any': return true;
      default: return version === c.value;
    }
  }

  compareVersions(a, b) {
    const pa = a.split('.').map(Number);
    const pb = b.split('.').map(Number);
    for (let i = 0; i < 3; i++) {
      if ((pa[i] || 0) > (pb[i] || 0)) return 1;
      if ((pa[i] || 0) < (pb[i] || 0)) return -1;
    }
    return 0;
  }

  async resolve(name, constraint, source = 'default') {
    const key = `${name}@${constraint}`;
    if (this.resolved.has(key)) return this.resolved.get(key);
    if (this.visited.has(key)) return { name, version: null, circular: true };
    this.visited.add(key);

    if (constraint === '*') {
      const info = await this.registry.fetchPackageInfo(name, source);
      if (!info) throw new ResolverError(`Package "${name}" not found`);
      constraint = `^${info['dist-tags']?.latest || info.versions?.[0]}`;
    }

    const pkg = await this.registry.fetchPackageVersion(name, constraint, source);
    if (!pkg) throw new ResolverError(`No version of "${name}" satisfies "${constraint}"`);

    const deps = pkg.dependencies || {};
    const resolvedDeps = {};
    for (const [depName, depConstraint] of Object.entries(deps)) {
      try {
        resolvedDeps[depName] = await this.resolve(depName, depConstraint, source);
      } catch (err) {
        throw new ResolverError(
          `Failed to resolve dependency "${depName}" for "${name}"`,
          { package: name, dependency: depName, constraint: depConstraint, cause: err.message }
        );
      }
    }

    const result = {
      name: pkg.name,
      version: pkg.version,
      resolved: true,
      dependencies: resolvedDeps,
      manifest: pkg
    };

    this.resolved.set(key, result);
    return result;
  }

  flatten(resolvedTree, depth = 0) {
    const flat = [];
    const seen = new Set();
    const walk = (node, level) => {
      const key = `${node.name}@${node.version}`;
      if (!seen.has(key)) {
        seen.add(key);
        flat.push({ ...node, depth: level });
      }
      if (node.dependencies) {
        for (const dep of Object.values(node.dependencies)) {
          walk(dep, level + 1);
        }
      }
    };
    walk(resolvedTree, depth);
    return flat;
  }

  detectConflicts(flatList) {
    const versionMap = new Map();
    const conflicts = [];
    for (const pkg of flatList) {
      if (versionMap.has(pkg.name)) {
        if (versionMap.get(pkg.name) !== pkg.version) {
          conflicts.push({
            package: pkg.name,
            versions: [versionMap.get(pkg.name), pkg.version]
          });
        }
      } else {
        versionMap.set(pkg.name, pkg.version);
      }
    }
    return conflicts;
  }
}

module.exports = { DependencyResolver, ResolverError };

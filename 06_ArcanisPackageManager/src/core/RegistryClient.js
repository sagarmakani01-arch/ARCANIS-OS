'use strict';

const https = require('https');
const http = require('http');
const { URL } = require('url');

class RegistryError extends Error {
  constructor(message, statusCode) {
    super(message);
    this.name = 'RegistryError';
    this.statusCode = statusCode;
  }
}

class RegistryClient {
  constructor(config = {}) {
    this.defaultRegistry = config.defaultRegistry || 'https://registry.arcanis.dev/v1';
    this.fallbackRegistries = config.fallbackRegistries || [];
    this.timeout = config.timeout || 15000;
    this.cache = new Map();
  }

  buildUrl(endpoint, registryUrl) {
    const base = registryUrl || this.defaultRegistry;
    return `${base.replace(/\/+$/, '')}/${endpoint.replace(/^\//, '')}`;
  }

  async fetch(url) {
    const parsed = new URL(url);
    const lib = parsed.protocol === 'https:' ? https : http;

    return new Promise((resolve, reject) => {
      const req = lib.get(url, { timeout: this.timeout }, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          if (res.statusCode < 200 || res.statusCode >= 300) {
            return reject(new RegistryError(`HTTP ${res.statusCode}: ${data}`, res.statusCode));
          }
          try {
            resolve(JSON.parse(data));
          } catch {
            reject(new RegistryError('Invalid JSON response from registry'));
          }
        });
      });
      req.on('error', reject);
      req.on('timeout', () => { req.destroy(); reject(new RegistryError('Request timed out')); });
    });
  }

  async fetchPackageInfo(name, registryUrl) {
    const url = this.buildUrl(`packages/${encodeURIComponent(name)}`, registryUrl);
    const cacheKey = url;
    if (this.cache.has(cacheKey)) return this.cache.get(cacheKey);

    try {
      const result = await this.fetch(url);
      this.cache.set(cacheKey, result);
      return result;
    } catch (err) {
      for (const fallback of this.fallbackRegistries) {
        try {
          return await this.fetch(this.buildUrl(`packages/${encodeURIComponent(name)}`, fallback));
        } catch {}
      }
      throw err;
    }
  }

  async fetchPackageVersion(name, version, registryUrl) {
    const info = await this.fetchPackageInfo(name, registryUrl);
    if (!info || !info.versions) return null;

    if (info.versions[version]) return info.versions[version];

    const tags = info['dist-tags'] || {};
    if (tags[version]) return info.versions[tags[version]];

    const sorted = Object.keys(info.versions).sort((a, b) => {
      const pa = a.split('.').map(Number);
      const pb = b.split('.').map(Number);
      for (let i = 0; i < 3; i++) {
        if ((pa[i] || 0) > (pb[i] || 0)) return -1;
        if ((pa[i] || 0) < (pb[i] || 0)) return 1;
      }
      return 0;
    });

    for (const v of sorted) {
      if (this.satisfies(v, version)) {
        return info.versions[v];
      }
    }
    return null;
  }

  satisfies(version, constraint) {
    if (constraint === '*') return true;
    if (/^\d+\.\d+\.\d+$/.test(constraint)) return version === constraint;
    const v = version.split('.').map(Number);
    const match = constraint.match(/^([~^><=]*)\s*(\d+\.\d+\.\d+)$/);
    if (!match) return version === constraint;
    const [, op, target] = match;
    const tv = target.split('.').map(Number);
    switch (op) {
      case '~': return v[0] === tv[0] && v[1] === tv[1];
      case '^': return v[0] === tv[0];
      case '>=': return this.compare(version, target) >= 0;
      case '<=': return this.compare(version, target) <= 0;
      case '>': return this.compare(version, target) > 0;
      case '<': return this.compare(version, target) < 0;
      default: return version === target;
    }
  }

  compare(a, b) {
    const pa = a.split('.').map(Number);
    const pb = b.split('.').map(Number);
    for (let i = 0; i < 3; i++) {
      if ((pa[i] || 0) > (pb[i] || 0)) return 1;
      if ((pa[i] || 0) < (pb[i] || 0)) return -1;
    }
    return 0;
  }

  async publishPackage(packageData, registryUrl) {
    const url = this.buildUrl('publish', registryUrl);
    return new Promise((resolve, reject) => {
      const parsed = new URL(url);
      const lib = parsed.protocol === 'https:' ? https : http;
      const body = JSON.stringify(packageData);
      const req = lib.request(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }
      }, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          if (res.statusCode < 200 || res.statusCode >= 300) {
            reject(new RegistryError(`Publish failed: HTTP ${res.statusCode}`, res.statusCode));
          } else {
            resolve(JSON.parse(data));
          }
        });
      });
      req.on('error', reject);
      req.write(body);
      req.end();
    });
  }

  async searchPackages(query, registryUrl) {
    const url = this.buildUrl(`search?q=${encodeURIComponent(query)}`, registryUrl);
    return this.fetch(url);
  }
}

module.exports = { RegistryClient, RegistryError };

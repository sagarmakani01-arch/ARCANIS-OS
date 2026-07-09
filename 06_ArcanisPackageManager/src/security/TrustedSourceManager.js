'use strict';

const fs = require('fs');
const path = require('path');

class TrustedSourceManager {
  constructor(sources = []) {
    this.trustedSources = new Set(sources);
    this.builtinSources = new Set([
      'https://registry.arcanis.dev',
      'https://packages.arcanis.org'
    ]);
  }

  async isTrusted(source) {
    if (!source) return false;
    const normalized = source.replace(/\/+$/, '');
    if (this.trustedSources.has(normalized)) return true;
    if (this.builtinSources.has(normalized)) return true;
    for (const trusted of this.trustedSources) {
      if (normalized.startsWith(trusted)) return true;
    }
    return false;
  }

  addSource(source) {
    const normalized = source.replace(/\/+$/, '');
    this.trustedSources.add(normalized);
    return { source: normalized, added: true };
  }

  removeSource(source) {
    const normalized = source.replace(/\/+$/, '');
    if (this.builtinSources.has(normalized)) {
      return { source: normalized, removed: false, error: 'Cannot remove built-in source' };
    }
    const existed = this.trustedSources.delete(normalized);
    return { source: normalized, removed: existed };
  }

  listSources() {
    return {
      builtin: [...this.builtinSources],
      user: [...this.trustedSources].filter(s => !this.builtinSources.has(s)),
      all: [...this.builtinSources, ...this.trustedSources]
    };
  }

  async verifySourceIntegrity(source) {
    try {
      const https = require('https');
      const { URL } = require('url');
      const parsed = new URL(source);
      return new Promise((resolve) => {
        const req = https.get(`${source.replace(/\/+$/, '')}/.well-known/arcanis.txt`, { timeout: 5000 }, (res) => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => {
            resolve(data.includes('arcanis-registry'));
          });
        });
        req.on('error', () => resolve(false));
        req.on('timeout', () => { req.destroy(); resolve(false); });
      });
    } catch {
      return false;
    }
  }

  async addAndVerify(source) {
    this.addSource(source);
    const verified = await this.verifySourceIntegrity(source);
    if (!verified) {
      this.removeSource(source);
      return { source, added: false, verified: false, reason: 'Source verification failed' };
    }
    return { source, added: true, verified: true };
  }
}

module.exports = { TrustedSourceManager };

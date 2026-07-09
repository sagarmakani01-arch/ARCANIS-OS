'use strict';

class PermissionManager {
  constructor(config = {}) {
    this.defaultPolicy = config.defaultPolicy || 'ask';
    this.allowedScopes = config.allowedScopes || [];
    this.grantedPermissions = new Map();
    this.pendingRequests = [];
  }

  async requestPermission(action, reason, options = {}) {
    const key = `${action}:${reason}`;
    if (this.grantedPermissions.has(key)) {
      return this.grantedPermissions.get(key);
    }

    const policy = options.policy || this.defaultPolicy;

    switch (policy) {
      case 'allow':
        this.grantedPermissions.set(key, true);
        return true;

      case 'deny':
        this.grantedPermissions.set(key, false);
        return false;

      case 'ask': {
        const result = await this.promptUser(action, reason);
        this.grantedPermissions.set(key, result);
        return result;
      }

      default:
        return false;
    }
  }

  async promptUser(action, reason) {
    if (process.stdout.isTTY) {
      return new Promise((resolve) => {
        const rl = require('readline').createInterface({
          input: process.stdin,
          output: process.stdout
        });
        rl.question(
          `\n  Arcanis requires permission to: ${action}\n  Reason: ${reason}\n  Allow? (y/N) `,
          (answer) => {
            rl.close();
            resolve(answer.toLowerCase() === 'y' || answer.toLowerCase() === 'yes');
          }
        );
      });
    }
    return false;
  }

  checkScope(packageName) {
    if (this.allowedScopes.length === 0) return true;
    return this.allowedScopes.some(scope => packageName.startsWith(scope));
  }

  grantPermission(action, reason) {
    const key = `${action}:${reason}`;
    this.grantedPermissions.set(key, true);
  }

  revokePermission(action, reason) {
    const key = `${action}:${reason}`;
    this.grantedPermissions.delete(key);
  }

  listPermissions() {
    const result = [];
    for (const [key, granted] of this.grantedPermissions) {
      const [action, ...reasonParts] = key.split(':');
      result.push({ action, reason: reasonParts.join(':'), granted });
    }
    return result;
  }

  setDefaultPolicy(policy) {
    if (!['allow', 'deny', 'ask'].includes(policy)) {
      throw new Error(`Invalid policy: ${policy}. Must be allow, deny, or ask`);
    }
    this.defaultPolicy = policy;
  }
}

module.exports = { PermissionManager };

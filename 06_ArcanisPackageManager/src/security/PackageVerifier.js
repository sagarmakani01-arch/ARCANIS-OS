'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

class PackageVerifier {
  async verify(packagePath) {
    const manifestPath = path.join(packagePath, 'arcanis.json');
    let manifest;
    try {
      manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
    } catch {
      return { valid: false, errors: ['Missing or invalid manifest'] };
    }

    const errors = [];
    const warnings = [];

    if (manifest.signature) {
      const valid = this.verifySignature(manifest);
      if (!valid) {
        errors.push('Package signature verification failed');
      }
    } else {
      warnings.push('Package is not signed');
    }

    if (manifest.checksums) {
      const checksumErrors = this.verifyChecksums(packagePath, manifest.checksums);
      errors.push(...checksumErrors);
    } else {
      warnings.push('No checksums to verify');
    }

    if (manifest.version && !/^\d+\.\d+\.\d+$/.test(manifest.version)) {
      errors.push('Invalid version format in manifest');
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      manifest
    };
  }

  verifySignature(manifest) {
    const { signature, ...data } = manifest;
    if (!signature || !signature.value || !signature.publicKey) {
      return false;
    }
    try {
      const verifier = crypto.createVerify('SHA256');
      verifier.update(JSON.stringify(data));
      return verifier.verify(signature.publicKey, signature.value, 'base64');
    } catch {
      return false;
    }
  }

  verifyChecksums(packagePath, checksums) {
    const errors = [];
    for (const [filePath, expectedHash] of Object.entries(checksums)) {
      const fullPath = path.join(packagePath, filePath);
      try {
        const content = fs.readFileSync(fullPath);
        const actualHash = crypto.createHash('sha256').update(content).digest('hex');
        if (actualHash !== expectedHash) {
          errors.push(`Checksum mismatch for ${filePath}: expected ${expectedHash}, got ${actualHash}`);
        }
      } catch {
        errors.push(`Cannot read file for checksum: ${filePath}`);
      }
    }
    return errors;
  }

  generateChecksums(packagePath) {
    const checksums = {};
    const entries = this.walkDirectory(packagePath);
    for (const entry of entries) {
      const relativePath = path.relative(packagePath, entry);
      if (relativePath === 'arcanis.json') continue;
      const content = fs.readFileSync(entry);
      checksums[relativePath] = crypto.createHash('sha256').update(content).digest('hex');
    }
    return checksums;
  }

  walkDirectory(dir) {
    const results = [];
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        results.push(...this.walkDirectory(fullPath));
      } else {
        results.push(fullPath);
      }
    }
    return results;
  }

  signPackage(packagePath, privateKey) {
    const manifestPath = path.join(packagePath, 'arcanis.json');
    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));

    manifest.checksums = this.generateChecksums(packagePath);

    const signer = crypto.createSign('SHA256');
    signer.update(JSON.stringify({ ...manifest, signature: undefined }));
    manifest.signature = {
      value: signer.sign(privateKey, 'base64'),
      publicKey: crypto.createPublicKey(privateKey).export({ type: 'spki', format: 'pem' }).toString(),
      algorithm: 'SHA256',
      timestamp: new Date().toISOString()
    };

    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf-8');
    return manifest;
  }
}

module.exports = { PackageVerifier };

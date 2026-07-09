const { PackageVerifier } = require('../src/security/PackageVerifier');
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');

describe('PackageVerifier', () => {
  let verifier;
  let tmpDir;

  beforeEach(() => {
    verifier = new PackageVerifier();
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'verifier-test-'));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('verify', () => {
    test('fails on missing manifest', async () => {
      const result = await verifier.verify(tmpDir);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing or invalid manifest');
    });

    test('warns when package is not signed', async () => {
      fs.writeFileSync(path.join(tmpDir, 'arcanis.json'), JSON.stringify({
        name: 'test', version: '1.0.0'
      }));
      const result = await verifier.verify(tmpDir);
      expect(result.warnings).toContain('Package is not signed');
    });

    test('warns when no checksums', async () => {
      fs.writeFileSync(path.join(tmpDir, 'arcanis.json'), JSON.stringify({
        name: 'test', version: '1.0.0'
      }));
      const result = await verifier.verify(tmpDir);
      expect(result.warnings).toContain('No checksums to verify');
    });

    test('validates checksums', async () => {
      const content = 'hello world';
      const hash = crypto.createHash('sha256').update(content).digest('hex');
      fs.writeFileSync(path.join(tmpDir, 'arcanis.json'), JSON.stringify({
        name: 'test', version: '1.0.0',
        checksums: { 'index.js': hash }
      }));
      fs.writeFileSync(path.join(tmpDir, 'index.js'), content);

      const result = await verifier.verify(tmpDir);
      expect(result.valid).toBe(true);
    });

    test('detects checksum mismatch', async () => {
      fs.writeFileSync(path.join(tmpDir, 'arcanis.json'), JSON.stringify({
        name: 'test', version: '1.0.0',
        checksums: { 'index.js': 'wronghash' }
      }));
      fs.writeFileSync(path.join(tmpDir, 'index.js'), 'content');

      const result = await verifier.verify(tmpDir);
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.includes('Checksum mismatch'))).toBe(true);
    });

    test('detects invalid version format', async () => {
      fs.writeFileSync(path.join(tmpDir, 'arcanis.json'), JSON.stringify({
        name: 'test', version: '1.0'
      }));

      const result = await verifier.verify(tmpDir);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Invalid version format in manifest');
    });
  });

  describe('generateChecksums', () => {
    test('generates checksums for all files except manifest', () => {
      fs.writeFileSync(path.join(tmpDir, 'arcanis.json'), '{}');
      fs.writeFileSync(path.join(tmpDir, 'index.js'), 'code');
      fs.writeFileSync(path.join(tmpDir, 'style.css'), 'css');

      const checksums = verifier.generateChecksums(tmpDir);
      expect(checksums['index.js']).toBeDefined();
      expect(checksums['style.css']).toBeDefined();
      expect(checksums['arcanis.json']).toBeUndefined();
    });
  });

  describe('signPackage', () => {
    test('signs a package with a private key', () => {
      const { privateKey } = crypto.generateKeyPairSync('rsa', {
        modulusLength: 2048,
        privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
      });

      fs.writeFileSync(path.join(tmpDir, 'arcanis.json'), JSON.stringify({
        name: 'test', version: '1.0.0'
      }));
      fs.writeFileSync(path.join(tmpDir, 'index.js'), 'code');

      const manifest = verifier.signPackage(tmpDir, privateKey);
      expect(manifest.signature).toBeDefined();
      expect(manifest.signature.algorithm).toBe('SHA256');
      expect(manifest.checksums).toBeDefined();
      expect(manifest.checksums['index.js']).toBeDefined();
    });
  });
});

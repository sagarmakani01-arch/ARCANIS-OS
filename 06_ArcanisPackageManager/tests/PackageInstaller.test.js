const { PackageInstaller } = require('../src/core/PackageInstaller');
const fs = require('fs');
const path = require('path');
const os = require('os');

describe('PackageInstaller', () => {
  let installer;
  let tmpDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'arcanis-test-'));
    installer = new PackageInstaller({
      installRoot: tmpDir,
      modulesDir: 'modules'
    });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe('getInstallPath', () => {
    test('returns correct path', () => {
      const p = installer.getInstallPath('my-package');
      expect(p).toBe(path.join(tmpDir, 'modules', 'my-package'));
    });
  });

  describe('installPackage', () => {
    test('installs a package with files', async () => {
      const pkg = {
        name: 'test-pkg',
        version: '1.0.0',
        manifest: {
          description: 'Test package',
          files: { 'index.js': 'console.log("hello");' }
        }
      };

      const result = await installer.installPackage(pkg);
      expect(result.status).toBe('installed');
      expect(result.name).toBe('test-pkg');

      const indexPath = path.join(tmpDir, 'modules', 'test-pkg', 'index.js');
      expect(fs.readFileSync(indexPath, 'utf-8')).toBe('console.log("hello");');
    });

    test('writes arcanis.json manifest', async () => {
      const pkg = {
        name: 'test-pkg',
        version: '1.0.0',
        manifest: { description: 'Test' },
        dependencies: {
          dep: { version: '1.0.0' }
        }
      };

      await installer.installPackage(pkg);
      const manifest = JSON.parse(
        fs.readFileSync(path.join(tmpDir, 'modules', 'test-pkg', 'arcanis.json'), 'utf-8')
      );
      expect(manifest.name).toBe('test-pkg');
      expect(manifest.version).toBe('1.0.0');
      expect(manifest.dependencies).toEqual({ dep: '1.0.0' });
    });

    test('skips if already installed and not force', async () => {
      const pkg = { name: 'test-pkg', version: '1.0.0', manifest: { description: 'T' } };
      await installer.installPackage(pkg);
      const result = await installer.installPackage(pkg, { force: false });
      expect(result.status).toBe('already-installed');
    });

    test('force reinstalls', async () => {
      const pkg = { name: 'test-pkg', version: '1.0.0', manifest: { description: 'T', files: { 'a.txt': 'v1' } } };
      await installer.installPackage(pkg);

      const pkg2 = { name: 'test-pkg', version: '1.0.0', manifest: { description: 'T', files: { 'a.txt': 'v2' } } };
      const result = await installer.installPackage(pkg2, { force: true });
      expect(result.status).toBe('installed');
    });

    test('handles base64 encoded files', async () => {
      const content = 'binary data here';
      const base64 = Buffer.from(content).toString('base64');
      const pkg = {
        name: 'bin-pkg',
        version: '1.0.0',
        manifest: { description: 'T', files: { 'data.bin': `base64:${base64}` } }
      };

      await installer.installPackage(pkg);
      const data = fs.readFileSync(path.join(tmpDir, 'modules', 'bin-pkg', 'data.bin'));
      expect(data.toString()).toBe(content);
    });

    test('handles nested file directories', async () => {
      const pkg = {
        name: 'nested',
        version: '1.0.0',
        manifest: {
          description: 'T',
          files: { 'src/utils/helper.js': 'module.exports = {};' }
        }
      };

      await installer.installPackage(pkg);
      const p = path.join(tmpDir, 'modules', 'nested', 'src', 'utils', 'helper.js');
      expect(fs.existsSync(p)).toBe(true);
    });
  });

  describe('remove', () => {
    test('removes installed package', async () => {
      const pkg = { name: 'to-remove', version: '1.0.0', manifest: { description: 'T' } };
      await installer.installPackage(pkg);
      const result = await installer.remove('to-remove');
      expect(result.status).toBe('removed');
      expect(fs.existsSync(path.join(tmpDir, 'modules', 'to-remove'))).toBe(false);
    });

    test('returns not-found for missing package', async () => {
      const result = await installer.remove('nonexistent');
      expect(result.status).toBe('not-found');
    });
  });

  describe('listInstalled', () => {
    test('lists installed packages', async () => {
      await installer.installPackage({ name: 'a', version: '1.0.0', manifest: { description: 'A' } });
      await installer.installPackage({ name: 'b', version: '2.0.0', manifest: { description: 'B' } });
      const list = await installer.listInstalled();
      expect(list).toHaveLength(2);
      expect(list.map(p => p.name)).toContain('a');
      expect(list.map(p => p.name)).toContain('b');
    });

    test('returns empty for empty modules dir', async () => {
      const list = await installer.listInstalled();
      expect(list).toEqual([]);
    });
  });

  describe('install (tree)', () => {
    test('installs a dependency tree', async () => {
      const tree = {
        name: 'root',
        version: '1.0.0',
        manifest: { description: 'Root' },
        dependencies: {
          child: {
            name: 'child',
            version: '1.0.0',
            manifest: { description: 'Child' },
            dependencies: {}
          }
        }
      };

      const results = await installer.install(tree);
      expect(results).toHaveLength(2);
      expect(results.map(r => r.name)).toContain('root');
      expect(results.map(r => r.name)).toContain('child');
    });
  });
});

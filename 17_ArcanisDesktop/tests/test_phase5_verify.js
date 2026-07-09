const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

let passed = 0;
let failed = 0;
function test(name, fn) {
  try { fn(); passed++; console.log(`  ✓ ${name}`); }
  catch (e) { failed++; console.log(`  ✗ ${name}`); console.log(`    ${e.message}`); }
}
function expect(v) {
  return {
    toBe(e) { if (v !== e) throw new Error(`Expected ${JSON.stringify(e)}, got ${JSON.stringify(v)}`); },
    toBeTruthy() { if (!v) throw new Error(`Expected truthy, got ${JSON.stringify(v)}`); },
    toBeGreaterThan(n) { if (!(v > n)) throw new Error(`${v} not > ${n}`); },
    toContain(s) { if (!v.includes(s)) throw new Error(`Expected "${v}" to contain "${s}"`); },
  };
}

const BASE = path.resolve(__dirname, '..', '..');

// ===== ArcanisKernel =====
console.log('\n=== ArcanisKernel ===');
test('kernel has kernel.c', () => {
  expect(fs.existsSync(path.join(BASE, '18_ArcanisKernel', 'src', 'kernel', 'kernel.c'))).toBeTruthy();
});
test('kernel has VGA driver', () => {
  expect(fs.existsSync(path.join(BASE, '18_ArcanisKernel', 'src', 'drivers', 'vga.c'))).toBeTruthy();
});
test('kernel has keyboard driver', () => {
  expect(fs.existsSync(path.join(BASE, '18_ArcanisKernel', 'src', 'drivers', 'keyboard.c'))).toBeTruthy();
});
test('kernel has timer driver', () => {
  expect(fs.existsSync(path.join(BASE, '18_ArcanisKernel', 'src', 'drivers', 'timer.c'))).toBeTruthy();
});
test('kernel has process scheduler', () => {
  expect(fs.existsSync(path.join(BASE, '18_ArcanisKernel', 'src', 'process', 'scheduler.c'))).toBeTruthy();
});
test('kernel has memory manager (pmm)', () => {
  expect(fs.existsSync(path.join(BASE, '18_ArcanisKernel', 'src', 'memory', 'pmm.c'))).toBeTruthy();
});
test('kernel has virtual memory (vmm)', () => {
  expect(fs.existsSync(path.join(BASE, '18_ArcanisKernel', 'src', 'memory', 'vmm.c'))).toBeTruthy();
});
test('kernel has heap allocator', () => {
  expect(fs.existsSync(path.join(BASE, '18_ArcanisKernel', 'src', 'memory', 'heap.c'))).toBeTruthy();
});
test('kernel has IDT', () => {
  expect(fs.existsSync(path.join(BASE, '18_ArcanisKernel', 'src', 'interrupts', 'idt.c'))).toBeTruthy();
});
test('kernel has syscalls', () => {
  expect(fs.existsSync(path.join(BASE, '18_ArcanisKernel', 'src', 'syscall', 'syscall.c'))).toBeTruthy();
});
test('kernel has VFS', () => {
  expect(fs.existsSync(path.join(BASE, '18_ArcanisKernel', 'src', 'fs', 'vfs.c'))).toBeTruthy();
});
test('kernel has test suite', () => {
  expect(fs.existsSync(path.join(BASE, '18_ArcanisKernel', 'tests', 'test_suite.c'))).toBeTruthy();
});
test('kernel has Makefile', () => {
  expect(fs.existsSync(path.join(BASE, '18_ArcanisKernel', 'Makefile'))).toBeTruthy();
});
test('kernel has linker script', () => {
  expect(fs.existsSync(path.join(BASE, '18_ArcanisKernel', 'linker.ld'))).toBeTruthy();
});

// ===== ArcanisDrivers =====
console.log('\n=== ArcanisDrivers ===');
test('drivers has core driver framework', () => {
  expect(fs.existsSync(path.join(BASE, '19_ArcanisDrivers', 'ArcanisDrivers', 'src', 'core', 'driver.c'))).toBeTruthy();
});
test('drivers has display driver', () => {
  expect(fs.existsSync(path.join(BASE, '19_ArcanisDrivers', 'ArcanisDrivers', 'src', 'drivers', 'display.c'))).toBeTruthy();
});
test('drivers has keyboard driver', () => {
  expect(fs.existsSync(path.join(BASE, '19_ArcanisDrivers', 'ArcanisDrivers', 'src', 'drivers', 'keyboard.c'))).toBeTruthy();
});
test('drivers has mouse driver', () => {
  expect(fs.existsSync(path.join(BASE, '19_ArcanisDrivers', 'ArcanisDrivers', 'src', 'drivers', 'mouse.c'))).toBeTruthy();
});
test('drivers has network driver', () => {
  expect(fs.existsSync(path.join(BASE, '19_ArcanisDrivers', 'ArcanisDrivers', 'src', 'drivers', 'network.c'))).toBeTruthy();
});
test('drivers has storage driver', () => {
  expect(fs.existsSync(path.join(BASE, '19_ArcanisDrivers', 'ArcanisDrivers', 'src', 'drivers', 'storage.c'))).toBeTruthy();
});
test('drivers has HAL', () => {
  expect(fs.existsSync(path.join(BASE, '19_ArcanisDrivers', 'ArcanisDrivers', 'src', 'hal', 'hal.c'))).toBeTruthy();
});
test('drivers has PnP manager', () => {
  expect(fs.existsSync(path.join(BASE, '19_ArcanisDrivers', 'ArcanisDrivers', 'src', 'pnp', 'pnp.c'))).toBeTruthy();
});
test('drivers has test suite', () => {
  expect(fs.existsSync(path.join(BASE, '19_ArcanisDrivers', 'ArcanisDrivers', 'tests', 'test_main.c'))).toBeTruthy();
});

// ===== ArcanisFileSystem =====
console.log('\n=== ArcanisFileSystem ===');
test('filesystem has core filesystem module', () => {
  expect(fs.existsSync(path.join(BASE, '20_ArcanisFileSystem', 'src', 'core', 'filesystem.py'))).toBeTruthy();
});
test('filesystem has inode implementation', () => {
  expect(fs.existsSync(path.join(BASE, '20_ArcanisFileSystem', 'src', 'core', 'inode.py'))).toBeTruthy();
});
test('filesystem has block device', () => {
  expect(fs.existsSync(path.join(BASE, '20_ArcanisFileSystem', 'src', 'core', 'blocks.py'))).toBeTruthy();
});
test('filesystem has directory support', () => {
  expect(fs.existsSync(path.join(BASE, '20_ArcanisFileSystem', 'src', 'core', 'directory.py'))).toBeTruthy();
});
test('filesystem has metadata', () => {
  expect(fs.existsSync(path.join(BASE, '20_ArcanisFileSystem', 'src', 'core', 'metadata.py'))).toBeTruthy();
});
test('filesystem has permissions/ACL', () => {
  expect(fs.existsSync(path.join(BASE, '20_ArcanisFileSystem', 'src', 'permissions', 'acl.py'))).toBeTruthy();
});
test('filesystem has AI search', () => {
  expect(fs.existsSync(path.join(BASE, '20_ArcanisFileSystem', 'src', 'ai', 'search.py'))).toBeTruthy();
});
test('filesystem has tests', () => {
  expect(fs.existsSync(path.join(BASE, '20_ArcanisFileSystem', 'tests'))).toBeTruthy();
});
test('filesystem has setup.py', () => {
  expect(fs.existsSync(path.join(BASE, '20_ArcanisFileSystem', 'setup.py'))).toBeTruthy();
});

// ===== ArcanisNetwork =====
console.log('\n=== ArcanisNetwork ===');
test('network has TCP', () => {
  expect(fs.existsSync(path.join(BASE, '21_ArcanisNetwork', 'src', 'core', 'tcp.ts'))).toBeTruthy();
});
test('network has UDP', () => {
  expect(fs.existsSync(path.join(BASE, '21_ArcanisNetwork', 'src', 'core', 'udp.ts'))).toBeTruthy();
});
test('network has IP layer', () => {
  expect(fs.existsSync(path.join(BASE, '21_ArcanisNetwork', 'src', 'core', 'ip.ts'))).toBeTruthy();
});
test('network has connection manager', () => {
  expect(fs.existsSync(path.join(BASE, '21_ArcanisNetwork', 'src', 'core', 'connection.ts'))).toBeTruthy();
});
test('network has network stack', () => {
  expect(fs.existsSync(path.join(BASE, '21_ArcanisNetwork', 'src', 'core', 'stack.ts'))).toBeTruthy();
});
test('network has AI integration', () => {
  expect(fs.existsSync(path.join(BASE, '21_ArcanisNetwork', 'src', 'ai', 'index.ts'))).toBeTruthy();
});
test('network has cloud integration', () => {
  expect(fs.existsSync(path.join(BASE, '21_ArcanisNetwork', 'src', 'cloud', 'index.ts'))).toBeTruthy();
});
test('network has package.json', () => {
  expect(fs.existsSync(path.join(BASE, '21_ArcanisNetwork', 'package.json'))).toBeTruthy();
});
test('network has vitest config', () => {
  expect(fs.existsSync(path.join(BASE, '21_ArcanisNetwork', 'vitest.config.ts'))).toBeTruthy();
});

// ===== ArcanisSecurity =====
console.log('\n=== ArcanisSecurity ===');
test('security has encryption module', () => {
  expect(fs.existsSync(path.join(BASE, '22_ArcanisSecurity', 'arcanis_security', 'encryption.py'))).toBeTruthy();
});
test('security has audit module', () => {
  expect(fs.existsSync(path.join(BASE, '22_ArcanisSecurity', 'arcanis_security', 'audit.py'))).toBeTruthy();
});
test('security has access control', () => {
  expect(fs.existsSync(path.join(BASE, '22_ArcanisSecurity', 'arcanis_security', 'access_control.py'))).toBeTruthy();
});
test('security has policy engine', () => {
  expect(fs.existsSync(path.join(BASE, '22_ArcanisSecurity', 'arcanis_security', 'policy.py'))).toBeTruthy();
});
test('security has sandbox', () => {
  expect(fs.existsSync(path.join(BASE, '22_ArcanisSecurity', 'arcanis_security', 'sandbox.py'))).toBeTruthy();
});
test('security has threat detection', () => {
  expect(fs.existsSync(path.join(BASE, '22_ArcanisSecurity', 'arcanis_security', 'threat_detection.py'))).toBeTruthy();
});
test('security has 209 passing tests', () => {
  const r = execSync('cd "C:\\Users\\Sagar Makani\\OneDrive\\ARCANIS LAB\\22_ArcanisSecurity" && python -m pytest tests/ -q --tb=no 2>&1', { encoding: 'utf-8', timeout: 60000 });
  expect(r).toContain('209 passed');
});

// ===== ArcanisDesktop (source exists) =====
console.log('\n=== ArcanisDesktop ===');
test('desktop has main.js', () => {
  expect(fs.existsSync(path.join(BASE, '17_ArcanisDesktop', 'js', 'main.js'))).toBeTruthy();
});
test('desktop has window-manager.js', () => {
  expect(fs.existsSync(path.join(BASE, '17_ArcanisDesktop', 'js', 'core', 'window-manager.js'))).toBeTruthy();
});
test('desktop has taskbar.js', () => {
  expect(fs.existsSync(path.join(BASE, '17_ArcanisDesktop', 'js', 'core', 'taskbar.js'))).toBeTruthy();
});
test('desktop has terminal app', () => {
  expect(fs.existsSync(path.join(BASE, '17_ArcanisDesktop', 'js', 'apps', 'terminal.js'))).toBeTruthy();
});
test('desktop has AI center', () => {
  expect(fs.existsSync(path.join(BASE, '17_ArcanisDesktop', 'js', 'ai', 'ai-center.js'))).toBeTruthy();
});
test('desktop has existing test suite (109 passing)', () => {
  let r = '';
  try { r = execSync('cd "C:\\Users\\Sagar Makani\\OneDrive\\ARCANIS LAB\\17_ArcanisDesktop" && node tests/test_desktop.js 2>&1', { encoding: 'utf-8', timeout: 30000 }); }
  catch (e) { r = e.stdout || e.message; }
  expect(r).toContain('109 passed');
});

console.log('\n' + '='.repeat(50));
console.log(`Results: ${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);

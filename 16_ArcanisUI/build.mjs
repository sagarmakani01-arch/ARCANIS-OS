import { writeFileSync, mkdirSync, existsSync, readdirSync, statSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const srcDir = join(__dirname, 'src');
const distDir = join(__dirname, 'dist');

function ensureDir(dir) {
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

function copyFiles(src, dest) {
  ensureDir(dest);
  for (const entry of readdirSync(src)) {
    const srcPath = join(src, entry);
    const destPath = join(dest, entry);
    const stat = statSync(srcPath);
    if (stat.isDirectory()) {
      copyFiles(srcPath, destPath);
    } else if (entry.endsWith('.ts') && !entry.endsWith('.test.ts') && !entry.endsWith('.d.ts')) {
      const content = readFileSync(srcPath, 'utf-8');
      const jsContent = content
        .replace(/import\s+\{([^}]+)\}\s+from\s+['"]([^'"]+)['"]\s*;/g, (_, imports, path) => {
          const cleanPath = path.replace(/\.ts$/, '.js');
          return `import {${imports}} from '${cleanPath}';`;
        })
        .replace(/export\s+\{([^}]+)\}\s+from\s+['"]([^'"]+)['"]\s*;/g, (_, exports, path) => {
          const cleanPath = path.replace(/\.ts$/, '.js');
          return `export {${exports}} from '${cleanPath}';`;
        })
        .replace(/export\s+default\s+/g, 'export default ')
        .replace(/export\s+type\s+/g, 'export type ')
        .replace(/export\s+(interface|type)\s+/g, 'export $1 ');
      writeFileSync(destPath.replace(/\.ts$/, '.js'), jsContent);
    }
  }
}

console.log('Building ArcanisUI...');
ensureDir(distDir);
copyFiles(srcDir, distDir);
console.log('Build complete! Output in dist/');

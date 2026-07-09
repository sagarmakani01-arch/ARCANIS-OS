'use strict';

const fs = require('fs');
const path = require('path');

function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
  return dirPath;
}

function readJSON(filePath) {
  try {
    const data = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(data);
  } catch {
    return null;
  }
}

function writeJSON(filePath, data, pretty = true) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, JSON.stringify(data, null, pretty ? 2 : 0), 'utf-8');
  return filePath;
}

function copyRecursive(src, dest) {
  ensureDir(dest);
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyRecursive(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function findManifest(dir) {
  let current = path.resolve(dir);
  while (true) {
    const manifestPath = path.join(current, 'arcanis.json');
    if (fs.existsSync(manifestPath)) return manifestPath;
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
}

function isGlobPattern(str) {
  return /[\*\?\[\]{}]/.test(str);
}

module.exports = { ensureDir, readJSON, writeJSON, copyRecursive, findManifest, isGlobPattern };

"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.IncrementalCompiler = void 0;
const crypto = __importStar(require("crypto"));
const fs = __importStar(require("fs"));
class IncrementalCompiler {
    constructor(cachePath) {
        this.cache = {
            version: '0.1.0',
            entries: new Map(),
        };
        this.cachePath = cachePath || '.arcanis-cache.json';
        this.load();
    }
    hashContent(content) {
        return crypto.createHash('sha256').update(content).digest('hex');
    }
    isCached(sourceId, content, stage) {
        const hash = this.hashContent(content);
        const entry = this.cache.entries.get(sourceId);
        if (!entry)
            return false;
        if (entry.hash !== hash)
            return false;
        if (stage && entry.stage !== stage)
            return false;
        return true;
    }
    updateCache(sourceId, content, dependencies, stage) {
        const hash = this.hashContent(content);
        const outputHash = this.hashContent(hash + dependencies.join(','));
        this.cache.entries.set(sourceId, {
            hash,
            dependencies,
            outputHash,
            stage,
            timestamp: Date.now(),
        });
        this.save();
    }
    invalidate(sourceId) {
        this.cache.entries.delete(sourceId);
        for (const [key, entry] of this.cache.entries) {
            if (entry.dependencies.includes(sourceId)) {
                this.cache.entries.delete(key);
            }
        }
        this.save();
    }
    getCachedOutput(sourceId) {
        const cacheDir = '.arcanis-cache';
        const cacheFile = `${cacheDir}/${sourceId.replace(/[^a-zA-Z0-9_-]/g, '_')}.out`;
        try {
            return fs.readFileSync(cacheFile, 'utf-8');
        }
        catch {
            return null;
        }
    }
    load() {
        try {
            const raw = fs.readFileSync(this.cachePath, 'utf-8');
            const parsed = JSON.parse(raw);
            this.cache.version = parsed.version;
            this.cache.entries = new Map(Object.entries(parsed.entries));
        }
        catch {
            this.cache.entries = new Map();
        }
    }
    save() {
        const obj = {
            version: this.cache.version,
            entries: Object.fromEntries(this.cache.entries),
        };
        try {
            fs.writeFileSync(this.cachePath, JSON.stringify(obj, null, 2));
        }
        catch {
            // Silently fail if we can't write cache
        }
    }
    clear() {
        this.cache.entries.clear();
        this.save();
    }
}
exports.IncrementalCompiler = IncrementalCompiler;
//# sourceMappingURL=incremental.js.map
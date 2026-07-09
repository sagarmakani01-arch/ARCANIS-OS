"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PluginManager = void 0;
class PluginManager {
    constructor() {
        this.plugins = [];
    }
    register(plugin) {
        if (this.plugins.find((p) => p.name === plugin.name)) {
            throw new Error(`Plugin '${plugin.name}' is already registered`);
        }
        this.plugins.push(plugin);
    }
    unregister(name) {
        this.plugins = this.plugins.filter((p) => p.name !== name);
    }
    getPlugins() {
        return [...this.plugins];
    }
    runHook(hookName, ...args) {
        let result = undefined;
        for (const plugin of this.plugins) {
            const hook = plugin.hooks[hookName];
            if (hook) {
                try {
                    result = hook(...args);
                    if (result !== undefined) {
                        args = [result];
                    }
                }
                catch (e) {
                    console.error(`Plugin '${plugin.name}' failed on hook '${hookName}':`, e);
                }
            }
        }
        return result;
    }
    runStageHooks(stage, compiler) {
        for (const plugin of this.plugins) {
            plugin.hooks.beforeStage?.(stage, compiler);
        }
    }
    clear() {
        this.plugins = [];
    }
}
exports.PluginManager = PluginManager;
//# sourceMappingURL=plugin.js.map
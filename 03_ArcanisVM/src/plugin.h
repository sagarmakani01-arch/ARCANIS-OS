#ifndef ARCANIS_PLUGIN_H
#define ARCANIS_PLUGIN_H

#include "vm.h"
#include <stdint.h>
#include <stdbool.h>

typedef struct Plugin {
    char* name;
    char* version;
    char* description;
    bool (*onLoad)(struct Plugin* plugin, VM* vm);
    void (*onUnload)(struct Plugin* plugin, VM* vm);
    bool (*onImport)(struct Plugin* plugin, VM* vm, ObjString* moduleName, Value* result);
    void* userData;
    struct Plugin* next;
} Plugin;

typedef struct PluginSystem {
    Plugin* plugins;
    uint32_t pluginCount;
    uint32_t maxPlugins;
    char* pluginPath;
    void (*onPluginLoad)(struct PluginSystem* ps, Plugin* plugin);
    void (*onPluginUnload)(struct PluginSystem* ps, Plugin* plugin);
} PluginSystem;

void initPluginSystem(PluginSystem* ps);
void freePluginSystem(PluginSystem* ps);
bool pluginRegister(PluginSystem* ps, Plugin* plugin);
bool pluginUnregister(PluginSystem* ps, const char* name);
bool pluginLoad(PluginSystem* ps, VM* vm, const char* path);
void pluginUnloadAll(PluginSystem* ps, VM* vm);
bool pluginImport(PluginSystem* ps, VM* vm, ObjString* moduleName, Value* result);
Plugin* pluginFind(PluginSystem* ps, const char* name);
void pluginSetPath(PluginSystem* ps, const char* path);

#endif

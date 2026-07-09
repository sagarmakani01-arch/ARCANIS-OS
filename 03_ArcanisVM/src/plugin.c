#include "plugin.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#ifdef _WIN32
#include <windows.h>
typedef HMODULE LibraryHandle;
#define LoadLibraryEx(name) LoadLibraryA(name)
#define GetProcAddressEx(handle, name) GetProcAddress(handle, name)
#define FreeLibraryEx(handle) FreeLibrary(handle)
#else
#include <dlfcn.h>
typedef void* LibraryHandle;
#define LoadLibraryEx(name) dlopen(name, RTLD_NOW | RTLD_LOCAL)
#define GetProcAddressEx(handle, name) dlsym(handle, name)
#define FreeLibraryEx(handle) dlclose(handle)
#endif

void initPluginSystem(PluginSystem* ps) {
    memset(ps, 0, sizeof(PluginSystem));
    ps->plugins = NULL;
    ps->pluginCount = 0;
    ps->maxPlugins = 256;
    ps->pluginPath = NULL;
    ps->onPluginLoad = NULL;
    ps->onPluginUnload = NULL;
}

void freePluginSystem(PluginSystem* ps) {
    Plugin* plugin = ps->plugins;
    while (plugin) {
        Plugin* next = plugin->next;
        free(plugin->name);
        free(plugin->version);
        free(plugin->description);
        free(plugin);
        plugin = next;
    }
    ps->plugins = NULL;
    ps->pluginCount = 0;
    free(ps->pluginPath);
    ps->pluginPath = NULL;
}

bool pluginRegister(PluginSystem* ps, Plugin* plugin) {
    if (ps->pluginCount >= ps->maxPlugins) return false;
    Plugin* existing = pluginFind(ps, plugin->name);
    if (existing) return false;
    plugin->next = ps->plugins;
    ps->plugins = plugin;
    ps->pluginCount++;
    return true;
}

bool pluginUnregister(PluginSystem* ps, const char* name) {
    Plugin** prev = &ps->plugins;
    Plugin* plugin = ps->plugins;
    while (plugin) {
        if (plugin->name && strcmp(plugin->name, name) == 0) {
            *prev = plugin->next;
            free(plugin->name);
            free(plugin->version);
            free(plugin->description);
            free(plugin);
            ps->pluginCount--;
            return true;
        }
        prev = &plugin->next;
        plugin = plugin->next;
    }
    return false;
}

bool pluginLoad(PluginSystem* ps, VM* vm, const char* path) {
    LibraryHandle lib = LoadLibraryEx(path);
    if (!lib) return false;

    typedef Plugin* (*CreatePluginFn)();
    CreatePluginFn createFn = (CreatePluginFn)GetProcAddressEx(lib, "createPlugin");
    if (!createFn) {
        FreeLibraryEx(lib);
        return false;
    }

    Plugin* plugin = createFn();
    if (!plugin) {
        FreeLibraryEx(lib);
        return false;
    }

    if (!pluginRegister(ps, plugin)) {
        free(plugin);
        FreeLibraryEx(lib);
        return false;
    }

    if (plugin->onLoad && !plugin->onLoad(plugin, vm)) {
        pluginUnregister(ps, plugin->name);
        FreeLibraryEx(lib);
        return false;
    }

    if (ps->onPluginLoad) ps->onPluginLoad(ps, plugin);
    return true;
}

void pluginUnloadAll(PluginSystem* ps, VM* vm) {
    Plugin* plugin = ps->plugins;
    while (plugin) {
        if (plugin->onUnload) plugin->onUnload(plugin, vm);
        if (ps->onPluginUnload) ps->onPluginUnload(ps, plugin);
        plugin = plugin->next;
    }
    freePluginSystem(ps);
}

bool pluginImport(PluginSystem* ps, VM* vm, ObjString* moduleName, Value* result) {
    Plugin* plugin = ps->plugins;
    while (plugin) {
        if (plugin->onImport && plugin->onImport(plugin, vm, moduleName, result))
            return true;
        plugin = plugin->next;
    }
    return false;
}

Plugin* pluginFind(PluginSystem* ps, const char* name) {
    Plugin* plugin = ps->plugins;
    while (plugin) {
        if (plugin->name && strcmp(plugin->name, name) == 0)
            return plugin;
        plugin = plugin->next;
    }
    return NULL;
}

void pluginSetPath(PluginSystem* ps, const char* path) {
    free(ps->pluginPath);
    ps->pluginPath = path ? strdup(path) : NULL;
}

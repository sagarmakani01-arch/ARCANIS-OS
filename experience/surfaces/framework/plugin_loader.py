import importlib.util
import inspect
import os
import sys


def _get_base_surface():
    from .base import BaseSurface
    return BaseSurface


def discover_plugins(plugin_dir=None):
    if plugin_dir is None:
        plugin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "plugins")
    if not os.path.isdir(plugin_dir):
        os.makedirs(plugin_dir, exist_ok=True)
        return []

    BaseSurface = _get_base_surface()
    plugins = []
    for fname in sorted(os.listdir(plugin_dir)):
        if fname.endswith(".py") and not fname.startswith("_"):
            path = os.path.join(plugin_dir, fname)
            mod_name = f"plugin_{fname[:-3]}"
            spec = importlib.util.spec_from_file_location(mod_name, path)
            if spec and spec.loader:
                try:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[mod_name] = mod
                    spec.loader.exec_module(mod)
                    plugin_info = _extract_plugin_info(mod, fname, BaseSurface)
                    if plugin_info:
                        plugins.append(plugin_info)
                except Exception as e:
                    print(f"[PluginLoader] Failed to load {fname}: {e}")
    return plugins


def _extract_plugin_info(module, filename, base_cls):
    sid = getattr(module, "_surface_id", filename[:-3])
    title = getattr(module, "_title_hint", filename[:-3].replace("_", " ").title())

    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, base_cls) and obj is not base_cls:
            return {
                "name": sid,
                "title": title,
                "class": obj,
                "file": filename,
            }
    return None

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Callable, Optional

from .device import Device, DeviceType, DeviceCapabilities


class DriverRegistry:
    def __init__(self):
        self._drivers: dict[str, dict[str, Any]] = {}
        self._loaded: dict[str, Any] = {}

    def register(self, name: str, device_type: DeviceType,
                 init_fn: Callable[[Device], bool],
                 read_fn: Optional[Callable] = None,
                 write_fn: Optional[Callable] = None,
                 shutdown_fn: Optional[Callable] = None) -> None:
        self._drivers[name] = {
            "device_type": device_type,
            "init": init_fn,
            "read": read_fn,
            "write": write_fn,
            "shutdown": shutdown_fn,
        }

    def load(self, name: str, device: Device) -> bool:
        driver = self._drivers.get(name)
        if not driver:
            return False
        try:
            if driver["init"](device):
                device.driver_name = name
                device.driver_loaded = True
                device.state = "ready"
                self._loaded[name] = driver
                return True
        except Exception:
            pass
        return False

    def unload(self, name: str, device: Device) -> bool:
        driver = self._loaded.get(name)
        if not driver:
            return False
        try:
            if driver["shutdown"]:
                driver["shutdown"](device)
        except Exception:
            pass
        device.driver_name = None
        device.driver_loaded = False
        device.state = "detected"
        self._loaded.pop(name, None)
        return True

    def get_driver(self, name: str) -> Optional[dict[str, Any]]:
        return self._drivers.get(name)

    def list_drivers(self) -> list[str]:
        return list(self._drivers.keys())

    def list_loaded(self) -> list[str]:
        return list(self._loaded.keys())


class HAL:
    def __init__(self):
        self._devices: dict[str, Device] = {}
        self._drivers = DriverRegistry()
        self._event_log: list[dict[str, Any]] = []
        self._initialized = False

    def initialize(self) -> None:
        self._scan_builtin_devices()
        self._initialized = True
        self._log_event("hal_initialized", {"device_count": len(self._devices)})

    def _scan_builtin_devices(self) -> None:
        self.register_device(Device(
            name="CPU0", device_type=DeviceType.CPU,
            capabilities=DeviceCapabilities(executable=True, power_manageable=True),
            state="ready",
        ))
        self.register_device(Device(
            name="MEM0", device_type=DeviceType.MEMORY,
            capabilities=DeviceCapabilities(readable=True, writable=True),
            state="ready",
        ))
        self.register_device(Device(
            name="VGA0", device_type=DeviceType.DISPLAY,
            capabilities=DeviceCapabilities(readable=True, writable=True, interrupt_capable=True),
            io_base=0xB8000, mmio_size=0x2000, state="ready",
        ))
        self.register_device(Device(
            name="KBD0", device_type=DeviceType.INPUT,
            capabilities=DeviceCapabilities(readable=True, interrupt_capable=True),
            irq=1, io_base=0x60, state="ready",
        ))
        self.register_device(Device(
            name="TMR0", device_type=DeviceType.FIRMWARE,
            capabilities=DeviceCapabilities(interrupt_capable=True),
            irq=0, io_base=0x40, state="ready",
        ))
        self.register_device(Device(
            name="COM0", device_type=DeviceType.SERIAL,
            capabilities=DeviceCapabilities(readable=True, writable=True, interrupt_capable=True),
            irq=4, io_base=0x3F8, state="ready",
        ))

    def register_device(self, device: Device) -> None:
        self._devices[device.device_id] = device
        self._log_event("device_registered", device.to_dict())

    def unregister_device(self, device_id: str) -> bool:
        device = self._devices.pop(device_id, None)
        if device:
            self._log_event("device_unregistered", device.to_dict())
            return True
        return False

    def get_device(self, device_id: str) -> Optional[Device]:
        return self._devices.get(device_id)

    def get_devices_by_type(self, device_type: DeviceType) -> list[Device]:
        return [d for d in self._devices.values() if d.device_type == device_type]

    def get_all_devices(self) -> list[Device]:
        return list(self._devices.values())

    def probe_devices(self) -> list[Device]:
        detected: list[Device] = []
        for device in self._devices.values():
            if device.state == "detected":
                driver_name = self._auto_detect_driver(device)
                if driver_name:
                    self._drivers.load(driver_name, device)
                    detected.append(device)
        return detected

    def _auto_detect_driver(self, device: Device) -> Optional[str]:
        type_drivers = {
            DeviceType.DISPLAY: "vga_driver",
            DeviceType.INPUT: "kbd_driver",
            DeviceType.SERIAL: "serial_driver",
            DeviceType.STORAGE: "ata_driver",
            DeviceType.NETWORK: "nic_driver",
        }
        return type_drivers.get(device.device_type)

    def enumerate_bus(self, bus: str) -> list[Device]:
        return [d for d in self._devices.values() if d.bus == bus]

    def get_device_info(self, device_id: str) -> Optional[dict[str, Any]]:
        device = self._devices.get(device_id)
        if not device:
            return None
        info = device.to_dict()
        info["capabilities"] = {
            "readable": device.capabilities.readable,
            "writable": device.capabilities.writable,
            "executable": device.capabilities.executable,
            "hot_pluggable": device.capabilities.hot_pluggable,
            "interrupt_capable": device.capabilities.interrupt_capable,
        }
        info["driver_loaded"] = device.driver_loaded
        return info

    def shutdown_device(self, device_id: str) -> bool:
        device = self._devices.get(device_id)
        if not device:
            return False
        if device.driver_name:
            self._drivers.unload(device.driver_name, device)
        device.state = "shutdown"
        self._log_event("device_shutdown", {"device_id": device_id})
        return True

    def get_stats(self) -> dict[str, Any]:
        by_type = defaultdict(int)
        for d in self._devices.values():
            by_type[d.device_type.value] += 1
        return {
            "total_devices": len(self._devices),
            "by_type": dict(by_type),
            "drivers_registered": len(self._drivers.list_drivers()),
            "drivers_loaded": len(self._drivers.list_loaded()),
        }

    def _log_event(self, event: str, data: dict[str, Any]) -> None:
        self._event_log.append({
            "timestamp": time.time(),
            "event": event,
            "data": data,
        })

    def get_event_log(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._event_log[-limit:]

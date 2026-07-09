"""Universal driver model — hardware-agnostic driver interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class DriverCapability(Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    INTERRUPT = "interrupt"
    DMA = "dma"
    POWER_MANAGE = "power_manage"
    HOT_PLUG = "hot_plug"


class DriverState(Enum):
    UNLOADED = "unloaded"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    RUNNING = "running"
    SUSPENDED = "suspended"
    ERROR = "error"


@dataclass
class HardwareDescriptor:
    device_class: str = ""
    vendor_id: int = 0
    product_id: int = 0
    revision: int = 0
    io_ports: list[tuple[int, int]] = field(default_factory=list)
    memory_ranges: list[tuple[int, int]] = field(default_factory=list)
    interrupts: list[int] = field(default_factory=list)
    dma_channels: list[int] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class DriverInterface:
    name: str = ""
    version: str = "1.0"
    supported_classes: list[str] = field(default_factory=list)
    capabilities: list[DriverCapability] = field(default_factory=list)
    init: Optional[Callable] = None
    read: Optional[Callable] = None
    write: Optional[Callable] = None
    ioctl: Optional[Callable] = None
    shutdown: Optional[Callable] = None
    suspend: Optional[Callable] = None
    resume: Optional[Callable] = None


class UniversalDriverModel:
    def __init__(self):
        self._drivers: dict[str, DriverInterface] = {}
        self._bindings: dict[str, str] = {}  # device_id -> driver_name
        self._states: dict[str, DriverState] = {}
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

    def register_driver(self, driver: DriverInterface) -> None:
        self._drivers[driver.name] = driver

    def unregister_driver(self, name: str) -> bool:
        return self._drivers.pop(name, None) is not None

    def bind(self, device_id: str, driver_name: str) -> bool:
        driver = self._drivers.get(driver_name)
        if not driver:
            return False
        self._bindings[device_id] = driver_name
        self._states[device_id] = DriverState.LOADED
        if driver.init:
            try:
                driver.init()
                self._states[device_id] = DriverState.INITIALIZED
            except Exception:
                self._states[device_id] = DriverState.ERROR
                return False
        return True

    def unbind(self, device_id: str) -> bool:
        driver_name = self._bindings.pop(device_id, None)
        if not driver_name:
            return False
        driver = self._drivers.get(driver_name)
        if driver and driver.shutdown:
            try:
                driver.shutdown()
            except Exception:
                pass
        self._states.pop(device_id, None)
        return True

    def read(self, device_id: str, *args, **kwargs) -> Any:
        driver_name = self._bindings.get(device_id)
        if not driver_name:
            return None
        driver = self._drivers.get(driver_name)
        if driver and driver.read:
            return driver.read(*args, **kwargs)
        return None

    def write(self, device_id: str, *args, **kwargs) -> bool:
        driver_name = self._bindings.get(device_id)
        if not driver_name:
            return False
        driver = self._drivers.get(driver_name)
        if driver and driver.write:
            driver.write(*args, **kwargs)
            return True
        return False

    def auto_bind(self, descriptor: HardwareDescriptor) -> Optional[str]:
        for name, driver in self._drivers.items():
            if descriptor.device_class in driver.supported_classes:
                device_id = f"{descriptor.device_class}_{descriptor.vendor_id:04X}_{descriptor.product_id:04X}"
                if self.bind(device_id, name):
                    return device_id
        return None

    def get_state(self, device_id: str) -> DriverState:
        return self._states.get(device_id, DriverState.UNLOADED)

    def list_drivers(self) -> list[str]:
        return list(self._drivers.keys())

    def list_devices(self) -> list[dict[str, Any]]:
        return [{"device_id": did, "driver": dname, "state": self._states.get(did, DriverState.UNLOADED).value}
                for did, dname in self._bindings.items()]

    def get_stats(self) -> dict:
        states = {}
        for s in self._states.values():
            states[s.value] = states.get(s.value, 0) + 1
        return {
            "initialized": self._initialized,
            "drivers_registered": len(self._drivers),
            "devices_bound": len(self._bindings),
            "device_states": states,
        }

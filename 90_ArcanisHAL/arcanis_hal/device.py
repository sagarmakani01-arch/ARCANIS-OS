from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class DeviceType(Enum):
    STORAGE = "storage"
    NETWORK = "network"
    DISPLAY = "display"
    INPUT = "input"
    AUDIO = "audio"
    USB = "usb"
    SERIAL = "serial"
    GPU = "gpu"
    CPU = "cpu"
    MEMORY = "memory"
    FIRMWARE = "firmware"
    UNKNOWN = "unknown"


@dataclass
class DeviceCapabilities:
    readable: bool = True
    writable: bool = False
    executable: bool = False
    hot_pluggable: bool = False
    interrupt_capable: bool = False
    dma_capable: bool = False
    power_manageable: bool = False
    custom: dict[str, Any] = field(default_factory=dict)


@dataclass
class Device:
    device_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    device_type: DeviceType = DeviceType.UNKNOWN
    vendor_id: int = 0
    product_id: int = 0
    revision: int = 0
    bus: str = ""
    port: int = 0
    capabilities: DeviceCapabilities = field(default_factory=DeviceCapabilities)
    driver_name: Optional[str] = None
    driver_loaded: bool = False
    irq: Optional[int] = None
    io_base: Optional[int] = None
    mmio_base: Optional[int] = None
    mmio_size: Optional[int] = None
    state: str = "detected"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.device_type.value,
            "vendor_id": self.vendor_id,
            "product_id": self.product_id,
            "bus": self.bus,
            "driver": self.driver_name,
            "state": self.state,
            "irq": self.irq,
        }

"""90_ArcanisHAL — Hardware Abstraction Layer prototype.

Provides device enumeration, capability queries, and driver management
for the Arcanis kernel.
"""

__version__ = "0.1.0"

from arcanis_hal.device import Device, DeviceType, DeviceCapabilities
from arcanis_hal.hal import HAL

__all__ = ["Device", "DeviceType", "DeviceCapabilities", "HAL"]

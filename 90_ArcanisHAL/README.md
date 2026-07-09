# ArcanisHAL (90)

Hardware Abstraction Layer prototype. Device enumeration, driver registry, capability queries for kernel hardware management.

```python
from arcanis_hal import HAL
hal = HAL()
hal.initialize()
devices = hal.get_all_devices()
hal.probe_devices()
```

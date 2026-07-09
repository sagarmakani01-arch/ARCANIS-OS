import pytest

from arcanis_hal.device import Device, DeviceType, DeviceCapabilities
from arcanis_hal.hal import HAL, DriverRegistry


class TestDevice:
    def test_create(self):
        dev = Device(name="TestDev", device_type=DeviceType.STORAGE)
        assert dev.name == "TestDev"
        assert dev.device_type == DeviceType.STORAGE
        assert dev.state == "detected"

    def test_to_dict(self):
        dev = Device(name="COM0", device_type=DeviceType.SERIAL, irq=4)
        d = dev.to_dict()
        assert d["name"] == "COM0"
        assert d["type"] == "serial"
        assert d["irq"] == 4


class TestDriverRegistry:
    def test_register_and_load(self):
        reg = DriverRegistry()
        loaded = []
        reg.register("test_driver", DeviceType.INPUT,
                     init_fn=lambda dev: (loaded.append(dev), True)[1])
        dev = Device(name="Input0", device_type=DeviceType.INPUT)
        assert reg.load("test_driver", dev)
        assert dev.driver_loaded
        assert dev.state == "ready"
        assert "test_driver" in reg.list_loaded()

    def test_unload(self):
        reg = DriverRegistry()
        shutdown_called = []
        reg.register("drv", DeviceType.SERIAL,
                     init_fn=lambda d: True,
                     shutdown_fn=lambda d: shutdown_called.append(d))
        dev = Device(name="COM0", device_type=DeviceType.SERIAL)
        reg.load("drv", dev)
        assert reg.unload("drv", dev)
        assert not dev.driver_loaded
        assert len(shutdown_called) == 1

    def test_unknown_driver(self):
        reg = DriverRegistry()
        dev = Device(name="X", device_type=DeviceType.UNKNOWN)
        assert not reg.load("nonexistent", dev)


class TestHAL:
    def setup_method(self):
        self.hal = HAL()

    def test_initialize(self):
        self.hal.initialize()
        assert self.hal._initialized
        devices = self.hal.get_all_devices()
        assert len(devices) >= 6

    def test_register_device(self):
        self.hal.initialize()
        dev = Device(name="Custom0", device_type=DeviceType.USB)
        self.hal.register_device(dev)
        assert self.hal.get_device(dev.device_id) is not None

    def test_get_by_type(self):
        self.hal.initialize()
        cpu_devices = self.hal.get_devices_by_type(DeviceType.CPU)
        assert len(cpu_devices) == 1
        assert cpu_devices[0].name == "CPU0"

    def test_probe_devices(self):
        self.hal.initialize()
        probed = self.hal.probe_devices()
        assert len(probed) >= 3

    def test_shutdown_device(self):
        self.hal.initialize()
        devices = self.hal.get_all_devices()
        vga = next(d for d in devices if d.name == "VGA0")
        assert self.hal.shutdown_device(vga.device_id)
        assert vga.state == "shutdown"

    def test_stats(self):
        self.hal.initialize()
        stats = self.hal.get_stats()
        assert stats["total_devices"] >= 6
        assert "cpu" in stats["by_type"]

    def test_event_log(self):
        self.hal.initialize()
        log = self.hal.get_event_log()
        assert len(log) >= 1
        assert log[0]["event"] == "hal_initialized"

    def test_enumerate_bus(self):
        self.hal.initialize()
        for d in self.hal.get_all_devices():
            if d.name == "KBD0":
                d.bus = "isa"
        isa = self.hal.enumerate_bus("isa")
        assert len(isa) >= 1

    def test_device_info(self):
        self.hal.initialize()
        devices = self.hal.get_all_devices()
        info = self.hal.get_device_info(devices[0].device_id)
        assert info is not None
        assert "capabilities" in info

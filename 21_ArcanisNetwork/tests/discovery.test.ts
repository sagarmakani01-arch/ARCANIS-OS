import { describe, it, expect, beforeEach } from "vitest";
import { DeviceManager, MDNSDiscovery, UPnPDiscovery } from "../src/discovery";

describe("DeviceManager", () => {
  let manager: DeviceManager;

  beforeEach(() => {
    manager = new DeviceManager();
  });

  it("should discover devices", async () => {
    const devices = await manager.discoverAll();
    expect(Array.isArray(devices)).toBe(true);
  });

  it("should get stats", () => {
    const stats = manager.getStats();
    expect(stats).toBeDefined();
    expect(stats.mdns).toBeDefined();
    expect(stats.upnp).toBeDefined();
  });
});

describe("MDNSDiscovery", () => {
  let mdns: MDNSDiscovery;

  beforeEach(() => {
    mdns = new MDNSDiscovery();
  });

  it("should register service", () => {
    mdns.registerService({
      name: "Test Service",
      type: "_http._tcp",
      domain: "local",
      port: 8080,
      TXT: { path: "/" },
    });
    const services = mdns.getServices();
    expect(services.length).toBe(1);
  });

  it("should add device", () => {
    const device = mdns.addDevice({
      name: "Test Device",
      type: "printer",
      address: { ip: "192.168.1.100", port: 80 },
      mac: "aa:bb:cc:dd:ee:ff",
      manufacturer: "Test",
      model: "Model 1",
      services: ["printing"],
      metadata: {},
    });
    expect(device).toBeDefined();
    expect(device.isOnline).toBe(true);
  });

  it("should find device by MAC", () => {
    mdns.addDevice({
      name: "Test Device",
      type: "printer",
      address: { ip: "192.168.1.100", port: 80 },
      mac: "aa:bb:cc:dd:ee:ff",
      manufacturer: "Test",
      model: "Model 1",
      services: ["printing"],
      metadata: {},
    });
    const device = mdns.findDeviceByMac("aa:bb:cc:dd:ee:ff");
    expect(device).toBeDefined();
    expect(device?.name).toBe("Test Device");
  });

  it("should get online devices", () => {
    mdns.addDevice({
      name: "Online Device",
      type: "printer",
      address: { ip: "192.168.1.100", port: 80 },
      mac: "aa:bb:cc:dd:ee:ff",
      manufacturer: "Test",
      model: "Model 1",
      services: [],
      metadata: {},
    });
    const online = mdns.getOnlineDevices();
    expect(online.length).toBe(1);
  });

  it("should cleanup old devices", () => {
    mdns.addDevice({
      name: "Old Device",
      type: "printer",
      address: { ip: "192.168.1.100", port: 80 },
      mac: "aa:bb:cc:dd:ee:ff",
      manufacturer: "Test",
      model: "Model 1",
      services: [],
      metadata: {},
    });
    mdns.cleanup(0);
    const devices = mdns.getDevices();
    expect(devices.length).toBe(0);
  });

  it("should return stats", () => {
    mdns.addDevice({
      name: "Test Device",
      type: "printer",
      address: { ip: "192.168.1.100", port: 80 },
      mac: "aa:bb:cc:dd:ee:ff",
      manufacturer: "Test",
      model: "Model 1",
      services: [],
      metadata: {},
    });
    const stats = mdns.getStats();
    expect(stats.totalDevices).toBe(1);
    expect(stats.onlineDevices).toBe(1);
  });
});

describe("UPnPDiscovery", () => {
  let upnp: UPnPDiscovery;

  beforeEach(() => {
    upnp = new UPnPDiscovery();
  });

  it("should add device", () => {
    const device = upnp.addDevice({
      name: "Test UPnP Device",
      type: "urn:schemas-upnp-org:device:MediaServer:1",
      location: "http://192.168.1.100:49152/description.xml",
      manufacturer: "Test",
      modelName: "Model 1",
      services: [],
    });
    expect(device).toBeDefined();
    expect(device.id).toBeDefined();
  });

  it("should get devices", () => {
    upnp.addDevice({
      name: "Test UPnP Device",
      type: "urn:schemas-upnp-org:device:MediaServer:1",
      location: "http://192.168.1.100:49152/description.xml",
      manufacturer: "Test",
      modelName: "Model 1",
      services: [],
    });
    const devices = upnp.getDevices();
    expect(devices.length).toBe(1);
  });

  it("should return stats", () => {
    const stats = upnp.getStats();
    expect(stats).toBeDefined();
    expect(stats.totalDevices).toBe(0);
  });
});

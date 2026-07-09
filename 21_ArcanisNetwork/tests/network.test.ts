import { describe, it, expect, beforeEach } from "vitest";
import { CoreNetworking } from "../src/core";
import { NetworkStack } from "../src/core/stack";
import { ConnectionManager } from "../src/core/connection";
import { TcpSocket, TcpServer } from "../src/core/tcp";
import { UdpSocket, UdpServer, BroadcastManager } from "../src/core/udp";
import { IpLayer } from "../src/core/ip";
import {
  Protocol,
  ConnectionState,
  NetworkInterfaceType,
  DEFAULT_NETWORK_CONFIG,
} from "../src/types";

describe("CoreNetworking", () => {
  let core: CoreNetworking;

  beforeEach(() => {
    core = new CoreNetworking();
  });

  it("should initialize successfully", async () => {
    await core.initialize();
    expect(core.stack).toBeDefined();
    expect(core.connectionManager).toBeDefined();
    expect(core.ipLayer).toBeDefined();
  });

  it("should shutdown successfully", async () => {
    await core.initialize();
    await core.shutdown();
    expect(true).toBe(true);
  });

  it("should create TCP server", async () => {
    await core.initialize();
    const server = core.createTcpServer(8080);
    expect(server).toBeDefined();
    expect(core.getTcpServer(8080)).toBe(server);
  });

  it("should create UDP socket", async () => {
    await core.initialize();
    const socket = await core.createUdpSocket(9999);
    expect(socket).toBeDefined();
    expect(socket.isBound()).toBe(true);
  });

  it("should return stats", async () => {
    await core.initialize();
    const stats = core.getStats();
    expect(stats).toBeDefined();
    expect(stats.stack).toBeDefined();
    expect(stats.connections).toBeDefined();
  });
});

describe("NetworkStack", () => {
  let stack: NetworkStack;

  beforeEach(() => {
    stack = new NetworkStack();
  });

  it("should have loopback interface", () => {
    const loopback = stack.getInterface("lo");
    expect(loopback).toBeDefined();
    expect(loopback?.type).toBe(NetworkInterfaceType.Loopback);
  });

  it("should create network interface", () => {
    const iface = stack.createInterface("eth0", NetworkInterfaceType.Ethernet);
    expect(iface).toBeDefined();
    expect(iface.name).toBe("eth0");
    expect(iface.type).toBe(NetworkInterfaceType.Ethernet);
  });

  it("should list interfaces", () => {
    stack.createInterface("eth0", NetworkInterfaceType.Ethernet);
    stack.createInterface("wlan0", NetworkInterfaceType.WiFi);
    const interfaces = stack.listInterfaces();
    expect(interfaces.length).toBeGreaterThanOrEqual(3);
  });

  it("should convert IP to string", () => {
    const ip = NetworkStack.ipToString({ octets: [192, 168, 1, 1] });
    expect(ip).toBe("192.168.1.1");
  });

  it("should convert string to IP", () => {
    const ip = NetworkStack.stringToIp("192.168.1.1");
    expect(ip.octets).toEqual([192, 168, 1, 1]);
  });
});

describe("ConnectionManager", () => {
  let manager: ConnectionManager;

  beforeEach(() => {
    manager = new ConnectionManager();
  });

  it("should create connection", () => {
    const connection = manager.createConnection(
      { ip: "127.0.0.1", port: 1234 },
      { ip: "192.168.1.1", port: 8080 },
      Protocol.TCP
    );
    expect(connection).toBeDefined();
    expect(connection.info.state).toBe(ConnectionState.Created);
  });

  it("should list connections", () => {
    manager.createConnection(
      { ip: "127.0.0.1", port: 1234 },
      { ip: "192.168.1.1", port: 8080 },
      Protocol.TCP
    );
    const connections = manager.listConnections();
    expect(connections.length).toBe(1);
  });

  it("should return stats", () => {
    manager.createConnection(
      { ip: "127.0.0.1", port: 1234 },
      { ip: "192.168.1.1", port: 8080 },
      Protocol.TCP
    );
    const stats = manager.getStats();
    expect(stats.total).toBe(1);
  });
});

describe("IpLayer", () => {
  let ipLayer: IpLayer;
  let stack: NetworkStack;

  beforeEach(() => {
    stack = new NetworkStack();
    ipLayer = new IpLayer(stack);
  });

  it("should add route", () => {
    ipLayer.addRoute({
      destination: "10.0.0.0",
      gateway: "192.168.1.1",
      interface: "eth0",
      metric: 1,
    });
    const routes = ipLayer.getRoutes();
    expect(routes.length).toBeGreaterThanOrEqual(2);
  });

  it("should resolve ARP entry", () => {
    ipLayer.addArpEntry("192.168.1.1", "aa:bb:cc:dd:ee:ff", "eth0");
    const mac = ipLayer.resolveMac("192.168.1.1");
    expect(mac).toBe("aa:bb:cc:dd:ee:ff");
  });

  it("should detect local network", () => {
    expect(ipLayer.isLocalNetwork("192.168.1.1")).toBe(true);
    expect(ipLayer.isLocalNetwork("10.0.0.1")).toBe(true);
    expect(ipLayer.isLocalNetwork("172.16.0.1")).toBe(true);
    expect(ipLayer.isLocalNetwork("8.8.8.8")).toBe(false);
  });

  it("should route packet", () => {
    const route = ipLayer.routePacket("192.168.1.100");
    expect(route).toBeDefined();
  });
});

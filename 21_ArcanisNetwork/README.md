# ArcanisNetwork

**AI-native networking foundation for ArcanisOS**

## Overview

ArcanisNetwork is a comprehensive networking module that provides the networking foundation for ArcanisOS. It implements TCP/IP support, connection management, secure communication, device discovery, and AI-powered network optimization.

## Architecture

```
ArcanisNetwork
├── Core (TCP/IP, UDP, Connection Management)
├── Transfer (Data Transfer, Streams, Packet Building)
├── Security (TLS, Firewall, Encryption)
├── Discovery (mDNS, UPnP, Device Management)
├── Services (DNS, DHCP, Local Network Services)
├── Cloud (Cloud Connectivity, Data Sync)
├── AI (Network Optimization, Monitoring, Security Analysis)
├── Integration (ArcanisKernel, ArcanisSecurity, ArcanisBrain)
└── Monitoring (Metrics, Logging, Packet Tracing)
```

## Features

### Core Networking
- **Network Stack**: Full network stack with interface management
- **TCP/IP**: Complete TCP implementation with connection states
- **UDP**: Connectionless UDP communication
- **Connection Management**: Create, track, and manage network connections
- **IP Layer**: Routing, ARP table, subnet calculations

### Data Transfer
- **Stream-based Transfer**: Reliable data transfer over streams
- **Packet Building**: Create and parse network packets
- **Buffer Management**: Network buffers and ring buffers

### Security
- **TLS/SSL**: Secure communication with session key management
- **Firewall**: Rule-based packet filtering and IP blocking
- **Encryption**: AES-256-GCM encryption for data protection
- **Security Events**: Track and log security incidents

### Device Discovery
- **mDNS**: Multicast DNS for local network device discovery
- **UPnP**: Universal Plug and Play device discovery
- **Device Management**: Track and manage discovered devices

### Local Network Services
- **DNS Resolver**: Domain name resolution with caching
- **DHCP Server**: Dynamic IP address assignment
- **Network Services**: Local network service management

### Cloud Connectivity
- **Cloud Connector**: Multi-cloud provider support
- **Data Sync**: File and data synchronization
- **Cloud Services**: Storage, compute, and AI service integration

### AI Features
- **Network Optimization**: AI-powered network optimization recommendations
- **Connection Monitoring**: Real-time connection health monitoring
- **Security Analysis**: Threat detection and analysis
- **Traffic Pattern Analysis**: Anomaly detection and prediction

### Integration
- **ArcanisKernel**: Integration with ArcanisKernel low-level primitives
- **ArcanisSecurity**: Integration with ArcanisSecurity permission system
- **ArcanisBrain**: Integration with ArcanisBrain AI intelligence

### Monitoring
- **Metrics Collection**: Real-time network metrics collection
- **Network Logging**: Comprehensive network event logging
- **Packet Tracing**: Network packet path tracing

## Usage

### Basic Usage

```typescript
import { ArcanisNetwork, Protocol } from "@arcanis/network";

const network = new ArcanisNetwork();
await network.initialize();

// Connect to remote server
const connection = await network.connect(
  { ip: "192.168.1.1", port: 80 },
  Protocol.TCP
);

// Send data
await network.sendData(connection.id, Buffer.from("Hello, World!"));

// Get network statistics
const stats = network.getNetworkStats();
console.log(stats);

await network.shutdown();
```

### TCP Server

```typescript
import { ArcanisNetwork } from "@arcanis/network";

const network = new ArcanisNetwork();
await network.initialize();

const server = network.core.createTcpServer(8080);
await server.start();

server.on("connection", (socket) => {
  console.log("New connection:", socket.id);
});

server.on("data", ({ socket, data }) => {
  console.log("Received data:", data.toString());
});
```

### UDP Communication

```typescript
import { ArcanisNetwork } from "@arcanis/network";

const network = new ArcanisNetwork();
await network.initialize();

const socket = await network.core.createUdpSocket(9999);
await socket.send(Buffer.from("Hello UDP!"), { ip: "192.168.1.1", port: 9999 });

socket.on("message", (msg) => {
  console.log("Received:", msg.data.toString());
});
```

### Security

```typescript
import { ArcanisNetwork } from "@arcanis/network";

const network = new ArcanisNetwork();
await network.initialize();

// Add firewall rule
network.security.firewall.addRule({
  id: "block-port-4444",
  name: "Block Suspicious Port",
  action: "deny",
  destinationPort: 4444,
  direction: "inbound",
  priority: 1,
  enabled: true,
});

// Encrypt data
const encrypted = network.security.encryptData(Buffer.from("Secret data"));
const decrypted = network.security.decryptData(
  encrypted.iv,
  encrypted.encrypted,
  encrypted.tag
);
```

### Device Discovery

```typescript
import { ArcanisNetwork } from "@arcanis/network";

const network = new ArcanisNetwork();
await network.initialize();

// Discover devices
const devices = await network.discovery.discoverAll();
console.log("Found devices:", devices.length);

// Add device manually
network.discovery.mdns.addDevice({
  name: "My Printer",
  type: "printer",
  address: { ip: "192.168.1.100", port: 80 },
  mac: "aa:bb:cc:dd:ee:ff",
  manufacturer: "HP",
  model: "LaserJet",
  services: ["printing"],
  metadata: {},
});
```

### AI Optimization

```typescript
import { ArcanisNetwork } from "@arcanis/network";

const network = new ArcanisNetwork();
await network.initialize();

// Analyze network stats
const recommendations = network.optimizer.analyzeStats({
  totalPacketsSent: 10000,
  totalPacketsReceived: 9500,
  totalBytesSent: 10000000,
  totalBytesReceived: 9500000,
  activeConnections: 500,
  totalConnections: 600,
  errors: 10,
  droppedPackets: 500,
  averageLatency: 150,
  bandwidth: 5000000,
});

console.log("Recommendations:", recommendations);
```

## Configuration

```typescript
const network = new ArcanisNetwork({
  maxConnections: 2048,
  maxPacketSize: 65535,
  connectionTimeout: 30000,
  keepAliveInterval: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
  enableCompression: true,
  enableEncryption: true,
  bufferSize: 16384,
});
```

## API Reference

### ArcanisNetwork
- `initialize()` - Initialize the network
- `shutdown()` - Shutdown the network
- `connect(address, protocol)` - Connect to remote
- `disconnect(connectionId)` - Disconnect
- `sendData(connectionId, data)` - Send data
- `getNetworkStats()` - Get statistics
- `getConfig()` - Get configuration
- `isInitialized()` - Check if initialized

### CoreNetworking
- `createTcpServer(port)` - Create TCP server
- `createTcpConnection(remoteAddress)` - Create TCP connection
- `createUdpSocket(port?)` - Create UDP socket
- `getStats()` - Get statistics

### NetworkSecurity
- `checkPermission(source, dest, protocol, ...)` - Check firewall permission
- `encryptData(data)` - Encrypt data
- `decryptData(iv, encrypted, tag)` - Decrypt data
- `logSecurityEvent(event)` - Log security event

### DeviceManager
- `discoverAll()` - Discover all devices
- `getDevice(id)` - Get device by ID
- `getDevices()` - Get all devices
- `getStats()` - Get statistics

## Integration

ArcanisNetwork integrates with other ArcanisOS components:

- **ArcanisKernel**: Low-level network primitives
- **ArcanisSecurity**: Permission and policy enforcement
- **ArcanisBrain**: AI-powered optimization and analysis

## Testing

```bash
npm test
npm run test:coverage
```

## License

MIT

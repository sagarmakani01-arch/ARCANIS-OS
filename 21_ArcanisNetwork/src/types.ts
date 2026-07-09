export enum Protocol {
  TCP = "tcp",
  UDP = "udp",
  ICMP = "icmp",
  HTTP = "http",
  HTTPS = "https",
  WebSocket = "ws",
  QUIC = "quic",
}

export enum ConnectionState {
  Created = "created",
  Connecting = "connecting",
  Connected = "connected",
  Disconnected = "disconnected",
  Error = "error",
}

export enum NetworkInterfaceType {
  Ethernet = "ethernet",
  WiFi = "wifi",
  Loopback = "loopback",
  Virtual = "virtual",
}

export enum PacketDirection {
  Inbound = "inbound",
  Outbound = "outbound",
  Bidirectional = "bidirectional",
}

export interface MacAddress {
  octets: [number, number, number, number, number, number];
}

export interface IPv4Address {
  octets: [number, number, number, number];
}

export interface IPv6Address {
  groups: [number, number, number, number, number, number, number, number];
}

export interface NetworkAddress {
  ip: string;
  port: number;
  mac?: MacAddress;
}

export interface NetworkInterface {
  id: string;
  name: string;
  type: NetworkInterfaceType;
  mac: MacAddress;
  ipv4: IPv4Address;
  ipv6?: IPv6Address;
  subnet: string;
  gateway: string;
  dns: string[];
  mtu: number;
  speed: number;
  status: "up" | "down" | "error";
}

export interface NetworkPacket {
  id: string;
  timestamp: number;
  source: NetworkAddress;
  destination: NetworkAddress;
  protocol: Protocol;
  direction: PacketDirection;
  size: number;
  data: Buffer;
  ttl: number;
  sequence?: number;
  acknowledgment?: number;
  flags?: PacketFlags;
}

export interface PacketFlags {
  syn: boolean;
  ack: boolean;
  fin: boolean;
  rst: boolean;
  psh: boolean;
  urg: boolean;
}

export interface ConnectionInfo {
  id: string;
  localAddress: NetworkAddress;
  remoteAddress: NetworkAddress;
  protocol: Protocol;
  state: ConnectionState;
  createdAt: number;
  lastActivity: number;
  bytesSent: number;
  bytesReceived: number;
  latency: number;
  isActive: boolean;
}

export interface NetworkConfig {
  maxConnections: number;
  maxPacketSize: number;
  connectionTimeout: number;
  keepAliveInterval: number;
  retryAttempts: number;
  retryDelay: number;
  enableCompression: boolean;
  enableEncryption: boolean;
  bufferSize: number;
}

export interface NetworkStats {
  totalPacketsSent: number;
  totalPacketsReceived: number;
  totalBytesSent: number;
  totalBytesReceived: number;
  activeConnections: number;
  totalConnections: number;
  errors: number;
  droppedPackets: number;
  averageLatency: number;
  bandwidth: number;
}

export interface SecurityEvent {
  id: string;
  type: string;
  severity: "low" | "medium" | "high" | "critical";
  source: string;
  destination: string;
  timestamp: number;
  description: string;
  metadata: Record<string, unknown>;
}

export interface NetworkEvent {
  type: string;
  source: string;
  data: unknown;
  timestamp: number;
  id: string;
}

export type NetworkEventHandler = (event: NetworkEvent) => void;

export const DEFAULT_NETWORK_CONFIG: NetworkConfig = {
  maxConnections: 1024,
  maxPacketSize: 65535,
  connectionTimeout: 30000,
  keepAliveInterval: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
  enableCompression: true,
  enableEncryption: true,
  bufferSize: 8192,
};

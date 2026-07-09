import {
  NetworkPacket,
  NetworkAddress,
  PacketFlags,
  Protocol,
  PacketDirection,
} from "../types";
import { v4 as uuidv4 } from "uuid";

export class PacketBuilder {
  static createPacket(
    source: NetworkAddress,
    destination: NetworkAddress,
    protocol: Protocol,
    data: Buffer,
    options: Partial<{
      direction: PacketDirection;
      ttl: number;
      sequence: number;
      acknowledgment: number;
      flags: PacketFlags;
    }> = {}
  ): NetworkPacket {
    return {
      id: uuidv4(),
      timestamp: Date.now(),
      source,
      destination,
      protocol,
      direction: options.direction || PacketDirection.Bidirectional,
      size: data.length,
      data,
      ttl: options.ttl || 64,
      sequence: options.sequence,
      acknowledgment: options.acknowledgment,
      flags: options.flags || {
        syn: false,
        ack: false,
        fin: false,
        rst: false,
        psh: false,
        urg: false,
      },
    };
  }

  static createTcpSyn(
    source: NetworkAddress,
    destination: NetworkAddress,
    sequence: number
  ): NetworkPacket {
    return this.createPacket(
      source,
      destination,
      Protocol.TCP,
      Buffer.alloc(0),
      {
        direction: PacketDirection.Outbound,
        sequence,
        flags: {
          syn: true,
          ack: false,
          fin: false,
          rst: false,
          psh: false,
          urg: false,
        },
      }
    );
  }

  static createTcpSynAck(
    source: NetworkAddress,
    destination: NetworkAddress,
    sequence: number,
    acknowledgment: number
  ): NetworkPacket {
    return this.createPacket(
      source,
      destination,
      Protocol.TCP,
      Buffer.alloc(0),
      {
        direction: PacketDirection.Inbound,
        sequence,
        acknowledgment,
        flags: {
          syn: true,
          ack: true,
          fin: false,
          rst: false,
          psh: false,
          urg: false,
        },
      }
    );
  }

  static createTcpAck(
    source: NetworkAddress,
    destination: NetworkAddress,
    sequence: number,
    acknowledgment: number
  ): NetworkPacket {
    return this.createPacket(
      source,
      destination,
      Protocol.TCP,
      Buffer.alloc(0),
      {
        direction: PacketDirection.Outbound,
        sequence,
        acknowledgment,
        flags: {
          syn: false,
          ack: true,
          fin: false,
          rst: false,
          psh: false,
          urg: false,
        },
      }
    );
  }

  static createTcpFin(
    source: NetworkAddress,
    destination: NetworkAddress,
    sequence: number,
    acknowledgment: number
  ): NetworkPacket {
    return this.createPacket(
      source,
      destination,
      Protocol.TCP,
      Buffer.alloc(0),
      {
        direction: PacketDirection.Outbound,
        sequence,
        acknowledgment,
        flags: {
          syn: false,
          ack: false,
          fin: true,
          rst: false,
          psh: false,
          urg: false,
        },
      }
    );
  }

  static createUdpPacket(
    source: NetworkAddress,
    destination: NetworkAddress,
    data: Buffer
  ): NetworkPacket {
    return this.createPacket(
      source,
      destination,
      Protocol.UDP,
      data,
      {
        direction: PacketDirection.Bidirectional,
        ttl: 64,
      }
    );
  }

  static parseFlags(flags: PacketFlags): number {
    let value = 0;
    if (flags.urg) value |= 0x20;
    if (flags.ack) value |= 0x10;
    if (flags.psh) value |= 0x08;
    if (flags.rst) value |= 0x04;
    if (flags.syn) value |= 0x02;
    if (flags.fin) value |= 0x01;
    return value;
  }

  static parseFlagsFromValue(value: number): PacketFlags {
    return {
      urg: (value & 0x20) !== 0,
      ack: (value & 0x10) !== 0,
      psh: (value & 0x08) !== 0,
      rst: (value & 0x04) !== 0,
      syn: (value & 0x02) !== 0,
      fin: (value & 0x01) !== 0,
    };
  }

  static calculateChecksum(data: Buffer): number {
    let sum = 0;
    for (let i = 0; i < data.length; i += 2) {
      const word = (data[i] << 8) + (data[i + 1] || 0);
      sum += word;
    }
    while (sum >> 16) {
      sum = (sum & 0xffff) + (sum >> 16);
    }
    return ~sum & 0xffff;
  }

  static serializePacket(packet: NetworkPacket): Buffer {
    const header = Buffer.alloc(24);
    header.writeUInt32BE(packet.source.port, 0);
    header.writeUInt32BE(packet.destination.port, 4);
    header.writeUInt32BE(packet.size, 8);
    header.writeUInt32BE(packet.ttl, 12);
    header.writeUInt32BE(packet.sequence || 0, 16);
    header.writeUInt32BE(packet.acknowledgment || 0, 20);
    return Buffer.concat([header, packet.data]);
  }

  static deserializePacket(data: Buffer): NetworkPacket {
    if (data.length < 24) {
      throw new Error("Invalid packet: too short");
    }
    const sourcePort = data.readUInt32BE(0);
    const destPort = data.readUInt32BE(4);
    const size = data.readUInt32BE(8);
    const ttl = data.readUInt32BE(12);
    const sequence = data.readUInt32BE(16);
    const acknowledgment = data.readUInt32BE(20);
    const packetData = data.slice(24, 24 + size);
    return {
      id: uuidv4(),
      timestamp: Date.now(),
      source: { ip: "0.0.0.0", port: sourcePort },
      destination: { ip: "0.0.0.0", port: destPort },
      protocol: Protocol.TCP,
      direction: PacketDirection.Bidirectional,
      size: size,
      data: packetData,
      ttl,
      sequence: sequence || undefined,
      acknowledgment: acknowledgment || undefined,
      flags: { syn: false, ack: false, fin: false, rst: false, psh: false, urg: false },
    };
  }
}

import { describe, it, expect, beforeEach } from 'vitest';
import { NetworkManager } from '../src/networking/network-manager.js';

describe('NetworkManager', () => {
  let networks: NetworkManager;

  beforeEach(() => {
    networks = new NetworkManager();
  });

  describe('constructor', () => {
    it('should create default networks', async () => {
      const list = await networks.list();
      expect(list.length).toBeGreaterThanOrEqual(3);
    });

    it('should have bridge network', async () => {
      const bridge = await networks.resolve('bridge');
      expect(bridge.driver).toBe('bridge');
    });

    it('should have host network', async () => {
      const host = await networks.resolve('host');
      expect(host.driver).toBe('host');
    });

    it('should have none network', async () => {
      const none = await networks.resolve('none');
      expect(none.driver).toBe('none');
    });
  });

  describe('createNetwork', () => {
    it('should create a new network', async () => {
      const network = networks.createNetwork({
        name: 'custom',
        driver: 'bridge',
        subnet: '10.0.0.0/24',
        gateway: '10.0.0.1',
      });
      expect(network).toBeDefined();
      expect(network.name).toBe('custom');
      expect(network.subnet).toBe('10.0.0.0/24');
    });

    it('should reject duplicate network names', async () => {
      expect(() => networks.createNetwork({ name: 'bridge', driver: 'bridge', subnet: 'x', gateway: 'x' })).toThrow('already exists');
    });

    it('should emit create event', async () => {
      let emitted = false;
      networks.on('network:create', () => { emitted = true; });
      networks.createNetwork({ name: 'ev-net', driver: 'bridge', subnet: '10.1.0.0/24', gateway: '10.1.0.1' });
      expect(emitted).toBe(true);
    });
  });

  describe('connectContainer', () => {
    it('should connect container to network', async () => {
      const ip = await networks.connectContainer('bridge', 'container-1');
      expect(ip).toBeDefined();
      expect(ip).toMatch(/^\d+\.\d+\.\d+\.\d+$/);
    });

    it('should allocate unique IPs', async () => {
      const ip1 = await networks.connectContainer('bridge', 'c1');
      const ip2 = await networks.connectContainer('bridge', 'c2');
      expect(ip1).not.toBe(ip2);
    });

    it('should reject connecting to none network', async () => {
      await expect(networks.connectContainer('none', 'c1')).rejects.toThrow('Cannot connect');
    });

    it('should reject connecting to non-existent network', async () => {
      await expect(networks.connectContainer('nonexistent', 'c1')).rejects.toThrow('not found');
    });
  });

  describe('disconnectContainer', () => {
    it('should disconnect container from network', async () => {
      await networks.connectContainer('bridge', 'c1');
      await networks.disconnectContainer('bridge', 'c1');
      const containers = await networks.getConnectedContainers('bridge');
      expect(containers.has('c1')).toBe(false);
    });

    it('should reject disconnecting non-connected container', async () => {
      await expect(networks.disconnectContainer('bridge', 'c1')).rejects.toThrow('not connected');
    });
  });

  describe('inspect', () => {
    it('should return network details', async () => {
      const net = await networks.inspect('bridge');
      expect(net.name).toBe('bridge');
      expect(net.containers).toBeInstanceOf(Map);
    });

    it('should throw for non-existent network', async () => {
      await expect(networks.inspect('nonexistent')).rejects.toThrow('not found');
    });
  });

  describe('list', () => {
    it('should list all networks', async () => {
      const list = await networks.list();
      expect(list.length).toBe(3);
    });

    it('should filter by driver', async () => {
      const bridges = await networks.list({ driver: 'bridge' });
      expect(bridges.length).toBe(1);
    });
  });

  describe('createOverlay', () => {
    it('should create overlay network', async () => {
      const net = await networks.createOverlay('overlay-net', '10.10.0.0/24', '10.10.0.1');
      expect(net.driver).toBe('overlay');
    });
  });

  describe('getContainerIP', () => {
    it('should return container IP on network', async () => {
      const ip = await networks.connectContainer('bridge', 'ip-test');
      const retrieved = await networks.getContainerIP('bridge', 'ip-test');
      expect(retrieved).toBe(ip);
    });
  });

  describe('counts', () => {
    it('should track network count', () => {
      expect(networks.getNetworkCount()).toBe(3);
    });

    it('should return DNS servers', () => {
      const dns = networks.getDnsServers();
      expect(dns.length).toBeGreaterThan(0);
    });
  });
});

/**
 * net_stack.c — TCP/IP Network Stack Implementation
 *
 * Ethernet, ARP, IP, TCP, UDP for Arcanis OS.
 * Simulated NIC for now — real driver would call into hardware.
 */
#include <arcanis/net_stack.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

static net_interface_t net_iface;
static arp_entry_t arp_table[NET_MAX_ARP];
static net_socket_t sockets[NET_MAX_SOCKETS];
static uint32_t seq_counter = 1000;

/* ---- Checksum ---- */
uint16_t net_checksum(const uint16_t* data, uint32_t len) {
    uint32_t sum = 0;
    while (len > 1) { sum += *data++; len -= 2; }
    if (len) sum += *(const uint8_t*)data;
    while (sum >> 16) sum = (sum & 0xFFFF) + (sum >> 16);
    return (uint16_t)~sum;
}

/* ---- IP utilities ---- */
uint32_t net_ip_from_str(const char* str) {
    uint32_t ip = 0;
    int octet = 0;
    int val = 0;
    for (int i = 0; str[i]; i++) {
        if (str[i] == '.') { ip = (ip << 8) | val; val = 0; octet++; }
        else { val = val * 10 + (str[i] - '0'); }
    }
    return (ip << 8) | val;
}

void net_ip_to_str(uint32_t ip, char* str) {
    char tmp[16];
    int pos = 0;
    for (int i = 3; i >= 0; i--) {
        int octet = (ip >> (i * 8)) & 0xFF;
        int start = pos;
        if (octet == 0) { tmp[pos++] = '0'; }
        else {
            char rev[4]; int r = 0;
            while (octet > 0) { rev[r++] = '0' + (octet % 10); octet /= 10; }
            while (r > 0) tmp[pos++] = rev[--r];
        }
        if (i > 0) tmp[pos++] = '.';
    }
    tmp[pos] = '\0';
    for (int i = 0; i <= pos; i++) str[i] = tmp[i];
}

/* ---- Init ---- */
void net_initialize(void) {
    memset(&net_iface, 0, sizeof(net_iface));
    memset(arp_table, 0, sizeof(arp_table));
    memset(sockets, 0, sizeof(sockets));
    seq_counter = 1000;
}

void net_set_interface(uint8_t* mac, uint32_t ip, uint32_t gateway, uint32_t subnet) {
    memcpy(net_iface.mac, mac, NET_MAC_SIZE);
    net_iface.ip = ip;
    net_iface.gateway = gateway;
    net_iface.subnet = subnet;
    net_iface.link_up = 1;
}

/* ---- ARP ---- */
static void arp_add_entry(uint32_t ip, uint8_t* mac) {
    for (int i = 0; i < NET_MAX_ARP; i++) {
        if (arp_table[i].valid && arp_table[i].ip == ip) {
            memcpy(arp_table[i].mac, mac, NET_MAC_SIZE);
            arp_table[i].age = 0;
            return;
        }
    }
    for (int i = 0; i < NET_MAX_ARP; i++) {
        if (!arp_table[i].valid) {
            arp_table[i].ip = ip;
            memcpy(arp_table[i].mac, mac, NET_MAC_SIZE);
            arp_table[i].valid = 1;
            arp_table[i].age = 0;
            return;
        }
    }
}

int net_arp_resolve(uint32_t ip, uint8_t* mac_out) {
    for (int i = 0; i < NET_MAX_ARP; i++) {
        if (arp_table[i].valid && arp_table[i].ip == ip) {
            memcpy(mac_out, arp_table[i].mac, NET_MAC_SIZE);
            return 0;
        }
    }
    return -1; /* Not found — would need to send ARP request */
}

static void arp_handle(uint8_t* packet, uint32_t len) {
    if (len < sizeof(arp_header_t)) return;
    arp_header_t* arp = (arp_header_t*)packet;

    if (arp->opcode == ARP_OP_REQUEST && arp->target_ip == net_iface.ip) {
        /* Send ARP reply */
        uint8_t reply[42];
        eth_header_t* eth = (eth_header_t*)reply;
        arp_header_t* rarp = (arp_header_t*)(reply + ETH_HDR_LEN);

        memcpy(eth->dst, arp->sender_mac, NET_MAC_SIZE);
        memcpy(eth->src, net_iface.mac, NET_MAC_SIZE);
        eth->ethertype = htons(ETH_P_ARP);

        rarp->hw_type = htons(1);
        rarp->proto_type = htons(ETH_P_IP);
        rarp->hw_len = 6;
        rarp->proto_len = 4;
        rarp->opcode = htons(ARP_OP_REPLY);
        memcpy(rarp->sender_mac, net_iface.mac, NET_MAC_SIZE);
        rarp->sender_ip = net_iface.ip;
        memcpy(rarp->target_mac, arp->sender_mac, NET_MAC_SIZE);
        rarp->target_ip = arp->sender_ip;

        /* net_send_raw(reply, 42); */
    }

    if (arp->opcode == ARP_OP_REPLY) {
        arp_add_entry(arp->sender_ip, arp->sender_mac);
    }
}

/* ---- IP ---- */
static void ip_handle(uint8_t* packet, uint32_t len) {
    if (len < IP_HDR_LEN) return;
    ip_header_t* ip = (ip_header_t*)packet;

    /* Verify checksum */
    uint16_t cksum = net_checksum((const uint16_t*)ip, IP_HDR_LEN);
    if (cksum != 0 && cksum != 0xFFFF) return;

    uint8_t* payload = packet + IP_HDR_LEN;
    uint32_t payload_len = ntohs(ip->total_len) - IP_HDR_LEN;

    switch (ip->protocol) {
        case IP_PROTO_ICMP:
            /* TODO: handle ICMP (ping) */
            break;
        case IP_PROTO_TCP:
            /* TODO: TCP processing */
            break;
        case IP_PROTO_UDP:
            /* TODO: UDP processing */
            break;
    }
}

void net_handle_packet(uint8_t* packet, uint32_t len) {
    if (len < ETH_HDR_LEN) return;

    eth_header_t* eth = (eth_header_t*)packet;
    uint16_t proto = ntohs(eth->ethertype);

    switch (proto) {
        case ETH_P_ARP:
            arp_handle(packet + ETH_HDR_LEN, len - ETH_HDR_LEN);
            break;
        case ETH_P_IP:
            ip_handle(packet + ETH_HDR_LEN, len - ETH_HDR_LEN);
            break;
    }
}

/* ---- Send ---- */
int net_send_packet(uint32_t dst_ip, uint16_t proto, const uint8_t* data, uint32_t len) {
    if (!net_iface.link_up) return -1;

    uint8_t dst_mac[NET_MAC_SIZE];
    if (net_arp_resolve(dst_ip, dst_mac) != 0) {
        /* Would need to send ARP request and wait */
        return -1;
    }

    uint8_t packet[NET_MAX_PACKET];
    eth_header_t* eth = (eth_header_t*)packet;
    memcpy(eth->dst, dst_mac, NET_MAC_SIZE);
    memcpy(eth->src, net_iface.mac, NET_MAC_SIZE);
    eth->ethertype = htons(proto);

    memcpy(packet + ETH_HDR_LEN, data, len);
    net_iface.tx_packets++;

    /* In real OS: send to NIC driver */
    return (int)len;
}

/* ---- Sockets ---- */
int net_socket_create(int proto) {
    for (int i = 0; i < NET_MAX_SOCKETS; i++) {
        if (!sockets[i].in_use) {
            sockets[i].in_use = 1;
            sockets[i].protocol = proto;
            sockets[i].state = 0;
            sockets[i].rx_len = 0;
            sockets[i].tx_len = 0;
            return i;
        }
    }
    return -1;
}

int net_socket_connect(int sock, uint32_t ip, uint16_t port) {
    if (sock < 0 || sock >= NET_MAX_SOCKETS) return -1;
    net_socket_t* s = &sockets[sock];
    s->remote_ip = ip;
    s->remote_port = port;
    s->state = 1; /* SYN_SENT */
    /* In real OS: send TCP SYN */
    return 0;
}

int net_socket_send(int sock, const void* data, uint32_t len) {
    if (sock < 0 || sock >= NET_MAX_SOCKETS) return -1;
    net_socket_t* s = &sockets[sock];
    uint32_t to_write = len;
    if (to_write > sizeof(s->tx_buf) - s->tx_len)
        to_write = sizeof(s->tx_buf) - s->tx_len;
    memcpy(s->tx_buf + s->tx_len, data, to_write);
    s->tx_len += to_write;
    return (int)to_write;
}

int net_socket_recv(int sock, void* buf, uint32_t len) {
    if (sock < 0 || sock >= NET_MAX_SOCKETS) return -1;
    net_socket_t* s = &sockets[sock];
    if (s->rx_len == 0) return 0;
    uint32_t to_read = (len < s->rx_len) ? len : s->rx_len;
    memcpy(buf, s->rx_buf, to_read);
    /* Shift remaining data */
    if (to_read < s->rx_len)
        memmove(s->rx_buf, s->rx_buf + to_read, s->rx_len - to_read);
    s->rx_len -= to_read;
    return (int)to_read;
}

int net_socket_close(int sock) {
    if (sock < 0 || sock >= NET_MAX_SOCKETS) return -1;
    sockets[sock].in_use = 0;
    return 0;
}

int net_socket_listen(int sock, uint16_t port) {
    if (sock < 0 || sock >= NET_MAX_SOCKETS) return -1;
    sockets[sock].local_port = port;
    sockets[sock].state = 2; /* LISTEN */
    return 0;
}

int net_socket_accept(int sock) {
    if (sock < 0 || sock >= NET_MAX_SOCKETS) return -1;
    /* In real OS: accept incoming TCP connection */
    return -1;
}

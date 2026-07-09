#include <arcanis/net.h>
#include <arcanis/string.h>
#include <arcanis/types.h>
#include <arcanis/heap.h>

static net_interface_t* net_interfaces = NULL;

void net_initialize(void) {
    net_interfaces = NULL;
}

void net_register_interface(net_interface_t* iface) {
    if (!iface) return;
    iface->next = net_interfaces;
    net_interfaces = iface;
}

net_interface_t* net_get_interface(const char* name) {
    net_interface_t* iface = net_interfaces;
    while (iface) {
        if (strcmp(iface->name, name) == 0) return iface;
        iface = iface->next;
    }
    return NULL;
}

void net_receive_packet(net_interface_t* iface, uint8_t* data, uint32_t length) {
    if (!iface || length < NET_ETH_HEADER) return;

    net_eth_header_t* eth = (net_eth_header_t*)data;
    uint16_t type = net_htons(eth->type);

    switch (type) {
        case NET_PACKET_ARP:
            break;
        case NET_PACKET_IP:
            break;
        default:
            break;
    }
}

uint16_t net_checksum(uint16_t* data, uint32_t length) {
    uint32_t sum = 0;

    while (length > 1) {
        sum += *data++;
        length -= 2;
    }

    if (length > 0) {
        sum += *(uint8_t*)data;
    }

    while (sum >> 16) {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }

    return (uint16_t)~sum;
}

uint16_t net_htons(uint16_t val) {
    return ((val & 0xFF) << 8) | ((val >> 8) & 0xFF);
}

uint32_t net_htonl(uint32_t val) {
    return ((val & 0xFF) << 24) | ((val & 0xFF00) << 8) |
           ((val >> 8) & 0xFF00) | ((val >> 24) & 0xFF);
}

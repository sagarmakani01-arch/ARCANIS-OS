#ifndef ARCANIS_NET_H
#define ARCANIS_NET_H

#include <arcanis/types.h>

#define NET_MAC_SIZE    6
#define NET_IP_SIZE     4
#define NET_ETH_MTU     1500
#define NET_ETH_HEADER  14

enum net_packet_type {
    NET_PACKET_ARP  = 0x0806,
    NET_PACKET_IP   = 0x0800,
    NET_PACKET_IPV6 = 0x86DD,
};

typedef struct {
    uint8_t  dest_mac[NET_MAC_SIZE];
    uint8_t  src_mac[NET_MAC_SIZE];
    uint16_t type;
} __attribute__((packed)) net_eth_header_t;

typedef struct {
    uint8_t  hardware_type;
    uint8_t  protocol_type;
    uint8_t  hardware_size;
    uint8_t  protocol_size;
    uint16_t opcode;
    uint8_t  sender_mac[NET_MAC_SIZE];
    uint8_t  sender_ip[NET_IP_SIZE];
    uint8_t  target_mac[NET_MAC_SIZE];
    uint8_t  target_ip[NET_IP_SIZE];
} __attribute__((packed)) net_arp_packet_t;

typedef struct {
    uint8_t  version_ihl;
    uint8_t  tos;
    uint16_t total_length;
    uint16_t identification;
    uint16_t flags_fragment;
    uint8_t  ttl;
    uint8_t  protocol;
    uint16_t checksum;
    uint8_t  src_ip[NET_IP_SIZE];
    uint8_t  dest_ip[NET_IP_SIZE];
} __attribute__((packed)) net_ip_header_t;

typedef struct {
    uint16_t src_port;
    uint16_t dest_port;
    uint16_t length;
    uint16_t checksum;
} __attribute__((packed)) net_udp_header_t;

typedef struct {
    uint8_t  mac[NET_MAC_SIZE];
    uint8_t  ip[NET_IP_SIZE];
    uint16_t port;
} net_endpoint_t;

typedef struct net_interface {
    char     name[16];
    uint8_t  mac[NET_MAC_SIZE];
    uint8_t  ip[NET_IP_SIZE];
    uint8_t  subnet[NET_IP_SIZE];
    uint8_t  gateway[NET_IP_SIZE];
    uint32_t flags;
    void*    driver_data;
    void     (*send)(struct net_interface*, uint8_t*, uint32_t);
    void     (*receive)(struct net_interface*, uint8_t*, uint32_t);
    struct net_interface* next;
} net_interface_t;

void net_initialize(void);
void net_register_interface(net_interface_t* iface);
net_interface_t* net_get_interface(const char* name);
void net_receive_packet(net_interface_t* iface, uint8_t* data, uint32_t length);
uint16_t net_checksum(uint16_t* data, uint32_t length);
uint16_t net_htons(uint16_t val);
uint32_t net_htonl(uint32_t val);

#endif

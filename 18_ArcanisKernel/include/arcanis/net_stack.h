/**
 * net.h — TCP/IP Network Stack
 *
 * Layers: Ethernet -> ARP -> IP -> TCP/UDP
 * Supports basic networking for Arcanis OS.
 */
#ifndef ARCANIS_NET_STACK_H
#define ARCANIS_NET_STACK_H

#include <arcanis/types.h>

#define NET_MAX_PACKET  1518
#define NET_MAX_SOCKETS 32
#define NET_MAC_SIZE     6
#define NET_IP_SIZE      4
#define NET_MAX_ARP     64

/* Ethernet */
#define ETH_P_IP    0x0800
#define ETH_P_ARP   0x0806
#define ETH_HDR_LEN 14

/* IP */
#define IP_PROTO_ICMP 1
#define IP_PROTO_TCP  6
#define IP_PROTO_UDP  17
#define IP_HDR_LEN   20

/* TCP */
#define TCP_SYN  0x02
#define TCP_ACK  0x10
#define TCP_FIN  0x01
#define TCP_RST  0x04
#define TCP_HDR_LEN 20

/* ARP */
#define ARP_OP_REQUEST 1
#define ARP_OP_REPLY   2

#pragma pack(push, 1)

typedef struct {
    uint8_t  dst[NET_MAC_SIZE];
    uint8_t  src[NET_MAC_SIZE];
    uint16_t ethertype;
} eth_header_t;

typedef struct {
    uint16_t hw_type;
    uint16_t proto_type;
    uint8_t  hw_len;
    uint8_t  proto_len;
    uint16_t opcode;
    uint8_t  sender_mac[NET_MAC_SIZE];
    uint32_t sender_ip;
    uint8_t  target_mac[NET_MAC_SIZE];
    uint32_t target_ip;
} arp_header_t;

typedef struct {
    uint8_t  ver_ihl;
    uint8_t  tos;
    uint16_t total_len;
    uint16_t id;
    uint16_t flags_frag;
    uint8_t  ttl;
    uint8_t  protocol;
    uint16_t checksum;
    uint32_t src_ip;
    uint32_t dst_ip;
} ip_header_t;

typedef struct {
    uint16_t src_port;
    uint16_t dst_port;
    uint32_t seq;
    uint32_t ack;
    uint8_t  flags;
    uint16_t window;
    uint16_t checksum;
    uint16_t urgent;
} tcp_header_t;

typedef struct {
    uint16_t src_port;
    uint16_t dst_port;
    uint16_t length;
    uint16_t checksum;
} udp_header_t;

#pragma pack(pop)

/* ARP table entry */
typedef struct {
    uint32_t ip;
    uint8_t  mac[NET_MAC_SIZE];
    uint32_t age;
    uint8_t  valid;
} arp_entry_t;

/* Network interface */
typedef struct {
    uint8_t  mac[NET_MAC_SIZE];
    uint32_t ip;
    uint32_t gateway;
    uint32_t subnet;
    uint8_t  link_up;
    uint32_t rx_packets;
    uint32_t tx_packets;
} net_interface_t;

/* Socket */
typedef struct {
    int      in_use;
    int      protocol;  /* TCP or UDP */
    uint16_t local_port;
    uint32_t remote_ip;
    uint16_t remote_port;
    int      state;     /* TCP states */
    uint8_t  rx_buf[8192];
    uint32_t rx_len;
    uint8_t  tx_buf[8192];
    uint32_t tx_len;
} net_socket_t;

/* API */
void     net_initialize(void);
void     net_set_interface(uint8_t* mac, uint32_t ip, uint32_t gateway, uint32_t subnet);
int      net_send_packet(uint32_t dst_ip, uint16_t proto, const uint8_t* data, uint32_t len);
int      net_arp_resolve(uint32_t ip, uint8_t* mac_out);
void     net_handle_packet(uint8_t* packet, uint32_t len);

/* Sockets */
int      net_socket_create(int proto);
int      net_socket_connect(int sock, uint32_t ip, uint16_t port);
int      net_socket_send(int sock, const void* data, uint32_t len);
int      net_socket_recv(int sock, void* buf, uint32_t len);
int      net_socket_close(int sock);
int      net_socket_listen(int sock, uint16_t port);
int      net_socket_accept(int sock);

/* Utilities */
uint32_t net_ip_from_str(const char* str);
void     net_ip_to_str(uint32_t ip, char* str);
uint16_t net_checksum(const uint16_t* data, uint32_t len);

#endif

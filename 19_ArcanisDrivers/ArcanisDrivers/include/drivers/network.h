#ifndef ARCANIS_NETWORK_H
#define ARCANIS_NETWORK_H

#include "drivers/driver.h"
#include "utils/driver_ringbuffer.h"
#include <stdint.h>
#include <stdbool.h>

#define NET_MAC_SIZE        6
#define NET_IP_SIZE         4
#define NET_MAX_PACKET      1518
#define NET_MIN_PACKET      64
#define NET_BUFFER_SIZE     8192

#define NET_ETH_TYPE_IPV4   0x0800
#define NET_ETH_TYPE_ARP    0x0806
#define NET_ETH_TYPE_IPV6   0x86DD

#define NET_ETH_HDR_SIZE    14
#define NET_IP_HDR_SIZE     20
#define NET_UDP_HDR_SIZE    8
#define NET_TCP_HDR_SIZE    20
#define NET_ARP_HDR_SIZE    28

typedef enum {
    NET_TYPE_ETHERNET = 0,
    NET_TYPE_WIFI,
    NET_TYPE_LOOPBACK,
    NET_TYPE_VIRTUAL
} NetworkType;

typedef enum {
    NET_STATE_DOWN = 0,
    NET_STATE_UP,
    NET_STATE_LINKED,
    NET_STATE_ERROR
} NetworkState;

typedef struct {
    uint8_t mac[NET_MAC_SIZE];
    uint32_t ip;
    uint32_t subnet;
    uint32_t gateway;
    uint32_t dns;
    bool dhcp;
} NetworkConfig;

typedef struct {
    uint8_t dest_mac[NET_MAC_SIZE];
    uint8_t src_mac[NET_MAC_SIZE];
    uint16_t eth_type;
} __attribute__((packed)) EthernetHeader;

typedef struct {
    uint8_t version_ihl;
    uint8_t tos;
    uint16_t total_length;
    uint16_t identification;
    uint16_t flags_fragment;
    uint8_t ttl;
    uint8_t protocol;
    uint16_t checksum;
    uint32_t src_ip;
    uint32_t dest_ip;
} __attribute__((packed)) IPv4Header;

typedef struct {
    uint8_t type;
    uint8_t code;
    uint16_t checksum;
    uint16_t id;
    uint16_t sequence;
} __attribute__((packed)) ICMPHeader;

typedef struct {
    uint16_t src_port;
    uint16_t dest_port;
    uint16_t length;
    uint16_t checksum;
} __attribute__((packed)) UDPHeader;

typedef struct {
    uint16_t src_port;
    uint16_t dest_port;
    uint32_t seq_num;
    uint32_t ack_num;
    uint8_t data_offset_flags;
    uint8_t flags;
    uint16_t window;
    uint16_t checksum;
    uint16_t urgent;
} __attribute__((packed)) TCPHeader;

typedef struct {
    uint16_t hw_type;
    uint16_t proto_type;
    uint8_t hw_size;
    uint8_t proto_size;
    uint16_t opcode;
    uint8_t sender_mac[NET_MAC_SIZE];
    uint32_t sender_ip;
    uint8_t target_mac[NET_MAC_SIZE];
    uint32_t target_ip;
} __attribute__((packed)) ARPHeader;

typedef enum {
    NET_EVENT_RX = 0,
    NET_EVENT_TX_COMPLETE,
    NET_EVENT_LINK_UP,
    NET_EVENT_LINK_DOWN,
    NET_EVENT_ERROR
} NetworkEventType;

typedef struct {
    NetworkEventType type;
    uint32_t data_len;
    uint8_t data[NET_MAX_PACKET];
} NetworkEvent;

typedef void (*NetworkCallback)(NetworkEvent* event, void* user_data);

typedef struct {
    Driver driver;
    Device device;
    NetworkType type;
    NetworkState state;
    NetworkConfig config;
    uint16_t io_base;
    uint32_t irq;
    uint32_t mmio_base;
    bool tx_busy;
    bool link_up;
    uint32_t link_speed;
    uint32_t tx_packets;
    uint32_t rx_packets;
    uint32_t tx_errors;
    uint32_t rx_errors;
    NetworkCallback callback;
    void* callback_data;
    RingBuffer rx_buffer;
    uint8_t rx_buffer_data[NET_BUFFER_SIZE];
    RingBuffer tx_buffer;
    uint8_t tx_buffer_data[NET_BUFFER_SIZE];
    HALContext* hal;
    bool initialized;
} NetworkDriver;

DriverStatus network_init_driver(NetworkDriver* net, HALContext* hal, uint16_t io_base, uint32_t irq);
DriverStatus network_shutdown_driver(NetworkDriver* net);

DriverStatus network_get_mac(NetworkDriver* net, uint8_t* mac);
DriverStatus network_set_mac(NetworkDriver* net, const uint8_t* mac);
DriverStatus network_set_ip(NetworkDriver* net, uint32_t ip, uint32_t subnet, uint32_t gateway);
DriverStatus network_get_config(NetworkDriver* net, NetworkConfig* config);

DriverStatus network_send_packet(NetworkDriver* net, const void* data, uint32_t len);
DriverStatus network_receive_packet(NetworkDriver* net, void* data, uint32_t len, uint32_t* received);

DriverStatus network_set_callback(NetworkDriver* net, NetworkCallback callback, void* user_data);
NetworkState network_get_state(NetworkDriver* net);
bool network_is_linked(NetworkDriver* net);

uint16_t network_calc_checksum(const void* data, uint32_t len);
void network_set_mac_addr(uint8_t* dest, const uint8_t* src);
bool network_cmp_mac(const uint8_t* mac1, const uint8_t* mac2);
void network_ip_to_str(uint32_t ip, char* str);
uint32_t network_str_to_ip(const char* str);

#endif
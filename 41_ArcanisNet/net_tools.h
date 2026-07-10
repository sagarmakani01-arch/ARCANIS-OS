/**
 * net_tools.h — Network Configuration Tools
 *
 * ifconfig, netstat, route, arp, and network utilities.
 */
#ifndef ARCANIS_NET_TOOLS_H
#define ARCANIS_NET_TOOLS_H

#include <arcanis/types.h>
#include <arcanis/net_stack.h>

#define NET_MAX_INTERFACES  8
#define NET_MAX_ROUTES     32
#define NET_MAX_ARP        64
#define NET_MAX_SOCKETS    32
#define NET_IF_NAME_LEN    16

typedef enum {
    IFACE_DOWN,
    IFACE_UP,
    IFACE_RUNNING
} iface_state_t;

typedef struct {
    char        name[NET_IF_NAME_LEN];
    uint32_t    ip;
    uint32_t    netmask;
    uint32_t    gateway;
    uint32_t    broadcast;
    uint8_t     mac[6];
    iface_state_t state;
    uint64_t    rx_bytes;
    uint64_t    tx_bytes;
    uint64_t    rx_packets;
    uint64_t    tx_packets;
    uint64_t    rx_errors;
    uint64_t    tx_errors;
    uint64_t    rx_dropped;
    uint64_t    tx_dropped;
    int         mtu;
    int         metric;
    int         is_loopback;
} net_interface_t;

typedef struct {
    uint32_t    dest;
    uint32_t    gateway;
    uint32_t    netmask;
    char        iface[NET_IF_NAME_LEN];
    uint32_t    metric;
    uint32_t    flags;
    uint32_t    refcnt;
    uint32_t    use;
} net_route_t;

typedef struct {
    uint32_t    ip;
    uint8_t     mac[6];
    char        iface[NET_IF_NAME_LEN];
    uint32_t    flags;
    uint32_t    expires;
} net_arp_entry_t;

typedef struct {
    int         fd;
    uint32_t    local_ip;
    uint16_t    local_port;
    uint32_t    remote_ip;
    uint16_t    remote_port;
    int         state;
    uint64_t    rx_bytes;
    uint64_t    tx_bytes;
    char        process[32];
    uint32_t    pid;
} net_socket_info_t;

typedef struct {
    net_interface_t interfaces[NET_MAX_INTERFACES];
    uint32_t        num_interfaces;
    net_route_t     routes[NET_MAX_ROUTES];
    uint32_t        num_routes;
    net_arp_entry_t arp_table[NET_MAX_ARP];
    uint32_t        num_arp;
    net_socket_info_t sockets[NET_MAX_SOCKETS];
    uint32_t        num_sockets;
} net_tools_state_t;

/* Initialize network tools */
void net_tools_init(net_tools_state_t* state);

/* ifconfig */
int  net_ifconfig_list(net_tools_state_t* state);
int  net_ifconfig_up(net_tools_state_t* state, const char* name);
int  net_ifconfig_down(net_tools_state_t* state, const char* name);
int  net_ifconfig_set_ip(net_tools_state_t* state, const char* name, uint32_t ip);
int  net_ifconfig_set_mask(net_tools_state_t* state, const char* name, uint32_t mask);
int  net_ifconfig_set_gw(net_tools_state_t* state, const char* name, uint32_t gw);
net_interface_t* net_ifconfig_find(net_tools_state_t* state, const char* name);

/* netstat */
int  net_netstat_sockets(net_tools_state_t* state);
int  net_netstat_routes(net_tools_state_t* state);
int  net_netstat_arp(net_tools_state_t* state);
int  net_netstat_stats(net_tools_state_t* state);

/* route */
int  net_route_add(net_tools_state_t* state, uint32_t dest, uint32_t gw, uint32_t mask, const char* iface);
int  net_route_del(net_tools_state_t* state, uint32_t dest);
net_route_t* net_route_lookup(net_tools_state_t* state, uint32_t dest);

/* arp */
int  net_arp_add(net_tools_state_t* state, uint32_t ip, const uint8_t* mac, const char* iface);
int  net_arp_del(net_tools_state_t* state, uint32_t ip);
net_arp_entry_t* net_arp_lookup(net_tools_state_t* state, uint32_t ip);

/* Utility */
const char* net_ip_str(uint32_t ip, char* buf);
uint32_t    net_str_ip(const char* str);
const char* net_iface_state_str(iface_state_t state);
const char* net_sock_state_str(int state);

#endif

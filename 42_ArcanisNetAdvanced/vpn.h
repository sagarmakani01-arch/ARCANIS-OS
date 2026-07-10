/**
 * vpn.h — Virtual Private Network
 *
 * VPN tunnel support with encryption, authentication, and routing.
 */
#ifndef ARCANIS_VPN_H
#define ARCANIS_VPN_H

#include <arcanis/types.h>

#define VPN_MAX_TUNNELS    8
#define VPN_MAX_PEERS      32
#define VPN_MAX_ROUTES     64
#define VPN_MAX_NAME       64
#define VPN_MAX_KEY        32
#define VPN_MAX_ADDR       16

typedef enum {
    VPN_STATE_DISCONNECTED,
    VPN_STATE_CONNECTING,
    VPN_STATE_CONNECTED,
    VPN_STATE_ERROR
} vpn_state_t;

typedef enum {
    VPN_TYPE_OPENVPN,
    VPN_TYPE_WIREGUARD,
    VPN_TYPE_IPSEC,
    VPN_TYPE_L2TP
} vpn_type_t;

typedef struct {
    uint32_t id;
    char name[VPN_MAX_NAME];
    vpn_type_t type;
    vpn_state_t state;

    /* Local config */
    char local_addr[VPN_MAX_ADDR];
    uint16_t local_port;

    /* Remote config */
    char remote_addr[VPN_MAX_ADDR];
    uint16_t remote_port;

    /* Keys */
    uint8_t private_key[VPN_MAX_KEY];
    uint8_t public_key[VPN_MAX_KEY];
    uint8_t preshared_key[VPN_MAX_KEY];

    /* Tunnel */
    uint32_t tunnel_fd;
    char tunnel_dev[32];
    uint32_t mtu;

    /* Encryption */
    char cipher[32];
    char hash[32];

    /* Statistics */
    uint64_t bytes_sent;
    uint64_t bytes_received;
    uint64_t packets_sent;
    uint64_t packets_received;
    uint64_t errors;
    uint64_t reconnects;

    /* Timeouts */
    uint32_t keepalive_interval;
    uint32_t keepalive_timeout;
    uint32_t handshake_timeout;
} vpn_tunnel_t;

typedef struct {
    uint32_t id;
    char name[VPN_MAX_NAME];
    char address[VPN_MAX_ADDR];
    uint32_t public_key;
    uint32_t allowed_ips;
    uint32_t endpoint;
    uint16_t port;
    int      connected;
    uint64_t last_handshake;
} vpn_peer_t;

typedef struct {
    char destination[VPN_MAX_ADDR];
    uint32_t mask;
    char gateway[VPN_MAX_ADDR];
    uint32_t metric;
    int enabled;
} vpn_route_t;

typedef struct {
    vpn_tunnel_t tunnels[VPN_MAX_TUNNELS];
    vpn_peer_t peers[VPN_MAX_PEERS];
    vpn_route_t routes[VPN_MAX_ROUTES];
    uint32_t num_tunnels;
    uint32_t num_peers;
    uint32_t num_routes;
    uint32_t next_id;
} vpn_manager_t;

/* Initialize VPN manager */
void vpn_init(vpn_manager_t* mgr);

/* Tunnel management */
int   vpn_create_tunnel(vpn_manager_t* mgr, const char* name, vpn_type_t type);
int   vpn_destroy_tunnel(vpn_manager_t* mgr, uint32_t id);
int   vpn_connect(vpn_manager_t* mgr, uint32_t id);
int   vpn_disconnect(vpn_manager_t* mgr, uint32_t id);
int   vpn_reconnect(vpn_manager_t* mgr, uint32_t id);

/* Configuration */
int   vpn_set_local(vpn_manager_t* mgr, uint32_t id, const char* addr, uint16_t port);
int   vpn_set_remote(vpn_manager_t* mgr, uint32_t id, const char* addr, uint16_t port);
int   vpn_set_keys(vpn_manager_t* mgr, uint32_t id,
                   const uint8_t* privkey, const uint8_t* pubkey);
int   vpn_set_cipher(vpn_manager_t* mgr, uint32_t id, const char* cipher, const char* hash);

/* Peer management */
int   vpn_add_peer(vpn_manager_t* mgr, uint32_t tunnel_id, const vpn_peer_t* peer);
int   vpn_remove_peer(vpn_manager_t* mgr, uint32_t tunnel_id, uint32_t peer_id);
int   vpn_list_peers(vpn_manager_t* mgr, uint32_t tunnel_id, char* buf, uint32_t buf_len);

/* Route management */
int   vpn_add_route(vpn_manager_t* mgr, const char* dest, uint32_t mask, const char* gw);
int   vpn_remove_route(vpn_manager_t* mgr, const char* dest);
int   vpn_list_routes(vpn_manager_t* mgr, char* buf, uint32_t buf_len);

/* Data transfer */
int   vpn_send(vpn_manager_t* mgr, uint32_t id, const uint8_t* data, uint32_t len);
int   vpn_recv(vpn_manager_t* mgr, uint32_t id, uint8_t* data, uint32_t len, uint32_t* actual);

/* Status */
int   vpn_get_status(vpn_manager_t* mgr, uint32_t id, char* buf, uint32_t buf_len);
int   vpn_get_stats(vpn_manager_t* mgr, uint32_t id, char* buf, uint32_t buf_len);
int   vpn_list_tunnels(vpn_manager_t* mgr, char* buf, uint32_t buf_len);

#endif

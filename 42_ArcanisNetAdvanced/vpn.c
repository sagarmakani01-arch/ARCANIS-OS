/**
 * vpn.c — Virtual Private Network Implementation
 *
 * VPN tunnel support with encryption, authentication, and routing.
 */
#include <arcanis/vpn.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <stdio.h>
#include <stdlib.h>

/* ---- Initialization ---- */

void vpn_init(vpn_manager_t* mgr) {
    if (!mgr) return;
    memset(mgr, 0, sizeof(vpn_manager_t));
    mgr->next_id = 1;
}

/* ---- Tunnel management ---- */

static vpn_tunnel_t* find_tunnel(vpn_manager_t* mgr, uint32_t id) {
    for (uint32_t i = 0; i < mgr->num_tunnels; i++) {
        if (mgr->tunnels[i].id == id)
            return &mgr->tunnels[i];
    }
    return NULL;
}

int vpn_create_tunnel(vpn_manager_t* mgr, const char* name, vpn_type_t type) {
    if (!mgr || !name) return -1;
    if (mgr->num_tunnels >= VPN_MAX_TUNNELS) return -1;

    vpn_tunnel_t* tunnel = &mgr->tunnels[mgr->num_tunnels];
    memset(tunnel, 0, sizeof(vpn_tunnel_t));

    tunnel->id = mgr->next_id++;
    string_copy(tunnel->name, name, VPN_MAX_NAME);
    tunnel->type = type;
    tunnel->state = VPN_STATE_DISCONNECTED;
    tunnel->mtu = 1500;
    string_copy(tunnel->cipher, "AES-256-GCM", 32);
    string_copy(tunnel->hash, "SHA-256", 32);
    tunnel->keepalive_interval = 25;
    tunnel->keepalive_timeout = 120;

    mgr->num_tunnels++;
    return (int)tunnel->id;
}

int vpn_destroy_tunnel(vpn_manager_t* mgr, uint32_t id) {
    if (!mgr) return -1;

    vpn_tunnel_t* tunnel = find_tunnel(mgr, id);
    if (!tunnel) return -1;

    if (tunnel->state == VPN_STATE_CONNECTED)
        vpn_disconnect(mgr, id);

    /* Remove from array */
    for (uint32_t i = 0; i < mgr->num_tunnels; i++) {
        if (mgr->tunnels[i].id == id) {
            for (uint32_t j = i; j < mgr->num_tunnels - 1; j++)
                mgr->tunnels[j] = mgr->tunnels[j + 1];
            mgr->num_tunnels--;
            break;
        }
    }

    return 0;
}

int vpn_connect(vpn_manager_t* mgr, uint32_t id) {
    if (!mgr) return -1;

    vpn_tunnel_t* tunnel = find_tunnel(mgr, id);
    if (!tunnel) return -1;
    if (tunnel->state != VPN_STATE_DISCONNECTED) return -1;

    tunnel->state = VPN_STATE_CONNECTING;

    /* Simulate connection process */
    printf("[VPN] Connecting to %s:%u...\n", tunnel->remote_addr, tunnel->remote_port);
    printf("[VPN] Performing handshake...\n");
    printf("[VPN] Establishing encrypted tunnel...\n");

    tunnel->state = VPN_STATE_CONNECTED;
    printf("[VPN] Connected to %s\n", tunnel->remote_addr);

    return 0;
}

int vpn_disconnect(vpn_manager_t* mgr, uint32_t id) {
    if (!mgr) return -1;

    vpn_tunnel_t* tunnel = find_tunnel(mgr, id);
    if (!tunnel) return -1;
    if (tunnel->state != VPN_STATE_CONNECTED) return -1;

    tunnel->state = VPN_STATE_DISCONNECTED;
    printf("[VPN] Disconnected from %s\n", tunnel->remote_addr);

    return 0;
}

int vpn_reconnect(vpn_manager_t* mgr, uint32_t id) {
    if (!mgr) return -1;

    vpn_tunnel_t* tunnel = find_tunnel(mgr, id);
    if (!tunnel) return -1;

    tunnel->reconnects++;
    vpn_disconnect(mgr, id);
    return vpn_connect(mgr, id);
}

/* ---- Configuration ---- */

int vpn_set_local(vpn_manager_t* mgr, uint32_t id, const char* addr, uint16_t port) {
    if (!mgr || !addr) return -1;

    vpn_tunnel_t* tunnel = find_tunnel(mgr, id);
    if (!tunnel) return -1;

    string_copy(tunnel->local_addr, addr, VPN_MAX_ADDR);
    tunnel->local_port = port;
    return 0;
}

int vpn_set_remote(vpn_manager_t* mgr, uint32_t id, const char* addr, uint16_t port) {
    if (!mgr || !addr) return -1;

    vpn_tunnel_t* tunnel = find_tunnel(mgr, id);
    if (!tunnel) return -1;

    string_copy(tunnel->remote_addr, addr, VPN_MAX_ADDR);
    tunnel->remote_port = port;
    return 0;
}

int vpn_set_keys(vpn_manager_t* mgr, uint32_t id,
                 const uint8_t* privkey, const uint8_t* pubkey) {
    if (!mgr) return -1;

    vpn_tunnel_t* tunnel = find_tunnel(mgr, id);
    if (!tunnel) return -1;

    if (privkey) memcpy(tunnel->private_key, privkey, VPN_MAX_KEY);
    if (pubkey) memcpy(tunnel->public_key, pubkey, VPN_MAX_KEY);
    return 0;
}

int vpn_set_cipher(vpn_manager_t* mgr, uint32_t id, const char* cipher, const char* hash) {
    if (!mgr) return -1;

    vpn_tunnel_t* tunnel = find_tunnel(mgr, id);
    if (!tunnel) return -1;

    if (cipher) string_copy(tunnel->cipher, cipher, 32);
    if (hash) string_copy(tunnel->hash, hash, 32);
    return 0;
}

/* ---- Peer management ---- */

int vpn_add_peer(vpn_manager_t* mgr, uint32_t tunnel_id, const vpn_peer_t* peer) {
    if (!mgr || !peer) return -1;
    if (mgr->num_peers >= VPN_MAX_PEERS) return -1;

    vpn_peer_t* new_peer = &mgr->peers[mgr->num_peers++];
    memcpy(new_peer, peer, sizeof(vpn_peer_t));
    new_peer->id = mgr->num_peers;

    return (int)new_peer->id;
}

int vpn_remove_peer(vpn_manager_t* mgr, uint32_t tunnel_id, uint32_t peer_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_peers; i++) {
        if (mgr->peers[i].id == peer_id) {
            for (uint32_t j = i; j < mgr->num_peers - 1; j++)
                mgr->peers[j] = mgr->peers[j + 1];
            mgr->num_peers--;
            return 0;
        }
    }
    return -1;
}

int vpn_list_peers(vpn_manager_t* mgr, uint32_t tunnel_id, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos,
        "PEER            ADDRESS         STATUS\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "----------------------------------------\n");

    for (uint32_t i = 0; i < mgr->num_peers && pos < buf_len - 100; i++) {
        vpn_peer_t* p = &mgr->peers[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-15s %-15s %s\n",
            p->name, p->address, p->connected ? "connected" : "disconnected");
    }

    return (int)pos;
}

/* ---- Route management ---- */

int vpn_add_route(vpn_manager_t* mgr, const char* dest, uint32_t mask, const char* gw) {
    if (!mgr || !dest || !gw) return -1;
    if (mgr->num_routes >= VPN_MAX_ROUTES) return -1;

    vpn_route_t* route = &mgr->routes[mgr->num_routes++];
    string_copy(route->destination, dest, VPN_MAX_ADDR);
    route->mask = mask;
    string_copy(route->gateway, gw, VPN_MAX_ADDR);
    route->metric = 0;
    route->enabled = 1;

    return 0;
}

int vpn_remove_route(vpn_manager_t* mgr, const char* dest) {
    if (!mgr || !dest) return -1;

    for (uint32_t i = 0; i < mgr->num_routes; i++) {
        if (string_compare(mgr->routes[i].destination, dest) == 0) {
            for (uint32_t j = i; j < mgr->num_routes - 1; j++)
                mgr->routes[j] = mgr->routes[j + 1];
            mgr->num_routes--;
            return 0;
        }
    }
    return -1;
}

int vpn_list_routes(vpn_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos,
        "DESTINATION     GATEWAY         METRIC\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "----------------------------------------\n");

    for (uint32_t i = 0; i < mgr->num_routes && pos < buf_len - 100; i++) {
        vpn_route_t* r = &mgr->routes[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-15s %-15s %u\n",
            r->destination, r->gateway, r->metric);
    }

    return (int)pos;
}

/* ---- Data transfer ---- */

int vpn_send(vpn_manager_t* mgr, uint32_t id, const uint8_t* data, uint32_t len) {
    if (!mgr || !data) return -1;

    vpn_tunnel_t* tunnel = find_tunnel(mgr, id);
    if (!tunnel) return -1;
    if (tunnel->state != VPN_STATE_CONNECTED) return -1;

    /* Simulate encryption and sending */
    tunnel->bytes_sent += len;
    tunnel->packets_sent++;

    return (int)len;
}

int vpn_recv(vpn_manager_t* mgr, uint32_t id, uint8_t* data, uint32_t len, uint32_t* actual) {
    if (!mgr || !data || !actual) return -1;

    vpn_tunnel_t* tunnel = find_tunnel(mgr, id);
    if (!tunnel) return -1;
    if (tunnel->state != VPN_STATE_CONNECTED) return -1;

    /* Simulate receiving and decryption */
    *actual = 0; /* No data available */
    return 0;
}

/* ---- Status ---- */

int vpn_get_status(vpn_manager_t* mgr, uint32_t id, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    vpn_tunnel_t* tunnel = find_tunnel(mgr, id);
    if (!tunnel) return -1;

    const char* state_str = "unknown";
    switch (tunnel->state) {
        case VPN_STATE_DISCONNECTED: state_str = "disconnected"; break;
        case VPN_STATE_CONNECTING:   state_str = "connecting"; break;
        case VPN_STATE_CONNECTED:    state_str = "connected"; break;
        case VPN_STATE_ERROR:        state_str = "error"; break;
    }

    const char* type_str = "unknown";
    switch (tunnel->type) {
        case VPN_TYPE_OPENVPN:  type_str = "OpenVPN"; break;
        case VPN_TYPE_WIREGUARD: type_str = "WireGuard"; break;
        case VPN_TYPE_IPSEC:    type_str = "IPSec"; break;
        case VPN_TYPE_L2TP:     type_str = "L2TP"; break;
    }

    return snprintf(buf, buf_len,
        "VPN Tunnel: %s\n"
        "  Type: %s\n"
        "  State: %s\n"
        "  Local: %s:%u\n"
        "  Remote: %s:%u\n"
        "  Cipher: %s\n"
        "  Hash: %s\n"
        "  MTU: %u\n",
        tunnel->name, type_str, state_str,
        tunnel->local_addr, tunnel->local_port,
        tunnel->remote_addr, tunnel->remote_port,
        tunnel->cipher, tunnel->hash,
        tunnel->mtu);
}

int vpn_get_stats(vpn_manager_t* mgr, uint32_t id, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    vpn_tunnel_t* tunnel = find_tunnel(mgr, id);
    if (!tunnel) return -1;

    return snprintf(buf, buf_len,
        "VPN Statistics for %s:\n"
        "  Bytes Sent: %llu\n"
        "  Bytes Received: %llu\n"
        "  Packets Sent: %llu\n"
        "  Packets Received: %llu\n"
        "  Errors: %llu\n"
        "  Reconnects: %u\n",
        tunnel->name,
        (unsigned long long)tunnel->bytes_sent,
        (unsigned long long)tunnel->bytes_received,
        (unsigned long long)tunnel->packets_sent,
        (unsigned long long)tunnel->packets_received,
        (unsigned long long)tunnel->errors,
        tunnel->reconnects);
}

int vpn_list_tunnels(vpn_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos,
        "ID  NAME            TYPE         STATE        REMOTE\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "------------------------------------------------------\n");

    for (uint32_t i = 0; i < mgr->num_tunnels && pos < buf_len - 150; i++) {
        vpn_tunnel_t* t = &mgr->tunnels[i];
        const char* state = t->state == 0 ? "disconnected" :
                           t->state == 1 ? "connecting" :
                           t->state == 2 ? "connected" : "error";
        pos += snprintf(buf + pos, buf_len - pos,
            "%-3u %-15s %-12s %-12s %s\n",
            t->id, t->name,
            t->type == 0 ? "OpenVPN" : t->type == 1 ? "WireGuard" : "Other",
            state, t->remote_addr);
    }

    return (int)pos;
}

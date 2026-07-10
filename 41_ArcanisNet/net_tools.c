/**
 * net_tools.c — Network Configuration Tools Implementation
 *
 * ifconfig, netstat, route, arp utilities.
 */
#include <arcanis/net_tools.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

void net_tools_init(net_tools_state_t* state) {
    if (!state) return;
    memset(state, 0, sizeof(net_tools_state_t));

    /* Add default interfaces */
    net_interface_t* lo = &state->interfaces[state->num_interfaces++];
    string_copy(lo->name, "lo", NET_IF_NAME_LEN);
    lo->ip = 0x7F000001; /* 127.0.0.1 */
    lo->netmask = 0xFF000000;
    lo->state = IFACE_UP;
    lo->is_loopback = 1;
    lo->mtu = 65536;

    net_interface_t* eth0 = &state->interfaces[state->num_interfaces++];
    string_copy(eth0->name, "eth0", NET_IF_NAME_LEN);
    eth0->ip = 0xC0A80164; /* 192.168.1.100 */
    eth0->netmask = 0xFFFFFF00; /* 255.255.255.0 */
    eth0->gateway = 0xC0A80101; /* 192.168.1.1 */
    eth0->broadcast = 0xC0A801FF;
    eth0->mac[0] = 0x02; eth0->mac[1] = 0x42;
    eth0->mac[2] = 0xAC; eth0->mac[3] = 0x11;
    eth0->mac[4] = 0x00; eth0->mac[5] = 0x02;
    eth0->state = IFACE_RUNNING;
    eth0->mtu = 1500;

    /* Add default route */
    net_route_t* rt = &state->routes[state->num_routes++];
    rt->dest = 0x00000000;
    rt->gateway = 0xC0A80101;
    rt->netmask = 0x00000000;
    string_copy(rt->iface, "eth0", NET_IF_NAME_LEN);
    rt->metric = 100;

    net_route_t* rt2 = &state->routes[state->num_routes++];
    rt2->dest = 0xC0A80100; /* 192.168.1.0 */
    rt2->gateway = 0x00000000;
    rt2->netmask = 0xFFFFFF00;
    string_copy(rt2->iface, "eth0", NET_IF_NAME_LEN);
    rt2->metric = 0;

    /* Add ARP entry */
    net_arp_entry_t* arp = &state->arp_table[state->num_arp++];
    arp->ip = 0xC0A80101;
    arp->mac[0] = 0xAA; arp->mac[1] = 0xBB;
    arp->mac[2] = 0xCC; arp->mac[3] = 0xDD;
    arp->mac[4] = 0xEE; arp->mac[5] = 0xFF;
    string_copy(arp->iface, "eth0", NET_IF_NAME_LEN);

    /* Add socket info */
    net_socket_info_t* sock = &state->sockets[state->num_sockets++];
    sock->fd = 3;
    sock->local_ip = 0xC0A80164;
    sock->local_port = 22;
    sock->remote_ip = 0xC0A8010A;
    sock->remote_port = 45678;
    sock->state = 1; /* ESTABLISHED */
    string_copy(sock->process, "sshd", 32);
    sock->pid = 12;
}

/* ---- Utility ---- */

const char* net_ip_str(uint32_t ip, char* buf) {
    if (!buf) return "";
    uint8_t* bytes = (uint8_t*)&ip;
    uint32_t pos = 0;
    for (int i = 0; i < 4; i++) {
        uint8_t b = bytes[i];
        if (b >= 100) buf[pos++] = '0' + b / 100;
        if (b >= 10) buf[pos++] = '0' + (b / 10) % 10;
        buf[pos++] = '0' + b % 10;
        if (i < 3) buf[pos++] = '.';
    }
    buf[pos] = '\0';
    return buf;
}

uint32_t net_str_ip(const char* str) {
    if (!str) return 0;
    uint32_t result = 0;
    uint32_t octet = 0;
    while (*str) {
        if (*str == '.') {
            result = (result << 8) | octet;
            octet = 0;
        } else if (*str >= '0' && *str <= '9') {
            octet = octet * 10 + (*str - '0');
        }
        str++;
    }
    result = (result << 8) | octet;
    return result;
}

const char* net_iface_state_str(iface_state_t state) {
    switch (state) {
        case IFACE_DOWN:    return "DOWN";
        case IFACE_UP:      return "UP";
        case IFACE_RUNNING: return "UP,RUNNING";
        default:            return "UNKNOWN";
    }
}

const char* net_sock_state_str(int state) {
    switch (state) {
        case 0: return "LISTEN";
        case 1: return "ESTABLISHED";
        case 2: return "TIME_WAIT";
        case 3: return "CLOSE_WAIT";
        case 4: return "FIN_WAIT1";
        case 5: return "FIN_WAIT2";
        case 6: return "SYN_SENT";
        case 7: return "SYN_RECV";
        default: return "UNKNOWN";
    }
}

/* ---- ifconfig ---- */

net_interface_t* net_ifconfig_find(net_tools_state_t* state, const char* name) {
    if (!state || !name) return NULL;
    for (uint32_t i = 0; i < state->num_interfaces; i++)
        if (string_compare(state->interfaces[i].name, name) == 0)
            return &state->interfaces[i];
    return NULL;
}

int net_ifconfig_list(net_tools_state_t* state) {
    if (!state) return -1;
    for (uint32_t i = 0; i < state->num_interfaces; i++) {
        net_interface_t* iface = &state->interfaces[i];
        /* Print interface info */
    }
    return 0;
}

int net_ifconfig_up(net_tools_state_t* state, const char* name) {
    net_interface_t* iface = net_ifconfig_find(state, name);
    if (!iface) return -1;
    iface->state = IFACE_UP;
    return 0;
}

int net_ifconfig_down(net_tools_state_t* state, const char* name) {
    net_interface_t* iface = net_ifconfig_find(state, name);
    if (!iface) return -1;
    iface->state = IFACE_DOWN;
    return 0;
}

int net_ifconfig_set_ip(net_tools_state_t* state, const char* name, uint32_t ip) {
    net_interface_t* iface = net_ifconfig_find(state, name);
    if (!iface) return -1;
    iface->ip = ip;
    return 0;
}

int net_ifconfig_set_mask(net_tools_state_t* state, const char* name, uint32_t mask) {
    net_interface_t* iface = net_ifconfig_find(state, name);
    if (!iface) return -1;
    iface->netmask = mask;
    return 0;
}

int net_ifconfig_set_gw(net_tools_state_t* state, const char* name, uint32_t gw) {
    net_interface_t* iface = net_ifconfig_find(state, name);
    if (!iface) return -1;
    iface->gateway = gw;
    return 0;
}

/* ---- netstat ---- */

int net_netstat_sockets(net_tools_state_t* state) {
    if (!state) return -1;
    /* Print socket table */
    return 0;
}

int net_netstat_routes(net_tools_state_t* state) {
    if (!state) return -1;
    /* Print routing table */
    return 0;
}

int net_netstat_arp(net_tools_state_t* state) {
    if (!state) return -1;
    /* Print ARP table */
    return 0;
}

int net_netstat_stats(net_tools_state_t* state) {
    if (!state) return -1;
    /* Print network statistics */
    return 0;
}

/* ---- route ---- */

int net_route_add(net_tools_state_t* state, uint32_t dest, uint32_t gw, uint32_t mask, const char* iface) {
    if (!state || state->num_routes >= NET_MAX_ROUTES) return -1;

    net_route_t* rt = &state->routes[state->num_routes++];
    rt->dest = dest;
    rt->gateway = gw;
    rt->netmask = mask;
    string_copy(rt->iface, iface, NET_IF_NAME_LEN);
    rt->metric = 0;
    return 0;
}

int net_route_del(net_tools_state_t* state, uint32_t dest) {
    if (!state) return -1;
    for (uint32_t i = 0; i < state->num_routes; i++) {
        if (state->routes[i].dest == dest) {
            for (uint32_t j = i; j < state->num_routes - 1; j++)
                state->routes[j] = state->routes[j + 1];
            state->num_routes--;
            return 0;
        }
    }
    return -1;
}

net_route_t* net_route_lookup(net_tools_state_t* state, uint32_t dest) {
    if (!state) return NULL;
    /* Longest prefix match */
    net_route_t* best = NULL;
    int best_prefix = -1;
    for (uint32_t i = 0; i < state->num_routes; i++) {
        net_route_t* rt = &state->routes[i];
        if ((dest & rt->netmask) == (rt->dest & rt->netmask)) {
            int prefix = 0;
            uint32_t m = rt->netmask;
            while (m & 0x80000000) { prefix++; m <<= 1; }
            if (prefix > best_prefix) {
                best_prefix = prefix;
                best = rt;
            }
        }
    }
    return best;
}

/* ---- arp ---- */

int net_arp_add(net_tools_state_t* state, uint32_t ip, const uint8_t* mac, const char* iface) {
    if (!state || state->num_arp >= NET_MAX_ARP) return -1;

    net_arp_entry_t* entry = &state->arp_table[state->num_arp++];
    entry->ip = ip;
    memcpy(entry->mac, mac, 6);
    string_copy(entry->iface, iface, NET_IF_NAME_LEN);
    entry->flags = 0x2; /* PERMANENT */
    return 0;
}

int net_arp_del(net_tools_state_t* state, uint32_t ip) {
    if (!state) return -1;
    for (uint32_t i = 0; i < state->num_arp; i++) {
        if (state->arp_table[i].ip == ip) {
            for (uint32_t j = i; j < state->num_arp - 1; j++)
                state->arp_table[j] = state->arp_table[j + 1];
            state->num_arp--;
            return 0;
        }
    }
    return -1;
}

net_arp_entry_t* net_arp_lookup(net_tools_state_t* state, uint32_t ip) {
    if (!state) return NULL;
    for (uint32_t i = 0; i < state->num_arp; i++)
        if (state->arp_table[i].ip == ip)
            return &state->arp_table[i];
    return NULL;
}

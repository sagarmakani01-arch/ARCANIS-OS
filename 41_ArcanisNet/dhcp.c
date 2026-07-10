/**
 * dhcp.c — DHCP Client Implementation
 *
 * DHCP discovery, request, and lease management.
 */
#include <arcanis/dhcp.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

void dhcp_init(dhcp_client_t* client, const uint8_t* mac) {
    if (!client) return;
    memset(client, 0, sizeof(dhcp_client_t));
    client->state = DHCP_STATE_INIT;
    client->enabled = 1;
    if (mac) memcpy(client->mac, mac, 6);
    client->xid = 0x12345678;
}

/* ---- Packet building ---- */

static void dhcp_add_option(uint8_t* buf, uint32_t* offset, uint8_t code, const uint8_t* data, uint8_t len) {
    buf[(*offset)++] = code;
    buf[(*offset)++] = len;
    if (data && len > 0) {
        memcpy(buf + *offset, data, len);
        *offset += len;
    }
}

int dhcp_build_packet(dhcp_client_t* client, uint8_t type,
                       uint8_t* buf, uint32_t* buf_len) {
    if (!client || !buf || !buf_len) return -1;

    memset(buf, 0, DHCP_BUF_SIZE);
    dhcp_header_t* hdr = (dhcp_header_t*)buf;

    hdr->op = 1; /* BOOTREQUEST */
    hdr->htype = 1; /* Ethernet */
    hdr->hlen = 6;
    hdr->hops = 0;
    hdr->xid = client->xid;
    hdr->secs = 0;
    hdr->flags = 0x0080; /* Broadcast */
    hdr->ciaddr = 0;
    hdr->yiaddr = 0;
    hdr->siaddr = 0;
    hdr->giaddr = 0;
    memcpy(hdr->chaddr, client->mac, 6);
    hdr->magic = DHCP_MAGIC;

    uint32_t offset = sizeof(dhcp_header_t);

    /* Message type option */
    dhcp_add_option(buf, &offset, DHCP_OPT_MSG_TYPE, &type, 1);

    /* Requested IP (for REQUEST) */
    if (type == DHCP_REQUEST && client->offer_ip) {
        uint8_t ip_buf[4];
        ip_buf[0] = client->offer_ip & 0xFF;
        ip_buf[1] = (client->offer_ip >> 8) & 0xFF;
        ip_buf[2] = (client->offer_ip >> 16) & 0xFF;
        ip_buf[3] = (client->offer_ip >> 24) & 0xFF;
        dhcp_add_option(buf, &offset, DHCP_OPT_REQUESTED_IP, ip_buf, 4);
    }

    /* Server ID (for REQUEST) */
    if (type == DHCP_REQUEST && client->server_ip) {
        uint8_t srv_buf[4];
        srv_buf[0] = client->server_ip & 0xFF;
        srv_buf[1] = (client->server_ip >> 8) & 0xFF;
        srv_buf[2] = (client->server_ip >> 16) & 0xFF;
        srv_buf[3] = (client->server_ip >> 24) & 0xFF;
        dhcp_add_option(buf, &offset, DHCP_OPT_SERVER_ID, srv_buf, 4);
    }

    /* Parameter request list */
    uint8_t req_list[] = { DHCP_OPT_SUBNET_MASK, DHCP_OPT_ROUTER,
                           DHCP_OPT_DNS_SERVER, DHCP_OPT_DOMAIN_NAME };
    dhcp_add_option(buf, &offset, DHCP_OPT_REQUEST_LIST, req_list, sizeof(req_list));

    /* Hostname */
    if (client->hostname[0]) {
        dhcp_add_option(buf, &offset, DHCP_OPT_HOSTNAME,
                        (const uint8_t*)client->hostname, string_length(client->hostname));
    }

    /* End option */
    buf[offset++] = DHCP_OPT_END;

    /* Pad to minimum size */
    while (offset < 300) buf[offset++] = DHCP_OPT_PAD;

    *buf_len = offset;
    return 0;
}

/* ---- Options parsing ---- */

int dhcp_parse_options(const uint8_t* data, uint32_t len,
                        dhcp_option_t* options, uint32_t* num_options) {
    if (!data || !options || !num_options) return -1;

    uint32_t offset = 0;
    uint32_t count = 0;

    while (offset < len && count < DHCP_MAX_OPTIONS) {
        uint8_t code = data[offset];

        if (code == DHCP_OPT_END) break;
        if (code == DHCP_OPT_PAD) { offset++; continue; }

        if (offset + 2 > len) break;
        uint8_t opt_len = data[offset + 1];
        if (offset + 2 + opt_len > len) break;

        options[count].code = code;
        options[count].len = opt_len;
        memcpy(options[count].data, data + offset + 2, opt_len);
        count++;
        offset += 2 + opt_len;
    }

    *num_options = count;
    return 0;
}

const dhcp_option_t* dhcp_get_option(const dhcp_option_t* options, uint32_t num, uint8_t code) {
    if (!options) return NULL;
    for (uint32_t i = 0; i < num; i++)
        if (options[i].code == code)
            return &options[i];
    return NULL;
}

/* ---- State machine ---- */

int dhcp_discover(dhcp_client_t* client) {
    if (!client) return -1;
    client->state = DHCP_STATE_SELECTING;
    client->xid++;
    /* In real implementation: send broadcast DHCPDISCOVER */
    return 0;
}

int dhcp_handle_packet(dhcp_client_t* client, const uint8_t* data, uint32_t len) {
    if (!client || !data || len < sizeof(dhcp_header_t)) return -1;

    dhcp_header_t* hdr = (dhcp_header_t*)data;
    if (hdr->magic != DHCP_MAGIC) return -1;

    /* Parse options */
    dhcp_option_t options[DHCP_MAX_OPTIONS];
    uint32_t num_options = 0;
    dhcp_parse_options(data + sizeof(dhcp_header_t),
                       len - sizeof(dhcp_header_t),
                       options, &num_options);

    /* Get message type */
    const dhcp_option_t* msg_type = dhcp_get_option(options, num_options, DHCP_OPT_MSG_TYPE);
    if (!msg_type) return -1;
    uint8_t type = msg_type->data[0];

    switch (client->state) {
        case DHCP_STATE_SELECTING:
            if (type == DHCP_OFFER) {
                client->offer_ip = hdr->yiaddr;
                client->server_ip = 0;
                const dhcp_option_t* srv = dhcp_get_option(options, num_options, DHCP_OPT_SERVER_ID);
                if (srv && srv->len == 4)
                    client->server_ip = *(uint32_t*)srv->data;
                client->state = DHCP_STATE_REQUESTING;
                /* Send DHCPREQUEST */
                dhcp_build_packet(client, DHCP_REQUEST, NULL, NULL);
            }
            break;

        case DHCP_STATE_REQUESTING:
            if (type == DHCP_ACK) {
                client->ip = hdr->yiaddr;
                client->state = DHCP_STATE_BOUND;

                /* Extract options */
                const dhcp_option_t* subnet = dhcp_get_option(options, num_options, DHCP_OPT_SUBNET_MASK);
                if (subnet && subnet->len == 4)
                    client->subnet = *(uint32_t*)subnet->data;

                const dhcp_option_t* router = dhcp_get_option(options, num_options, DHCP_OPT_ROUTER);
                if (router && router->len == 4)
                    client->gateway = *(uint32_t*)router->data;

                const dhcp_option_t* dns = dhcp_get_option(options, num_options, DHCP_OPT_DNS_SERVER);
                if (dns && dns->len >= 4) {
                    for (uint32_t i = 0; i < 4 && i * 4 < dns->len; i++)
                        client->dns[i] = ((uint32_t*)dns->data)[i];
                }

                const dhcp_option_t* lease = dhcp_get_option(options, num_options, DHCP_OPT_LEASE_TIME);
                if (lease && lease->len == 4)
                    client->lease_time = *(uint32_t*)lease->data;

                client->lease_start = 0; /* Current time */
                client->t1 = client->lease_time / 2;
                client->t2 = (client->lease_time * 7) / 8;

            } else if (type == DHCP_NAK) {
                client->state = DHCP_STATE_INIT;
                dhcp_discover(client);
            }
            break;

        default:
            break;
    }

    return 0;
}

/* ---- Lease management ---- */

int dhcp_is_expired(dhcp_client_t* client) {
    if (!client || client->state != DHCP_STATE_BOUND) return 0;
    /* In real implementation: compare current time with lease_start + lease_time */
    return 0;
}

void dhcp_renew(dhcp_client_t* client) {
    if (!client) return;
    if (dhcp_is_expired(client)) {
        client->state = DHCP_STATE_RENEWING;
        /* Send DHCPREQUEST to original server */
    }
}

void dhcp_release(dhcp_client_t* client) {
    if (!client) return;
    /* Send DHCPRELEASE */
    client->state = DHCP_STATE_INIT;
    client->ip = 0;
}

const char* dhcp_state_name(dhcp_state_t state) {
    switch (state) {
        case DHCP_STATE_INIT:       return "INIT";
        case DHCP_STATE_SELECTING:  return "SELECTING";
        case DHCP_STATE_REQUESTING: return "REQUESTING";
        case DHCP_STATE_BOUND:      return "BOUND";
        case DHCP_STATE_RENEWING:   return "RENEWING";
        case DHCP_STATE_REBINDING:  return "REBINDING";
        default:                    return "UNKNOWN";
    }
}

const char* dhcp_msg_type_name(uint8_t type) {
    switch (type) {
        case DHCP_DISCOVER: return "DISCOVER";
        case DHCP_OFFER:    return "OFFER";
        case DHCP_REQUEST:  return "REQUEST";
        case DHCP_ACK:      return "ACK";
        case DHCP_NAK:      return "NAK";
        case DHCP_RELEASE:  return "RELEASE";
        case DHCP_INFORM:   return "INFORM";
        default:            return "UNKNOWN";
    }
}

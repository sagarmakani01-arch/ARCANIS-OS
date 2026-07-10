/**
 * dhcp.h — DHCP Client
 *
 * DHCP discovery, request, and lease management.
 * Supports options parsing and renewal.
 */
#ifndef ARCANIS_DHCP_H
#define ARCANIS_DHCP_H

#include <arcanis/types.h>

#define DHCP_PORT_CLIENT  68
#define DHCP_PORT_SERVER  67
#define DHCP_MAGIC        0x63825363
#define DHCP_MAX_OPTIONS  32
#define DHCP_MAX_SERVERS  4
#define DHCP_BUF_SIZE     548

/* DHCP message types */
#define DHCP_DISCOVER  1
#define DHCP_OFFER     2
#define DHCP_REQUEST   3
#define DHCP_ACK       5
#define DHCP_NAK       6
#define DHCP_RELEASE   7
#define DHCP_INFORM    8

/* DHCP options */
#define DHCP_OPT_PAD           0
#define DHCP_OPT_SUBNET_MASK   1
#define DHCP_OPT_ROUTER        3
#define DHCP_OPT_DNS_SERVER    6
#define DHCP_OPT_HOSTNAME      12
#define DHCP_OPT_DOMAIN_NAME   15
#define DHCP_OPT_BROADCAST     28
#define DHCP_OPT_REQUESTED_IP  50
#define DHCP_OPT_LEASE_TIME    51
#define DHCP_OPT_MSG_TYPE      53
#define DHCP_OPT_SERVER_ID     54
#define DHCP_OPT_REQUEST_LIST  55
#define DHCP_OPT_END           255

#pragma pack(push, 1)
typedef struct {
    uint8_t  op;
    uint8_t  htype;
    uint8_t  hlen;
    uint8_t  hops;
    uint32_t xid;
    uint16_t secs;
    uint16_t flags;
    uint32_t ciaddr;
    uint32_t yiaddr;
    uint32_t siaddr;
    uint32_t giaddr;
    uint8_t  chaddr[16];
    uint8_t  sname[64];
    uint8_t  file[128];
    uint32_t magic;
} dhcp_header_t;
#pragma pack(pop)

typedef struct {
    uint8_t  code;
    uint8_t  len;
    uint8_t  data[255];
} dhcp_option_t;

typedef enum {
    DHCP_STATE_INIT,
    DHCP_STATE_SELECTING,
    DHCP_STATE_REQUESTING,
    DHCP_STATE_BOUND,
    DHCP_STATE_RENEWING,
    DHCP_STATE_REBINDING
} dhcp_state_t;

typedef struct {
    dhcp_state_t state;
    uint32_t     xid;
    uint8_t      mac[6];
    uint32_t     ip;
    uint32_t     subnet;
    uint32_t     gateway;
    uint32_t     dns[DHCP_MAX_SERVERS];
    uint32_t     broadcast;
    uint32_t     lease_time;
    uint32_t     lease_start;
    uint32_t     server_ip;
    uint32_t     t1;       /* Renewal time */
    uint32_t     t2;       /* Rebinding time */
    uint32_t     offer_ip;
    int          enabled;
    char         hostname[64];
} dhcp_client_t;

/* Initialize DHCP client */
void dhcp_init(dhcp_client_t* client, const uint8_t* mac);

/* Start DHCP process */
int  dhcp_discover(dhcp_client_t* client);

/* Handle incoming DHCP packet */
int  dhcp_handle_packet(dhcp_client_t* client, const uint8_t* data, uint32_t len);

/* Build DHCP packet */
int  dhcp_build_packet(dhcp_client_t* client, uint8_t type,
                       uint8_t* buf, uint32_t* buf_len);

/* Parse DHCP options */
int  dhcp_parse_options(const uint8_t* data, uint32_t len,
                        dhcp_option_t* options, uint32_t* num_options);

/* Get option by code */
const dhcp_option_t* dhcp_get_option(const dhcp_option_t* options, uint32_t num, uint8_t code);

/* Lease management */
int  dhcp_is_expired(dhcp_client_t* client);
void dhcp_renew(dhcp_client_t* client);
void dhcp_release(dhcp_client_t* client);

/* State */
const char* dhcp_state_name(dhcp_state_t state);
const char* dhcp_msg_type_name(uint8_t type);

#endif

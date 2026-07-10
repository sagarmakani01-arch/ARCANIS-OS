/**
 * firewall.h — Packet Filtering Firewall
 *
 * iptables-like firewall with chains, rules, and NAT support.
 */
#ifndef ARCANIS_FIREWALL_H
#define ARCANIS_FIREWALL_H

#include <arcanis/types.h>

#define FW_MAX_RULES      256
#define FW_MAX_CHAINS      8
#define FW_MAX_NAME        64
#define FW_MAX_PORTS       32
#define FW_MAX_IFACE       16

typedef enum {
    FW_ACTION_ACCEPT,
    FW_ACTION_DROP,
    FW_ACTION_REJECT,
    FW_ACTION_LOG,
    FW_ACTION_RETURN
} fw_action_t;

typedef enum {
    FW_CHAIN_INPUT,
    FW_CHAIN_OUTPUT,
    FW_CHAIN_FORWARD,
    FW_CHAIN_PREROUTING,
    FW_CHAIN_POSTROUTING
} fw_chain_t;

typedef enum {
    FW_PROTO_TCP,
    FW_PROTO_UDP,
    FW_PROTO_ICMP,
    FW_PROTO_ALL
} fw_protocol_t;

typedef struct {
    uint32_t ip;
    uint32_t mask;
} fw_ip_range_t;

typedef struct {
    uint16_t start;
    uint16_t end;
} fw_port_range_t;

typedef struct {
    uint32_t id;
    int      enabled;
    fw_chain_t chain;
    fw_action_t action;
    fw_protocol_t protocol;

    /* Source */
    fw_ip_range_t src_ip;
    fw_port_range_t src_port;
    char src_iface[FW_MAX_IFACE];

    /* Destination */
    fw_ip_range_t dst_ip;
    fw_port_range_t dst_port;
    char dst_iface[FW_MAX_IFACE];

    /* ICMP */
    uint8_t icmp_type;
    uint8_t icmp_code;

    /* Connection tracking */
    int      stateful;
    int      established;
    int      related;
    int      new_connection;

    /* Logging */
    int      log_packets;
    char     log_prefix[32];

    /* Statistics */
    uint64_t packets_matched;
    uint64_t bytes_matched;

    /* Target */
    char     jump_chain[FW_MAX_NAME];
} fw_rule_t;

typedef struct {
    char name[FW_MAX_NAME];
    fw_action_t default_action;
    fw_rule_t rules[FW_MAX_RULES];
    uint32_t num_rules;
    uint64_t packets_count;
    uint64_t bytes_count;
} fw_chain_def_t;

typedef struct {
    fw_chain_def_t chains[FW_MAX_CHAINS];
    uint32_t num_chains;
    int      enabled;
    uint64_t total_packets;
    uint64_t total_bytes;
    uint64_t packets_dropped;
    uint64_t packets_accepted;
    uint64_t packets_rejected;
} firewall_t;

/* Initialize firewall */
void fw_init(firewall_t* fw);

/* Chain management */
int   fw_create_chain(firewall_t* fw, const char* name, fw_action_t default_action);
int   fw_delete_chain(firewall_t* fw, const char* name);
int   fw_flush_chain(firewall_t* fw, const char* name);
fw_chain_def_t* fw_get_chain(firewall_t* fw, const char* name);

/* Rule management */
int   fw_add_rule(firewall_t* fw, const char* chain_name, const fw_rule_t* rule);
int   fw_delete_rule(firewall_t* fw, const char* chain_name, uint32_t rule_id);
int   fw_replace_rule(firewall_t* fw, const char* chain_name, uint32_t rule_id, const fw_rule_t* rule);
int   fw_enable_rule(firewall_t* fw, const char* chain_name, uint32_t rule_id);
int   fw_disable_rule(firewall_t* fw, const char* chain_name, uint32_t rule_id);

/* Packet matching */
int   fw_match_packet(firewall_t* fw, const char* chain_name,
                      uint32_t src_ip, uint16_t src_port,
                      uint32_t dst_ip, uint16_t dst_port,
                      uint8_t protocol, uint8_t* action);

/* NAT */
int   fw_add_nat_rule(firewall_t* fw, const char* chain_name,
                      uint32_t src_ip, uint32_t dst_ip,
                      uint16_t src_port, uint16_t dst_port);

/* Statistics */
int   fw_get_stats(firewall_t* fw, char* buf, uint32_t buf_len);
int   fw_get_chain_stats(firewall_t* fw, const char* chain_name, char* buf, uint32_t buf_len);
void  fw_reset_stats(firewall_t* fw);

/* Enable/Disable */
void  fw_enable(firewall_t* fw);
void  fw_disable(firewall_t* fw);

/* Utilities */
const char* fw_action_to_string(fw_action_t action);
const char* fw_chain_to_string(fw_chain_t chain);
const char* fw_protocol_to_string(fw_protocol_t proto);

#endif

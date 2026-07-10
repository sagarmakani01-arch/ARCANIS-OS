/**
 * firewall.c — Packet Filtering Firewall Implementation
 *
 * iptables-like firewall with chains, rules, and NAT support.
 */
#include <arcanis/firewall.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <stdio.h>

/* ---- Initialization ---- */

void fw_init(firewall_t* fw) {
    if (!fw) return;
    memset(fw, 0, sizeof(firewall_t));

    /* Create default chains */
    fw_create_chain(fw, "INPUT", FW_ACTION_DROP);
    fw_create_chain(fw, "OUTPUT", FW_ACTION_ACCEPT);
    fw_create_chain(fw, "FORWARD", FW_ACTION_DROP);
    fw_create_chain(fw, "PREROUTING", FW_ACTION_ACCEPT);
    fw_create_chain(fw, "POSTROUTING", FW_ACTION_ACCEPT);

    fw->enabled = 1;
}

/* ---- Chain management ---- */

int fw_create_chain(firewall_t* fw, const char* name, fw_action_t default_action) {
    if (!fw || !name) return -1;
    if (fw->num_chains >= FW_MAX_CHAINS) return -1;

    /* Check if exists */
    for (uint32_t i = 0; i < fw->num_chains; i++) {
        if (string_compare(fw->chains[i].name, name) == 0)
            return -1; /* Already exists */
    }

    fw_chain_def_t* chain = &fw->chains[fw->num_chains++];
    memset(chain, 0, sizeof(fw_chain_def_t));
    string_copy(chain->name, name, FW_MAX_NAME);
    chain->default_action = default_action;

    return 0;
}

int fw_delete_chain(firewall_t* fw, const char* name) {
    if (!fw || !name) return -1;

    /* Cannot delete built-in chains */
    if (string_compare(name, "INPUT") == 0 ||
        string_compare(name, "OUTPUT") == 0 ||
        string_compare(name, "FORWARD") == 0)
        return -1;

    for (uint32_t i = 0; i < fw->num_chains; i++) {
        if (string_compare(fw->chains[i].name, name) == 0) {
            for (uint32_t j = i; j < fw->num_chains - 1; j++)
                fw->chains[j] = fw->chains[j + 1];
            fw->num_chains--;
            return 0;
        }
    }
    return -1;
}

int fw_flush_chain(firewall_t* fw, const char* name) {
    if (!fw || !name) return -1;

    for (uint32_t i = 0; i < fw->num_chains; i++) {
        if (string_compare(fw->chains[i].name, name) == 0) {
            fw->chains[i].num_rules = 0;
            return 0;
        }
    }
    return -1;
}

fw_chain_def_t* fw_get_chain(firewall_t* fw, const char* name) {
    if (!fw || !name) return NULL;

    for (uint32_t i = 0; i < fw->num_chains; i++) {
        if (string_compare(fw->chains[i].name, name) == 0)
            return &fw->chains[i];
    }
    return NULL;
}

/* ---- Rule management ---- */

int fw_add_rule(firewall_t* fw, const char* chain_name, const fw_rule_t* rule) {
    if (!fw || !chain_name || !rule) return -1;

    fw_chain_def_t* chain = fw_get_chain(fw, chain_name);
    if (!chain) return -1;
    if (chain->num_rules >= FW_MAX_RULES) return -1;

    fw_rule_t* new_rule = &chain->rules[chain->num_rules++];
    memcpy(new_rule, rule, sizeof(fw_rule_t));
    new_rule->id = chain->num_rules;

    return (int)new_rule->id;
}

int fw_delete_rule(firewall_t* fw, const char* chain_name, uint32_t rule_id) {
    if (!fw || !chain_name) return -1;

    fw_chain_def_t* chain = fw_get_chain(fw, chain_name);
    if (!chain) return -1;

    for (uint32_t i = 0; i < chain->num_rules; i++) {
        if (chain->rules[i].id == rule_id) {
            for (uint32_t j = i; j < chain->num_rules - 1; j++)
                chain->rules[j] = chain->rules[j + 1];
            chain->num_rules--;
            return 0;
        }
    }
    return -1;
}

int fw_replace_rule(firewall_t* fw, const char* chain_name, uint32_t rule_id, const fw_rule_t* rule) {
    if (!fw || !chain_name || !rule) return -1;

    fw_chain_def_t* chain = fw_get_chain(fw, chain_name);
    if (!chain) return -1;

    for (uint32_t i = 0; i < chain->num_rules; i++) {
        if (chain->rules[i].id == rule_id) {
            memcpy(&chain->rules[i], rule, sizeof(fw_rule_t));
            chain->rules[i].id = rule_id;
            return 0;
        }
    }
    return -1;
}

int fw_enable_rule(firewall_t* fw, const char* chain_name, uint32_t rule_id) {
    if (!fw || !chain_name) return -1;

    fw_chain_def_t* chain = fw_get_chain(fw, chain_name);
    if (!chain) return -1;

    for (uint32_t i = 0; i < chain->num_rules; i++) {
        if (chain->rules[i].id == rule_id) {
            chain->rules[i].enabled = 1;
            return 0;
        }
    }
    return -1;
}

int fw_disable_rule(firewall_t* fw, const char* chain_name, uint32_t rule_id) {
    if (!fw || !chain_name) return -1;

    fw_chain_def_t* chain = fw_get_chain(fw, chain_name);
    if (!chain) return -1;

    for (uint32_t i = 0; i < chain->num_rules; i++) {
        if (chain->rules[i].id == rule_id) {
            chain->rules[i].enabled = 0;
            return 0;
        }
    }
    return -1;
}

/* ---- Packet matching ---- */

static int match_ip(uint32_t packet_ip, fw_ip_range_t* rule_ip) {
    if (rule_ip->ip == 0) return 1; /* Any IP */
    if (rule_ip->mask == 0) return 1;
    return (packet_ip & rule_ip->mask) == (rule_ip->ip & rule_ip->mask);
}

static int match_port(uint16_t packet_port, fw_port_range_t* rule_port) {
    if (rule_port->start == 0 && rule_port->end == 0) return 1; /* Any port */
    return packet_port >= rule_port->start && packet_port <= rule_port->end;
}

int fw_match_packet(firewall_t* fw, const char* chain_name,
                    uint32_t src_ip, uint16_t src_port,
                    uint32_t dst_ip, uint16_t dst_port,
                    uint8_t protocol, uint8_t* action) {
    if (!fw || !chain_name || !action) return -1;

    fw_chain_def_t* chain = fw_get_chain(fw, chain_name);
    if (!chain) return -1;

    chain->packets_count++;

    for (uint32_t i = 0; i < chain->num_rules; i++) {
        fw_rule_t* rule = &chain->rules[i];
        if (!rule->enabled) continue;

        /* Match protocol */
        if (rule->protocol != FW_PROTO_ALL && rule->protocol != protocol)
            continue;

        /* Match source IP */
        if (!match_ip(src_ip, &rule->src_ip))
            continue;

        /* Match destination IP */
        if (!match_ip(dst_ip, &rule->dst_ip))
            continue;

        /* Match source port */
        if (!match_port(src_port, &rule->src_port))
            continue;

        /* Match destination port */
        if (!match_port(dst_port, &rule->dst_port))
            continue;

        /* Rule matched */
        rule->packets_matched++;
        *action = rule->action;

        if (rule->log_packets)
            printf("[FW LOG] %s packet matched rule %u\n", rule->log_prefix, rule->id);

        return 0;
    }

    /* No rule matched, use default action */
    *action = chain->default_action;
    return 0;
}

/* ---- NAT ---- */

int fw_add_nat_rule(firewall_t* fw, const char* chain_name,
                    uint32_t src_ip, uint32_t dst_ip,
                    uint16_t src_port, uint16_t dst_port) {
    if (!fw || !chain_name) return -1;

    fw_rule_t rule;
    memset(&rule, 0, sizeof(fw_rule_t));
    rule.enabled = 1;
    rule.action = FW_ACTION_ACCEPT;
    rule.protocol = FW_PROTO_ALL;
    rule.src_ip.ip = src_ip;
    rule.src_ip.mask = 0xFFFFFFFF;
    rule.dst_ip.ip = dst_ip;
    rule.dst_ip.mask = 0xFFFFFFFF;
    rule.src_port.start = src_port;
    rule.src_port.end = src_port;
    rule.dst_port.start = dst_port;
    rule.dst_port.end = dst_port;

    return fw_add_rule(fw, chain_name, &rule);
}

/* ---- Statistics ---- */

int fw_get_stats(firewall_t* fw, char* buf, uint32_t buf_len) {
    if (!fw || !buf) return 0;

    uint64_t total_packets = 0, total_bytes = 0;
    for (uint32_t i = 0; i < fw->num_chains; i++) {
        total_packets += fw->chains[i].packets_count;
        total_bytes += fw->chains[i].bytes_count;
    }

    return snprintf(buf, buf_len,
        "Firewall Statistics:\n"
        "  Enabled:    %s\n"
        "  Chains:     %u\n"
        "  Total Packets: %llu\n"
        "  Total Bytes:   %llu\n"
        "  Dropped:    %llu\n"
        "  Accepted:   %llu\n"
        "  Rejected:   %llu\n",
        fw->enabled ? "yes" : "no",
        fw->num_chains,
        (unsigned long long)total_packets,
        (unsigned long long)total_bytes,
        (unsigned long long)fw->packets_dropped,
        (unsigned long long)fw->packets_accepted,
        (unsigned long long)fw->packets_rejected);
}

int fw_get_chain_stats(firewall_t* fw, const char* chain_name, char* buf, uint32_t buf_len) {
    if (!fw || !chain_name || !buf) return 0;

    fw_chain_def_t* chain = fw_get_chain(fw, chain_name);
    if (!chain) return -1;

    return snprintf(buf, buf_len,
        "Chain %s (default: %s)\n"
        "  Packets: %llu  Bytes: %llu\n"
        "  Rules: %u\n",
        chain->name, fw_action_to_string(chain->default_action),
        (unsigned long long)chain->packets_count,
        (unsigned long long)chain->bytes_count,
        chain->num_rules);
}

void fw_reset_stats(firewall_t* fw) {
    if (!fw) return;

    for (uint32_t i = 0; i < fw->num_chains; i++) {
        fw->chains[i].packets_count = 0;
        fw->chains[i].bytes_count = 0;
        for (uint32_t j = 0; j < fw->chains[i].num_rules; j++) {
            fw->chains[i].rules[j].packets_matched = 0;
            fw->chains[i].rules[j].bytes_matched = 0;
        }
    }
}

/* ---- Enable/Disable ---- */

void fw_enable(firewall_t* fw) {
    if (fw) fw->enabled = 1;
}

void fw_disable(firewall_t* fw) {
    if (fw) fw->enabled = 0;
}

/* ---- Utilities ---- */

const char* fw_action_to_string(fw_action_t action) {
    switch (action) {
        case FW_ACTION_ACCEPT: return "ACCEPT";
        case FW_ACTION_DROP:   return "DROP";
        case FW_ACTION_REJECT: return "REJECT";
        case FW_ACTION_LOG:    return "LOG";
        case FW_ACTION_RETURN: return "RETURN";
        default: return "UNKNOWN";
    }
}

const char* fw_chain_to_string(fw_chain_t chain) {
    switch (chain) {
        case FW_CHAIN_INPUT:      return "INPUT";
        case FW_CHAIN_OUTPUT:     return "OUTPUT";
        case FW_CHAIN_FORWARD:    return "FORWARD";
        case FW_CHAIN_PREROUTING: return "PREROUTING";
        case FW_CHAIN_POSTROUTING:return "POSTROUTING";
        default: return "UNKNOWN";
    }
}

const char* fw_protocol_to_string(fw_protocol_t proto) {
    switch (proto) {
        case FW_PROTO_TCP:  return "tcp";
        case FW_PROTO_UDP:  return "udp";
        case FW_PROTO_ICMP: return "icmp";
        case FW_PROTO_ALL:  return "all";
        default: return "unknown";
    }
}

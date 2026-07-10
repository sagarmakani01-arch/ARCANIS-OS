/**
 * sdn.h — Software-Defined Networking
 *
 * SDN controller, flow tables, network virtualization, and programmable networking.
 */
#ifndef ARCANIS_SDN_H
#define ARCANIS_SDN_H

#include <arcanis/types.h>

#define SDN_MAX_SWITCHES     128
#define SDN_MAX_PORTS        64
#define SDN_MAX_FLOWS        4096
#define SDN_MAX_CONTROLLERS  16
#define SDN_MAX_VLANS        256
#define SDN_MAX_NAME         64

typedef enum {
    SDN_PORT_UP,
    SDN_PORT_DOWN,
    SDN_PORT_BLOCKED
} sdn_port_state_t;

typedef struct {
    uint32_t port_no;
    char name[32];
    sdn_port_state_t state;
    uint64_t rx_packets;
    uint64_t tx_packets;
    uint64_t rx_bytes;
    uint64_t tx_bytes;
    uint32_t speed_mbps;
    int configured;
} sdn_port_t;

typedef struct {
    char switch_id[32];
    char name[SDN_NAME];
    char dpid[32]; /* Datapath ID */

    sdn_port_t ports[SDN_MAX_PORTS];
    uint32_t num_ports;

    uint64_t flow_count;
    uint64_t packet_count;
    uint64_t byte_count;
    int connected;
    uint64_t last_alive;
} sdn_switch_t;

typedef struct {
    uint32_t priority;
    uint32_t match_fields; /* Bitmap: src_ip, dst_ip, src_port, dst_port, protocol */
    uint32_t src_ip;
    uint32_t dst_ip;
    uint16_t src_port;
    uint16_t dst_port;
    uint8_t  protocol;

    enum { SDN_ACTION_FORWARD, SDN_ACTION_DROP, SDN_ACTION_MODIFY, SDN_ACTION_OUTPUT } action;
    uint32_t output_port;
    uint32_t action_data;

    uint64_t packet_count;
    uint64_t byte_count;
    uint32_t timeout;
    int active;
} sdn_flow_t;

typedef struct {
    char id[32];
    char name[SDN_NAME];
    char host[64];
    uint16_t port;
    int role; /* 0=slave, 1=master */
    uint32_t connected_switches;
    uint64_t total_flow_mods;
    int active;
} sdn_controller_t;

typedef struct {
    uint16_t vlan_id;
    char name[32];
    uint32_t ports[SDN_MAX_PORTS];
    uint32_t num_ports;
    int enabled;
} sdn_vlan_t;

typedef struct {
    sdn_switch_t switches[SDN_MAX_SWITCHES];
    uint32_t num_switches;

    sdn_flow_t flows[SDN_MAX_FLOWS];
    uint32_t num_flows;

    sdn_controller_t controllers[SDN_MAX_CONTROLLERS];
    uint32_t num_controllers;

    sdn_vlan_t vlans[SDN_MAX_VLANS];
    uint32_t num_vlans;

    uint64_t total_packets;
    uint64_t total_bytes;
    uint32_t topology_version;
} sdn_system_t;

/* Initialize SDN */
void sdn_init(sdn_system_t* sys);

/* Switch management */
int   sdn_add_switch(sdn_system_t* sys, const char* name, const char* dpid);
int   sdn_remove_switch(sdn_system_t* sys, const char* switch_id);
int   sdn_get_switch(sdn_system_t* sys, const char* switch_id, sdn_switch_t* sw);
int   sdn_list_switches(sdn_system_t* sys, char* buf, uint32_t buf_len);

/* Port management */
int   sdn_add_port(sdn_system_t* sys, const char* switch_id, uint32_t port_no,
                   const char* name);
int   sdn_set_port_state(sdn_system_t* sys, const char* switch_id,
                         uint32_t port_no, sdn_port_state_t state);

/* Flow management */
int   sdn_add_flow(sdn_system_t* sys, const char* switch_id,
                   const sdn_flow_t* flow);
int   sdn_remove_flow(sdn_system_t* sys, const char* switch_id, uint32_t priority,
                      uint32_t src_ip, uint32_t dst_ip);
int   sdn_list_flows(sdn_system_t* sys, const char* switch_id,
                     char* buf, uint32_t buf_len);

/* Controller management */
int   sdn_add_controller(sdn_system_t* sys, const char* name,
                         const char* host, uint16_t port);
int   sdn_list_controllers(sdn_system_t* sys, char* buf, uint32_t buf_len);

/* VLAN management */
int   sdn_create_vlan(sdn_system_t* sys, uint16_t vlan_id, const char* name);
int   sdn_add_port_to_vlan(sdn_system_t* sys, uint16_t vlan_id,
                           const char* switch_id, uint32_t port_no);
int   sdn_list_vlans(sdn_system_t* sys, char* buf, uint32_t buf_len);

/* Statistics */
int   sdn_get_stats(sdn_system_t* sys, char* buf, uint32_t buf_len);

/* Topology */
int   sdn_get_topology(sdn_system_t* sys, char* buf, uint32_t buf_len);

#endif

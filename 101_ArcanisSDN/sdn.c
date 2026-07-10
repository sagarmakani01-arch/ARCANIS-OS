/**
 * sdn.c — Software-Defined Networking Implementation
 *
 * SDN controller, flow tables, network virtualization, and programmable networking.
 */
#include <arcanis/sdn.h>
#include <arcanis/string.h>
#include <stdio.h>
#include <string.h>

/* ---- Initialization ---- */

void sdn_init(sdn_system_t* sys) {
    if (!sys) return;
    memset(sys, 0, sizeof(sdn_system_t));
    printf("[SDN] Controller initialized\n");
}

/* ---- Switch management ---- */

int sdn_add_switch(sdn_system_t* sys, const char* name, const char* dpid) {
    if (!sys || !name || !dpid) return -1;
    if (sys->num_switches >= SDN_MAX_SWITCHES) return -1;

    sdn_switch_t* sw = &sys->switches[sys->num_switches];
    memset(sw, 0, sizeof(sdn_switch_t));

    snprintf(sw->switch_id, 32, "sw-%u", sys->num_switches);
    string_copy(sw->name, name, SDN_NAME);
    string_copy(sw->dpid, dpid, 32);
    sw->connected = 1;

    sys->num_switches++;
    printf("[SDN] Switch '%s' added (dpid=%s)\n", name, dpid);
    return 0;
}

int sdn_remove_switch(sdn_system_t* sys, const char* switch_id) {
    if (!sys || !switch_id) return -1;

    for (uint32_t i = 0; i < sys->num_switches; i++) {
        if (string_compare(sys->switches[i].switch_id, switch_id) == 0) {
            for (uint32_t j = i; j < sys->num_switches - 1; j++) {
                sys->switches[j] = sys->switches[j + 1];
            }
            sys->num_switches--;
            printf("[SDN] Switch '%s' removed\n", switch_id);
            return 0;
        }
    }
    return -1;
}

int sdn_get_switch(sdn_system_t* sys, const char* switch_id, sdn_switch_t* sw) {
    if (!sys || !switch_id || !sw) return -1;

    for (uint32_t i = 0; i < sys->num_switches; i++) {
        if (string_compare(sys->switches[i].switch_id, switch_id) == 0) {
            memcpy(sw, &sys->switches[i], sizeof(sdn_switch_t));
            return 0;
        }
    }
    return -1;
}

int sdn_list_switches(sdn_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "SWITCHES: %u\n", sys->num_switches);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID         NAME                 DPID           PORTS  FLOWS    STATUS\n");

    for (uint32_t i = 0; i < sys->num_switches && pos < buf_len - 120; i++) {
        sdn_switch_t* s = &sys->switches[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-10s %-20s %-14s %4u  %6llu  %s\n",
            s->switch_id, s->name, s->dpid,
            s->num_ports, (unsigned long long)s->flow_count,
            s->connected ? "CONNECTED" : "DISCONNECTED");
    }

    return (int)pos;
}

/* ---- Port management ---- */

int sdn_add_port(sdn_system_t* sys, const char* switch_id, uint32_t port_no,
                 const char* name) {
    if (!sys || !switch_id || !name) return -1;

    for (uint32_t i = 0; i < sys->num_switches; i++) {
        if (string_compare(sys->switches[i].switch_id, switch_id) == 0) {
            sdn_switch_t* sw = &sys->switches[i];
            if (sw->num_ports >= SDN_MAX_PORTS) return -1;

            sdn_port_t* port = &sw->ports[sw->num_ports];
            port->port_no = port_no;
            string_copy(port->name, name, 32);
            port->state = SDN_PORT_UP;
            port->speed_mbps = 1000;
            port->configured = 1;

            sw->num_ports++;
            return 0;
        }
    }
    return -1;
}

int sdn_set_port_state(sdn_system_t* sys, const char* switch_id,
                       uint32_t port_no, sdn_port_state_t state) {
    if (!sys || !switch_id) return -1;

    for (uint32_t i = 0; i < sys->num_switches; i++) {
        if (string_compare(sys->switches[i].switch_id, switch_id) == 0) {
            sdn_switch_t* sw = &sys->switches[i];
            for (uint32_t j = 0; j < sw->num_ports; j++) {
                if (sw->ports[j].port_no == port_no) {
                    sw->ports[j].state = state;
                    return 0;
                }
            }
        }
    }
    return -1;
}

/* ---- Flow management ---- */

int sdn_add_flow(sdn_system_t* sys, const char* switch_id,
                 const sdn_flow_t* flow) {
    if (!sys || !switch_id || !flow) return -1;
    if (sys->num_flows >= SDN_MAX_FLOWS) return -1;

    sdn_flow_t* new_flow = &sys->flows[sys->num_flows];
    memcpy(new_flow, flow, sizeof(sdn_flow_t));
    new_flow->active = 1;

    sys->num_flows++;

    /* Update switch flow count */
    for (uint32_t i = 0; i < sys->num_switches; i++) {
        if (string_compare(sys->switches[i].switch_id, switch_id) == 0) {
            sys->switches[i].flow_count++;
            break;
        }
    }

    printf("[SDN] Flow added to %s (priority=%u)\n", switch_id, flow->priority);
    return 0;
}

int sdn_remove_flow(sdn_system_t* sys, const char* switch_id, uint32_t priority,
                    uint32_t src_ip, uint32_t dst_ip) {
    if (!sys || !switch_id) return -1;

    for (uint32_t i = 0; i < sys->num_flows; i++) {
        if (sys->flows[i].active &&
            sys->flows[i].priority == priority &&
            sys->flows[i].src_ip == src_ip &&
            sys->flows[i].dst_ip == dst_ip) {
            sys->flows[i].active = 0;
            printf("[SDN] Flow removed from %s\n", switch_id);
            return 0;
        }
    }
    return -1;
}

int sdn_list_flows(sdn_system_t* sys, const char* switch_id,
                   char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "FLOWS:\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "PRIO  SRC_IP         DST_IP       PROTO  ACTION     PACKETS\n");

    for (uint32_t i = 0; i < sys->num_flows && pos < buf_len - 100; i++) {
        if (!sys->flows[i].active) continue;
        sdn_flow_t* f = &sys->flows[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%4u  %08x      %08x    %3u    %-10s %llu\n",
            f->priority, f->src_ip, f->dst_ip, f->protocol,
            f->action == SDN_ACTION_FORWARD ? "FORWARD" : "DROP",
            (unsigned long long)f->packet_count);
    }

    return (int)pos;
}

/* ---- Controller management ---- */

int sdn_add_controller(sdn_system_t* sys, const char* name,
                       const char* host, uint16_t port) {
    if (!sys || !name || !host) return -1;
    if (sys->num_controllers >= SDN_MAX_CONTROLLERS) return -1;

    sdn_controller_t* ctrl = &sys->controllers[sys->num_controllers];
    memset(ctrl, 0, sizeof(sdn_controller_t));

    snprintf(ctrl->id, 32, "ctrl-%u", sys->num_controllers);
    string_copy(ctrl->name, name, SDN_NAME);
    string_copy(ctrl->host, host, 64);
    ctrl->port = port;
    ctrl->role = 1; /* master */
    ctrl->active = 1;

    sys->num_controllers++;
    printf("[SDN] Controller '%s' added (%s:%u)\n", name, host, port);
    return 0;
}

int sdn_list_controllers(sdn_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "CONTROLLERS: %u\n", sys->num_controllers);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID        NAME                 HOST             PORT   ROLE     STATUS\n");

    for (uint32_t i = 0; i < sys->num_controllers && pos < buf_len - 120; i++) {
        sdn_controller_t* c = &sys->controllers[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-9s %-20s %-16s %5u  %-8s %s\n",
            c->id, c->name, c->host, c->port,
            c->role ? "MASTER" : "SLAVE",
            c->active ? "ACTIVE" : "INACTIVE");
    }

    return (int)pos;
}

/* ---- VLAN management ---- */

int sdn_create_vlan(sdn_system_t* sys, uint16_t vlan_id, const char* name) {
    if (!sys || !name) return -1;
    if (sys->num_vlans >= SDN_MAX_VLANS) return -1;

    sdn_vlan_t* vlan = &sys->vlans[sys->num_vlans];
    memset(vlan, 0, sizeof(sdn_vlan_t));

    vlan->vlan_id = vlan_id;
    string_copy(vlan->name, name, 32);
    vlan->enabled = 1;

    sys->num_vlans++;
    printf("[SDN] VLAN %u '%s' created\n", vlan_id, name);
    return 0;
}

int sdn_add_port_to_vlan(sdn_system_t* sys, uint16_t vlan_id,
                         const char* switch_id, uint32_t port_no) {
    if (!sys || !switch_id) return -1;

    for (uint32_t i = 0; i < sys->num_vlans; i++) {
        if (sys->vlans[i].vlan_id == vlan_id) {
            sdn_vlan_t* vlan = &sys->vlans[i];
            if (vlan->num_ports >= SDN_MAX_PORTS) return -1;

            /* Store as combined switch+port */
            vlan->ports[vlan->num_ports] = (port_no << 16) | (sys->num_vlans);
            vlan->num_ports++;
            return 0;
        }
    }
    return -1;
}

int sdn_list_vlans(sdn_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "VLANs: %u\n", sys->num_vlans);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID    NAME                 PORTS   STATUS\n");

    for (uint32_t i = 0; i < sys->num_vlans && pos < buf_len - 80; i++) {
        sdn_vlan_t* v = &sys->vlans[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-5u %-20s %5u   %s\n",
            v->vlan_id, v->name, v->num_ports,
            v->enabled ? "ACTIVE" : "DISABLED");
    }

    return (int)pos;
}

/* ---- Statistics ---- */

int sdn_get_stats(sdn_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;

    uint64_t total_packets = 0, total_bytes = 0;
    uint32_t total_ports = 0;

    for (uint32_t i = 0; i < sys->num_switches; i++) {
        total_packets += sys->switches[i].packet_count;
        total_bytes += sys->switches[i].byte_count;
        total_ports += sys->switches[i].num_ports;
    }

    return snprintf(buf, buf_len,
        "SDN Statistics:\n"
        "  Switches: %u\n"
        "  Ports: %u\n"
        "  Active Flows: %u\n"
        "  Controllers: %u\n"
        "  VLANs: %u\n"
        "  Total Packets: %llu\n"
        "  Total Bytes: %llu\n"
        "  Topology Version: %u\n",
        sys->num_switches, total_ports, sys->num_flows,
        sys->num_controllers, sys->num_vlans,
        (unsigned long long)total_packets,
        (unsigned long long)total_bytes,
        sys->topology_version);
}

/* ---- Topology ---- */

int sdn_get_topology(sdn_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos,
        "NETWORK TOPOLOGY (version %u):\n", sys->topology_version);

    for (uint32_t i = 0; i < sys->num_switches && pos < buf_len - 200; i++) {
        sdn_switch_t* s = &sys->switches[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "  %s (%s)\n", s->name, s->dpid);

        for (uint32_t j = 0; j < s->num_ports; j++) {
            pos += snprintf(buf + pos, buf_len - pos,
                "    port %u: %s [%s]\n",
                s->ports[j].port_no, s->ports[j].name,
                s->ports[j].state == SDN_PORT_UP ? "UP" : "DOWN");
        }
    }

    return (int)pos;
}

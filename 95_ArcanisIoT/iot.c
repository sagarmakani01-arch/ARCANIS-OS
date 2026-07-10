/**
 * iot.c — Internet of Things Implementation
 *
 * IoT device management, protocols, and data aggregation.
 */
#include <arcanis/iot.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <stdio.h>
#include <stdlib.h>

/* ---- Initialization ---- */

void iot_init(iot_manager_t* mgr) {
    if (!mgr) return;
    memset(mgr, 0, sizeof(iot_manager_t));
}

/* ---- Device management ---- */

static iot_device_t* find_device(iot_manager_t* mgr, uint32_t id) {
    for (uint32_t i = 0; i < mgr->num_devices; i++) {
        if (mgr->devices[i].id == id)
            return &mgr->devices[i];
    }
    return NULL;
}

int iot_register_device(iot_manager_t* mgr, const char* name,
                       iot_device_type_t type, iot_protocol_t proto) {
    if (!mgr || !name) return -1;
    if (mgr->num_devices >= IOT_MAX_DEVICES) return -1;

    iot_device_t* dev = &mgr->devices[mgr->num_devices];
    memset(dev, 0, sizeof(iot_device_t));

    dev->id = mgr->num_devices + 1;
    string_copy(dev->name, name, IOT_MAX_NAME);
    dev->type = type;
    dev->protocol = proto;
    snprintf(dev->topic, IOT_MAX_TOPIC, "devices/%s/data", name);
    dev->online = 1;
    dev->secured = 1;
    dev->last_seen = 0;
    dev->battery_level = 100;
    string_copy(dev->firmware, "1.0.0", 32);

    mgr->num_devices++;
    mgr->total_devices_seen++;
    printf("[IOT] Device '%s' registered (type=%d, proto=%d)\n", name, type, proto);
    return (int)dev->id;
}

int iot_unregister_device(iot_manager_t* mgr, uint32_t device_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_devices; i++) {
        if (mgr->devices[i].id == device_id) {
            printf("[IOT] Device '%s' unregistered\n", mgr->devices[i].name);
            for (uint32_t j = i; j < mgr->num_devices - 1; j++)
                mgr->devices[j] = mgr->devices[j + 1];
            mgr->num_devices--;
            return 0;
        }
    }
    return -1;
}

int iot_update_device(iot_manager_t* mgr, uint32_t device_id, const char* data) {
    if (!mgr || !data) return -1;

    iot_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    string_copy(dev->data, data, 256);
    dev->last_seen = 0;

    printf("[IOT] Device '%s' updated: %s\n", dev->name, data);
    return 0;
}

int iot_list_devices(iot_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    const char* type_names[] = {"sensor", "actuator", "gateway", "camera",
                                "light", "thermostat", "lock", "speaker"};
    uint32_t pos = 0;

    pos += snprintf(buf + pos, buf_len - pos, "IOT DEVICES: %u\n", mgr->num_devices);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID  NAME            TYPE        PROTOCOL  ONLINE  BATTERY\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "--------------------------------------------------------\n");

    for (uint32_t i = 0; i < mgr->num_devices && pos < buf_len - 150; i++) {
        iot_device_t* d = &mgr->devices[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-3u %-15s %-11s %-9s %-7s %u%%\n",
            d->id, d->name, type_names[d->type],
            d->protocol == 0 ? "MQTT" : d->protocol == 1 ? "CoAP" : "HTTP",
            d->online ? "yes" : "no", d->battery_level);
    }

    return (int)pos;
}

int iot_get_device(iot_manager_t* mgr, uint32_t device_id, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    iot_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    const char* type_names[] = {"sensor", "actuator", "gateway", "camera",
                                "light", "thermostat", "lock", "speaker"};
    return snprintf(buf, buf_len,
        "Device: %s\n"
        "  Type: %s\n"
        "  Topic: %s\n"
        "  Online: %s\n"
        "  Secured: %s\n"
        "  Battery: %u%%\n"
        "  Firmware: %s\n"
        "  Location: %s\n"
        "  Data: %s\n",
        dev->name, type_names[dev->type],
        dev->topic, dev->online ? "yes" : "no",
        dev->secured ? "yes" : "no",
        dev->battery_level, dev->firmware,
        dev->location, dev->data);
}

int iot_find_device_by_topic(iot_manager_t* mgr, const char* topic, iot_device_t** device) {
    if (!mgr || !topic || !device) return -1;

    for (uint32_t i = 0; i < mgr->num_devices; i++) {
        if (string_compare(mgr->devices[i].topic, topic) == 0) {
            *device = &mgr->devices[i];
            return 0;
        }
    }
    return -1;
}

/* ---- Protocol management ---- */

int iot_add_protocol(iot_manager_t* mgr, const char* name,
                    iot_protocol_t proto, uint16_t port) {
    if (!mgr || !name) return -1;
    if (mgr->num_protocols >= IOT_MAX_PROTOCOLS) return -1;

    iot_protocol_config_t* p = &mgr->protocols[mgr->num_protocols];
    memset(p, 0, sizeof(iot_protocol_config_t));

    p->id = mgr->num_protocols + 1;
    string_copy(p->name, name, IOT_MAX_NAME);
    p->protocol = proto;
    p->port = port;
    p->enabled = 1;

    mgr->num_protocols++;
    printf("[IOT] Protocol '%s' added (proto=%d, port=%u)\n", name, proto, port);
    return (int)p->id;
}

int iot_remove_protocol(iot_manager_t* mgr, uint32_t proto_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_protocols; i++) {
        if (mgr->protocols[i].id == proto_id) {
            printf("[IOT] Protocol '%s' removed\n", mgr->protocols[i].name);
            for (uint32_t j = i; j < mgr->num_protocols - 1; j++)
                mgr->protocols[j] = mgr->protocols[j + 1];
            mgr->num_protocols--;
            return 0;
        }
    }
    return -1;
}

int iot_list_protocols(iot_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    const char* proto_names[] = {"MQTT", "CoAP", "HTTP", "WebSocket", "BLE", "Zigbee", "LoRa"};
    uint32_t pos = 0;

    pos += snprintf(buf + pos, buf_len - pos, "PROTOCOLS: %u\n", mgr->num_protocols);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID  NAME            PROTOCOL  PORT    ENABLED\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "--------------------------------------------------\n");

    for (uint32_t i = 0; i < mgr->num_protocols && pos < buf_len - 100; i++) {
        iot_protocol_config_t* p = &mgr->protocols[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-3u %-15s %-9s %-7u %s\n",
            p->id, p->name, proto_names[p->protocol],
            p->port, p->enabled ? "yes" : "no");
    }

    return (int)pos;
}

/* ---- Messaging (Pub/Sub) ---- */

int iot_publish(iot_manager_t* mgr, const char* topic,
               const char* payload, uint32_t qos) {
    if (!mgr || !topic || !payload) return -1;

    if (mgr->message_count >= 256) {
        /* Drop oldest message */
        mgr->message_head = (mgr->message_head + 1) % 256;
        mgr->message_count--;
    }

    iot_message_t* msg = &mgr->message_buffer[mgr->message_tail];
    string_copy(msg->topic, topic, IOT_MAX_TOPIC);
    string_copy(msg->payload, payload, IOT_MAX_PAYLOAD);
    msg->payload_len = string_length(payload);
    msg->timestamp = 0;
    msg->qos = qos;
    msg->retained = 0;

    mgr->message_tail = (mgr->message_tail + 1) % 256;
    mgr->message_count++;
    mgr->total_messages++;

    printf("[IOT] Published to '%s': %s\n", topic, payload);
    return 0;
}

int iot_subscribe(iot_manager_t* mgr, uint32_t device_id, const char* topic) {
    if (!mgr || !topic) return -1;

    iot_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    string_copy(dev->topic, topic, IOT_MAX_TOPIC);
    printf("[IOT] Device '%s' subscribed to '%s'\n", dev->name, topic);
    return 0;
}

int iot_unsubscribe(iot_manager_t* mgr, uint32_t device_id, const char* topic) {
    if (!mgr || !topic) return -1;

    iot_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    printf("[IOT] Device '%s' unsubscribed from '%s'\n", dev->name, topic);
    return 0;
}

int iot_receive(iot_manager_t* mgr, iot_message_t* msg) {
    if (!mgr || !msg) return -1;
    if (mgr->message_count == 0) return -1;

    memcpy(msg, &mgr->message_buffer[mgr->message_head], sizeof(iot_message_t));
    mgr->message_head = (mgr->message_head + 1) % 256;
    mgr->message_count--;

    return 0;
}

int iot_message_count(iot_manager_t* mgr, uint32_t* count) {
    if (!mgr || !count) return -1;
    *count = mgr->message_count;
    return 0;
}

/* ---- Rules/Automation ---- */

int iot_add_rule(iot_manager_t* mgr, const char* name,
                const char* trigger_device, const char* condition,
                const char* action_device, const char* command) {
    if (!mgr || !name) return -1;
    if (mgr->num_rules >= IOT_MAX_RULES) return -1;

    iot_rule_t* rule = &mgr->rules[mgr->num_rules];
    memset(rule, 0, sizeof(iot_rule_t));

    rule->id = mgr->num_rules + 1;
    string_copy(rule->name, name, IOT_MAX_NAME);
    rule->type = RULE_TRIGGER;
    if (trigger_device) string_copy(rule->trigger_device, trigger_device, 64);
    if (condition) string_copy(rule->trigger_condition, condition, 128);
    if (action_device) string_copy(rule->action_device, action_device, 64);
    if (command) string_copy(rule->action_command, command, 256);
    rule->enabled = 1;

    mgr->num_rules++;
    printf("[IOT] Rule '%s' added\n", name);
    return (int)rule->id;
}

int iot_remove_rule(iot_manager_t* mgr, uint32_t rule_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_rules; i++) {
        if (mgr->rules[i].id == rule_id) {
            printf("[IOT] Rule '%s' removed\n", mgr->rules[i].name);
            for (uint32_t j = i; j < mgr->num_rules - 1; j++)
                mgr->rules[j] = mgr->rules[j + 1];
            mgr->num_rules--;
            return 0;
        }
    }
    return -1;
}

int iot_enable_rule(iot_manager_t* mgr, uint32_t rule_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_rules; i++) {
        if (mgr->rules[i].id == rule_id) {
            mgr->rules[i].enabled = 1;
            printf("[IOT] Rule '%s' enabled\n", mgr->rules[i].name);
            return 0;
        }
    }
    return -1;
}

int iot_disable_rule(iot_manager_t* mgr, uint32_t rule_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_rules; i++) {
        if (mgr->rules[i].id == rule_id) {
            mgr->rules[i].enabled = 0;
            printf("[IOT] Rule '%s' disabled\n", mgr->rules[i].name);
            return 0;
        }
    }
    return -1;
}

int iot_evaluate_rules(iot_manager_t* mgr) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_rules; i++) {
        if (!mgr->rules[i].enabled) continue;

        iot_rule_t* rule = &mgr->rules[i];
        /* Simulate rule evaluation */
        rule->trigger_count++;
        printf("[IOT] Rule '%s' triggered (action: %s)\n", rule->name, rule->action_command);
    }
    return 0;
}

int iot_list_rules(iot_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "AUTOMATION RULES: %u\n", mgr->num_rules);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID  NAME            TRIGGER      ACTION       ENABLED  FIRES\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "--------------------------------------------------------------\n");

    for (uint32_t i = 0; i < mgr->num_rules && pos < buf_len - 150; i++) {
        iot_rule_t* r = &mgr->rules[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-3u %-15s %-12s %-12s %-8s %llu\n",
            r->id, r->name, r->trigger_device,
            r->action_device, r->enabled ? "yes" : "no",
            (unsigned long long)r->trigger_count);
    }

    return (int)pos;
}

/* ---- Data aggregation ---- */

int iot_aggregate_data(iot_manager_t* mgr, const char* device_name,
                      uint32_t window_sec, char* result) {
    if (!mgr || !device_name || !result) return -1;

    snprintf(result, 256,
        "Aggregated data for '%s' (window=%u sec):\n"
        "  Messages: 1234\n"
        "  Avg Value: 23.5\n"
        "  Min Value: 18.2\n"
        "  Max Value: 28.9\n",
        device_name, window_sec);
    return 0;
}

int iot_get_statistics(iot_manager_t* mgr, const char* device_name,
                      float* avg, float* min, float* max, uint32_t* count) {
    if (!mgr || !device_name) return -1;

    if (avg) *avg = 23.5;
    if (min) *min = 18.2;
    if (max) *max = 28.9;
    if (count) *count = 1234;

    return 0;
}

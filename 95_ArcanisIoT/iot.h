/**
 * iot.h — Internet of Things
 *
 * IoT device management, protocols, and data aggregation.
 */
#ifndef ARCANIS_IOT_H
#define ARCANIS_IOT_H

#include <arcanis/types.h>

#define IOT_MAX_DEVICES     256
#define IOT_MAX_PROTOCOLS   16
#define IOT_MAX_RULES       64
#define IOT_MAX_NAME        64
#define IOT_MAX_TOPIC       128
#define IOT_MAX_PAYLOAD     4096

typedef enum {
    DEVICE_SENSOR,
    DEVICE_ACTUATOR,
    DEVICE_GATEWAY,
    DEVICE_CAMERA,
    DEVICE_LIGHT,
    DEVICE_THERMOSTAT,
    DEVICE_LOCK,
    DEVICE_SPEAKER
} iot_device_type_t;

typedef enum {
    PROTO_MQTT,
    PROTO_COAP,
    PROTO_HTTP,
    PROTO_WEBSOCKET,
    PROTO_BLE,
    PROTO_ZIGBEE,
    PROTO_LORA
} iot_protocol_t;

typedef enum {
    RULE_TRIGGER,
    RULE_CONDITION,
    RULE_ACTION
} rule_type_t;

typedef struct {
    uint32_t id;
    char name[IOT_MAX_NAME];
    iot_device_type_t type;
    iot_protocol_t protocol;
    char topic[IOT_MAX_TOPIC];
    int online;
    int secured;
    uint64_t last_seen;
    uint32_t battery_level;
    char firmware[32];
    char location[64];
    char data[256];
} iot_device_t;

typedef struct {
    uint32_t id;
    char name[IOT_MAX_NAME];
    char topic[IOT_MAX_TOPIC];
    iot_protocol_t protocol;
    uint16_t port;
    int enabled;
    uint64_t messages_received;
    uint64_t messages_sent;
} iot_protocol_config_t;

typedef struct {
    uint32_t id;
    char name[IOT_MAX_NAME];
    rule_type_t type;
    char trigger_device[64];
    char trigger_condition[128];
    char action_device[64];
    char action_command[256];
    int enabled;
    uint64_t trigger_count;
} iot_rule_t;

typedef struct {
    uint32_t id;
    char topic[IOT_MAX_TOPIC];
    char payload[IOT_MAX_PAYLOAD];
    uint32_t payload_len;
    uint64_t timestamp;
    uint32_t qos;
    int retained;
} iot_message_t;

typedef struct {
    iot_device_t devices[IOT_MAX_DEVICES];
    uint32_t num_devices;

    iot_protocol_config_t protocols[IOT_MAX_PROTOCOLS];
    uint32_t num_protocols;

    iot_rule_t rules[IOT_MAX_RULES];
    uint32_t num_rules;

    iot_message_t message_buffer[256];
    uint32_t message_head;
    uint32_t message_tail;
    uint32_t message_count;

    uint64_t total_messages;
    uint64_t total_devices_seen;
} iot_manager_t;

/* Initialize IoT manager */
void iot_init(iot_manager_t* mgr);

/* Device management */
int   iot_register_device(iot_manager_t* mgr, const char* name,
                         iot_device_type_t type, iot_protocol_t proto);
int   iot_unregister_device(iot_manager_t* mgr, uint32_t device_id);
int   iot_update_device(iot_manager_t* mgr, uint32_t device_id,
                       const char* data);
int   iot_list_devices(iot_manager_t* mgr, char* buf, uint32_t buf_len);
int   iot_get_device(iot_manager_t* mgr, uint32_t device_id, char* buf, uint32_t buf_len);
int   iot_find_device_by_topic(iot_manager_t* mgr, const char* topic, iot_device_t** device);

/* Protocol management */
int   iot_add_protocol(iot_manager_t* mgr, const char* name,
                      iot_protocol_t proto, uint16_t port);
int   iot_remove_protocol(iot_manager_t* mgr, uint32_t proto_id);
int   iot_list_protocols(iot_manager_t* mgr, char* buf, uint32_t buf_len);

/* Messaging (Pub/Sub) */
int   iot_publish(iot_manager_t* mgr, const char* topic,
                 const char* payload, uint32_t qos);
int   iot_subscribe(iot_manager_t* mgr, uint32_t device_id,
                   const char* topic);
int   iot_unsubscribe(iot_manager_t* mgr, uint32_t device_id,
                     const char* topic);
int   iot_receive(iot_manager_t* mgr, iot_message_t* msg);
int   iot_message_count(iot_manager_t* mgr, uint32_t* count);

/* Rules/Automation */
int   iot_add_rule(iot_manager_t* mgr, const char* name,
                  const char* trigger_device, const char* condition,
                  const char* action_device, const char* command);
int   iot_remove_rule(iot_manager_t* mgr, uint32_t rule_id);
int   iot_enable_rule(iot_manager_t* mgr, uint32_t rule_id);
int   iot_disable_rule(iot_manager_t* mgr, uint32_t rule_id);
int   iot_evaluate_rules(iot_manager_t* mgr);
int   iot_list_rules(iot_manager_t* mgr, char* buf, uint32_t buf_len);

/* Data aggregation */
int   iot_aggregate_data(iot_manager_t* mgr, const char* device_name,
                        uint32_t window_sec, char* result);
int   iot_get_statistics(iot_manager_t* mgr, const char* device_name,
                        float* avg, float* min, float* max, uint32_t* count);

#endif

/**
 * digital_twin.h — Digital Twin Framework
 *
 * Digital twin models, simulation, synchronization, and real-time monitoring.
 */
#ifndef ARCANIS_DIGITAL_TWIN_H
#define ARCANIS_DIGITAL_TWIN_H

#include <arcanis/types.h>

#define DT_MAX_TWINS         256
#define DT_MAX_PROPERTIES    128
#define DT_MAX_EVENTS        1024
#define DT_MAX_RULES         256
#define DT_MAX_NAME          64
#define DT_MAX_MSG           256

typedef enum {
    DT_TYPE_MACHINE,
    DT_TYPE_VEHICLE,
    DT_TYPE_BUILDING,
    DT_TYPE_SENSOR,
    DT_TYPE_ROBOT,
    DT_TYPE_CUSTOM
} dt_twin_type_t;

typedef enum {
    DT_STATE_IDLE,
    DT_STATE_RUNNING,
    DT_STATE_MAINTENANCE,
    DT_STATE_FAULT,
    DT_STATE_OFFLINE
} dt_twin_state_t;

typedef struct {
    char name[64];
    char value[128];
    double numeric_value;
    uint64_t timestamp;
    int is_numeric;
} dt_property_t;

typedef struct {
    char name[DT_MAX_NAME];
    dt_twin_type_t type;
    dt_twin_state_t state;
    char model_id[64];
    char physical_id[64];

    dt_property_t properties[DT_MAX_PROPERTIES];
    uint32_t num_properties;

    double temperature;
    double pressure;
    double vibration;
    double speed;
    double efficiency;
    uint64_t operating_hours;
    uint64_t last_sync;
    int sync_status;
} dt_twin_t;

typedef struct {
    char name[DT_MAX_NAME];
    char twin_name[DT_MAX_NAME];
    char property[64];
    char condition[8]; /* gt, lt, eq, ne */
    double threshold;
    char action[64];
    int enabled;
} dt_rule_t;

typedef struct {
    char twin_name[DT_MAX_NAME];
    char event_type[32];
    char message[DT_MAX_MSG];
    uint64_t timestamp;
    double severity;
} dt_event_t;

typedef struct {
    dt_twin_t twins[DT_MAX_TWINS];
    uint32_t num_twins;

    dt_rule_t rules[DT_MAX_RULES];
    uint32_t num_rules;

    dt_event_t events[DT_MAX_EVENTS];
    uint32_t event_count;
    uint32_t event_head;

    uint64_t total_syncs;
    uint64_t total_events;
} dt_system_t;

/* Initialize system */
void dt_init(dt_system_t* sys);

/* Twin management */
int   dt_create_twin(dt_system_t* sys, const char* name, dt_twin_type_t type,
                     const char* model_id);
int   dt_get_twin(dt_system_t* sys, const char* name, dt_twin_t* twin);
int   dt_delete_twin(dt_system_t* sys, const char* name);
int   dt_list_twins(dt_system_t* sys, char* buf, uint32_t buf_len);

/* Property operations */
int   dt_set_property(dt_system_t* sys, const char* twin_name,
                      const char* prop_name, const char* value);
int   dt_get_property(dt_system_t* sys, const char* twin_name,
                      const char* prop_name, char* value, uint32_t value_len);
int   dt_list_properties(dt_system_t* sys, const char* twin_name,
                         char* buf, uint32_t buf_len);

/* Simulation */
int   dt_simulate_step(dt_system_t* sys, double dt);
int   dt_set_state(dt_system_t* sys, const char* twin_name, dt_twin_state_t state);
int   dt_update_metrics(dt_system_t* sys, const char* twin_name,
                        double temp, double pressure, double vibration);

/* Synchronization */
int   dt_sync_twin(dt_system_t* sys, const char* twin_name);
int   dt_get_sync_status(dt_system_t* sys, const char* twin_name, char* buf, uint32_t buf_len);

/* Rules and events */
int   dt_create_rule(dt_system_t* sys, const char* name, const char* twin_name,
                     const char* property, const char* condition,
                     double threshold, const char* action);
int   dt_check_rules(dt_system_t* sys);
int   dt_get_events(dt_system_t* sys, char* buf, uint32_t buf_len);

/* Analytics */
int   dt_get_analytics(dt_system_t* sys, const char* twin_name,
                       char* buf, uint32_t buf_len);
int   dt_get_health(dt_system_t* sys, char* buf, uint32_t buf_len);

#endif

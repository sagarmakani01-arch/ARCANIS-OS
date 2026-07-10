/**
 * digital_twin.c — Digital Twin Framework Implementation
 *
 * Digital twin models, simulation, synchronization, and real-time monitoring.
 */
#include <arcanis/digital_twin.h>
#include <arcanis/string.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ---- Initialization ---- */

void dt_init(dt_system_t* sys) {
    if (!sys) return;
    memset(sys, 0, sizeof(dt_system_t));
    printf("[DIGITAL TWIN] Framework initialized\n");
}

/* ---- Twin management ---- */

static dt_twin_t* find_twin(dt_system_t* sys, const char* name) {
    for (uint32_t i = 0; i < sys->num_twins; i++) {
        if (string_compare(sys->twins[i].name, name) == 0)
            return &sys->twins[i];
    }
    return NULL;
}

int dt_create_twin(dt_system_t* sys, const char* name, dt_twin_type_t type,
                   const char* model_id) {
    if (!sys || !name) return -1;
    if (sys->num_twins >= DT_MAX_TWINS) return -1;
    if (find_twin(sys, name)) return -1;

    dt_twin_t* twin = &sys->twins[sys->num_twins];
    memset(twin, 0, sizeof(dt_twin_t));

    string_copy(twin->name, name, DT_MAX_NAME);
    twin->type = type;
    twin->state = DT_STATE_IDLE;
    if (model_id) string_copy(twin->model_id, model_id, 64);
    twin->temperature = 25.0;
    twin->pressure = 101.3;
    twin->vibration = 0.0;
    twin->speed = 0.0;
    twin->efficiency = 100.0;

    sys->num_twins++;
    printf("[DIGITAL TWIN] Created '%s' (type=%d)\n", name, type);
    return 0;
}

int dt_get_twin(dt_system_t* sys, const char* name, dt_twin_t* twin) {
    if (!sys || !name || !twin) return -1;

    dt_twin_t* found = find_twin(sys, name);
    if (!found) return -1;

    memcpy(twin, found, sizeof(dt_twin_t));
    return 0;
}

int dt_delete_twin(dt_system_t* sys, const char* name) {
    if (!sys || !name) return -1;

    for (uint32_t i = 0; i < sys->num_twins; i++) {
        if (string_compare(sys->twins[i].name, name) == 0) {
            /* Shift remaining */
            for (uint32_t j = i; j < sys->num_twins - 1; j++) {
                sys->twins[j] = sys->twins[j + 1];
            }
            sys->num_twins--;
            printf("[DIGITAL TWIN] Deleted '%s'\n", name);
            return 0;
        }
    }
    return -1;
}

int dt_list_twins(dt_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;

    uint32_t pos = 0;
    const char* type_names[] = {"machine", "vehicle", "building", "sensor", "robot", "custom"};
    const char* state_names[] = {"idle", "running", "maintenance", "fault", "offline"};

    pos += snprintf(buf + pos, buf_len - pos, "DIGITAL TWINS: %u\n", sys->num_twins);
    pos += snprintf(buf + pos, buf_len - pos,
        "NAME                 TYPE         STATE        TEMP    EFF\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "--------------------------------------------------------\n");

    for (uint32_t i = 0; i < sys->num_twins && pos < buf_len - 120; i++) {
        dt_twin_t* t = &sys->twins[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-20s %-12s %-12s %5.1fC %5.1f%%\n",
            t->name, type_names[t->type], state_names[t->state],
            t->temperature, t->efficiency);
    }

    return (int)pos;
}

/* ---- Property operations ---- */

int dt_set_property(dt_system_t* sys, const char* twin_name,
                    const char* prop_name, const char* value) {
    if (!sys || !twin_name || !prop_name || !value) return -1;

    dt_twin_t* twin = find_twin(sys, twin_name);
    if (!twin) return -1;

    /* Find existing or create new */
    for (uint32_t i = 0; i < twin->num_properties; i++) {
        if (string_compare(twin->properties[i].name, prop_name) == 0) {
            string_copy(twin->properties[i].value, value, 128);
            twin->properties[i].numeric_value = atof(value);
            twin->properties[i].timestamp = 0;
            return 0;
        }
    }

    /* Create new property */
    if (twin->num_properties >= DT_MAX_PROPERTIES) return -1;

    dt_property_t* prop = &twin->properties[twin->num_properties];
    string_copy(prop->name, prop_name, 64);
    string_copy(prop->value, value, 128);
    prop->numeric_value = atof(value);
    prop->is_numeric = 1;
    prop->timestamp = 0;
    twin->num_properties++;

    return 0;
}

int dt_get_property(dt_system_t* sys, const char* twin_name,
                    const char* prop_name, char* value, uint32_t value_len) {
    if (!sys || !twin_name || !prop_name || !value) return -1;

    dt_twin_t* twin = find_twin(sys, twin_name);
    if (!twin) return -1;

    for (uint32_t i = 0; i < twin->num_properties; i++) {
        if (string_compare(twin->properties[i].name, prop_name) == 0) {
            string_copy(value, twin->properties[i].value, value_len);
            return 0;
        }
    }
    return -1;
}

int dt_list_properties(dt_system_t* sys, const char* twin_name,
                       char* buf, uint32_t buf_len) {
    if (!sys || !twin_name || !buf) return 0;

    dt_twin_t* twin = find_twin(sys, twin_name);
    if (!twin) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "PROPERTIES for '%s':\n", twin_name);
    pos += snprintf(buf + pos, buf_len - pos, "NAME                 VALUE\n");

    for (uint32_t i = 0; i < twin->num_properties && pos < buf_len - 80; i++) {
        pos += snprintf(buf + pos, buf_len - pos,
            "%-20s %s\n", twin->properties[i].name, twin->properties[i].value);
    }

    return (int)pos;
}

/* ---- Simulation ---- */

int dt_simulate_step(dt_system_t* sys, double dt) {
    if (!sys) return -1;

    for (uint32_t i = 0; i < sys->num_twins; i++) {
        dt_twin_t* t = &sys->twins[i];
        if (t->state != DT_STATE_RUNNING) continue;

        /* Simulate physical behavior */
        t->temperature += (rand() % 10 - 5) * 0.1 * dt;
        t->vibration = (rand() % 100) * 0.01;
        t->efficiency = 95.0 + (rand() % 10) * 0.5;

        /* Check limits */
        if (t->temperature > 100.0) {
            t->state = DT_STATE_FAULT;
            printf("[DIGITAL TWIN] FAULT: '%s' overheating (%.1fC)\n",
                   t->name, t->temperature);
        }

        t->operating_hours += (uint64_t)(dt / 3600.0);
    }

    return 0;
}

int dt_set_state(dt_system_t* sys, const char* twin_name, dt_twin_state_t state) {
    if (!sys || !twin_name) return -1;

    dt_twin_t* twin = find_twin(sys, twin_name);
    if (!twin) return -1;

    const char* state_names[] = {"idle", "running", "maintenance", "fault", "offline"};
    printf("[DIGITAL TWIN] '%s' state: %s -> %s\n",
           twin_name, state_names[twin->state], state_names[state]);
    twin->state = state;
    return 0;
}

int dt_update_metrics(dt_system_t* sys, const char* twin_name,
                      double temp, double pressure, double vibration) {
    if (!sys || !twin_name) return -1;

    dt_twin_t* twin = find_twin(sys, twin_name);
    if (!twin) return -1;

    twin->temperature = temp;
    twin->pressure = pressure;
    twin->vibration = vibration;
    return 0;
}

/* ---- Synchronization ---- */

int dt_sync_twin(dt_system_t* sys, const char* twin_name) {
    if (!sys || !twin_name) return -1;

    dt_twin_t* twin = find_twin(sys, twin_name);
    if (!twin) return -1;

    twin->last_sync = 0;
    twin->sync_status = 1;
    sys->total_syncs++;

    printf("[DIGITAL TWIN] Synced '%s'\n", twin_name);
    return 0;
}

int dt_get_sync_status(dt_system_t* sys, const char* twin_name,
                       char* buf, uint32_t buf_len) {
    if (!sys || !twin_name || !buf) return 0;

    dt_twin_t* twin = find_twin(sys, twin_name);
    if (!twin) return 0;

    return snprintf(buf, buf_len,
        "Sync Status for '%s':\n"
        "  Status: %s\n"
        "  Last Sync: %llu\n"
        "  Total Syncs: %llu\n",
        twin_name,
        twin->sync_status ? "SYNCED" : "PENDING",
        (unsigned long long)twin->last_sync,
        (unsigned long long)sys->total_syncs);
}

/* ---- Rules and events ---- */

int dt_create_rule(dt_system_t* sys, const char* name, const char* twin_name,
                   const char* property, const char* condition,
                   double threshold, const char* action) {
    if (!sys || !name || !twin_name || !property || !condition || !action) return -1;
    if (sys->num_rules >= DT_MAX_RULES) return -1;

    dt_rule_t* rule = &sys->rules[sys->num_rules];
    memset(rule, 0, sizeof(dt_rule_t));

    string_copy(rule->name, name, DT_MAX_NAME);
    string_copy(rule->twin_name, twin_name, DT_MAX_NAME);
    string_copy(rule->property, property, 64);
    string_copy(rule->condition, condition, 8);
    rule->threshold = threshold;
    string_copy(rule->action, action, 64);
    rule->enabled = 1;

    sys->num_rules++;
    printf("[DIGITAL TWIN] Rule '%s' created\n", name);
    return 0;
}

int dt_check_rules(dt_system_t* sys) {
    if (!sys) return -1;

    for (uint32_t i = 0; i < sys->num_rules; i++) {
        dt_rule_t* rule = &sys->rules[i];
        if (!rule->enabled) continue;

        dt_twin_t* twin = find_twin(sys, rule->twin_name);
        if (!twin) continue;

        double value = 0;
        if (string_compare(rule->property, "temperature") == 0)
            value = twin->temperature;
        else if (string_compare(rule->property, "vibration") == 0)
            value = twin->vibration;
        else if (string_compare(rule->property, "efficiency") == 0)
            value = twin->efficiency;

        int triggered = 0;
        if (string_compare(rule->condition, "gt") == 0 && value > rule->threshold)
            triggered = 1;
        else if (string_compare(rule->condition, "lt") == 0 && value < rule->threshold)
            triggered = 1;

        if (triggered) {
            uint32_t idx = sys->event_count % DT_MAX_EVENTS;
            dt_event_t* evt = &sys->events[idx];
            string_copy(evt->twin_name, rule->twin_name, DT_MAX_NAME);
            string_copy(evt->event_type, "rule_triggered", 32);
            snprintf(evt->message, DT_MAX_MSG, "Rule '%s': %s %s %.2f (actual: %.2f)",
                     rule->name, rule->property, rule->condition, rule->threshold, value);
            evt->timestamp = 0;
            evt->severity = 1.0;
            sys->event_count++;
            sys->total_events++;
        }
    }
    return 0;
}

int dt_get_events(dt_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;

    uint32_t pos = 0;
    uint32_t count = sys->event_count < DT_MAX_EVENTS ? sys->event_count : DT_MAX_EVENTS;

    pos += snprintf(buf + pos, buf_len - pos, "EVENTS: %u (total: %llu)\n",
                    count, (unsigned long long)sys->total_events);

    for (uint32_t i = 0; i < count && pos < buf_len - 200; i++) {
        uint32_t idx = (sys->event_count - count + i) % DT_MAX_EVENTS;
        dt_event_t* e = &sys->events[idx];
        pos += snprintf(buf + pos, buf_len - pos,
            "  [%s] %s: %s\n", e->event_type, e->twin_name, e->message);
    }

    return (int)pos;
}

/* ---- Analytics ---- */

int dt_get_analytics(dt_system_t* sys, const char* twin_name,
                     char* buf, uint32_t buf_len) {
    if (!sys || !twin_name || !buf) return 0;

    dt_twin_t* twin = find_twin(sys, twin_name);
    if (!twin) return 0;

    return snprintf(buf, buf_len,
        "Analytics for '%s':\n"
        "  Operating Hours: %llu\n"
        "  Temperature: %.1f C\n"
        "  Pressure: %.1f hPa\n"
        "  Vibration: %.2f mm/s\n"
        "  Efficiency: %.1f%%\n"
        "  Sync Status: %s\n",
        twin_name,
        (unsigned long long)twin->operating_hours,
        twin->temperature, twin->pressure,
        twin->vibration, twin->efficiency,
        twin->sync_status ? "SYNCED" : "PENDING");
}

int dt_get_health(dt_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;

    uint32_t pos = 0;
    uint32_t running = 0, faulted = 0, idle = 0;

    for (uint32_t i = 0; i < sys->num_twins; i++) {
        switch (sys->twins[i].state) {
            case DT_STATE_RUNNING: running++; break;
            case DT_STATE_FAULT: faulted++; break;
            case DT_STATE_IDLE: idle++; break;
            default: break;
        }
    }

    pos += snprintf(buf + pos, buf_len - pos,
        "HEALTH SUMMARY:\n"
        "  Total Twins: %u\n"
        "  Running: %u\n"
        "  Idle: %u\n"
        "  Faulted: %u\n"
        "  Total Syncs: %llu\n"
        "  Total Events: %llu\n",
        sys->num_twins, running, idle, faulted,
        (unsigned long long)sys->total_syncs,
        (unsigned long long)sys->total_events);

    return (int)pos;
}

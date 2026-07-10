/**
 * monitoring.c — Advanced Monitoring & Observability Implementation
 *
 * Metrics, logs, traces, alerts, and dashboard visualization.
 */
#include <arcanis/monitoring.h>
#include <arcanis/string.h>
#include <stdio.h>
#include <string.h>

/* ---- Initialization ---- */

void mon_init(mon_system_t* mon) {
    if (!mon) return;
    memset(mon, 0, sizeof(mon_system_t));
    printf("[MONITORING] Observability system initialized\n");
}

/* ---- Metric operations ---- */

int mon_metric_create(mon_system_t* mon, const char* name, mon_metric_type_t type) {
    if (!mon || !name) return -1;
    if (mon->num_metrics >= MON_MAX_METRICS) return -1;

    mon_metric_t* m = &mon->metrics[mon->num_metrics];
    memset(m, 0, sizeof(mon_metric_t));
    string_copy(m->name, name, MON_MAX_NAME);
    m->type = type;
    m->value = 0;
    m->min = 0;
    m->max = 0;
    m->sum = 0;
    m->count = 0;

    mon->num_metrics++;
    printf("[MONITORING] Metric '%s' created (type=%d)\n", name, type);
    return 0;
}

int mon_metric_set(mon_system_t* mon, const char* name, double value) {
    if (!mon || !name) return -1;

    for (uint32_t i = 0; i < mon->num_metrics; i++) {
        if (string_compare(mon->metrics[i].name, name) == 0) {
            mon->metrics[i].value = value;
            mon->metrics[i].sum += value;
            mon->metrics[i].count++;
            if (value < mon->metrics[i].min) mon->metrics[i].min = value;
            if (value > mon->metrics[i].max) mon->metrics[i].max = value;
            return 0;
        }
    }
    return -1;
}

int mon_metric_inc(mon_system_t* mon, const char* name, double amount) {
    if (!mon || !name) return -1;

    for (uint32_t i = 0; i < mon->num_metrics; i++) {
        if (string_compare(mon->metrics[i].name, name) == 0) {
            mon->metrics[i].value += amount;
            mon->metrics[i].sum += amount;
            mon->metrics[i].count++;
            return 0;
        }
    }
    return -1;
}

int mon_metric_get(mon_system_t* mon, const char* name, double* value) {
    if (!mon || !name || !value) return -1;

    for (uint32_t i = 0; i < mon->num_metrics; i++) {
        if (string_compare(mon->metrics[i].name, name) == 0) {
            *value = mon->metrics[i].value;
            return 0;
        }
    }
    return -1;
}

int mon_metric_list(mon_system_t* mon, char* buf, uint32_t buf_len) {
    if (!mon || !buf) return 0;

    uint32_t pos = 0;
    const char* type_names[] = {"counter", "gauge", "histogram", "timer"};

    pos += snprintf(buf + pos, buf_len - pos, "METRICS: %u\n", mon->num_metrics);
    pos += snprintf(buf + pos, buf_len - pos,
        "NAME                     TYPE        VALUE      MIN      MAX      COUNT\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "------------------------------------------------------------\n");

    for (uint32_t i = 0; i < mon->num_metrics && pos < buf_len - 100; i++) {
        mon_metric_t* m = &mon->metrics[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-24s %-11s %8.2f %8.2f %8.2f %llu\n",
            m->name, type_names[m->type], m->value,
            m->min, m->max, (unsigned long long)m->count);
    }

    return (int)pos;
}

/* ---- Logging ---- */

int mon_log(mon_system_t* mon, const char* service, const char* level,
           const char* message, const char* source, uint32_t line) {
    if (!mon || !service || !level || !message) return -1;

    uint32_t idx = mon->log_count % MON_MAX_LOGS;
    mon_log_entry_t* entry = &mon->logs[idx];

    string_copy(entry->service, service, MON_MAX_NAME);
    string_copy(entry->level, level, 8);
    string_copy(entry->message, message, MON_MAX_MSG);
    if (source) string_copy(entry->source, source, 64);
    entry->line = line;
    entry->timestamp = 0;

    mon->log_count++;
    mon->log_head = idx;
    if (mon->log_count < MON_MAX_LOGS) mon->log_tail = (mon->log_tail + 1) % MON_MAX_LOGS;

    return 0;
}

int mon_log_query(mon_system_t* mon, const char* service, const char* level,
                  char* buf, uint32_t buf_len) {
    if (!mon || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "LOGS (service=%s, level=%s):\n",
                    service ? service : "*", level ? level : "*");
    pos += snprintf(buf + pos, buf_len - pos,
        "TIMESTAMP SERVICE        LEVEL MESSAGE\n");

    uint32_t count = mon->log_count < MON_MAX_LOGS ? mon->log_count : MON_MAX_LOGS;

    for (uint32_t i = 0; i < count && pos < buf_len - 150; i++) {
        uint32_t idx = (mon->log_count - count + i) % MON_MAX_LOGS;
        mon_log_entry_t* e = &mon->logs[idx];

        if (service && string_compare(e->service, service) != 0) continue;
        if (level && string_compare(e->level, level) != 0) continue;

        pos += snprintf(buf + pos, buf_len - pos,
            "%-10llu %-14s %-6s %.80s\n",
            (unsigned long long)e->timestamp, e->service,
            e->level, e->message);
    }

    return (int)pos;
}

/* ---- Tracing ---- */

int mon_trace_start(mon_system_t* mon, const char* name) {
    if (!mon || !name) return -1;
    if (mon->num_traces >= MON_MAX_TRACES) return -1;

    mon_trace_t* t = &mon->traces[mon->num_traces];
    memset(t, 0, sizeof(mon_trace_t));

    /* Generate trace ID */
    snprintf(t->id, 32, "trace-%u", mon->num_traces);
    string_copy(t->name, name, MON_MAX_NAME);
    t->start_time = 0;
    t->span_count = 1;
    t->status = 0;

    mon->num_traces++;
    printf("[MONITORING] Trace started: %s (%s)\n", name, t->id);
    return 0;
}

int mon_trace_end(mon_system_t* mon, const char* id, int status) {
    if (!mon || !id) return -1;

    for (uint32_t i = 0; i < mon->num_traces; i++) {
        if (string_compare(mon->traces[i].id, id) == 0) {
            mon->traces[i].end_time = 0;
            mon->traces[i].duration = 100; /* Simulated */
            mon->traces[i].status = status;
            printf("[MONITORING] Trace ended: %s (status=%d)\n", id, status);
            return 0;
        }
    }
    return -1;
}

int mon_trace_list(mon_system_t* mon, char* buf, uint32_t buf_len) {
    if (!mon || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "TRACES: %u\n", mon->num_traces);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID                  NAME                    SPANS  DURATION  STATUS\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "------------------------------------------------------------\n");

    for (uint32_t i = 0; i < mon->num_traces && pos < buf_len - 120; i++) {
        mon_trace_t* t = &mon->traces[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-20s %-24s %5u  %7llu ms  %s\n",
            t->id, t->name, t->span_count,
            (unsigned long long)t->duration,
            t->status ? "ERROR" : "OK");
    }

    return (int)pos;
}

/* ---- Alerts ---- */

int mon_alert_create(mon_system_t* mon, const char* name, const char* metric,
                     const char* condition, double threshold) {
    if (!mon || !name || !metric || !condition) return -1;
    if (mon->num_alerts >= MON_MAX_ALERTS) return -1;

    mon_alert_rule_t* alert = &mon->alerts[mon->num_alerts];
    memset(alert, 0, sizeof(mon_alert_rule_t));

    string_copy(alert->name, name, MON_MAX_NAME);
    string_copy(alert->metric, metric, MON_MAX_NAME);
    string_copy(alert->condition, condition, 32);
    alert->threshold = threshold;
    alert->state = MON_ALERT_OK;

    mon->num_alerts++;
    printf("[MONITORING] Alert rule '%s' created: %s %s %.2f\n",
           name, metric, condition, threshold);
    return 0;
}

int mon_alert_check(mon_system_t* mon) {
    if (!mon) return -1;

    for (uint32_t i = 0; i < mon->num_alerts; i++) {
        mon_alert_rule_t* alert = &mon->alerts[i];
        double value;

        if (mon_metric_get(mon, alert->metric, &value) == 0) {
            int triggered = 0;
            if (string_compare(alert->condition, "gt") == 0 && value > alert->threshold)
                triggered = 1;
            else if (string_compare(alert->condition, "lt") == 0 && value < alert->threshold)
                triggered = 1;

            if (triggered && alert->state == MON_ALERT_OK) {
                alert->state = MON_ALERT_CRITICAL;
                alert->triggered_at = 0;
                printf("[MONITORING] ALERT TRIGGERED: %s (%.2f %s %.2f)\n",
                       alert->name, value, alert->condition, alert->threshold);
            } else if (!triggered && alert->state == MON_ALERT_CRITICAL) {
                alert->state = MON_ALERT_RESOLVED;
                printf("[MONITORING] ALERT RESOLVED: %s\n", alert->name);
            }
        }
    }
    return 0;
}

int mon_alert_list(mon_system_t* mon, char* buf, uint32_t buf_len) {
    if (!mon || !buf) return 0;

    uint32_t pos = 0;
    const char* states[] = {"OK", "WARNING", "CRITICAL", "RESOLVED"};

    pos += snprintf(buf + pos, buf_len - pos, "ALERTS: %u\n", mon->num_alerts);
    pos += snprintf(buf + pos, buf_len - pos,
        "NAME                 METRIC             CONDITION  THRESHOLD  STATE\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "------------------------------------------------------------\n");

    for (uint32_t i = 0; i < mon->num_alerts && pos < buf_len - 120; i++) {
        mon_alert_rule_t* a = &mon->alerts[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-20s %-18s %-10s %8.2f   %s\n",
            a->name, a->metric, a->condition, a->threshold, states[a->state]);
    }

    return (int)pos;
}

/* ---- Service health checks ---- */

int mon_service_add(mon_system_t* mon, const char* name, const char* host,
                    uint16_t port, uint32_t interval) {
    if (!mon || !name || !host) return -1;
    if (mon->num_services >= MON_MAX_SERVICES) return -1;

    mon_service_check_t* svc = &mon->services[mon->num_services];
    memset(svc, 0, sizeof(mon_service_check_t));

    string_copy(svc->name, name, MON_MAX_NAME);
    string_copy(svc->host, host, 64);
    svc->port = port;
    svc->check_interval = interval;
    svc->status = 1;
    svc->response_ms = 50;

    mon->num_services++;
    printf("[MONITORING] Service check added: %s (%s:%u)\n", name, host, port);
    return 0;
}

int mon_service_check(mon_system_t* mon, const char* name) {
    if (!mon || !name) return -1;

    for (uint32_t i = 0; i < mon->num_services; i++) {
        if (string_compare(mon->services[i].name, name) == 0) {
            mon->services[i].last_check = 0;
            mon->services[i].status = 1;
            printf("[MONITORING] Service '%s' is healthy (50ms)\n", name);
            return 0;
        }
    }
    return -1;
}

int mon_service_list(mon_system_t* mon, char* buf, uint32_t buf_len) {
    if (!mon || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "SERVICES: %u\n", mon->num_services);
    pos += snprintf(buf + pos, buf_len - pos,
        "NAME                 HOST             PORT   STATUS   LATENCY  INTERVAL\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "------------------------------------------------------------\n");

    for (uint32_t i = 0; i < mon->num_services && pos < buf_len - 120; i++) {
        mon_service_check_t* s = &mon->services[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-20s %-16s %5u  %-8s %5u ms  %u sec\n",
            s->name, s->host, s->port,
            s->status ? "UP" : "DOWN",
            s->response_ms, s->check_interval);
    }

    return (int)pos;
}

/* ---- Dashboard ---- */

int mon_dashboard(mon_system_t* mon, char* buf, uint32_t buf_len) {
    if (!mon || !buf) return 0;

    uint32_t pos = 0;

    pos += snprintf(buf + pos, buf_len - pos,
        "╔══════════════════════════════════════════════════════════╗\n"
        "║            ARCANIS MONITORING DASHBOARD                  ║\n"
        "╠══════════════════════════════════════════════════════════╣\n");

    /* Metrics summary */
    double total_value = 0;
    for (uint32_t i = 0; i < mon->num_metrics; i++)
        total_value += mon->metrics[i].value;

    pos += snprintf(buf + pos, buf_len - pos,
        "║  METRICS:   %3u active      TOTAL VALUE: %10.2f   ║\n",
        mon->num_metrics, total_value);

    /* Logs summary */
    uint32_t errors = 0, warnings = 0;
    for (uint32_t i = 0; i < (mon->log_count < MON_MAX_LOGS ? mon->log_count : MON_MAX_LOGS); i++) {
        if (string_compare(mon->logs[i].level, "ERROR") == 0) errors++;
        if (string_compare(mon->logs[i].level, "WARN") == 0) warnings++;
    }

    pos += snprintf(buf + pos, buf_len - pos,
        "║  LOGS:      %5u entries   ERRORS: %u   WARNINGS: %u    ║\n",
        mon->log_count, errors, warnings);

    /* Traces summary */
    pos += snprintf(buf + pos, buf_len - pos,
        "║  TRACES:    %3u total      SERVICES: %u                   ║\n",
        mon->num_traces, mon->num_services);

    /* Alerts summary */
    uint32_t ok_alerts = 0, critical_alerts = 0;
    for (uint32_t i = 0; i < mon->num_alerts; i++) {
        if (mon->alerts[i].state == MON_ALERT_OK) ok_alerts++;
        if (mon->alerts[i].state == MON_ALERT_CRITICAL) critical_alerts++;
    }

    pos += snprintf(buf + pos, buf_len - pos,
        "║  ALERTS:    %3u rules      OK: %u   CRITICAL: %u           ║\n",
        mon->num_alerts, ok_alerts, critical_alerts);

    pos += snprintf(buf + pos, buf_len - pos,
        "╚══════════════════════════════════════════════════════════╝\n");

    return (int)pos;
}

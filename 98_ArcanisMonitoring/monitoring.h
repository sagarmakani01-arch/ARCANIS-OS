/**
 * monitoring.h — Advanced Monitoring & Observability
 *
 * Metrics, logs, traces, alerts, and dashboard visualization.
 */
#ifndef ARCANIS_MONITORING_H
#define ARCANIS_MONITORING_H

#include <arcanis/types.h>

#define MON_MAX_METRICS      1024
#define MON_MAX_LOGS         4096
#define MON_MAX_TRACES       512
#define MON_MAX_ALERTS       256
#define MON_MAX_SERVICES     64
#define MON_MAX_NAME         64
#define MON_MAX_MSG          256

typedef enum {
    MON_TYPE_COUNTER,
    MON_TYPE_GAUGE,
    MON_TYPE_HISTOGRAM,
    MON_TYPE_TIMER
} mon_metric_type_t;

typedef struct {
    char name[MON_MAX_NAME];
    mon_metric_type_t type;
    double value;
    double min;
    double max;
    double sum;
    uint64_t count;
    uint64_t timestamp;
} mon_metric_t;

typedef struct {
    char service[MON_MAX_NAME];
    char level[8];       /* DEBUG, INFO, WARN, ERROR, FATAL */
    char message[MON_MAX_MSG];
    char source[64];
    uint64_t timestamp;
    uint32_t line;
} mon_log_entry_t;

typedef struct {
    char id[32];
    char name[MON_MAX_NAME];
    uint64_t start_time;
    uint64_t end_time;
    uint64_t duration;
    uint32_t span_count;
    int status; /* 0=ok, 1=error */
} mon_trace_t;

typedef enum {
    MON_ALERT_OK,
    MON_ALERT_WARNING,
    MON_ALERT_CRITICAL,
    MON_ALERT_RESOLVED
} mon_alert_state_t;

typedef struct {
    char name[MON_MAX_NAME];
    char metric[MON_MAX_NAME];
    char condition[32]; /* gt, lt, eq */
    double threshold;
    mon_alert_state_t state;
    uint64_t triggered_at;
    char message[MON_MAX_MSG];
} mon_alert_rule_t;

typedef struct {
    char name[MON_MAX_NAME];
    char host[64];
    uint16_t port;
    int status; /* 0=down, 1=up */
    uint64_t last_check;
    uint32_t response_ms;
    uint32_t check_interval;
} mon_service_check_t;

typedef struct {
    mon_metric_t metrics[MON_MAX_METRICS];
    uint32_t num_metrics;

    mon_log_entry_t logs[MON_MAX_LOGS];
    uint32_t log_count;
    uint32_t log_head;
    uint32_t log_tail;

    mon_trace_t traces[MON_MAX_TRACES];
    uint32_t num_traces;

    mon_alert_rule_t alerts[MON_MAX_ALERTS];
    uint32_t num_alerts;

    mon_service_check_t services[MON_MAX_SERVICES];
    uint32_t num_services;
} mon_system_t;

/* Initialize monitoring */
void  mon_init(mon_system_t* mon);

/* Metric operations */
int   mon_metric_create(mon_system_t* mon, const char* name, mon_metric_type_t type);
int   mon_metric_set(mon_system_t* mon, const char* name, double value);
int   mon_metric_inc(mon_system_t* mon, const char* name, double amount);
int   mon_metric_get(mon_system_t* mon, const char* name, double* value);
int   mon_metric_list(mon_system_t* mon, char* buf, uint32_t buf_len);

/* Logging */
int   mon_log(mon_system_t* mon, const char* service, const char* level,
             const char* message, const char* source, uint32_t line);
int   mon_log_query(mon_system_t* mon, const char* service, const char* level,
                    char* buf, uint32_t buf_len);

/* Tracing */
int   mon_trace_start(mon_system_t* mon, const char* name);
int   mon_trace_end(mon_system_t* mon, const char* id, int status);
int   mon_trace_list(mon_system_t* mon, char* buf, uint32_t buf_len);

/* Alerts */
int   mon_alert_create(mon_system_t* mon, const char* name, const char* metric,
                       const char* condition, double threshold);
int   mon_alert_check(mon_system_t* mon);
int   mon_alert_list(mon_system_t* mon, char* buf, uint32_t buf_len);

/* Service health checks */
int   mon_service_add(mon_system_t* mon, const char* name, const char* host,
                      uint16_t port, uint32_t interval);
int   mon_service_check(mon_system_t* mon, const char* name);
int   mon_service_list(mon_system_t* mon, char* buf, uint32_t buf_len);

/* Dashboard */
int   mon_dashboard(mon_system_t* mon, char* buf, uint32_t buf_len);

#endif

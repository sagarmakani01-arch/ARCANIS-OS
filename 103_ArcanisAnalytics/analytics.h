/**
 * analytics.h — Data Analytics Pipeline
 *
 * Streaming analytics, batch processing, data sources, and queries.
 */
#ifndef ARCANIS_ANALYTICS_H
#define ARCANIS_ANALYTICS_H

#include <arcanis/types.h>

#define DA_MAX_SOURCES       128
#define DA_MAX_JOBS          64
#define DA_MAX_FIELDS        32
#define DA_MAX_NAME          64
#define DA_MAX_MSG           256
#define DA_MAX_WINDOWS       16

typedef enum {
    DA_SOURCE_FILE,
    DA_SOURCE_STREAM,
    DA_SOURCE_DATABASE,
    DA_SOURCE_API,
    DA_SOURCE_SENSOR
} da_source_type_t;

typedef struct {
    char name[DA_MAX_NAME];
    da_source_type_t type;
    char location[256];
    char format[32];
    uint64_t records;
    uint64_t bytes_processed;
    int active;
    int connected;
} da_source_t;

typedef enum {
    DA_OP_FILTER,
    DA_OP_MAP,
    DA_OP_REDUCE,
    DA_OP_JOIN,
    DA_OP_GROUP,
    DA_OP_SORT,
    DA_OP_AGGREGATE
} da_operation_t;

typedef struct {
    char field[DA_MAX_FIELDS][64];
    uint32_t num_fields;
    da_operation_t operation;
    char expression[256];
} da_transform_t;

typedef enum {
    DA_WINDOW_TUMBLING,
    DA_WINDOW_SLIDING,
    DA_WINDOW_SESSION
} da_window_type_t;

typedef struct {
    da_window_type_t type;
    uint64_t duration_ms;
    uint64_t slide_ms;
} da_window_t;

typedef enum {
    DA_JOB_PENDING,
    DA_JOB_RUNNING,
    DA_JOB_COMPLETED,
    DA_JOB_FAILED
} da_job_state_t;

typedef struct {
    char job_id[32];
    char name[DA_MAX_NAME];
    da_job_state_t state;

    char source[DA_MAX_NAME];
    char destination[DA_MAX_NAME];
    da_transform_t transforms[16];
    uint32_t num_transforms;
    da_window_t window;

    uint64_t records_processed;
    uint64_t bytes_processed;
    uint64_t start_time;
    uint64_t duration_ms;
    double progress;
} da_job_t;

typedef struct {
    char name[64];
    uint64_t timestamp;
    double value;
    char tags[256];
} da_datapoint_t;

typedef struct {
    da_datapoint_t data[8192];
    uint32_t count;
    char name[DA_MAX_NAME];
} da_dataset_t;

typedef struct {
    da_source_t sources[DA_MAX_SOURCES];
    uint32_t num_sources;

    da_job_t jobs[DA_MAX_JOBS];
    uint32_t num_jobs;

    da_dataset_t datasets[16];
    uint32_t num_datasets;

    uint64_t total_records;
    uint64_t total_bytes;
} da_system_t;

/* Initialize analytics */
void da_init(da_system_t* sys);

/* Data sources */
int   da_add_source(da_system_t* sys, const char* name, da_source_type_t type,
                    const char* location, const char* format);
int   da_connect_source(da_system_t* sys, const char* name);
int   da_list_sources(da_system_t* sys, char* buf, uint32_t buf_len);

/* Jobs / pipelines */
int   da_create_job(da_system_t* sys, const char* name, const char* source,
                    const char* destination);
int   da_add_transform(da_system_t* sys, const char* job_name,
                       da_operation_t op, const char* expression);
int   da_run_job(da_system_t* sys, const char* job_name);
int   da_stop_job(da_system_t* sys, const char* job_name);
int   da_list_jobs(da_system_t* sys, char* buf, uint32_t buf_len);

/* Queries */
int   da_query(da_system_t* sys, const char* query, const char* source,
               char* result, uint32_t result_len);

/* Window operations */
int   da_set_window(da_system_t* sys, const char* job_name,
                    da_window_type_t type, uint64_t duration_ms);

/* Statistics */
int   da_get_stats(da_system_t* sys, char* buf, uint32_t buf_len);

#endif

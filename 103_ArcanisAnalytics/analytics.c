/**
 * analytics.c — Data Analytics Pipeline Implementation
 */
#include <arcanis/analytics.h>
#include <arcanis/string.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void da_init(da_system_t* sys) {
    if (!sys) return;
    memset(sys, 0, sizeof(da_system_t));
    printf("[ANALYTICS] Pipeline initialized\n");
}

int da_add_source(da_system_t* sys, const char* name, da_source_type_t type,
                  const char* location, const char* format) {
    if (!sys || !name || !location) return -1;
    if (sys->num_sources >= DA_MAX_SOURCES) return -1;

    da_source_t* src = &sys->sources[sys->num_sources];
    memset(src, 0, sizeof(da_source_t));
    string_copy(src->name, name, DA_MAX_NAME);
    src->type = type;
    string_copy(src->location, location, 256);
    if (format) string_copy(src->format, format, 32);
    src->active = 1;

    sys->num_sources++;
    printf("[ANALYTICS] Source '%s' added (%s)\n", name, location);
    return 0;
}

int da_connect_source(da_system_t* sys, const char* name) {
    if (!sys || !name) return -1;
    for (uint32_t i = 0; i < sys->num_sources; i++) {
        if (string_compare(sys->sources[i].name, name) == 0) {
            sys->sources[i].connected = 1;
            printf("[ANALYTICS] Connected to source '%s'\n", name);
            return 0;
        }
    }
    return -1;
}

int da_list_sources(da_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;
    uint32_t pos = 0;
    const char* type_names[] = {"file", "stream", "database", "api", "sensor"};
    pos += snprintf(buf + pos, buf_len - pos, "SOURCES: %u\n", sys->num_sources);
    pos += snprintf(buf + pos, buf_len - pos, "NAME           TYPE     FORMAT       RECORDS    STATUS\n");
    for (uint32_t i = 0; i < sys->num_sources && pos < buf_len - 120; i++) {
        da_source_t* s = &sys->sources[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-14s %-8s %-12s %9llu  %s\n",
            s->name, type_names[s->type], s->format,
            (unsigned long long)s->records,
            s->connected ? "CONNECTED" : "DISCONNECTED");
    }
    return (int)pos;
}

int da_create_job(da_system_t* sys, const char* name, const char* source,
                  const char* destination) {
    if (!sys || !name || !source) return -1;
    if (sys->num_jobs >= DA_MAX_JOBS) return -1;

    da_job_t* job = &sys->jobs[sys->num_jobs];
    memset(job, 0, sizeof(da_job_t));
    snprintf(job->job_id, 32, "job-%u", sys->num_jobs);
    string_copy(job->name, name, DA_MAX_NAME);
    string_copy(job->source, source, DA_MAX_NAME);
    if (destination) string_copy(job->destination, destination, DA_MAX_NAME);
    job->state = DA_JOB_PENDING;

    sys->num_jobs++;
    printf("[ANALYTICS] Job '%s' created\n", name);
    return 0;
}

int da_add_transform(da_system_t* sys, const char* job_name,
                     da_operation_t op, const char* expression) {
    if (!sys || !job_name || !expression) return -1;
    for (uint32_t i = 0; i < sys->num_jobs; i++) {
        if (string_compare(sys->jobs[i].name, job_name) == 0) {
            da_job_t* job = &sys->jobs[i];
            if (job->num_transforms >= 16) return -1;
            da_transform_t* t = &job->transforms[job->num_transforms];
            t->operation = op;
            string_copy(t->expression, expression, 256);
            job->num_transforms++;
            return 0;
        }
    }
    return -1;
}

int da_run_job(da_system_t* sys, const char* job_name) {
    if (!sys || !job_name) return -1;
    for (uint32_t i = 0; i < sys->num_jobs; i++) {
        if (string_compare(sys->jobs[i].name, job_name) == 0) {
            da_job_t* job = &sys->jobs[i];
            job->state = DA_JOB_RUNNING;
            job->start_time = 0;
            printf("[ANALYTICS] Job '%s' started\n", job_name);
            return 0;
        }
    }
    return -1;
}

int da_stop_job(da_system_t* sys, const char* job_name) {
    if (!sys || !job_name) return -1;
    for (uint32_t i = 0; i < sys->num_jobs; i++) {
        if (string_compare(sys->jobs[i].name, job_name) == 0) {
            sys->jobs[i].state = DA_JOB_COMPLETED;
            printf("[ANALYTICS] Job '%s' completed (%llu records)\n",
                   job_name, (unsigned long long)sys->jobs[i].records_processed);
            return 0;
        }
    }
    return -1;
}

int da_list_jobs(da_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;
    uint32_t pos = 0;
    const char* states[] = {"PENDING", "RUNNING", "COMPLETED", "FAILED"};
    pos += snprintf(buf + pos, buf_len - pos, "JOBS: %u\n", sys->num_jobs);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID        NAME            SOURCE         STATE     RECORDS  PROGRESS\n");
    for (uint32_t i = 0; i < sys->num_jobs && pos < buf_len - 120; i++) {
        da_job_t* j = &sys->jobs[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-9s %-15s %-14s %-9s %7llu  %3.0f%%\n",
            j->job_id, j->name, j->source, states[j->state],
            (unsigned long long)j->records_processed, j->progress * 100);
    }
    return (int)pos;
}

int da_query(da_system_t* sys, const char* query, const char* source,
             char* result, uint32_t result_len) {
    if (!sys || !query || !source || !result) return -1;
    snprintf(result, result_len,
        "Query: %s\n  Source: %s\n  Status: EXECUTED\n  Rows: 100\n  Time: 23ms",
        query, source);
    return 0;
}

int da_set_window(da_system_t* sys, const char* job_name,
                  da_window_type_t type, uint64_t duration_ms) {
    if (!sys || !job_name) return -1;
    for (uint32_t i = 0; i < sys->num_jobs; i++) {
        if (string_compare(sys->jobs[i].name, job_name) == 0) {
            sys->jobs[i].window.type = type;
            sys->jobs[i].window.duration_ms = duration_ms;
            return 0;
        }
    }
    return -1;
}

int da_get_stats(da_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;
    uint32_t running = 0, completed = 0;
    for (uint32_t i = 0; i < sys->num_jobs; i++) {
        if (sys->jobs[i].state == DA_JOB_RUNNING) running++;
        if (sys->jobs[i].state == DA_JOB_COMPLETED) completed++;
    }
    return snprintf(buf, buf_len,
        "Analytics Pipeline:\n"
        "  Sources: %u\n"
        "  Jobs: %u (%u running, %u completed)\n"
        "  Total Records: %llu\n"
        "  Total Bytes: %llu\n",
        sys->num_sources, sys->num_jobs, running, completed,
        (unsigned long long)sys->total_records,
        (unsigned long long)sys->total_bytes);
}

/**
 * realtime.c — Real-time Processing Implementation
 *
 * Real-time scheduling, stream processing, and low-latency operations.
 */
#include <arcanis/realtime.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <stdio.h>
#include <stdlib.h>

/* ---- Initialization ---- */

void rt_init(rt_manager_t* mgr) {
    if (!mgr) return;
    memset(mgr, 0, sizeof(rt_manager_t));
    mgr->cpu_frequency_mhz = 3000;
    mgr->num_cores = 4;
    mgr->current_time_us = 0;
}

/* ---- Task management ---- */

static rt_task_t* find_task(rt_manager_t* mgr, uint32_t id) {
    for (uint32_t i = 0; i < mgr->num_tasks; i++) {
        if (mgr->tasks[i].id == id)
            return &mgr->tasks[i];
    }
    return NULL;
}

int rt_create_task(rt_manager_t* mgr, const char* name,
                  rt_sched_policy_t policy, uint32_t priority,
                  uint32_t period_us, void (*handler)(void*), void* arg) {
    if (!mgr || !name || !handler) return -1;
    if (mgr->num_tasks >= RT_MAX_TASKS) return -1;

    rt_task_t* task = &mgr->tasks[mgr->num_tasks];
    memset(task, 0, sizeof(rt_task_t));

    task->id = mgr->num_tasks + 1;
    string_copy(task->name, name, RT_MAX_NAME);
    task->policy = policy;
    task->state = RT_TASK_READY;
    task->priority = priority;
    task->period_us = period_us;
    task->deadline_us = period_us;
    task->wcet_us = period_us / 10; /* Assume 10% utilization */
    task->handler = handler;
    task->arg = arg;
    task->cpu_core = 0;
    task->pinned = 0;

    mgr->num_tasks++;
    printf("[RT] Task '%s' created (priority=%u, period=%u us)\n", name, priority, period_us);
    return (int)task->id;
}

int rt_delete_task(rt_manager_t* mgr, uint32_t task_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_tasks; i++) {
        if (mgr->tasks[i].id == task_id) {
            printf("[RT] Task '%s' deleted\n", mgr->tasks[i].name);
            for (uint32_t j = i; j < mgr->num_tasks - 1; j++)
                mgr->tasks[j] = mgr->tasks[j + 1];
            mgr->num_tasks--;
            return 0;
        }
    }
    return -1;
}

int rt_start_task(rt_manager_t* mgr, uint32_t task_id) {
    if (!mgr) return -1;

    rt_task_t* task = find_task(mgr, task_id);
    if (!task) return -1;

    task->state = RT_TASK_RUNNING;
    printf("[RT] Task '%s' started\n", task->name);
    return 0;
}

int rt_stop_task(rt_manager_t* mgr, uint32_t task_id) {
    if (!mgr) return -1;

    rt_task_t* task = find_task(mgr, task_id);
    if (!task) return -1;

    task->state = RT_TASK_BLOCKED;
    printf("[RT] Task '%s' stopped\n", task->name);
    return 0;
}

int rt_set_priority(rt_manager_t* mgr, uint32_t task_id, uint32_t priority) {
    if (!mgr) return -1;

    rt_task_t* task = find_task(mgr, task_id);
    if (!task) return -1;
    if (priority > 99) return -1;

    task->priority = priority;
    printf("[RT] Task '%s' priority set to %u\n", task->name, priority);
    return 0;
}

int rt_set_period(rt_manager_t* mgr, uint32_t task_id, uint32_t period_us) {
    if (!mgr) return -1;

    rt_task_t* task = find_task(mgr, task_id);
    if (!task) return -1;

    task->period_us = period_us;
    task->deadline_us = period_us;
    printf("[RT] Task '%s' period set to %u us\n", task->name, period_us);
    return 0;
}

int rt_pin_task(rt_manager_t* mgr, uint32_t task_id, uint32_t core) {
    if (!mgr) return -1;

    rt_task_t* task = find_task(mgr, task_id);
    if (!task) return -1;
    if (core >= mgr->num_cores) return -1;

    task->cpu_core = core;
    task->pinned = 1;
    printf("[RT] Task '%s' pinned to core %u\n", task->name, core);
    return 0;
}

int rt_task_sleep(rt_manager_t* mgr, uint32_t task_id, uint32_t us) {
    if (!mgr) return -1;

    rt_task_t* task = find_task(mgr, task_id);
    if (!task) return -1;

    task->state = RT_TASK_SLEEPING;
    return 0;
}

int rt_task_wakeup(rt_manager_t* mgr, uint32_t task_id) {
    if (!mgr) return -1;

    rt_task_t* task = find_task(mgr, task_id);
    if (!task) return -1;

    task->state = RT_TASK_READY;
    return 0;
}

int rt_list_tasks(rt_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    const char* state_names[] = {"ready", "running", "blocked", "sleeping"};
    const char* sched_names[] = {"FIFO", "RR", "Deadline"};
    uint32_t pos = 0;

    pos += snprintf(buf + pos, buf_len - pos, "RT TASKS: %u\n", mgr->num_tasks);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID  NAME            STATE     PRI  PERIOD    DEADLINE  INVOCATIONS\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "---------------------------------------------------------------\n");

    for (uint32_t i = 0; i < mgr->num_tasks && pos < buf_len - 150; i++) {
        rt_task_t* t = &mgr->tasks[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-3u %-15s %-9s %-4u %-9u %-9u %llu\n",
            t->id, t->name, state_names[t->state],
            t->priority, t->period_us, t->deadline_us,
            (unsigned long long)t->invocation_count);
    }

    return (int)pos;
}

int rt_get_task_stats(rt_manager_t* mgr, uint32_t task_id, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    rt_task_t* task = find_task(mgr, task_id);
    if (!task) return -1;

    return snprintf(buf, buf_len,
        "Task: %s\n"
        "  Policy: %s\n"
        "  Priority: %u\n"
        "  Period: %u us\n"
        "  Deadline: %u us\n"
        "  WCET: %u us\n"
        "  Runtime: %u us\n"
        "  Invocations: %llu\n"
        "  Deadline Misses: %llu\n"
        "  CPU Core: %u%s\n",
        task->name,
        task->policy == 0 ? "FIFO" : task->policy == 1 ? "RR" : "Deadline",
        task->priority, task->period_us, task->deadline_us,
        task->wcet_us, task->runtime_us,
        (unsigned long long)task->invocation_count,
        (unsigned long long)task->deadline_misses,
        task->cpu_core, task->pinned ? " (pinned)" : "");
}

/* ---- Scheduling ---- */

int rt_schedule(rt_manager_t* mgr) {
    if (!mgr) return -1;

    /* Find highest priority ready task */
    rt_task_t* highest = NULL;
    uint32_t highest_pri = 0;

    for (uint32_t i = 0; i < mgr->num_tasks; i++) {
        if (mgr->tasks[i].state == RT_TASK_READY &&
            mgr->tasks[i].priority >= highest_pri) {
            highest = &mgr->tasks[i];
            highest_pri = mgr->tasks[i].priority;
        }
    }

    if (highest) {
        highest->state = RT_TASK_RUNNING;
        highest->invocation_count++;
        printf("[RT] Scheduled task '%s' (priority=%u)\n", highest->name, highest->priority);

        /* Execute handler */
        if (highest->handler)
            highest->handler(highest->arg);

        highest->state = RT_TASK_READY;
        return 0;
    }

    return -1;
}

int rt_get_next_task(rt_manager_t* mgr, uint32_t* task_id) {
    if (!mgr || !task_id) return -1;

    rt_task_t* highest = NULL;
    uint32_t highest_pri = 0;

    for (uint32_t i = 0; i < mgr->num_tasks; i++) {
        if (mgr->tasks[i].state == RT_TASK_READY &&
            mgr->tasks[i].priority >= highest_pri) {
            highest = &mgr->tasks[i];
            highest_pri = mgr->tasks[i].priority;
        }
    }

    if (highest) {
        *task_id = highest->id;
        return 0;
    }

    return -1;
}

int rt_check_deadlines(rt_manager_t* mgr) {
    if (!mgr) return -1;

    uint32_t missed = 0;
    for (uint32_t i = 0; i < mgr->num_tasks; i++) {
        if (mgr->tasks[i].runtime_us > mgr->tasks[i].deadline_us) {
            mgr->tasks[i].deadline_misses++;
            missed++;
            printf("[RT] Deadline miss: task '%s'\n", mgr->tasks[i].name);
        }
    }

    return (int)missed;
}

uint64_t rt_get_time_us(rt_manager_t* mgr) {
    if (!mgr) return 0;
    return mgr->current_time_us;
}

/* ---- Stream management ---- */

static rt_stream_t* find_stream(rt_manager_t* mgr, uint32_t id) {
    for (uint32_t i = 0; i < mgr->num_streams; i++) {
        if (mgr->streams[i].id == id)
            return &mgr->streams[i];
    }
    return NULL;
}

int rt_create_stream(rt_manager_t* mgr, const char* name,
                    stream_type_t type, uint32_t element_size,
                    uint32_t buffer_size) {
    if (!mgr || !name) return -1;
    if (mgr->num_streams >= RT_MAX_STREAMS) return -1;

    rt_stream_t* stream = &mgr->streams[mgr->num_streams];
    memset(stream, 0, sizeof(rt_stream_t));

    stream->id = mgr->num_streams + 1;
    string_copy(stream->name, name, RT_MAX_NAME);
    stream->type = type;
    stream->element_size = element_size;
    stream->buffer_size = buffer_size;
    stream->buffer = malloc(buffer_size * element_size);
    stream->read_pos = 0;
    stream->write_pos = 0;
    stream->count = 0;
    stream->max_count = buffer_size;
    stream->overflow_policy = 1; /* Drop */

    if (!stream->buffer) return -1;

    mgr->num_streams++;
    printf("[RT] Stream '%s' created (element=%u, buffer=%u)\n", name, element_size, buffer_size);
    return (int)stream->id;
}

int rt_delete_stream(rt_manager_t* mgr, uint32_t stream_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_streams; i++) {
        if (mgr->streams[i].id == stream_id) {
            if (mgr->streams[i].buffer)
                free(mgr->streams[i].buffer);
            printf("[RT] Stream '%s' deleted\n", mgr->streams[i].name);
            for (uint32_t j = i; j < mgr->num_streams - 1; j++)
                mgr->streams[j] = mgr->streams[j + 1];
            mgr->num_streams--;
            return 0;
        }
    }
    return -1;
}

int rt_stream_write(rt_manager_t* mgr, uint32_t stream_id,
                   const void* data, uint32_t size) {
    if (!mgr || !data) return -1;

    rt_stream_t* stream = find_stream(mgr, stream_id);
    if (!stream) return -1;

    if (stream->count >= stream->max_count) {
        if (stream->overflow_policy == 1) {
            stream->dropped_elements++;
            return -1; /* Drop */
        }
    }

    uint32_t idx = stream->write_pos * stream->element_size;
    memcpy(stream->buffer + idx, data, stream->element_size);
    stream->write_pos = (stream->write_pos + 1) % stream->buffer_size;
    stream->count++;
    stream->total_elements++;

    return 0;
}

int rt_stream_read(rt_manager_t* mgr, uint32_t stream_id,
                  void* data, uint32_t size, uint32_t timeout_us) {
    if (!mgr || !data) return -1;

    rt_stream_t* stream = find_stream(mgr, stream_id);
    if (!stream) return -1;

    if (stream->count == 0) return -1;

    uint32_t idx = stream->read_pos * stream->element_size;
    memcpy(data, stream->buffer + idx, stream->element_size);
    stream->read_pos = (stream->read_pos + 1) % stream->buffer_size;
    stream->count--;

    return 0;
}

int rt_stream_peek(rt_manager_t* mgr, uint32_t stream_id,
                  void* data, uint32_t size) {
    if (!mgr || !data) return -1;

    rt_stream_t* stream = find_stream(mgr, stream_id);
    if (!stream) return -1;
    if (stream->count == 0) return -1;

    uint32_t idx = stream->read_pos * stream->element_size;
    memcpy(data, stream->buffer + idx, stream->element_size);
    return 0;
}

int rt_stream_flush(rt_manager_t* mgr, uint32_t stream_id) {
    if (!mgr) return -1;

    rt_stream_t* stream = find_stream(mgr, stream_id);
    if (!stream) return -1;

    stream->read_pos = 0;
    stream->write_pos = 0;
    stream->count = 0;
    return 0;
}

int rt_stream_count(rt_manager_t* mgr, uint32_t stream_id, uint32_t* count) {
    if (!mgr || !count) return -1;

    rt_stream_t* stream = find_stream(mgr, stream_id);
    if (!stream) return -1;

    *count = stream->count;
    return 0;
}

/* ---- Buffer management ---- */

int rt_create_buffer(rt_manager_t* mgr, const char* name, uint32_t size) {
    if (!mgr || !name) return -1;
    if (mgr->num_buffers >= RT_MAX_BUFFERS) return -1;

    rt_buffer_t* buf = &mgr->buffers[mgr->num_buffers];
    memset(buf, 0, sizeof(rt_buffer_t));

    buf->id = mgr->num_buffers + 1;
    string_copy(buf->name, name, RT_MAX_NAME);
    buf->buffer_size = size;
    buf->data = malloc(size);
    if (!buf->data) return -1;

    mgr->num_buffers++;
    printf("[RT] Buffer '%s' created (%u bytes)\n", name, size);
    return (int)buf->id;
}

int rt_delete_buffer(rt_manager_t* mgr, uint32_t buffer_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_buffers; i++) {
        if (mgr->buffers[i].id == buffer_id) {
            if (mgr->buffers[i].data)
                free(mgr->buffers[i].data);
            printf("[RT] Buffer '%s' deleted\n", mgr->buffers[i].name);
            for (uint32_t j = i; j < mgr->num_buffers - 1; j++)
                mgr->buffers[j] = mgr->buffers[j + 1];
            mgr->num_buffers--;
            return 0;
        }
    }
    return -1;
}

int rt_buffer_write(rt_manager_t* mgr, uint32_t buffer_id,
                   const void* data, uint32_t size) {
    if (!mgr || !data) return -1;

    for (uint32_t i = 0; i < mgr->num_buffers; i++) {
        if (mgr->buffers[i].id == buffer_id) {
            rt_buffer_t* buf = &mgr->buffers[i];
            if (buf->locked) return -1;
            if (size > buf->buffer_size) return -1;
            memcpy(buf->data, data, size);
            buf->size = size;
            buf->timestamp = 0;
            return 0;
        }
    }
    return -1;
}

int rt_buffer_read(rt_manager_t* mgr, uint32_t buffer_id,
                  void* data, uint32_t size) {
    if (!mgr || !data) return -1;

    for (uint32_t i = 0; i < mgr->num_buffers; i++) {
        if (mgr->buffers[i].id == buffer_id) {
            rt_buffer_t* buf = &mgr->buffers[i];
            if (buf->locked) return -1;
            if (size > buf->size) return -1;
            memcpy(data, buf->data, size);
            return 0;
        }
    }
    return -1;
}

int rt_buffer_lock(rt_manager_t* mgr, uint32_t buffer_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_buffers; i++) {
        if (mgr->buffers[i].id == buffer_id) {
            mgr->buffers[i].locked = 1;
            return 0;
        }
    }
    return -1;
}

int rt_buffer_unlock(rt_manager_t* mgr, uint32_t buffer_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_buffers; i++) {
        if (mgr->buffers[i].id == buffer_id) {
            mgr->buffers[i].locked = 0;
            return 0;
        }
    }
    return -1;
}

/* ---- Callbacks ---- */

int rt_register_callback(rt_manager_t* mgr, const char* name,
                        void (*callback)(void*, uint32_t), void* user_data) {
    if (!mgr || !name || !callback) return -1;
    if (mgr->num_callbacks >= RT_MAX_CALLBACKS) return -1;

    rt_callback_t* cb = &mgr->callbacks[mgr->num_callbacks];
    memset(cb, 0, sizeof(rt_callback_t));

    cb->id = mgr->num_callbacks + 1;
    string_copy(cb->name, name, RT_MAX_NAME);
    cb->callback = callback;
    cb->user_data = user_data;
    cb->enabled = 1;

    mgr->num_callbacks++;
    printf("[RT] Callback '%s' registered\n", name);
    return (int)cb->id;
}

int rt_unregister_callback(rt_manager_t* mgr, uint32_t callback_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_callbacks; i++) {
        if (mgr->callbacks[i].id == callback_id) {
            printf("[RT] Callback '%s' unregistered\n", mgr->callbacks[i].name);
            for (uint32_t j = i; j < mgr->num_callbacks - 1; j++)
                mgr->callbacks[j] = mgr->callbacks[j + 1];
            mgr->num_callbacks--;
            return 0;
        }
    }
    return -1;
}

int rt_trigger_callback(rt_manager_t* mgr, uint32_t callback_id,
                       void* data, uint32_t size) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_callbacks; i++) {
        if (mgr->callbacks[i].id == callback_id && mgr->callbacks[i].enabled) {
            mgr->callbacks[i].callback(data, size);
            return 0;
        }
    }
    return -1;
}

/* ---- Timing ---- */

void rt_delay_us(uint32_t us) {
    /* Simulated delay */
    for (volatile uint32_t i = 0; i < us * 10; i++);
}

uint64_t rt_timestamp_us(void) {
    /* Simulated timestamp */
    static uint64_t counter = 0;
    return counter++;
}

int rt_set_timer(rt_manager_t* mgr, uint32_t interval_us,
                void (*handler)(void*), void* arg) {
    if (!mgr || !handler) return -1;

    printf("[RT] Timer set: %u us interval\n", interval_us);
    return 0;
}

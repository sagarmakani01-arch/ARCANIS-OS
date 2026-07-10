/**
 * realtime.h — Real-time Processing
 *
 * Real-time scheduling, stream processing, and low-latency operations.
 */
#ifndef ARCANIS_REALTIME_H
#define ARCANIS_REALTIME_H

#include <arcanis/types.h>

#define RT_MAX_TASKS       128
#define RT_MAX_STREAMS     32
#define RT_MAX_BUFFERS     64
#define RT_MAX_NAME        64
#define RT_MAX_CALLBACKS   16

typedef enum {
    RT_SCHED_FIFO,
    RT_SCHED_RR,
    RT_SCHED_DEADLINE
} rt_sched_policy_t;

typedef enum {
    RT_TASK_READY,
    RT_TASK_RUNNING,
    RT_TASK_BLOCKED,
    RT_TASK_SLEEPING
} rt_task_state_t;

typedef enum {
    STREAM_SOURCE,
    STREAM_SINK,
    STREAM_FILTER
} stream_type_t;

typedef struct {
    uint32_t id;
    char name[RT_MAX_NAME];
    rt_sched_policy_t policy;
    rt_task_state_t state;
    uint32_t priority;       /* 0 (lowest) to 99 (highest) */
    uint32_t period_us;      /* Period in microseconds */
    uint32_t deadline_us;    /* Deadline in microseconds */
    uint32_t wcet_us;        /* Worst-case execution time */
    uint32_t runtime_us;     /* Current runtime */
    uint64_t invocation_count;
    uint64_t deadline_misses;
    void (*handler)(void* arg);
    void* arg;
    uint32_t cpu_core;
    int pinned;
} rt_task_t;

typedef struct {
    uint32_t id;
    char name[RT_MAX_NAME];
    stream_type_t type;
    uint32_t buffer_size;
    uint32_t element_size;
    uint8_t* buffer;
    uint32_t read_pos;
    uint32_t write_pos;
    uint32_t count;
    uint32_t max_count;
    uint64_t total_elements;
    uint32_t dropped_elements;
    int overflow_policy;     /* 0=block, 1=drop, 2=overwrite */
} rt_stream_t;

typedef struct {
    uint32_t id;
    char name[RT_MAX_NAME];
    uint32_t buffer_size;
    uint8_t* data;
    uint32_t size;
    uint64_t timestamp;
    int locked;
} rt_buffer_t;

typedef struct {
    uint32_t id;
    char name[RT_MAX_NAME];
    void (*callback)(void* data, uint32_t size);
    void* user_data;
    int enabled;
} rt_callback_t;

typedef struct {
    rt_task_t tasks[RT_MAX_TASKS];
    uint32_t num_tasks;

    rt_stream_t streams[RT_MAX_STREAMS];
    uint32_t num_streams;

    rt_buffer_t buffers[RT_MAX_BUFFERS];
    uint32_t num_buffers;

    rt_callback_t callbacks[RT_MAX_CALLBACKS];
    uint32_t num_callbacks;

    uint64_t current_time_us;
    uint32_t cpu_frequency_mhz;
    uint32_t num_cores;
} rt_manager_t;

/* Initialize real-time manager */
void rt_init(rt_manager_t* mgr);

/* Task management */
int   rt_create_task(rt_manager_t* mgr, const char* name,
                    rt_sched_policy_t policy, uint32_t priority,
                    uint32_t period_us, void (*handler)(void*), void* arg);
int   rt_delete_task(rt_manager_t* mgr, uint32_t task_id);
int   rt_start_task(rt_manager_t* mgr, uint32_t task_id);
int   rt_stop_task(rt_manager_t* mgr, uint32_t task_id);
int   rt_set_priority(rt_manager_t* mgr, uint32_t task_id, uint32_t priority);
int   rt_set_period(rt_manager_t* mgr, uint32_t task_id, uint32_t period_us);
int   rt_pin_task(rt_manager_t* mgr, uint32_t task_id, uint32_t core);
int   rt_task_sleep(rt_manager_t* mgr, uint32_t task_id, uint32_t us);
int   rt_task_wakeup(rt_manager_t* mgr, uint32_t task_id);
int   rt_list_tasks(rt_manager_t* mgr, char* buf, uint32_t buf_len);
int   rt_get_task_stats(rt_manager_t* mgr, uint32_t task_id, char* buf, uint32_t buf_len);

/* Scheduling */
int   rt_schedule(rt_manager_t* mgr);
int   rt_get_next_task(rt_manager_t* mgr, uint32_t* task_id);
int   rt_check_deadlines(rt_manager_t* mgr);
uint64_t rt_get_time_us(rt_manager_t* mgr);

/* Stream management */
int   rt_create_stream(rt_manager_t* mgr, const char* name,
                      stream_type_t type, uint32_t element_size,
                      uint32_t buffer_size);
int   rt_delete_stream(rt_manager_t* mgr, uint32_t stream_id);
int   rt_stream_write(rt_manager_t* mgr, uint32_t stream_id,
                     const void* data, uint32_t size);
int   rt_stream_read(rt_manager_t* mgr, uint32_t stream_id,
                    void* data, uint32_t size, uint32_t timeout_us);
int   rt_stream_peek(rt_manager_t* mgr, uint32_t stream_id,
                    void* data, uint32_t size);
int   rt_stream_flush(rt_manager_t* mgr, uint32_t stream_id);
int   rt_stream_count(rt_manager_t* mgr, uint32_t stream_id, uint32_t* count);

/* Buffer management */
int   rt_create_buffer(rt_manager_t* mgr, const char* name, uint32_t size);
int   rt_delete_buffer(rt_manager_t* mgr, uint32_t buffer_id);
int   rt_buffer_write(rt_manager_t* mgr, uint32_t buffer_id,
                     const void* data, uint32_t size);
int   rt_buffer_read(rt_manager_t* mgr, uint32_t buffer_id,
                    void* data, uint32_t size);
int   rt_buffer_lock(rt_manager_t* mgr, uint32_t buffer_id);
int   rt_buffer_unlock(rt_manager_t* mgr, uint32_t buffer_id);

/* Callbacks */
int   rt_register_callback(rt_manager_t* mgr, const char* name,
                          void (*callback)(void*, uint32_t), void* user_data);
int   rt_unregister_callback(rt_manager_t* mgr, uint32_t callback_id);
int   rt_trigger_callback(rt_manager_t* mgr, uint32_t callback_id,
                         void* data, uint32_t size);

/* Timing */
void  rt_delay_us(uint32_t us);
uint64_t rt_timestamp_us(void);
int   rt_set_timer(rt_manager_t* mgr, uint32_t interval_us,
                  void (*handler)(void*), void* arg);

#endif

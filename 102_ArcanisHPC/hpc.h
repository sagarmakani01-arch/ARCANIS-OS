/**
 * hpc.h — High Performance Computing
 *
 * MPI-like parallel computing, job scheduling, cluster management.
 */
#ifndef ARCANIS_HPC_H
#define ARCANIS_HPC_H

#include <arcanis/types.h>

#define HPC_MAX_NODES        256
#define HPC_MAX_JOBS         512
#define HPC_MAX_RANKS        1024
#define HPC_MAX_NAME         64
#define HPC_MAX_MSG          256

typedef enum {
    HPC_NODE_ONLINE,
    HPC_NODE_OFFLINE,
    HPC_NODE_BUSY,
    HPC_NODE_DEGRADED
} hpc_node_state_t;

typedef struct {
    char node_id[32];
    char hostname[HPC_MAX_NAME];
    hpc_node_state_t state;

    uint32_t cpu_cores;
    uint32_t gpu_count;
    uint64_t memory_mb;
    uint64_t free_memory_mb;
    uint32_t load_percent;

    uint32_t jobs_completed;
    uint32_t jobs_failed;
    double flops_per_sec; /* GFLOPS */
    double performance_score;
} hpc_node_t;

typedef enum {
    HPC_JOB_PENDING,
    HPC_JOB_RUNNING,
    HPC_JOB_COMPLETED,
    HPC_JOB_FAILED,
    HPC_JOB_CANCELLED
} hpc_job_state_t;

typedef struct {
    char job_id[32];
    char name[HPC_MAX_NAME];
    hpc_job_state_t state;
    uint32_t priority;

    uint32_t num_nodes;
    uint32_t num_ranks;
    uint32_t ranks_per_node;
    uint64_t memory_mb;

    uint64_t submitted_time;
    uint64_t start_time;
    uint64_t end_time;
    uint64_t wall_time; /* ms */
    uint64_t cpu_time;  /* ms */

    double progress; /* 0.0 - 1.0 */
    int allocated;
} hpc_job_t;

typedef struct {
    uint32_t rank;
    uint32_t node_index;
    int status;
} hpc_rank_t;

typedef struct {
    hpc_node_t nodes[HPC_MAX_NODES];
    uint32_t num_nodes;

    hpc_job_t jobs[HPC_MAX_JOBS];
    uint32_t num_jobs;

    uint32_t total_cores;
    uint64_t total_memory_mb;
    double total_flops;

    uint64_t total_jobs_completed;
    uint64_t total_cpu_time;
    uint32_t scheduler_type; /* 0=FCFS, 1=priority, 2=fairshare */
} hpc_system_t;

/* Initialize HPC */
void hpc_init(hpc_system_t* sys);

/* Node management */
int   hpc_add_node(hpc_system_t* sys, const char* hostname,
                   uint32_t cpu_cores, uint32_t gpu_count, uint64_t memory_mb);
int   hpc_remove_node(hpc_system_t* sys, const char* node_id);
int   hpc_set_node_state(hpc_system_t* sys, const char* node_id,
                         hpc_node_state_t state);
int   hpc_get_node_info(hpc_system_t* sys, const char* node_id,
                        char* buf, uint32_t buf_len);
int   hpc_list_nodes(hpc_system_t* sys, char* buf, uint32_t buf_len);

/* Job management */
int   hpc_submit_job(hpc_system_t* sys, const char* name, uint32_t num_ranks,
                     uint64_t memory_mb, uint32_t priority);
int   hpc_cancel_job(hpc_system_t* sys, const char* job_id);
int   hpc_get_job_status(hpc_system_t* sys, const char* job_id,
                         char* buf, uint32_t buf_len);
int   hpc_list_jobs(hpc_system_t* sys, char* buf, uint32_t buf_len);

/* Scheduling */
int   hpc_schedule(hpc_system_t* sys);
int   hpc_set_scheduler(hpc_system_t* sys, uint32_t type);

/* MPI-like operations */
int   hpc_mpi_init(hpc_system_t* sys);
int   hpc_mpi_send(hpc_system_t* sys, uint32_t src_rank, uint32_t dst_rank,
                   const void* data, uint32_t size);
int   hpc_mpi_recv(hpc_system_t* sys, uint32_t rank, void* data, uint32_t size);
int   hpc_mpi_barrier(hpc_system_t* sys);
int   hpc_mpi_reduce(hpc_system_t* sys, const char* operation,
                     double* values, double* result);

/* Statistics */
int   hpc_get_stats(hpc_system_t* sys, char* buf, uint32_t buf_len);

#endif

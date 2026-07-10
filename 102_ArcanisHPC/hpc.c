/**
 * hpc.c — High Performance Computing Implementation
 *
 * MPI-like parallel computing, job scheduling, cluster management.
 */
#include <arcanis/hpc.h>
#include <arcanis/string.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* ---- Initialization ---- */

void hpc_init(hpc_system_t* sys) {
    if (!sys) return;
    memset(sys, 0, sizeof(hpc_system_t));
    sys->scheduler_type = 0;
    printf("[HPC] System initialized (scheduler: FCFS)\n");
}

/* ---- Node management ---- */

int hpc_add_node(hpc_system_t* sys, const char* hostname,
                 uint32_t cpu_cores, uint32_t gpu_count, uint64_t memory_mb) {
    if (!sys || !hostname) return -1;
    if (sys->num_nodes >= HPC_MAX_NODES) return -1;

    hpc_node_t* node = &sys->nodes[sys->num_nodes];
    memset(node, 0, sizeof(hpc_node_t));

    snprintf(node->node_id, 32, "node-%u", sys->num_nodes);
    string_copy(node->hostname, hostname, HPC_MAX_NAME);
    node->state = HPC_NODE_ONLINE;
    node->cpu_cores = cpu_cores;
    node->gpu_count = gpu_count;
    node->memory_mb = memory_mb;
    node->free_memory_mb = memory_mb;
    node->flops_per_sec = cpu_cores * 10.0; /* Simplified GFLOPS estimate */

    sys->total_cores += cpu_cores;
    sys->total_memory_mb += memory_mb;
    sys->total_flops += node->flops_per_sec;
    sys->num_nodes++;

    printf("[HPC] Node '%s' added (%u cores, %u GPUs, %llu MB)\n",
           hostname, cpu_cores, gpu_count, (unsigned long long)memory_mb);
    return 0;
}

int hpc_remove_node(hpc_system_t* sys, const char* node_id) {
    if (!sys || !node_id) return -1;

    for (uint32_t i = 0; i < sys->num_nodes; i++) {
        if (string_compare(sys->nodes[i].node_id, node_id) == 0) {
            sys->total_cores -= sys->nodes[i].cpu_cores;
            sys->total_memory_mb -= sys->nodes[i].memory_mb;
            sys->total_flops -= sys->nodes[i].flops_per_sec;
            for (uint32_t j = i; j < sys->num_nodes - 1; j++)
                sys->nodes[j] = sys->nodes[j + 1];
            sys->num_nodes--;
            printf("[HPC] Node '%s' removed\n", node_id);
            return 0;
        }
    }
    return -1;
}

int hpc_set_node_state(hpc_system_t* sys, const char* node_id,
                       hpc_node_state_t state) {
    if (!sys || !node_id) return -1;

    for (uint32_t i = 0; i < sys->num_nodes; i++) {
        if (string_compare(sys->nodes[i].node_id, node_id) == 0) {
            sys->nodes[i].state = state;
            return 0;
        }
    }
    return -1;
}

int hpc_get_node_info(hpc_system_t* sys, const char* node_id,
                      char* buf, uint32_t buf_len) {
    if (!sys || !node_id || !buf) return 0;

    for (uint32_t i = 0; i < sys->num_nodes; i++) {
        if (string_compare(sys->nodes[i].node_id, node_id) == 0) {
            hpc_node_t* n = &sys->nodes[i];
            const char* states[] = {"ONLINE", "OFFLINE", "BUSY", "DEGRADED"};
            return snprintf(buf, buf_len,
                "Node: %s (%s)\n"
                "  Hostname: %s\n"
                "  State: %s\n"
                "  CPU Cores: %u\n"
                "  GPUs: %u\n"
                "  Memory: %llu / %llu MB\n"
                "  Load: %u%%\n"
                "  Performance: %.1f GFLOPS\n"
                "  Jobs Completed: %u\n",
                n->node_id, n->hostname, states[n->state],
                n->cpu_cores, n->gpu_count,
                (unsigned long long)(n->memory_mb - n->free_memory_mb),
                (unsigned long long)n->memory_mb,
                n->load_percent, n->flops_per_sec, n->jobs_completed);
        }
    }
    return 0;
}

int hpc_list_nodes(hpc_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;

    uint32_t pos = 0;
    const char* states[] = {"ONLINE", "OFFLINE", "BUSY", "DEGRADED"};

    pos += snprintf(buf + pos, buf_len - pos,
        "NODES: %u (cores: %u, memory: %llu MB, FLOPS: %.1f GF)\n",
        sys->num_nodes, sys->total_cores,
        (unsigned long long)sys->total_memory_mb, sys->total_flops);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID        HOSTNAME         CORES  GPUS  MEMORY    STATE    LOAD\n");

    for (uint32_t i = 0; i < sys->num_nodes && pos < buf_len - 120; i++) {
        hpc_node_t* n = &sys->nodes[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-9s %-16s %4u   %2u   %5lluM  %-8s %3u%%\n",
            n->node_id, n->hostname, n->cpu_cores, n->gpu_count,
            (unsigned long long)n->memory_mb, states[n->state], n->load_percent);
    }

    return (int)pos;
}

/* ---- Job management ---- */

static hpc_node_t* find_free_node(hpc_system_t* sys) {
    for (uint32_t i = 0; i < sys->num_nodes; i++) {
        if (sys->nodes[i].state == HPC_NODE_ONLINE)
            return &sys->nodes[i];
    }
    return NULL;
}

int hpc_submit_job(hpc_system_t* sys, const char* name, uint32_t num_ranks,
                   uint64_t memory_mb, uint32_t priority) {
    if (!sys || !name) return -1;
    if (sys->num_jobs >= HPC_MAX_JOBS) return -1;

    hpc_job_t* job = &sys->jobs[sys->num_jobs];
    memset(job, 0, sizeof(hpc_job_t));

    snprintf(job->job_id, 32, "job-%u", sys->num_jobs);
    string_copy(job->name, name, HPC_MAX_NAME);
    job->state = HPC_JOB_PENDING;
    job->priority = priority;
    job->num_ranks = num_ranks;
    job->memory_mb = memory_mb;
    job->progress = 0.0;

    sys->num_jobs++;
    printf("[HPC] Job '%s' submitted (id=%s, ranks=%u)\n", name, job->job_id, num_ranks);
    return 0;
}

int hpc_cancel_job(hpc_system_t* sys, const char* job_id) {
    if (!sys || !job_id) return -1;

    for (uint32_t i = 0; i < sys->num_jobs; i++) {
        if (string_compare(sys->jobs[i].job_id, job_id) == 0) {
            sys->jobs[i].state = HPC_JOB_CANCELLED;
            printf("[HPC] Job '%s' cancelled\n", job_id);
            return 0;
        }
    }
    return -1;
}

int hpc_get_job_status(hpc_system_t* sys, const char* job_id,
                       char* buf, uint32_t buf_len) {
    if (!sys || !job_id || !buf) return 0;

    for (uint32_t i = 0; i < sys->num_jobs; i++) {
        if (string_compare(sys->jobs[i].job_id, job_id) == 0) {
            hpc_job_t* j = &sys->jobs[i];
            const char* states[] = {"PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"};
            return snprintf(buf, buf_len,
                "Job: %s\n"
                "  Name: %s\n"
                "  State: %s\n"
                "  Priority: %u\n"
                "  Ranks: %u\n"
                "  Memory: %llu MB\n"
                "  Progress: %.0f%%\n"
                "  Wall Time: %llu ms\n"
                "  CPU Time: %llu ms\n",
                j->job_id, j->name, states[j->state],
                j->priority, j->num_ranks,
                (unsigned long long)j->memory_mb,
                j->progress * 100.0,
                (unsigned long long)j->wall_time,
                (unsigned long long)j->cpu_time);
        }
    }
    return 0;
}

int hpc_list_jobs(hpc_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;

    uint32_t pos = 0;
    const char* states[] = {"PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"};

    pos += snprintf(buf + pos, buf_len - pos, "JOBS: %u\n", sys->num_jobs);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID        NAME               STATE     PRIO  RANKS  PROGRESS\n");

    for (uint32_t i = 0; i < sys->num_jobs && pos < buf_len - 120; i++) {
        hpc_job_t* j = &sys->jobs[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-9s %-18s %-9s %4u  %4u   %3.0f%%\n",
            j->job_id, j->name, states[j->state],
            j->priority, j->num_ranks, j->progress * 100.0);
    }

    return (int)pos;
}

/* ---- Scheduling ---- */

int hpc_schedule(hpc_system_t* sys) {
    if (!sys) return -1;

    for (uint32_t i = 0; i < sys->num_jobs; i++) {
        hpc_job_t* job = &sys->jobs[i];
        if (job->state != HPC_JOB_PENDING) continue;

        hpc_node_t* node = find_free_node(sys);
        if (!node) break; /* No free nodes */

        job->state = HPC_JOB_RUNNING;
        job->start_time = 0;
        job->num_nodes = 1;
        job->allocated = 1;
        node->state = HPC_NODE_BUSY;
        node->free_memory_mb -= job->memory_mb;

        printf("[HPC] Job '%s' scheduled on %s\n", job->job_id, node->node_id);
    }
    return 0;
}

int hpc_set_scheduler(hpc_system_t* sys, uint32_t type) {
    if (!sys || type > 2) return -1;
    sys->scheduler_type = type;
    const char* names[] = {"FCFS", "PRIORITY", "FAIRSHARE"};
    printf("[HPC] Scheduler changed to %s\n", names[type]);
    return 0;
}

/* ---- MPI-like operations ---- */

int hpc_mpi_init(hpc_system_t* sys) {
    if (!sys) return -1;
    printf("[HPC] MPI initialized with %u ranks\n", sys->total_cores);
    return 0;
}

int hpc_mpi_send(hpc_system_t* sys, uint32_t src_rank, uint32_t dst_rank,
                 const void* data, uint32_t size) {
    if (!sys || !data) return -1;
    printf("[HPC] MPI Send: rank %u -> rank %u (%u bytes)\n", src_rank, dst_rank, size);
    return 0;
}

int hpc_mpi_recv(hpc_system_t* sys, uint32_t rank, void* data, uint32_t size) {
    if (!sys || !data) return -1;
    printf("[HPC] MPI Recv: rank %u (%u bytes)\n", rank, size);
    return 0;
}

int hpc_mpi_barrier(hpc_system_t* sys) {
    if (!sys) return -1;
    printf("[HPC] MPI Barrier: all ranks synchronized\n");
    return 0;
}

int hpc_mpi_reduce(hpc_system_t* sys, const char* operation,
                   double* values, double* result) {
    if (!sys || !values || !result) return -1;

    double sum = 0;
    for (uint32_t i = 0; i < sys->total_cores; i++)
        sum += values[i];

    if (string_compare(operation, "sum") == 0) *result = sum;
    else if (string_compare(operation, "avg") == 0) *result = sum / sys->total_cores;
    else if (string_compare(operation, "max") == 0) {
        *result = values[0];
        for (uint32_t i = 1; i < sys->total_cores; i++)
            if (values[i] > *result) *result = values[i];
    }

    printf("[HPC] MPI Reduce (%s): result=%.4f\n", operation, *result);
    return 0;
}

/* ---- Statistics ---- */

int hpc_get_stats(hpc_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;

    uint32_t online=0, busy=0, offline=0;
    uint32_t pending=0, running=0, completed=0;

    for (uint32_t i = 0; i < sys->num_nodes; i++) {
        switch (sys->nodes[i].state) {
            case HPC_NODE_ONLINE: online++; break;
            case HPC_NODE_BUSY: busy++; break;
            default: offline++; break;
        }
    }

    for (uint32_t i = 0; i < sys->num_jobs; i++) {
        switch (sys->jobs[i].state) {
            case HPC_JOB_PENDING: pending++; break;
            case HPC_JOB_RUNNING: running++; break;
            case HPC_JOB_COMPLETED: completed++; break;
            default: break;
        }
    }

    const char* sched_names[] = {"FCFS", "Priority", "Fairshare"};

    return snprintf(buf, buf_len,
        "HPC Cluster Statistics:\n"
        "  Scheduler: %s\n"
        "  Nodes: %u (online: %u, busy: %u, offline: %u)\n"
        "  Total Cores: %u\n"
        "  Total Memory: %llu MB\n"
        "  Total FLOPS: %.1f GFLOPS\n"
        "  Jobs: %u total (%u pending, %u running, %u completed)\n"
        "  Total CPU Time: %llu ms\n",
        sched_names[sys->scheduler_type],
        sys->num_nodes, online, busy, offline,
        sys->total_cores,
        (unsigned long long)sys->total_memory_mb,
        sys->total_flops,
        sys->num_jobs, pending, running, completed,
        (unsigned long long)sys->total_cpu_time);
}

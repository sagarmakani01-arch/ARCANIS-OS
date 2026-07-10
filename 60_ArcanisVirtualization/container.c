/**
 * container.c — Container Runtime Implementation
 *
 * Lightweight container runtime with namespaces, cgroups, and image support.
 */
#include <arcanis/container.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <stdio.h>

/* ---- Initialization ---- */

void container_init(container_runtime_t* runtime) {
    if (!runtime) return;
    memset(runtime, 0, sizeof(container_runtime_t));
    runtime->next_id = 1;

    /* Create default images */
    container_pull_image(runtime, "arcanis-base", "latest");
    container_pull_image(runtime, "arcanis-kernel", "1.7.0");
    container_pull_image(runtime, "arcanis-shell", "1.0.0");
}

/* ---- Container management ---- */

static container_t* find_container(container_runtime_t* runtime, uint32_t id) {
    for (uint32_t i = 0; i < runtime->num_containers; i++) {
        if (runtime->containers[i].id == id)
            return &runtime->containers[i];
    }
    return NULL;
}

int container_create(container_runtime_t* runtime, const char* name,
                     const char* image, const char* command) {
    if (!runtime || !name) return -1;
    if (runtime->num_containers >= CONT_MAX_CONTAINERS) return -1;

    container_t* cont = &runtime->containers[runtime->num_containers];
    memset(cont, 0, sizeof(container_t));

    cont->id = runtime->next_id++;
    string_copy(cont->name, name, CONT_MAX_NAME);
    cont->state = CONT_STATE_CREATED;
    string_copy(cont->image, image ? image : "arcanis-base", CONT_MAX_NAME);
    string_copy(cont->command, command ? command : "/bin/sh", CONT_MAX_CMD);
    string_copy(cont->entrypoint, "/bin/sh", CONT_MAX_CMD);
    string_copy(cont->workdir, "/workspace", CONT_MAX_PATH);
    snprintf(cont->rootfs, CONT_MAX_PATH, "/var/lib/containers/%u/rootfs", cont->id);

    /* Enable default namespaces */
    cont->namespaces[NS_PID].type = NS_PID;
    cont->namespaces[NS_PID].enabled = 1;
    cont->namespaces[NS_MOUNT].type = NS_MOUNT;
    cont->namespaces[NS_MOUNT].enabled = 1;
    cont->namespaces[NS_NET].type = NS_NET;
    cont->namespaces[NS_NET].enabled = 1;
    cont->namespaces[NS_UTS].type = NS_UTS;
    cont->namespaces[NS_UTS].enabled = 1;

    /* Default cgroup limits */
    cont->cgroup.cpu_quota = 100000;
    cont->cgroup.cpu_period = 100000;
    cont->cgroup.memory_limit = 256 * 1024 * 1024; /* 256MB */
    cont->cgroup.pids_limit = 1024;

    runtime->num_containers++;
    return (int)cont->id;
}

int container_start(container_runtime_t* runtime, uint32_t id) {
    if (!runtime) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;
    if (cont->state != CONT_STATE_CREATED && cont->state != CONT_STATE_STOPPED)
        return -1;

    cont->state = CONT_STATE_RUNNING;
    cont->started_time = 0; /* Would be real timestamp */
    cont->pid = 1000 + cont->id; /* Simulated PID */

    return 0;
}

int container_stop(container_runtime_t* runtime, uint32_t id) {
    if (!runtime) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;
    if (cont->state != CONT_STATE_RUNNING && cont->state != CONT_STATE_PAUSED)
        return -1;

    cont->state = CONT_STATE_STOPPED;
    return 0;
}

int container_pause(container_runtime_t* runtime, uint32_t id) {
    if (!runtime) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;
    if (cont->state != CONT_STATE_RUNNING) return -1;

    cont->state = CONT_STATE_PAUSED;
    return 0;
}

int container_resume(container_runtime_t* runtime, uint32_t id) {
    if (!runtime) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;
    if (cont->state != CONT_STATE_PAUSED) return -1;

    cont->state = CONT_STATE_RUNNING;
    return 0;
}

int container_destroy(container_runtime_t* runtime, uint32_t id) {
    if (!runtime) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;

    if (cont->state == CONT_STATE_RUNNING || cont->state == CONT_STATE_PAUSED)
        container_stop(runtime, id);

    /* Remove from array */
    for (uint32_t i = 0; i < runtime->num_containers; i++) {
        if (runtime->containers[i].id == id) {
            for (uint32_t j = i; j < runtime->num_containers - 1; j++)
                runtime->containers[j] = runtime->containers[j + 1];
            runtime->num_containers--;
            break;
        }
    }

    return 0;
}

int container_exec(container_runtime_t* runtime, uint32_t id, const char* command) {
    if (!runtime || !command) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;
    if (cont->state != CONT_STATE_RUNNING) return -1;

    printf("[CONTAINER:%s] Executing: %s\n", cont->name, command);
    return 0;
}

int container_list(container_runtime_t* runtime, char* buf, uint32_t buf_len) {
    if (!runtime || !buf) return 0;

    const char* state_names[] = {"CREATED", "RUNNING", "PAUSED", "STOPPED", "DEAD"};
    uint32_t pos = 0;

    pos += snprintf(buf + pos, buf_len - pos,
        "CONTAINER ID  IMAGE                COMMAND        STATUS\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "--------------------------------------------------------\n");

    for (uint32_t i = 0; i < runtime->num_containers && pos < buf_len - 200; i++) {
        container_t* c = &runtime->containers[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-13u %-20s %-14s %s\n",
            c->id, c->image, c->command, state_names[c->state]);
    }

    return (int)pos;
}

int container_inspect(container_runtime_t* runtime, uint32_t id, char* buf, uint32_t buf_len) {
    if (!runtime || !buf) return 0;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;

    return snprintf(buf, buf_len,
        "{\n"
        "  \"id\": %u,\n"
        "  \"name\": \"%s\",\n"
        "  \"image\": \"%s\",\n"
        "  \"state\": \"%s\",\n"
        "  \"pid\": %u,\n"
        "  \"rootfs\": \"%s\",\n"
        "  \"workdir\": \"%s\",\n"
        "  \"command\": \"%s\",\n"
        "  \"memory_limit\": %llu,\n"
        "  \"cpu_quota\": %llu\n"
        "}",
        cont->id, cont->name, cont->image,
        cont->state == 0 ? "created" : cont->state == 1 ? "running" : "stopped",
        cont->pid, cont->rootfs, cont->workdir, cont->command,
        (unsigned long long)cont->cgroup.memory_limit,
        (unsigned long long)cont->cgroup.cpu_quota);
}

/* ---- Container operations ---- */

int container_logs(container_runtime_t* runtime, uint32_t id, uint32_t lines) {
    if (!runtime) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;

    printf("\033[90m[LOG:%s]\033[0m Container started\n", cont->name);
    printf("\033[90m[LOG:%s]\033[0m PID: %u\n", cont->name, cont->pid);
    return 0;
}

int container_cp(container_runtime_t* runtime, uint32_t id, const char* src, const char* dst) {
    if (!runtime || !src || !dst) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;

    printf("[CONTAINER:%s] Copied %s to %s\n", cont->name, src, dst);
    return 0;
}

int container_stats(container_runtime_t* runtime, uint32_t id, char* buf, uint32_t buf_len) {
    if (!runtime || !buf) return 0;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;

    return snprintf(buf, buf_len,
        "CONTAINER %u (%s)\n"
        "CPU:     %u%%\n"
        "Memory:  %llu / %llu bytes\n"
        "PIDs:    %u / %u\n"
        "Net I/O: %llu bytes RX / %llu bytes TX\n"
        "Block I/O: %llu bytes read / %llu bytes write\n",
        cont->id, cont->name,
        cont->cpu_percent,
        (unsigned long long)cont->memory_used,
        (unsigned long long)cont->cgroup.memory_limit,
        cont->cgroup.pids_current, cont->cgroup.pids_limit,
        (unsigned long long)cont->cgroup.blkio_read,
        (unsigned long long)cont->cgroup.blkio_write,
        (unsigned long long)cont->cgroup.blkio_read,
        (unsigned long long)cont->cgroup.blkio_write);
}

/* ---- Image management ---- */

int container_pull_image(container_runtime_t* runtime, const char* name, const char* tag) {
    if (!runtime || !name) return -1;
    if (runtime->num_images >= CONT_MAX_IMAGES) return -1;

    /* Check if exists */
    for (uint32_t i = 0; i < runtime->num_images; i++) {
        if (string_compare(runtime->images[i].name, name) == 0 &&
            string_compare(runtime->images[i].tag, tag ? tag : "latest") == 0)
            return 0; /* Already exists */
    }

    container_image_t* img = &runtime->images[runtime->num_images++];
    memset(img, 0, sizeof(container_image_t));
    string_copy(img->name, name, CONT_MAX_NAME);
    string_copy(img->tag, tag ? tag : "latest", 32);
    img->present = 1;

    /* Create simulated layers */
    img->num_layers = 3;
    for (uint32_t i = 0; i < img->num_layers; i++) {
        snprintf(img->layers[i].name, CONT_MAX_NAME, "layer-%u", i);
        img->layers[i].size = 1024 * (i + 1);
        img->layers[i].present = 1;
        img->total_size += img->layers[i].size;
    }

    return 0;
}

int container_list_images(container_runtime_t* runtime, char* buf, uint32_t buf_len) {
    if (!runtime || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos,
        "REPOSITORY         TAG        SIZE       LAYERS\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "--------------------------------------------------\n");

    for (uint32_t i = 0; i < runtime->num_images && pos < buf_len - 150; i++) {
        container_image_t* img = &runtime->images[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-18s %-10s %8llu    %u\n",
            img->name, img->tag,
            (unsigned long long)(img->total_size / 1024),
            img->num_layers);
    }

    return (int)pos;
}

int container_remove_image(container_runtime_t* runtime, const char* name) {
    if (!runtime || !name) return -1;

    for (uint32_t i = 0; i < runtime->num_images; i++) {
        if (string_compare(runtime->images[i].name, name) == 0) {
            for (uint32_t j = i; j < runtime->num_images - 1; j++)
                runtime->images[j] = runtime->images[j + 1];
            runtime->num_images--;
            return 0;
        }
    }
    return -1;
}

int container_image_info(container_runtime_t* runtime, const char* name, char* buf, uint32_t buf_len) {
    if (!runtime || !name || !buf) return 0;

    for (uint32_t i = 0; i < runtime->num_images; i++) {
        if (string_compare(runtime->images[i].name, name) == 0) {
            container_image_t* img = &runtime->images[i];
            return snprintf(buf, buf_len,
                "Image: %s:%s\n"
                "Layers: %u\n"
                "Size: %llu bytes\n",
                img->name, img->tag,
                img->num_layers,
                (unsigned long long)img->total_size);
        }
    }
    return -1;
}

/* ---- Namespace management ---- */

int container_enable_namespace(container_runtime_t* runtime, uint32_t id, namespace_type_t ns) {
    if (!runtime) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;
    if (ns >= 6) return -1;

    cont->namespaces[ns].enabled = 1;
    return 0;
}

int container_disable_namespace(container_runtime_t* runtime, uint32_t id, namespace_type_t ns) {
    if (!runtime) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;
    if (ns >= 6) return -1;

    cont->namespaces[ns].enabled = 0;
    return 0;
}

/* ---- Cgroup management ---- */

int container_set_cpu_limit(container_runtime_t* runtime, uint32_t id, uint64_t quota, uint64_t period) {
    if (!runtime) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;

    cont->cgroup.cpu_quota = quota;
    cont->cgroup.cpu_period = period;
    return 0;
}

int container_set_memory_limit(container_runtime_t* runtime, uint32_t id, uint64_t limit) {
    if (!runtime) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;

    cont->cgroup.memory_limit = limit;
    return 0;
}

int container_set_pids_limit(container_runtime_t* runtime, uint32_t id, uint32_t limit) {
    if (!runtime) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;

    cont->cgroup.pids_limit = limit;
    return 0;
}

int container_get_stats(container_runtime_t* runtime, uint32_t id, container_cgroup_t* stats) {
    if (!runtime || !stats) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;

    memcpy(stats, &cont->cgroup, sizeof(container_cgroup_t));
    return 0;
}

/* ---- Network ---- */

int container_set_ip(container_runtime_t* runtime, uint32_t id, const char* ip) {
    if (!runtime || !ip) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;

    string_copy(cont->ip_address, ip, 16);
    return 0;
}

int container_add_port(container_runtime_t* runtime, uint32_t id, uint16_t port) {
    if (!runtime) return -1;

    container_t* cont = find_container(runtime, id);
    if (!cont) return -1;
    if (cont->num_ports >= 32) return -1;

    cont->ports[cont->num_ports++] = port;
    return 0;
}

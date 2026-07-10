/**
 * ipc.c — Inter-Process Communication Implementation
 *
 * POSIX-like IPC: message queues, shared memory, semaphores.
 */
#include <arcanis/ipc.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

void ipc_init(ipc_state_t* state) {
    if (!state) return;
    memset(state, 0, sizeof(ipc_state_t));
    state->next_qid = 1;
    state->next_shmid = 1;
    state->next_semid = 1;
}

/* ---- Message Queues ---- */

ipc_queue_t* ipc_find_queue(ipc_state_t* state, uint32_t key) {
    if (!state) return NULL;
    for (uint32_t i = 0; i < IPC_MAX_QUEUES; i++)
        if (state->queues[i].active && state->queues[i].key == key)
            return &state->queues[i];
    return NULL;
}

int ipc_msgget(ipc_state_t* state, uint32_t key, int flags) {
    if (!state) return -1;

    /* Find existing queue */
    ipc_queue_t* existing = ipc_find_queue(state, key);
    if (existing) {
        if (flags & IPC_EXCL) return -1; /* Already exists */
        return (int)existing->qid;
    }

    /* Create new queue */
    if (!(flags & IPC_CREAT)) return -1;

    for (uint32_t i = 0; i < IPC_MAX_QUEUES; i++) {
        if (!state->queues[i].active) {
            ipc_queue_t* q = &state->queues[i];
            memset(q, 0, sizeof(ipc_queue_t));
            q->key = key;
            q->qid = state->next_qid++;
            q->head = 0;
            q->tail = 0;
            q->count = 0;
            q->max_msgs = IPC_MAX_MSGS;
            q->max_size = IPC_MAX_MSG_SIZE;
            q->flags = flags;
            q->active = 1;
            state->num_queues++;
            return (int)q->qid;
        }
    }
    return -1;
}

int ipc_msgsnd(ipc_state_t* state, uint32_t qid, const ipc_message_t* msg, int flags) {
    if (!state || !msg) return -1;

    ipc_queue_t* q = NULL;
    for (uint32_t i = 0; i < IPC_MAX_QUEUES; i++)
        if (state->queues[i].active && state->queues[i].qid == qid)
            q = &state->queues[i];
    if (!q) return -1;

    if (q->count >= q->max_msgs) {
        if (flags & IPC_NOWAIT) return -1;
        /* Block until space available */
        return -1;
    }

    /* Copy message */
    memcpy(&q->messages[q->tail], msg, sizeof(ipc_message_t));
    q->tail = (q->tail + 1) % IPC_MAX_MSGS;
    q->count++;

    return 0;
}

int ipc_msgrcv(ipc_state_t* state, uint32_t qid, ipc_message_t* msg, uint32_t type, int flags) {
    if (!state || !msg) return -1;

    ipc_queue_t* q = NULL;
    for (uint32_t i = 0; i < IPC_MAX_QUEUES; i++)
        if (state->queues[i].active && state->queues[i].qid == qid)
            q = &state->queues[i];
    if (!q) return -1;

    if (q->count == 0) {
        if (flags & IPC_NOWAIT) return -1;
        return -1;
    }

    /* Find message of requested type */
    uint32_t start = q->head;
    uint32_t idx = start;
    int found = 0;

    for (uint32_t i = 0; i < q->count; i++) {
        uint32_t pos = (start + i) % IPC_MAX_MSGS;
        if (type == 0 || q->messages[pos].mtype == type) {
            memcpy(msg, &q->messages[pos], sizeof(ipc_message_t));
            /* Shift remaining messages */
            for (uint32_t j = i; j < q->count - 1; j++) {
                uint32_t next = (pos + 1) % IPC_MAX_MSGS;
                q->messages[pos] = q->messages[next];
                pos = next;
            }
            q->count--;
            found = 1;
            break;
        }
    }

    return found ? 0 : -1;
}

int ipc_msgctl(ipc_state_t* state, uint32_t qid, int cmd) {
    if (!state) return -1;

    for (uint32_t i = 0; i < IPC_MAX_QUEUES; i++) {
        if (state->queues[i].active && state->queues[i].qid == qid) {
            if (cmd == IPC_RMID) {
                state->queues[i].active = 0;
                state->num_queues--;
                return 0;
            }
        }
    }
    return -1;
}

/* ---- Shared Memory ---- */

ipc_shm_t* ipc_find_shm(ipc_state_t* state, uint32_t key) {
    if (!state) return NULL;
    for (uint32_t i = 0; i < IPC_MAX_SHM; i++)
        if (state->shm[i].active && state->shm[i].key == key)
            return &state->shm[i];
    return NULL;
}

int ipc_shmget(ipc_state_t* state, uint32_t key, uint32_t size, int flags) {
    if (!state) return -1;

    ipc_shm_t* existing = ipc_find_shm(state, key);
    if (existing) {
        if (flags & IPC_EXCL) return -1;
        return (int)existing->shmid;
    }

    if (!(flags & IPC_CREAT)) return -1;

    for (uint32_t i = 0; i < IPC_MAX_SHM; i++) {
        if (!state->shm[i].active) {
            ipc_shm_t* s = &state->shm[i];
            memset(s, 0, sizeof(ipc_shm_t));
            s->key = key;
            s->shmid = state->next_shmid++;
            s->size = size;
            s->data = (uint8_t*)kmalloc(size);
            if (!s->data) return -1;
            memset(s->data, 0, size);
            s->attach_count = 0;
            s->active = 1;
            state->num_shm++;
            return (int)s->shmid;
        }
    }
    return -1;
}

void* ipc_shmat(ipc_state_t* state, uint32_t shmid, int flags) {
    if (!state) return NULL;

    for (uint32_t i = 0; i < IPC_MAX_SHM; i++) {
        if (state->shm[i].active && state->shm[i].shmid == shmid) {
            state->shm[i].attach_count++;
            return state->shm[i].data;
        }
    }
    return NULL;
}

int ipc_shmdt(ipc_state_t* state, uint32_t shmid) {
    if (!state) return -1;

    for (uint32_t i = 0; i < IPC_MAX_SHM; i++) {
        if (state->shm[i].active && state->shm[i].shmid == shmid) {
            if (state->shm[i].attach_count > 0)
                state->shm[i].attach_count--;
            return 0;
        }
    }
    return -1;
}

int ipc_shmctl(ipc_state_t* state, uint32_t shmid, int cmd) {
    if (!state) return -1;

    for (uint32_t i = 0; i < IPC_MAX_SHM; i++) {
        if (state->shm[i].active && state->shm[i].shmid == shmid) {
            if (cmd == IPC_RMID) {
                kfree(state->shm[i].data);
                state->shm[i].active = 0;
                state->num_shm--;
                return 0;
            }
        }
    }
    return -1;
}

/* ---- Semaphores ---- */

ipc_sem_t* ipc_find_sem(ipc_state_t* state, uint32_t key) {
    if (!state) return NULL;
    for (uint32_t i = 0; i < IPC_MAX_SEM; i++)
        if (state->sems[i].active && state->sems[i].key == key)
            return &state->sems[i];
    return NULL;
}

int ipc_semget(ipc_state_t* state, uint32_t key, int nsems, int flags) {
    if (!state) return -1;

    ipc_sem_t* existing = ipc_find_sem(state, key);
    if (existing) return (int)existing->semid;

    if (!(flags & IPC_CREAT)) return -1;

    for (uint32_t i = 0; i < IPC_MAX_SEM; i++) {
        if (!state->sems[i].active) {
            ipc_sem_t* s = &state->sems[i];
            memset(s, 0, sizeof(ipc_sem_t));
            s->key = key;
            s->semid = state->next_semid++;
            s->value = 1;
            s->max_value = 1;
            s->active = 1;
            state->num_sems++;
            return (int)s->semid;
        }
    }
    return -1;
}

int ipc_sem_wait(ipc_state_t* state, uint32_t semid) {
    if (!state) return -1;

    for (uint32_t i = 0; i < IPC_MAX_SEM; i++) {
        if (state->sems[i].active && state->sems[i].semid == semid) {
            ipc_sem_t* s = &state->sems[i];
            if (s->value > 0) {
                s->value--;
                return 0;
            }
            /* Block */
            return -1;
        }
    }
    return -1;
}

int ipc_sem_signal(ipc_state_t* state, uint32_t semid) {
    if (!state) return -1;

    for (uint32_t i = 0; i < IPC_MAX_SEM; i++) {
        if (state->sems[i].active && state->sems[i].semid == semid) {
            ipc_sem_t* s = &state->sems[i];
            if (s->value < s->max_value) {
                s->value++;
                return 0;
            }
            return -1;
        }
    }
    return -1;
}

int ipc_semop(ipc_state_t* state, uint32_t semid, int op) {
    if (!state) return -1;

    for (uint32_t i = 0; i < IPC_MAX_SEM; i++) {
        if (state->sems[i].active && state->sems[i].semid == semid) {
            ipc_sem_t* s = &state->sems[i];
            if (op > 0) {
                /* Signal */
                s->value += op;
                if (s->value > s->max_value) s->value = s->max_value;
            } else if (op < 0) {
                /* Wait */
                s->value += op;
                if (s->value < 0) {
                    s->value = 0;
                    return -1;
                }
            } else {
                /* Get value */
                return (int)s->value;
            }
            return 0;
        }
    }
    return -1;
}

int ipc_semctl(ipc_state_t* state, uint32_t semid, int cmd) {
    if (!state) return -1;

    for (uint32_t i = 0; i < IPC_MAX_SEM; i++) {
        if (state->sems[i].active && state->sems[i].semid == semid) {
            if (cmd == IPC_RMID) {
                state->sems[i].active = 0;
                state->num_sems--;
                return 0;
            }
        }
    }
    return -1;
}

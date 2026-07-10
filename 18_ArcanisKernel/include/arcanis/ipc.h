/**
 * ipc.h — Inter-Process Communication
 *
 * Message queues, shared memory, and semaphores for process communication.
 */
#ifndef ARCANIS_IPC_H
#define ARCANIS_IPC_H

#include <arcanis/types.h>

#define IPC_MAX_QUEUES     32
#define IPC_MAX_MSG_SIZE   256
#define IPC_MAX_MSGS       64
#define IPC_MAX_SHM        16
#define IPC_MAX_SEM        32
#define IPC_KEY_NONE       0
#define IPC_MAX_WAITERS    8

/* Message queue flags */
#define IPC_CREAT  0x200
#define IPC_EXCL   0x400
#define IPC_NOWAIT 0x800
#define IPC_RMID   0x1000

/* Message types */
#define MSG_TYPE_NORMAL  0
#define MSG_TYPE_URGENT  1
#define MSG_TYPE_CONTROL 2

typedef struct {
    uint32_t mtype;          /* Message type */
    uint32_t msize;          /* Message size */
    uint32_t sender_pid;     /* Sender PID */
    uint32_t receiver_pid;   /* Receiver PID (0 = any) */
    uint32_t timestamp;      /* Send time */
    uint32_t priority;       /* 0=low, 1=normal, 2=high */
    char     data[IPC_MAX_MSG_SIZE];
} ipc_message_t;

typedef struct {
    uint32_t       key;         /* Queue key (name) */
    uint32_t       qid;         /* Queue ID */
    ipc_message_t  messages[IPC_MAX_MSGS];
    uint32_t       head;        /* Next read position */
    uint32_t       tail;        /* Next write position */
    uint32_t       count;       /* Current message count */
    uint32_t       max_msgs;    /* Maximum messages */
    uint32_t       max_size;    /* Maximum message size */
    uint32_t       flags;       /* Queue flags */
    uint32_t       creator_pid; /* Creator PID */
    int            active;      /* Is queue in use */
} ipc_queue_t;

typedef struct {
    uint32_t key;          /* Shared memory key */
    uint32_t shmid;        /* Shared memory ID */
    uint32_t size;         /* Size in bytes */
    uint32_t attach_count; /* Number of attached processes */
    uint32_t creator_pid;  /* Creator PID */
    uint8_t* data;         /* Data pointer */
    int      active;       /* Is segment in use */
} ipc_shm_t;

typedef struct {
    uint32_t key;          /* Semaphore key */
    uint32_t semid;        /* Semaphore ID */
    int32_t  value;        /* Semaphore value */
    uint32_t max_value;    /* Maximum value */
    uint32_t owner_pid;    /* Owner PID */
    uint32_t waiters[IPC_MAX_WAITERS];
    uint32_t num_waiters;
    int      active;       /* Is semaphore in use */
} ipc_sem_t;

typedef struct {
    ipc_queue_t queues[IPC_MAX_QUEUES];
    uint32_t    num_queues;
    ipc_shm_t   shm[IPC_MAX_SHM];
    uint32_t    num_shm;
    ipc_sem_t   sems[IPC_MAX_SEM];
    uint32_t    num_sems;
    uint32_t    next_qid;
    uint32_t    next_shmid;
    uint32_t    next_semid;
} ipc_state_t;

/* Initialize IPC subsystem */
void ipc_init(ipc_state_t* state);

/* Message queues */
int     ipc_msgget(ipc_state_t* state, uint32_t key, int flags);
int     ipc_msgsnd(ipc_state_t* state, uint32_t qid, const ipc_message_t* msg, int flags);
int     ipc_msgrcv(ipc_state_t* state, uint32_t qid, ipc_message_t* msg, uint32_t type, int flags);
int     ipc_msgctl(ipc_state_t* state, uint32_t qid, int cmd);

/* Shared memory */
int     ipc_shmget(ipc_state_t* state, uint32_t key, uint32_t size, int flags);
void*   ipc_shmat(ipc_state_t* state, uint32_t shmid, int flags);
int     ipc_shmdt(ipc_state_t* state, uint32_t shmid);
int     ipc_shmctl(ipc_state_t* state, uint32_t shmid, int cmd);

/* Semaphores */
int     ipc_semget(ipc_state_t* state, uint32_t key, int nsems, int flags);
int     ipc_semop(ipc_state_t* state, uint32_t semid, int op);
int     ipc_semctl(ipc_state_t* state, uint32_t semid, int cmd);
int     ipc_sem_wait(ipc_state_t* state, uint32_t semid);
int     ipc_sem_signal(ipc_state_t* state, uint32_t semid);

/* Find by key */
ipc_queue_t* ipc_find_queue(ipc_state_t* state, uint32_t key);
ipc_shm_t*   ipc_find_shm(ipc_state_t* state, uint32_t key);
ipc_sem_t*   ipc_find_sem(ipc_state_t* state, uint32_t key);

#endif

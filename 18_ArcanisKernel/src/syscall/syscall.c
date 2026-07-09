#include <arcanis/syscall.h>
#include <arcanis/idt.h>
#include <arcanis/process.h>
#include <arcanis/vga.h>
#include <arcanis/keyboard.h>
#include <arcanis/timer.h>
#include <arcanis/string.h>
#include <arcanis/types.h>
#include <arcanis/defs.h>
#include <arcanis/vfs.h>
#include <arcanis/scheduler.h>
#include <arcanis/elf.h>
#include <arcanis/fd.h>

static syscall_handler_t syscall_handlers[SYSCALL_COUNT] = { NULL };

extern void syscall_stub(void);

/* ---- Process ---- */

static int32_t sys_exit(registers_t* regs) {
    process_t* proc = process_get_current();
    if (proc) {
        proc->exit_code = regs->ebx;
        process_destroy(proc);
        scheduler_schedule();
    }
    return 0;
}

static int32_t sys_fork(registers_t* regs) {
    process_t* parent = process_get_current();
    if (!parent) return -1;
    process_t* child = process_create("child", (void*)regs->eip, parent->priority);
    if (!child) return -1;
    child->uid = parent->uid;
    child->parent_pid = parent->pid;
    /* Copy file descriptors */
    for (int i = 0; i < FD_MAX; i++) {
        child->fd_table.entries[i] = parent->fd_table.entries[i];
        if (child->fd_table.entries[i].in_use)
            child->fd_table.count++;
    }
    return child->pid;
}

static int32_t sys_exec(registers_t* regs) {
    const char* path = (const char*)regs->ebx;
    if (!path) return -1;
    vfs_node_t* node = vfs_find(path);
    if (!node) return -1;
    if (node->data && node->length > 0) {
        int32_t entry = elf_load(node->data, node->length);
        if (entry > 0) {
            regs->eip = (uint32_t)entry;
            return 0;
        }
    }
    return -1;
}

static int32_t sys_getpid(registers_t* regs) {
    process_t* proc = process_get_current();
    return proc ? proc->pid : -1;
}

static int32_t sys_wait(registers_t* regs) {
    pid_t pid = (pid_t)regs->ebx;
    int* status = (int*)regs->ecx;
    return process_wait(pid, status);
}

static int32_t sys_kill(registers_t* regs) {
    pid_t pid = (pid_t)regs->ebx;
    process_t* proc = process_get_by_pid(pid);
    if (!proc) return -1;
    process_destroy(proc);
    return 0;
}

static int32_t sys_yield(registers_t* regs) {
    scheduler_schedule();
    return 0;
}

/* ---- I/O ---- */

static int32_t sys_putchar(registers_t* regs) {
    char c = (char)regs->ebx;
    vga_put_char(c);
    return 0;
}

static int32_t sys_getchar(registers_t* regs) {
    while (!keyboard_has_data()) {
        asm volatile("hlt");
    }
    uint8_t sc = keyboard_get_scancode();
    return (int32_t)scancode_to_ascii(sc);
}

static int32_t sys_cls(registers_t* regs) {
    vga_clear();
    return 0;
}

/* ---- Filesystem ---- */

static int32_t sys_open(registers_t* regs) {
    const char* path = (const char*)regs->ebx;
    uint32_t flags = regs->ecx;
    vfs_node_t* node = vfs_find(path);
    if (!node) return -1;
    if (node->ops && node->ops->open) node->ops->open(node);
    return (int32_t)(uintptr_t)node;
}

static int32_t sys_close(registers_t* regs) {
    vfs_node_t* node = (vfs_node_t*)(uintptr_t)regs->ebx;
    if (node && node->ops && node->ops->close) node->ops->close(node);
    return 0;
}

static int32_t sys_read(registers_t* regs) {
    vfs_node_t* node = (vfs_node_t*)(uintptr_t)regs->ebx;
    uint32_t offset = regs->ecx;
    uint32_t size = regs->edx;
    uint8_t* buf = (uint8_t*)regs->esi;
    if (!node || !buf) return -1;
    if (node->ops && node->ops->read)
        return node->ops->read(node, offset, size, buf);
    /* direct data read for simple files */
    if (node->data && node->type == VFS_FILE) {
        uint32_t to_read = size;
        if (offset + to_read > node->length) to_read = node->length - offset;
        for (uint32_t i = 0; i < to_read; i++)
            buf[i] = node->data[offset + i];
        return (ssize_t)to_read;
    }
    return -1;
}

static int32_t sys_write(registers_t* regs) {
    vfs_node_t* node = (vfs_node_t*)(uintptr_t)regs->ebx;
    uint32_t offset = regs->ecx;
    uint32_t size = regs->edx;
    const uint8_t* buf = (const uint8_t*)regs->esi;
    if (!node || !buf) return -1;
    if (node->ops && node->ops->write)
        return node->ops->write(node, offset, size, (uint8_t*)buf);
    /* direct data write for simple files */
    if (node->type == VFS_FILE) {
        if (!node->data) {
            node->data = (uint8_t*)kmalloc(offset + size + 256);
            if (!node->data) return -1;
        }
        for (uint32_t i = 0; i < size; i++)
            node->data[offset + i] = buf[i];
        if (offset + size > node->length)
            node->length = offset + size;
        return (ssize_t)size;
    }
    return -1;
}

static int32_t sys_mkdir(registers_t* regs) {
    const char* path = (const char*)regs->ebx;
    vfs_node_t* node = vfs_find(path);
    if (node) return -1;
    /* create directory node */
    vfs_node_t* parent = NULL;
    char name[VFS_NAME_MAX];
    /* extract parent and name from path */
    int len = string_length(path);
    int last_slash = -1;
    for (int i = 0; i < len; i++) {
        if (path[i] == '/') last_slash = i;
    }
    if (last_slash >= 0) {
        string_copy_n(name, path + last_slash + 1, VFS_NAME_MAX);
        char parent_path[VFS_NAME_MAX];
        string_copy_n(parent_path, path, last_slash);
        parent_path[last_slash] = '\0';
        parent = vfs_find(parent_path);
    } else {
        string_copy_n(name, path, VFS_NAME_MAX);
        parent = vfs_find("/");
    }
    if (!parent) return -1;
    vfs_node_t* dir = vfs_create_node(name, VFS_DIRECTORY);
    if (!dir) return -1;
    dir->next = parent->children;
    parent->children = dir;
    return 0;
}

static int32_t sys_rmdir(registers_t* regs) {
    const char* path = (const char*)regs->ebx;
    vfs_node_t* node = vfs_find(path);
    if (!node) return -1;
    /* TODO: unlink from parent, free */
    return 0;
}

static int32_t sys_unlink(registers_t* regs) {
    const char* path = (const char*)regs->ebx;
    vfs_node_t* node = vfs_find(path);
    if (!node) return -1;
    /* TODO: unlink from parent, free */
    return 0;
}

static int32_t sys_chdir(registers_t* regs) {
    const char* path = (const char*)regs->ebx;
    process_t* proc = process_get_current();
    if (!proc) return -1;
    vfs_node_t* node = vfs_find(path);
    if (!node || node->type != VFS_DIRECTORY) return -1;
    /* TODO: store cwd in process */
    return 0;
}

static int32_t sys_getcwd(registers_t* regs) {
    char* buf = (char*)regs->ebx;
    uint32_t size = regs->ecx;
    if (!buf) return -1;
    string_copy_n(buf, "/", size);
    return 0;
}

static int32_t sys_stat(registers_t* regs) {
    const char* path = (const char*)regs->ebx;
    stat_t* st = (stat_t*)regs->ecx;
    if (!st) return -1;
    vfs_node_t* node = vfs_find(path);
    if (!node) return -1;
    st->size = node->length;
    st->mode = (node->type == VFS_DIRECTORY) ? 0040000 : 0100000;
    st->nlink = 1;
    return 0;
}

/* ---- Pipe / IPC ---- */

static int32_t sys_pipe(registers_t* regs) {
    /* TODO: create pipe pair */
    (void)regs;
    return -1;
}

static int32_t sys_dup(registers_t* regs) {
    /* TODO: duplicate file descriptor */
    (void)regs;
    return -1;
}

/* ---- Time ---- */

static int32_t sys_time(registers_t* regs) {
    return (int32_t)timer_get_ticks();
}

/* ---- System info ---- */

static int32_t sys_uname(registers_t* regs) {
    utsname_t* buf = (utsname_t*)regs->ebx;
    if (!buf) return -1;
    string_copy_n(buf->sysname, "Arcanis", 64);
    string_copy_n(buf->nodename, "arcanis", 64);
    string_copy_n(buf->release, "0.1.0", 64);
    string_copy_n(buf->version, "#1 SMP", 64);
    string_copy_n(buf->machine, "i686", 64);
    return 0;
}

static int32_t sys_info(registers_t* regs) {
    return 0;
}

static int32_t sys_ioctl(registers_t* regs) {
    /* TODO: device control */
    (void)regs;
    return -1;
}

/* ---- Memory ---- */

static int32_t sys_mmap(registers_t* regs) {
    /* TODO: map memory region */
    (void)regs;
    return -1;
}

static int32_t sys_munmap(registers_t* regs) {
    /* TODO: unmap memory region */
    (void)regs;
    return 0;
}

/* ---- Security ---- */

static int32_t sys_getuid(registers_t* regs) {
    process_t* proc = process_get_current();
    return proc ? proc->uid : 0;
}

static int32_t sys_setuid(registers_t* regs) {
    process_t* proc = process_get_current();
    if (proc) proc->uid = (uid_t)regs->ebx;
    return 0;
}

/* ---- Legacy ---- */

static int32_t sys_sleep(registers_t* regs) {
    uint32_t ms = regs->ebx;
    timer_sleep(ms);
    return 0;
}

static int32_t sys_exec_cmd(registers_t* regs) {
    /* legacy: interpret command string */
    (void)regs;
    return -1;
}

/* ---- Init ---- */

void syscall_initialize(void) {
    syscall_handlers[SYS_EXIT]     = sys_exit;
    syscall_handlers[SYS_FORK]     = sys_fork;
    syscall_handlers[SYS_EXEC]     = sys_exec;
    syscall_handlers[SYS_READ]     = sys_read;
    syscall_handlers[SYS_WRITE]    = sys_write;
    syscall_handlers[SYS_OPEN]     = sys_open;
    syscall_handlers[SYS_CLOSE]    = sys_close;
    syscall_handlers[SYS_SLEEP]    = sys_sleep;
    syscall_handlers[SYS_GETPID]   = sys_getpid;
    syscall_handlers[SYS_PUTCHAR]  = sys_putchar;
    syscall_handlers[SYS_GETCHAR]  = sys_getchar;
    syscall_handlers[SYS_CLS]      = sys_cls;
    syscall_handlers[SYS_INFO]     = sys_info;
    syscall_handlers[SYS_EXEC_CMD] = sys_exec_cmd;
    syscall_handlers[SYS_CHDIR]    = sys_chdir;
    syscall_handlers[SYS_GETCWD]   = sys_getcwd;
    syscall_handlers[SYS_STAT]     = sys_stat;
    syscall_handlers[SYS_MKDIR]    = sys_mkdir;
    syscall_handlers[SYS_RMDIR]    = sys_rmdir;
    syscall_handlers[SYS_UNLINK]   = sys_unlink;
    syscall_handlers[SYS_PIPE]     = sys_pipe;
    syscall_handlers[SYS_DUP]      = sys_dup;
    syscall_handlers[SYS_TIME]     = sys_time;
    syscall_handlers[SYS_UNAME]    = sys_uname;
    syscall_handlers[SYS_IOCTL]    = sys_ioctl;
    syscall_handlers[SYS_MMAP]     = sys_mmap;
    syscall_handlers[SYS_MUNMAP]   = sys_munmap;
    syscall_handlers[SYS_WAIT]     = sys_wait;
    syscall_handlers[SYS_KILL]     = sys_kill;
    syscall_handlers[SYS_GETUID]   = sys_getuid;
    syscall_handlers[SYS_SETUID]   = sys_setuid;
    syscall_handlers[SYS_YIELD]    = sys_yield;
}

void syscall_handler(registers_t* regs) {
    uint32_t syscall_num = regs->eax;

    if (syscall_num >= SYSCALL_COUNT || !syscall_handlers[syscall_num]) {
        regs->eax = -1;
        return;
    }

    regs->eax = syscall_handlers[syscall_num](regs);
}

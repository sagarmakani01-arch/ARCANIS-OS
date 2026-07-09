/**
 * init.c — First userspace process (PID 1)
 *
 * Responsibilities:
 *   1. Mount essential filesystems
 *   2. Start system services (logger, device manager)
 *   3. Launch the shell
 *   4. Reap orphaned children
 *   5. Handle shutdown/reboot
 */
#include <arcanis/syscall.h>
#include <arcanis/string.h>

/* Forward declarations for services */
static void init_mount_filesystems(void);
static void init_start_services(void);
static void init_launch_shell(void);
static void init_reap_orphans(void);

static int shell_pid = -1;

void init_main(void) {
    /* Phase 1: System initialization */
    init_mount_filesystems();

    /* Phase 2: Start background services */
    init_start_services();

    /* Phase 3: Launch the shell (blocking) */
    init_launch_shell();

    /* Phase 4: Main loop — reap orphans, handle signals */
    while (1) {
        init_reap_orphans();
        sleep_ms(1000);
    }
}

/**
 * Mount essential filesystems.
 * In a real OS this would set up:
 *   /dev  — device nodes
 *   /proc — process info
 *   /tmp  — temporary storage
 */
static void init_mount_filesystems(void) {
    /* VFS is already mounted by kernel.
     * Create standard directories if they don't exist. */
    mkdir_p("/dev");
    mkdir_p("/proc");
    mkdir_p("/tmp");
    mkdir_p("/home");
    mkdir_p("/etc");
    mkdir_p("/var");
    mkdir_p("/bin");
}

/**
 * Start background system services.
 * Each service runs as a separate process.
 */
static void init_start_services(void) {
    /* Service: logger
     * Captures kernel messages and writes to /var/log/kernel.log
     * For now, just a placeholder. */
    /* pid_t logger = fork(); */
    /* if (logger == 0) { exec("/bin/loggerd"); } */

    /* Service: device manager
     * Monitors for hardware changes, loads drivers */
    /* pid_t devmgr = fork(); */
    /* if (devmgr == 0) { exec("/bin/devmgr"); } */
}

/**
 * Launch the interactive shell.
 * Forks a child process and waits for it to exit.
 * If the shell crashes, restarts it.
 */
static void init_launch_shell(void) {
    while (1) {
        shell_pid = fork();
        if (shell_pid == 0) {
            /* Child: run the shell */
            /* In a real OS, this would exec("/bin/arcanis-shell") */
            /* For now, the shell is loaded by the kernel as a module */
            exit(0);
        }

        /* Parent: wait for shell to exit */
        /* TODO: implement sys_wait */
        sleep_ms(500);

        /* If shell exited, log and restart */
        /* In production, check exit status */
    }
}

/**
 * Reap orphaned child processes.
 * Prevents zombie accumulation.
 */
static void init_reap_orphans(void) {
    /* TODO: implement sys_waitpid(-1, WNOHANG) */
    /* For now, this is a no-op placeholder */
}

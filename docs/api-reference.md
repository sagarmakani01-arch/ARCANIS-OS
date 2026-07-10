# Arcanis OS — API Reference

## System Calls

### Process Management

```c
// Create a new process
int fork(void);

// Execute a program
int exec(const char* path, char* const argv[], char* const envp[]);

// Exit current process
void exit(int status);

// Wait for child process
int wait(int* status);

// Send signal to process
int kill(int pid, int signal);

// Get process ID
int getpid(void);

// Set signal handler
sighandler_t signal(int signum, sighandler_t handler);
```

### Memory Management

```c
// Map memory region
void* mmap(void* addr, size_t length, int prot, int flags, int fd, off_t offset);

// Unmap memory region
int munmap(void* addr, size_t length);

// Change memory protection
int mprotect(void* addr, size_t length, int prot);

// Set program break (heap)
int brk(void* addr);
```

### File Operations

```c
// Open file
int open(const char* pathname, int flags, ...);

// Close file descriptor
int close(int fd);

// Read from file
ssize_t read(int fd, void* buf, size_t count);

// Write to file
ssize_t write(int fd, const void* buf, size_t count);

// Seek in file
off_t lseek(int fd, off_t offset, int whence);

// Get file status
int stat(const char* path, struct stat* buf);

// Delete file
int unlink(const char* pathname);
```

### Network Operations

```c
// Create socket
int socket(int domain, int type, int protocol);

// Bind socket
int bind(int sockfd, const struct sockaddr* addr, socklen_t addrlen);

// Listen for connections
int listen(int sockfd, int backlog);

// Accept connection
int accept(int sockfd, struct sockaddr* addr, socklen_t* addrlen);

// Connect to server
int connect(int sockfd, const struct sockaddr* addr, socklen_t addrlen);

// Send data
ssize_t send(int sockfd, const void* buf, size_t len, int flags);

// Receive data
ssize_t recv(int sockfd, void* buf, size_t len, int flags);
```

### IPC Operations

```c
// Message queues
int msgget(key_t key, int msgflg);
int msgsnd(int msqid, const void* msgp, size_t msgsz, int msgflg);
int msgrcv(int msqid, void* msgp, size_t msgsz, long msgtyp, int msgflg);

// Shared memory
int shmget(key_t key, size_t size, int shmflg);
void* shmat(int shmid, const void* shmaddr, int shmflg);

// Semaphores
int semget(key_t key, int nsems, int semflg);
int semop(int semid, struct sembuf* sops, unsigned int nsops);
```

## Library APIs

### String Operations (`libstring`)

```c
// String length
size_t strlen(const char* s);

// String copy
char* strcpy(char* dest, const char* src);
char* strncpy(char* dest, const char* src, size_t n);

// String concatenation
char* strcat(char* dest, const char* src);

// String comparison
int strcmp(const char* s1, const char* s2);
int strncmp(const char* s1, const char* s2, size_t n);

// String search
char* strstr(const char* haystack, const char* needle);
char* strchr(const char* s, int c);

// String to number
int atoi(const char* s);
long atol(const char* s);
double atof(const char* s);

// Number to string
char* itoa(int value, char* str, int base);
```

### Memory Operations (`libmemory`)

```c
// Memory allocation
void* malloc(size_t size);
void* calloc(size_t nmemb, size_t size);
void* realloc(void* ptr, size_t size);
void free(void* ptr);

// Memory operations
void* memcpy(void* dest, const void* src, size_t n);
void* memmove(void* dest, const void* src, size_t n);
void* memset(void* s, int c, size_t n);
int memcmp(const void* s1, const void* s2, size_t n);
```

### Math Operations (`libmath`)

```c
// Basic math
int abs(int x);
long labs(long x);
double fabs(double x);

// Trigonometric
double sin(double x);
double cos(double x);
double tan(double x);
double asin(double x);
double acos(double x);
double atan(double x);
double atan2(double y, double x);

// Hyperbolic
double sinh(double x);
double cosh(double x);
double tanh(double x);

// Exponential/Logarithmic
double exp(double x);
double log(double x);
double log10(double x);
double pow(double base, double exp);
double sqrt(double x);

// Rounding
double ceil(double x);
double floor(double x);
double round(double x);
```

### GUI Toolkit (`libgui`)

```c
// Window management
Window* window_create(const char* title, int width, int height);
void window_destroy(Window* win);
void window_show(Window* win);
void window_hide(Window* win);
void window_set_position(Window* win, int x, int y);
void window_set_size(Window* win, int width, int height);

// Widget creation
Button* button_create(Window* parent, const char* text, int x, int y, int w, int h);
Label* label_create(Window* parent, const char* text, int x, int y);
TextBox* textbox_create(Window* parent, int x, int y, int w, int h);
CheckBox* checkbox_create(Window* parent, const char* label, int x, int y);
ProgressBar* progress_create(Window* parent, int x, int y, int w);

// Widget operations
void widget_destroy(Widget* widget);
void widget_set_position(Widget* widget, int x, int y);
void widget_set_size(Widget* widget, int w, int h);
void widget_set_visible(Widget* widget, int visible);
```

### Network Operations (`libnetwork`)

```c
// DNS resolution
int dns_resolve(const char* hostname, char* ip_str, size_t ip_len);
int dns_resolve_reverse(const char* ip, char* hostname, size_t host_len);

// HTTP client
HttpConnection* http_connect(const char* host, uint16_t port);
HttpResponse* http_get(HttpConnection* conn, const char* path);
HttpResponse* http_post(HttpConnection* conn, const char* path, const void* data, size_t len);
void http_disconnect(HttpConnection* conn);

// DHCP client
int dhcp_discover(const char* interface, DhcpLease* lease);
int dhcp_renew(const char* interface, DhcpLease* lease);
```

### Security (`libsecurity`)

```c
// Encryption
int aes_init(AesCtx* ctx, const uint8_t* key, AesKeySize key_size);
int aes_encrypt_ecb(AesCtx* ctx, const uint8_t plaintext[16], uint8_t ciphertext[16]);
int aes_decrypt_ecb(AesCtx* ctx, const uint8_t ciphertext[16], uint8_t plaintext[16]);

// Password manager
void pw_init(PasswordMgr* mgr);
int pw_set_master(PasswordMgr* mgr, const char* password);
int pw_add_entry(PasswordMgr* mgr, const PwEntry* entry);
PwEntry* pw_find_entry(PasswordMgr* mgr, const char* name);
void pw_generate_password(char* buf, uint32_t len, int use_symbols, int use_upper);
```

### Container Operations (`libcontainer`)

```c
// Container management
int container_create(const char* name, const char* image, const char* command);
int container_start(uint32_t id);
int container_stop(uint32_t id);
int container_destroy(uint32_t id);
int container_exec(uint32_t id, const char* command);

// Image management
int container_pull_image(const char* name, const char* tag);
int container_list_images(char* buf, uint32_t buf_len);

// Cgroup operations
int container_set_cpu_limit(uint32_t id, uint64_t quota, uint64_t period);
int container_set_memory_limit(uint32_t id, uint64_t limit);
```

### VPN Operations (`libvpn`)

```c
// Tunnel management
int vpn_create_tunnel(const char* name, VpnType type);
int vpn_connect(uint32_t id);
int vpn_disconnect(uint32_t id);
int vpn_send(uint32_t id, const uint8_t* data, uint32_t len);
int vpn_recv(uint32_t id, uint8_t* data, uint32_t len, uint32_t* actual);

// Configuration
int vpn_set_local(uint32_t id, const char* addr, uint16_t port);
int vpn_set_remote(uint32_t id, const char* addr, uint16_t port);
int vpn_set_keys(uint32_t id, const uint8_t* privkey, const uint8_t* pubkey);
```

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | SUCCESS | Operation completed successfully |
| -1 | EINVAL | Invalid argument |
| -2 | ENOMEM | Out of memory |
| -3 | ENOENT | No such file or directory |
| -4 | EACCES | Permission denied |
| -5 | EEXIST | File exists |
| -6 | ENOTDIR | Not a directory |
| -7 | EISDIR | Is a directory |
| -8 | EMFILE | Too many open files |
| -9 | EPIPE | Broken pipe |
| -10 | EAGAIN | Resource temporarily unavailable |

## Constants

### File Flags
```c
#define O_RDONLY    0x0000
#define O_WRONLY    0x0001
#define O_RDWR      0x0002
#define O_CREAT     0x0040
#define O_EXCL      0x0080
#define O_TRUNC     0x0200
#define O_APPEND    0x0400
```

### Memory Protection
```c
#define PROT_NONE   0x00
#define PROT_READ   0x01
#define PROT_WRITE  0x02
#define PROT_EXEC   0x04
```

### Signal Numbers
```c
#define SIGHUP      1
#define SIGINT      2
#define SIGQUIT     3
#define SIGILL      4
#define SIGTRAP     5
#define SIGABRT     6
#define SIGBUS      7
#define SIGFPE      8
#define SIGKILL     9
#define SIGUSR1     10
#define SIGSEGV     11
#define SIGUSR2     12
#define SIGPIPE     13
#define SIGALRM     14
#define SIGTERM     15
```

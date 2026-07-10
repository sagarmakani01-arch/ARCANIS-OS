/**
 * debugger.h — GDB-like Debugger
 *
 * Breakpoints, single-step, register/memory inspection.
 * Supports remote GDB stub protocol.
 */
#ifndef ARCANIS_DEBUGGER_H
#define ARCANIS_DEBUGGER_H

#include <arcanis/types.h>

#define DBG_MAX_BREAKPOINTS  32
#define DBG_MAX_WATCHPOINTS  16
#define DBG_MAX_STACK_TRACE  32
#define DBG_REG_COUNT        16
#define DBG_MEM_BUF_SIZE     4096

typedef enum {
    DBG_BREAK_SOFT,   /* INT3 breakpoint */
    DBG_BREAK_HARD,   /* Hardware debug register */
    DBG_BREAK_WRITE,  /* Watchpoint on write */
    DBG_BREAK_READ,   /* Watchpoint on read */
    DBG_BREAK_ACCESS  /* Watchpoint on access */
} breakpoint_type_t;

typedef struct {
    uint32_t           addr;
    breakpoint_type_t  type;
    int                enabled;
    uint8_t            original_byte;
    uint32_t           hit_count;
    char               condition[128];
} breakpoint_t;

typedef struct {
    uint32_t eax, ebx, ecx, edx;
    uint32_t esi, edi, esp, ebp;
    uint32_t eip, eflags;
    uint16_t cs, ds, es, fs, gs, ss;
} dbg_registers_t;

typedef struct {
    uint32_t addr;
    uint32_t size;
    uint8_t  data[64];
} memory_read_t;

typedef enum {
    DBG_STATE_IDLE,
    DBG_STATE_RUNNING,
    DBG_STATE_STEPPING,
    DBG_STATE_BREAKPOINT,
    DBG_STATE_SIGNAL,
    DBG_STATE_EXITED
} dbg_state_t;

typedef struct {
    uint32_t address;
    uint32_t frame_pointer;
    uint32_t return_address;
    char     symbol[64];
} stack_frame_t;

typedef struct {
    dbg_state_t    state;
    uint32_t       pid;
    dbg_registers_t regs;
    breakpoint_t   breakpoints[DBG_MAX_BREAKPOINTS];
    uint32_t       num_breakpoints;
    stack_frame_t  stack_trace[DBG_MAX_STACK_TRACE];
    uint32_t       stack_depth;
    int            attached;
    int            running;
    char           last_cmd[128];
    uint8_t        mem_buf[DBG_MEM_BUF_SIZE];
} debugger_t;

/* Initialize debugger */
void dbg_init(debugger_t* dbg);

/* Breakpoints */
int      dbg_add_breakpoint(debugger_t* dbg, uint32_t addr, breakpoint_type_t type);
int      dbg_remove_breakpoint(debugger_t* dbg, uint32_t addr);
int      dbg_enable_breakpoint(debugger_t* dbg, uint32_t addr);
int      dbg_disable_breakpoint(debugger_t* dbg, uint32_t addr);
int      dbg_hit_breakpoint(debugger_t* dbg, uint32_t addr);

/* Execution control */
int      dbg_continue(debugger_t* dbg);
int      dbg_step(debugger_t* dbg);
int      dbg_step_over(debugger_t* dbg);
int      dbg_step_out(debugger_t* dbg);
int      dbg_finish(debugger_t* dbg);

/* Registers */
int      dbg_read_registers(debugger_t* dbg, dbg_registers_t* regs);
int      dbg_write_register(debugger_t* dbg, uint32_t reg, uint32_t value);
uint32_t dbg_get_register(debugger_t* dbg, const char* name);
int      dbg_set_register(debugger_t* dbg, const char* name, uint32_t value);

/* Memory */
int      dbg_read_memory(debugger_t* dbg, uint32_t addr, uint32_t len, uint8_t* buf);
int      dbg_write_memory(debugger_t* dbg, uint32_t addr, uint32_t len, const uint8_t* buf);

/* Stack */
int      dbg_backtrace(debugger_t* dbg);
int      dbg_read_stack(debugger_t* dbg, uint32_t offset, uint32_t count, uint32_t* values);

/* Attach/Detach */
int      dbg_attach(debugger_t* dbg, uint32_t pid);
int      dbg_detach(debugger_t* dbg);

/* Signal handling */
int      dbg_handle_signal(debugger_t* dbg, int signum);

/* GDB stub protocol */
int      dbg_gdb_handle(debugger_t* dbg, const char* packet, char* response, uint32_t resp_len);
int      dbg_gdb_read_registers(char* response, uint32_t resp_len, const dbg_registers_t* regs);
int      dbg_gdb_write_registers(const char* data, dbg_registers_t* regs);

/* Symbol resolution */
int      dbg_resolve_symbol(debugger_t* dbg, uint32_t addr, char* symbol, uint32_t sym_len);

/* State */
const char* dbg_state_name(dbg_state_t state);
const char* dbg_reg_name(uint32_t reg);

#endif

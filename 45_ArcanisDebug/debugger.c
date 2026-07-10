/**
 * debugger.c — GDB-like Debugger Implementation
 *
 * Breakpoints, stepping, register inspection, and GDB stub protocol.
 */
#include <arcanis/debugger.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

void dbg_init(debugger_t* dbg) {
    if (!dbg) return;
    memset(dbg, 0, sizeof(debugger_t));
    dbg->state = DBG_STATE_IDLE;
    dbg->attached = 0;
}

/* ---- Breakpoints ---- */

int dbg_add_breakpoint(debugger_t* dbg, uint32_t addr, breakpoint_type_t type) {
    if (!dbg || dbg->num_breakpoints >= DBG_MAX_BREAKPOINTS) return -1;

    /* Check for duplicate */
    for (uint32_t i = 0; i < dbg->num_breakpoints; i++) {
        if (dbg->breakpoints[i].addr == addr)
            return -1;
    }

    breakpoint_t* bp = &dbg->breakpoints[dbg->num_breakpoints++];
    bp->addr = addr;
    bp->type = type;
    bp->enabled = 1;
    bp->hit_count = 0;
    bp->condition[0] = '\0';

    /* Save original byte and patch with INT3 */
    if (type == DBG_BREAK_SOFT) {
        /* uint8_t orig; */
        /* dbg_read_memory(dbg, addr, 1, &orig); */
        /* bp->original_byte = orig; */
        /* uint8_t int3 = 0xCC; */
        /* dbg_write_memory(dbg, addr, 1, &int3); */
    }

    return 0;
}

int dbg_remove_breakpoint(debugger_t* dbg, uint32_t addr) {
    if (!dbg) return -1;

    for (uint32_t i = 0; i < dbg->num_breakpoints; i++) {
        if (dbg->breakpoints[i].addr == addr) {
            breakpoint_t* bp = &dbg->breakpoints[i];

            /* Restore original byte */
            if (bp->type == DBG_BREAK_SOFT) {
                /* dbg_write_memory(dbg, addr, 1, &bp->original_byte); */
            }

            /* Shift remaining */
            for (uint32_t j = i; j < dbg->num_breakpoints - 1; j++)
                dbg->breakpoints[j] = dbg->breakpoints[j + 1];
            dbg->num_breakpoints--;
            return 0;
        }
    }
    return -1;
}

int dbg_enable_breakpoint(debugger_t* dbg, uint32_t addr) {
    if (!dbg) return -1;
    for (uint32_t i = 0; i < dbg->num_breakpoints; i++) {
        if (dbg->breakpoints[i].addr == addr) {
            dbg->breakpoints[i].enabled = 1;
            return 0;
        }
    }
    return -1;
}

int dbg_disable_breakpoint(debugger_t* dbg, uint32_t addr) {
    if (!dbg) return -1;
    for (uint32_t i = 0; i < dbg->num_breakpoints; i++) {
        if (dbg->breakpoints[i].addr == addr) {
            dbg->breakpoints[i].enabled = 0;
            return 0;
        }
    }
    return -1;
}

int dbg_hit_breakpoint(debugger_t* dbg, uint32_t addr) {
    if (!dbg) return 0;
    for (uint32_t i = 0; i < dbg->num_breakpoints; i++) {
        if (dbg->breakpoints[i].addr == addr && dbg->breakpoints[i].enabled) {
            dbg->breakpoints[i].hit_count++;
            return 1;
        }
    }
    return 0;
}

/* ---- Execution control ---- */

int dbg_continue(debugger_t* dbg) {
    if (!dbg || dbg->state == DBG_STATE_IDLE) return -1;
    dbg->state = DBG_STATE_RUNNING;
    /* In real implementation: resume target process */
    return 0;
}

int dbg_step(debugger_t* dbg) {
    if (!dbg || dbg->state == DBG_STATE_IDLE) return -1;
    dbg->state = DBG_STATE_STEPPING;
    /* Single step one instruction */
    dbg->regs.eip++; /* Simplified */
    return 0;
}

int dbg_step_over(debugger_t* dbg) {
    if (!dbg) return -1;
    /* Step over CALL instructions by setting temp BP at return address */
    dbg_step(dbg);
    return 0;
}

int dbg_step_out(debugger_t) {
    /* Set breakpoint at return address from current frame */
    return 0;
}

int dbg_finish(debugger_t* dbg) {
    return dbg_step_out(dbg);
}

/* ---- Registers ---- */

int dbg_read_registers(debugger_t* dbg, dbg_registers_t* regs) {
    if (!dbg || !regs) return -1;
    *regs = dbg->regs;
    return 0;
}

uint32_t dbg_get_register(debugger_t* dbg, const char* name) {
    if (!dbg || !name) return 0;
    if (string_compare(name, "eax") == 0) return dbg->regs.eax;
    if (string_compare(name, "ebx") == 0) return dbg->regs.ebx;
    if (string_compare(name, "ecx") == 0) return dbg->regs.ecx;
    if (string_compare(name, "edx") == 0) return dbg->regs.edx;
    if (string_compare(name, "esi") == 0) return dbg->regs.esi;
    if (string_compare(name, "edi") == 0) return dbg->regs.edi;
    if (string_compare(name, "esp") == 0) return dbg->regs.esp;
    if (string_compare(name, "ebp") == 0) return dbg->regs.ebp;
    if (string_compare(name, "eip") == 0) return dbg->regs.eip;
    if (string_compare(name, "eflags") == 0) return dbg->regs.eflags;
    return 0;
}

int dbg_set_register(debugger_t* dbg, const char* name, uint32_t value) {
    if (!dbg || !name) return -1;
    if (string_compare(name, "eax") == 0) { dbg->regs.eax = value; return 0; }
    if (string_compare(name, "ebx") == 0) { dbg->regs.ebx = value; return 0; }
    if (string_compare(name, "ecx") == 0) { dbg->regs.ecx = value; return 0; }
    if (string_compare(name, "edx") == 0) { dbg->regs.edx = value; return 0; }
    if (string_compare(name, "esi") == 0) { dbg->regs.esi = value; return 0; }
    if (string_compare(name, "edi") == 0) { dbg->regs.edi = value; return 0; }
    if (string_compare(name, "esp") == 0) { dbg->regs.esp = value; return 0; }
    if (string_compare(name, "ebp") == 0) { dbg->regs.ebp = value; return 0; }
    if (string_compare(name, "eip") == 0) { dbg->regs.eip = value; return 0; }
    return -1;
}

int dbg_write_register(debugger_t* dbg, uint32_t reg, uint32_t value) {
    if (!dbg) return -1;
    switch (reg) {
        case 0: dbg->regs.eax = value; break;
        case 1: dbg->regs.ecx = value; break;
        case 2: dbg->regs.edx = value; break;
        case 3: dbg->regs.ebx = value; break;
        case 4: dbg->regs.esp = value; break;
        case 5: dbg->regs.ebp = value; break;
        case 6: dbg->regs.esi = value; break;
        case 7: dbg->regs.edi = value; break;
        case 8: dbg->regs.eip = value; break;
        default: return -1;
    }
    return 0;
}

/* ---- Memory ---- */

int dbg_read_memory(debugger_t* dbg, uint32_t addr, uint32_t len, uint8_t* buf) {
    if (!dbg || !buf || len > DBG_MEM_BUF_SIZE) return -1;
    /* In real implementation: read from target process memory */
    /* For now, copy from mem_buf (simulated) */
    memcpy(buf, dbg->mem_buf, len);
    return 0;
}

int dbg_write_memory(debugger_t* dbg, uint32_t addr, uint32_t len, const uint8_t* buf) {
    if (!dbg || !buf) return -1;
    /* In real implementation: write to target process memory */
    return 0;
}

/* ---- Stack ---- */

int dbg_backtrace(debugger_t* dbg) {
    if (!dbg) return -1;

    dbg->stack_depth = 0;
    uint32_t ebp = dbg->regs.ebp;

    while (ebp != 0 && dbg->stack_depth < DBG_MAX_STACK_TRACE) {
        stack_frame_t* frame = &dbg->stack_trace[dbg->stack_depth];
        frame->frame_pointer = ebp;

        /* Read return address from [ebp+4] */
        /* dbg_read_memory(dbg, ebp + 4, 4, (uint8_t*)&frame->return_address); */
        frame->return_address = 0;
        frame->address = dbg->regs.eip;
        dbg_resolve_symbol(dbg, frame->return_address, frame->symbol, 64);

        /* Read previous frame pointer from [ebp] */
        /* dbg_read_memory(dbg, ebp, 4, (uint8_t*)&ebp); */
        ebp = 0;

        dbg->stack_depth++;
    }
    return 0;
}

int dbg_read_stack(debugger_t* dbg, uint32_t offset, uint32_t count, uint32_t* values) {
    if (!dbg || !values) return -1;
    uint32_t esp = dbg->regs.esp + offset;
    for (uint32_t i = 0; i < count; i++) {
        /* dbg_read_memory(dbg, esp + i * 4, 4, (uint8_t*)&values[i]); */
        values[i] = 0;
    }
    return 0;
}

/* ---- Attach/Detach ---- */

int dbg_attach(debugger_t* dbg, uint32_t pid) {
    if (!dbg) return -1;
    dbg->pid = pid;
    dbg->attached = 1;
    dbg->state = DBG_STATE_IDLE;
    /* In real implementation: ptrace ATTACH */
    return 0;
}

int dbg_detach(debugger_t* dbg) {
    if (!dbg) return -1;
    /* Remove all breakpoints */
    for (uint32_t i = dbg->num_breakpoints; i > 0; i--)
        dbg_remove_breakpoint(dbg, dbg->breakpoints[i-1].addr);
    dbg->attached = 0;
    dbg->state = DBG_STATE_IDLE;
    return 0;
}

/* ---- Signals ---- */

int dbg_handle_signal(debugger_t* dbg, int signum) {
    if (!dbg) return -1;
    dbg->state = DBG_STATE_SIGNAL;
    /* SIGTRAP = breakpoint hit */
    if (signum == 5) {
        dbg->regs.eip--; /* Back up past INT3 */
        dbg->state = DBG_STATE_BREAKPOINT;
    }
    return 0;
}

/* ---- GDB Stub ---- */

static int hex_char(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static uint32_t hex_to_uint(const char* hex, int len) {
    uint32_t val = 0;
    for (int i = 0; i < len; i++) {
        int h = hex_char(hex[i]);
        if (h < 0) break;
        val = val * 16 + h;
    }
    return val;
}

int dbg_gdb_handle(debugger_t* dbg, const char* packet, char* response, uint32_t resp_len) {
    if (!dbg || !packet || !response) return -1;

    response[0] = '\0';

    if (packet[0] == 'g') {
        /* Read registers */
        dbg_gdb_read_registers(response, resp_len, &dbg->regs);
    } else if (packet[0] == 'P') {
        /* Write register */
        /* Preg=value */
        uint32_t reg = hex_to_uint(packet + 1, 2);
        uint32_t val = hex_to_uint(packet + 4, 8);
        dbg_write_register(dbg, reg, val);
        string_copy(response, "OK", resp_len);
    } else if (packet[0] == 'm') {
        /* Read memory: maddr,length */
        const char* p = packet + 1;
        uint32_t addr = 0;
        while (*p && *p != ',') addr = addr * 16 + hex_char(*p++);
        p++;
        uint32_t len = 0;
        while (*p) len = len * 16 + hex_char(*p++);

        uint8_t buf[256];
        dbg_read_memory(dbg, addr, len < 256 ? len : 256, buf);
        /* Convert to hex */
        uint32_t rpos = 0;
        for (uint32_t i = 0; i < len && rpos < resp_len - 2; i++) {
            response[rpos++] = "0123456789abcdef"[buf[i] >> 4];
            response[rpos++] = "0123456789abcdef"[buf[i] & 0xF];
        }
        response[rpos] = '\0';
    } else if (packet[0] == 'M') {
        /* Write memory */
        string_copy(response, "OK", resp_len);
    } else if (packet[0] == 'c') {
        /* Continue */
        dbg_continue(dbg);
        string_copy(response, "OK", resp_len);
    } else if (packet[0] == 's') {
        /* Single step */
        dbg_step(dbg);
        string_copy(response, "S05", resp_len); /* SIGTRAP */
    } else if (packet[0] == 'z') {
        /* Remove breakpoint: z type,addr,length */
        uint32_t addr = hex_to_uint(packet + 3, 8);
        dbg_remove_breakpoint(dbg, addr);
        string_copy(response, "OK", resp_len);
    } else if (packet[0] == 'Z') {
        /* Add breakpoint: Z type,addr,length */
        uint32_t addr = hex_to_uint(packet + 3, 8);
        dbg_add_breakpoint(dbg, addr, DBG_BREAK_SOFT);
        string_copy(response, "OK", resp_len);
    } else if (packet[0] == '?') {
        /* Stop reason */
        string_copy(response, "S05", resp_len); /* SIGTRAP */
    } else if (packet[0] == 'q') {
        /* Query packets */
        if (string_compare_n(packet, "qSupported", 10) == 0)
            string_copy(response, "PacketSize=4096", resp_len);
        else
            string_copy(response, "", resp_len);
    } else {
        string_copy(response, "", resp_len);
    }

    return 0;
}

int dbg_gdb_read_registers(char* response, uint32_t resp_len, const dbg_registers_t* regs) {
    if (!response || !regs) return -1;
    /* GDB expects registers in hex: eax,ecx,edx,ebx,esp,ebp,esi,edi,eip,eflags */
    uint32_t pos = 0;
    uint32_t vals[] = { regs->eax, regs->ecx, regs->edx, regs->ebx,
                        regs->esp, regs->ebp, regs->esi, regs->edi,
                        regs->eip, regs->eflags };
    for (int i = 0; i < 10 && pos < resp_len - 9; i++) {
        for (int j = 7; j >= 0; j--)
            response[pos++] = "0123456789abcdef"[(vals[i] >> (j * 4)) & 0xF];
    }
    response[pos] = '\0';
    return 0;
}

/* ---- Symbol resolution ---- */

int dbg_resolve_symbol(debugger_t* dbg, uint32_t addr, char* symbol, uint32_t sym_len) {
    if (!dbg || !symbol) return -1;
    /* In real implementation: lookup symbol table */
    string_copy(symbol, "unknown", sym_len);
    return -1;
}

const char* dbg_state_name(dbg_state_t state) {
    switch (state) {
        case DBG_STATE_IDLE:      return "idle";
        case DBG_STATE_RUNNING:   return "running";
        case DBG_STATE_STEPPING:  return "stepping";
        case DBG_STATE_BREAKPOINT: return "breakpoint";
        case DBG_STATE_SIGNAL:    return "signal";
        case DBG_STATE_EXITED:    return "exited";
        default:                  return "unknown";
    }
}

const char* dbg_reg_name(uint32_t reg) {
    static const char* names[] = { "eax","ecx","edx","ebx","esp","ebp","esi","edi","eip","eflags" };
    return (reg < 10) ? names[reg] : "???";
}

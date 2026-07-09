#ifndef ARCANIS_DEFS_H
#define ARCANIS_DEFS_H

#define ARCANIS_VERSION   "0.1.0"
#define ARCANIS_CODENAME  "Genesis"
#define ARCANIS_MAX_TASKS 64
#define ARCANIS_MAX_IRQ   16
#define ARCANIS_MAX_IDT   256

#define PIT_FREQ         1193182
#define TIMER_HZ         100
#define STACK_SIZE       4096

#define EFLAGS_IF        0x200
#define EFLAGS_IOPL_3    0x3000

#define SYSCALL_INT      0x80

#define GDT_NULL         0
#define GDT_KERNEL_CODE  1
#define GDT_KERNEL_DATA  2
#define GDT_USER_CODE    3
#define GDT_USER_DATA    4
#define GDT_TSS          5

#define SEG_DPL_KERNEL   0
#define SEG_DPL_USER     3

#define SEG_PRESENT      0x80
#define SEG_ABSENT       0x00

#define SEG_TYPE_CODE    0x0A
#define SEG_TYPE_DATA    0x02
#define SEG_TYPE_TSS     0x09

#define SEG_GRAN_4K      0x80
#define SEG_GRAN_BYTE    0x00

#define IDT_GATE_TASK    0x05
#define IDT_GATE_INT     0x0E
#define IDT_GATE_TRAP    0x0F

#endif

#include <arcanis/gdt.h>
#include <arcanis/io.h>
#include <arcanis/string.h>
#include <arcanis/defs.h>

static struct gdt_entry gdt[6];
static struct gdt_ptr   gdt_ptr;
static struct tss_entry tss;

extern void gdt_flush(uint32_t);
extern void tss_flush(void);

void gdt_set_gate(int num, uint32_t base, uint32_t limit, uint8_t access, uint8_t gran) {
    gdt[num].base_low    = base & 0xFFFF;
    gdt[num].base_middle = (base >> 16) & 0xFF;
    gdt[num].base_high   = (base >> 24) & 0xFF;
    gdt[num].limit_low   = limit & 0xFFFF;
    gdt[num].granularity  = ((limit >> 16) & 0x0F) | (gran & 0xF0);
    gdt[num].access      = access;
}

void gdt_initialize(void) {
    gdt_ptr.limit = sizeof(struct gdt_entry) * 6 - 1;
    gdt_ptr.base  = (uint32_t)&gdt;

    gdt_set_gate(0, 0, 0, 0, 0);

    gdt_set_gate(GDT_KERNEL_CODE, 0, 0xFFFFFFFF,
        SEG_PRESENT | SEG_DPL_KERNEL | SEG_TYPE_CODE | 0x09,
        SEG_GRAN_4K | 0x0F);

    gdt_set_gate(GDT_KERNEL_DATA, 0, 0xFFFFFFFF,
        SEG_PRESENT | SEG_DPL_KERNEL | SEG_TYPE_DATA | 0x09,
        SEG_GRAN_4K | 0x0F);

    gdt_set_gate(GDT_USER_CODE, 0, 0xFFFFFFFF,
        SEG_PRESENT | SEG_DPL_USER | SEG_TYPE_CODE | 0x09,
        SEG_GRAN_4K | 0x0F);

    gdt_set_gate(GDT_USER_DATA, 0, 0xFFFFFFFF,
        SEG_PRESENT | SEG_DPL_USER | SEG_TYPE_DATA | 0x09,
        SEG_GRAN_4K | 0x0F);

    uint32_t tss_base = (uint32_t)&tss;
    uint32_t tss_limit = sizeof(struct tss_entry) - 1;
    gdt_set_gate(GDT_TSS, tss_base, tss_limit,
        SEG_PRESENT | SEG_DPL_KERNEL | SEG_TYPE_TSS | 0x01,
        SEG_GRAN_BYTE | 0x00);

    asm volatile("lgdt %0" : : "m"(gdt_ptr));
    asm volatile(
        "ljmp $0x08, $.reload_cs\n"
        ".reload_cs:\n"
        "mov $0x10, %%ax\n"
        "mov %%ax, %%ds\n"
        "mov %%ax, %%es\n"
        "mov %%ax, %%fs\n"
        "mov %%ax, %%gs\n"
        "mov %%ax, %%ss\n"
        : : : "eax"
    );

    tss_initialize();
}

void tss_initialize(void) {
    uint32_t base = (uint32_t)&tss;
    uint32_t limit = base + sizeof(struct tss_entry);

    memset(&tss, 0, sizeof(struct tss_entry));

    tss.ss0  = GDT_KERNEL_DATA * 8;
    tss.esp0 = 0x90000;
    tss.cs   = GDT_KERNEL_CODE * 8 | 0x03;
    tss.ss   = GDT_KERNEL_DATA * 8 | 0x03;
    tss.ds   = GDT_KERNEL_DATA * 8 | 0x03;
    tss.es   = GDT_KERNEL_DATA * 8 | 0x03;
    tss.fs   = GDT_KERNEL_DATA * 8 | 0x03;
    tss.gs   = GDT_KERNEL_DATA * 8 | 0x03;

    asm volatile(
        "mov $0x2B, %%ax\n"
        "ltr %%ax\n"
        : : : "eax"
    );
}

void tss_set_stack(uint32_t kernel_esp) {
    tss.esp0 = kernel_esp;
}

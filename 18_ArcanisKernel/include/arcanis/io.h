#ifndef ARCANIS_IO_H
#define ARCANIS_IO_H

#include <arcanis/types.h>

static inline void outb(uint16_t port, uint8_t val) {
    asm volatile("outb %0, %1" : : "a"(val), "Nd"(port));
}

static inline uint8_t inb(uint16_t port) {
    uint8_t ret;
    asm volatile("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
}

static inline void outw(uint16_t port, uint16_t val) {
    asm volatile("outw %0, %1" : : "a"(val), "Nd"(port));
}

static inline uint16_t inw(uint16_t port) {
    uint16_t ret;
    asm volatile("inw %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
}

static inline void io_wait(void) {
    outb(0x80, 0);
}

static inline void cli(void) {
    asm volatile("cli");
}

static inline void sti(void) {
    asm volatile("sti");
}

static inline void hlt(void) {
    asm volatile("hlt");
}

static inline void invlpg(void* addr) {
    asm volatile("invlpg (%0)" : : "r"(addr) : "memory");
}

static inline uint32_t get_cr3(void) {
    uint32_t cr3;
    asm volatile("mov %%cr3, %0" : "=r"(cr3));
    return cr3;
}

static inline void set_cr3(uint32_t cr3) {
    asm volatile("mov %0, %%cr3" : : "r"(cr3));
}

static inline uint32_t get_cr2(void) {
    uint32_t cr2;
    asm volatile("mov %%cr2, %0" : "=r"(cr2));
    return cr2;
}

static inline uint32_t get_eflags(void) {
    uint32_t eflags;
    asm volatile("pushfl; pop %0" : "=r"(eflags));
    return eflags;
}

static inline void set_eflags(uint32_t eflags) {
    asm volatile("push %0; popfl" : : "r"(eflags));
}

#endif

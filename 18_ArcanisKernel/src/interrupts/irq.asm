; =============================================================================
; ArcanisKernel - IRQ (Hardware Interrupt Request) Stubs
; Handles hardware interrupts from PIC and routes to C handlers
; =============================================================================

[bits 32]
[extern irq_handler]

; IRQ stubs for IRQ 0-15 (mapped to INT 32-47)
%macro IRQ_STUB 1
global irq%1
irq%1:
    push dword 0        ; Dummy error code
    push dword %1 + 32  ; IRQ number + 32 = interrupt number
    jmp irq_common_stub
%endmacro

; =============================================================================
; IRQ Stubs (0-15)
; =============================================================================

IRQ_STUB 0      ; PIT Timer
IRQ_STUB 1      ; Keyboard
IRQ_STUB 2      ; Cascade
IRQ_STUB 3      ; COM2
IRQ_STUB 4      ; COM1
IRQ_STUB 5      ; LPT2
IRQ_STUB 6      ; Floppy
IRQ_STUB 7      ; LPT1 / Spurious
IRQ_STUB 8      ; CMOS RTC
IRQ_STUB 9      ; ACPI
IRQ_STUB 10     ; Open
IRQ_STUB 11     ; Open
IRQ_STUB 12     ; PS/2 Mouse
IRQ_STUB 13     ; FPU
IRQ_STUB 14     ; Primary ATA
IRQ_STUB 15     ; Secondary ATA

; =============================================================================
; Common IRQ Stub
; =============================================================================

irq_common_stub:
    ; Save all general purpose registers
    pusha

    ; Save data segment
    mov ax, ds
    push eax

    ; Load kernel data segment
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    ; Push pointer to registers_t as argument
    push esp
    call irq_handler
    add esp, 4

    ; Restore data segment
    pop eax
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    ; Restore registers
    popa
    add esp, 8
    iret

; =============================================================================
; ArcanisKernel - ISR (Interrupt Service Routine) Stubs
; These assembly stubs set up the CPU state and call the C handler
; =============================================================================

[bits 32]
[extern isr_handler]

; Common ISR stub that saves CPU state and calls C handler
%macro ISR_STUB 1
global isr%1
isr%1:
    ; Push dummy error code for exceptions that don't push one
    push dword 0
    push dword %1
    jmp isr_common_stub
%endmacro

; ISR stub with error code (CPU pushes error code automatically)
%macro ISR_STUB_ERR 1
global isr%1
isr%1:
    push dword %1
    jmp isr_common_stub
%endmacro

; =============================================================================
; CPU Exceptions (0-31)
; =============================================================================

ISR_STUB 0      ; Division by Zero
ISR_STUB 1      ; Debug
ISR_STUB 2      ; NMI
ISR_STUB 3      ; Breakpoint
ISR_STUB 4      ; Overflow
ISR_STUB 5      ; Bound Range Exceeded
ISR_STUB 6      ; Invalid Opcode
ISR_STUB 7      ; Device Not Available
ISR_STUB_ERR 8  ; Double Fault
ISR_STUB 9      ; Coprocessor Segment Overrun
ISR_STUB_ERR 10 ; Invalid TSS
ISR_STUB_ERR 11 ; Segment Not Present
ISR_STUB_ERR 12 ; Stack-Segment Fault
ISR_STUB_ERR 13 ; General Protection Fault
ISR_STUB_ERR 14 ; Page Fault
ISR_STUB 15     ; Reserved
ISR_STUB 16     ; x87 FPU Error
ISR_STUB_ERR 17 ; Alignment Check
ISR_STUB 18     ; Machine Check
ISR_STUB 19     ; SIMD Exception
ISR_STUB 20     ; Virtualization Exception
ISR_STUB 21     ; Control Protection Exception
ISR_STUB 22     ; Reserved
ISR_STUB 23     ; Reserved
ISR_STUB 24     ; Reserved
ISR_STUB 25     ; Reserved
ISR_STUB 26     ; Reserved
ISR_STUB 27     ; Reserved
ISR_STUB 28     ; Hypervisor Injection Exception
ISR_STUB 29     ; VMM Communication Exception
ISR_STUB_ERR 30 ; Security Exception
ISR_STUB 31     ; Reserved

; =============================================================================
; Common ISR Stub (assembly)
; =============================================================================

isr_common_stub:
    ; Save all general purpose registers
    pusha               ; Push edi, esi, ebp, esp, ebx, edx, ecx, eax

    ; Save data segment
    mov ax, ds
    push eax

    ; Load kernel data segment
    mov ax, 0x10        ; GDT data segment selector
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    ; Push pointer to registers_t struct as argument to isr_handler
    push esp
    call isr_handler
    add esp, 4          ; Clean up argument

    ; Restore data segment
    pop eax
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    ; Restore general purpose registers
    popa
    add esp, 8          ; Remove pushed error code and ISR number
    iret

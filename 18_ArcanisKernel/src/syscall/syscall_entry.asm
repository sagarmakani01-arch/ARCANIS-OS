; =============================================================================
; ArcanisKernel - Syscall Interrupt Handler
; Handles INT 0x80 system calls from user mode
; =============================================================================

[bits 32]
[extern syscall_handler]

global syscall_stub
syscall_stub:
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

    ; Push registers pointer as argument
    push esp
    call syscall_handler
    add esp, 4

    ; Store return value in eax (first register pushed by pusha = eax at [esp+28])
    mov [esp + 28], eax

    ; Restore data segment
    pop eax
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    ; Restore registers
    popa
    iret

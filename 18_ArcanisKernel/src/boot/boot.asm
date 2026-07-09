; =============================================================================
; ArcanisKernel Bootloader - Stage 1
; Loads kernel from disk and transitions to protected mode
; =============================================================================

[bits 16]
[org 0x7C00]

KERNEL_OFFSET equ 0x1000          ; Where kernel is loaded in memory
BOOT_DRIVE    equ 0x80            ; First hard disk

start:
    ; Set up segments and stack
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00                 ; Stack grows down from bootloader

    ; Save boot drive number
    mov [BOOT_DRIVE_NUM], dl

    ; Enable A20 line (fast A20 method)
    in al, 0x92
    or al, 2
    out 0x92, al

    ; Print boot message
    mov si, msg_boot
    call print_string_16

    ; Load kernel from disk
    call load_kernel

    ; Switch to protected mode
    cli
    lgdt [gdt_descriptor]
    mov eax, cr0
    or eax, 0x1
    mov cr0, eax

    ; Far jump to flush CPU pipeline and load CS
    jmp GDT_CODE_SEG:protected_mode_entry

; =============================================================================
; 16-bit Functions
; =============================================================================

print_string_16:
    pusha
.loop:
    lodsb
    test al, al
    jz .done
    mov ah, 0x0E
    mov bh, 0
    int 0x10
    jmp .loop
.done:
    popa
    ret

; Load kernel sectors from disk
load_kernel:
    mov si, msg_load
    call print_string_16

    ; Reset disk system
    mov ah, 0x00
    mov dl, [BOOT_DRIVE_NUM]
    int 0x13
    jc disk_error

    ; Read sectors using INT 13h extension
    mov ah, 0x42
    mov dl, [BOOT_DRIVE_NUM]
    mov si, dap
    int 0x13
    jc disk_error

    ret

disk_error:
    mov si, msg_disk_err
    call print_string_16
.halt:
    cli
    hlt
    jmp .halt

; =============================================================================
; Data
; =============================================================================

BOOT_DRIVE_NUM: db 0
msg_boot:       db '[ArcanisKernel] Stage 1 Boot', 13, 10, 0
msg_load:       db '[ArcanisKernel] Loading kernel...', 13, 10, 0
msg_disk_err:   db '[ArcanisKernel] Disk error!', 13, 10, 0

; Disk Address Packet for INT 13h ext
align 4
dap:
    db 0x10            ; Size of DAP
    db 0               ; Reserved
    dw 32              ; Number of sectors to read (16KB)
    dw 0x0000          ; Offset
    dw 0x1000          ; Segment (0x1000:0x0000 = physical 0x10000)
    dq 1               ; Starting LBA

; =============================================================================
; GDT (Global Descriptor Table)
; =============================================================================

gdt_start:
    ; Null descriptor
    dd 0x0
    dd 0x0

gdt_code:
    ; Code segment: base=0, limit=0xFFFFF, 4KB granularity, 32-bit
    dw 0xFFFF          ; Limit (bits 0-15)
    dw 0x0000          ; Base (bits 0-15)
    db 0x00            ; Base (bits 16-23)
    db 10011010b       ; Access: present, ring 0, code, readable
    db 11001111b       ; Flags: 4KB gran, 32-bit + limit (bits 16-19)
    db 0x00            ; Base (bits 24-31)

gdt_data:
    ; Data segment: base=0, limit=0xFFFFF, 4KB granularity, 32-bit
    dw 0xFFFF
    dw 0x0000
    db 0x00
    db 10010010b       ; Access: present, ring 0, data, writable
    db 11001111b
    db 0x00

gdt_end:

gdt_descriptor:
    dw gdt_end - gdt_start - 1   ; Size
    dd gdt_start                  ; Offset

GDT_CODE_SEG equ gdt_code - gdt_start
GDT_DATA_SEG equ gdt_data - gdt_start

; =============================================================================
; Padding and Boot Signature
; =============================================================================

times 510 - ($ - $$) db 0
dw 0xAA55

; =============================================================================
; Protected Mode Entry Point
; =============================================================================

[bits 32]
protected_mode_entry:
    ; Set up segment registers
    mov ax, GDT_DATA_SEG
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    mov esp, 0x90000   ; Set up stack at 576KB

    ; Jump to kernel entry point
    jmp KERNEL_OFFSET

; Pad to fill first 16KB (32 sectors) for kernel space
times 16384 - ($ - $$) db 0

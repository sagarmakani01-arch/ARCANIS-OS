; =============================================================================
; ArcanisKernel - Kernel Entry Point
; First C code called after bootloader hands off control
; =============================================================================

[bits 32]
[extern kernel_main]
[extern __bss_start]
[extern __bss_end]

global _start

_start:
    ; Clear BSS section
    mov edi, __bss_start
    mov ecx, __bss_end
    sub ecx, edi
    xor eax, eax
    rep stosb

    ; Call kernel main
    call kernel_main

    ; If kernel_main returns, halt
.halt:
    cli
    hlt
    jmp .halt

; =============================================================================
; ArcanisKernel - Context Switch
; Performs low-level context switching between processes
; =============================================================================

[bits 32]
[global context_switch]
[global context_switch_first]

; void context_switch(process_context_t* prev, process_context_t* next)
context_switch:
    ; Save callee-saved registers of previous process
    mov [esp + 4],  eax    ; eax is at offset 0 in process_context_t
    mov [esp + 8],  ebx    ; but we use the struct pointer to save properly

    ; Get pointers to context structs
    mov eax, [esp + 4]     ; eax = prev context
    mov ebx, [esp + 8]     ; ebx = next context

    ; Save previous process state
    mov [eax + 0],  eax
    mov [eax + 4],  ebx
    mov [eax + 8],  ecx
    mov [eax + 12], edx
    mov [eax + 16], esi
    mov [eax + 20], edi
    mov [eax + 24], ebp
    mov [eax + 28], esp

    ; Save EIP (return address)
    mov ecx, [esp]          ; Return address
    mov [eax + 32], ecx

    ; Save EFLAGS
    pushfd
    pop ecx
    mov [eax + 36], ecx

    ; Save segment registers
    mov ecx, cs
    mov [eax + 40], ecx
    mov ecx, ss
    mov [eax + 44], ecx
    mov ecx, ds
    mov [eax + 48], ecx
    mov ecx, es
    mov [eax + 52], ecx
    mov ecx, fs
    mov [eax + 56], ecx
    mov ecx, gs
    mov [eax + 60], ecx

    ; Save CR3 (page directory)
    mov ecx, cr3
    mov [eax + 64], ecx

    ; Load next process state
    mov ecx, [ebx + 36]    ; EFLAGS
    push ecx
    popfd

    mov ecx, [ebx + 64]    ; CR3
    mov cr3, ecx

    mov ecx, [ebx + 44]    ; SS
    mov ss, ecx
    mov ecx, [ebx + 48]    ; DS
    mov ds, ecx
    mov ecx, [ebx + 52]    ; ES
    mov es, ecx
    mov ecx, [ebx + 56]    ; FS
    mov fs, ecx
    mov ecx, [ebx + 60]    ; GS
    mov gs, ecx

    mov ecx, [ebx + 40]    ; CS

    mov eax, [ebx + 0]     ; EAX
    mov ecx, [ebx + 4]     ; EBX  (we'll use it after esp)
    mov edx, [ebx + 8]     ; ECX
    mov esi, [ebx + 12]    ; EDX
    mov edi, [ebx + 16]    ; ESI
    ; EDI saved for later
    mov ebp, [ebx + 24]    ; EBP
    mov esp, [ebx + 28]    ; ESP

    ; Push return EIP onto stack for iret
    push dword [ebx + 40]  ; CS
    push dword [ebx + 32]  ; EIP

    mov edi, [ebx + 20]    ; EDI
    mov ecx, [ebx + 4]     ; EBX

    iret

; First context switch - no previous process to save
context_switch_first:
    mov ebx, [esp + 4]     ; ebx = next context

    mov ecx, [ebx + 36]    ; EFLAGS
    push ecx
    popfd

    mov ecx, [ebx + 64]    ; CR3
    mov cr3, ecx

    mov ecx, [ebx + 44]    ; SS
    mov ss, ecx
    mov ecx, [ebx + 48]    ; DS
    mov ds, ecx
    mov ecx, [ebx + 52]    ; ES
    mov es, ecx
    mov ecx, [ebx + 56]    ; FS
    mov fs, ecx
    mov ecx, [ebx + 60]    ; GS
    mov gs, ecx

    mov eax, [ebx + 0]     ; EAX
    mov ecx, [ebx + 4]     ; EBX
    mov edx, [ebx + 8]     ; ECX
    mov esi, [ebx + 12]    ; EDX
    mov edi, [ebx + 16]    ; ESI
    mov ebp, [ebx + 24]    ; EBP
    mov esp, [ebx + 28]    ; ESP

    push dword [ebx + 40]  ; CS
    push dword [ebx + 32]  ; EIP

    mov edi, [ebx + 20]    ; EDI
    mov ecx, [ebx + 4]     ; EBX

    iret

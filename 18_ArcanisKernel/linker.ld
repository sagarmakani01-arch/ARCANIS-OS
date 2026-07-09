/* ArcanisKernel Linker Script */
ENTRY(_start)

SECTIONS
{
    . = 1M;  /* Load at 1MB - standard for x86 kernels */

    __kernel_start = .;

    .text BLOCK(4K) : ALIGN(4K)
    {
        *(.text)
    }

    .rodata BLOCK(4K) : ALIGN(4K)
    {
        *(.rodata)
    }

    .data BLOCK(4K) : ALIGN(4K)
    {
        *(.data)
    }

    .bss BLOCK(4K) : ALIGN(4K)
    {
        __bss_start = .;
        *(COMMON)
        *(.bss)
        __bss_end = .;
    }

    __kernel_end = .;
}

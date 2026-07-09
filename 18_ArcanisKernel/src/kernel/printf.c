#include <arcanis/io.h>
#include <arcanis/types.h>
#include <arcanis/string.h>
#include <arcanis/vga.h>

void kprintf(const char* format, ...) {
    va_list args;
    va_start(args, format);

    char buf[1024];
    char* ptr = buf;

    while (*format) {
        if (*format == '%') {
            format++;
            switch (*format) {
                case 'd': case 'i': {
                    int val = va_arg(args, int);
                    char num[12];
                    itoa(val, num, 10);
                    strcpy(ptr, num);
                    ptr += strlen(num);
                    break;
                }
                case 'u': {
                    unsigned int val = va_arg(args, unsigned int);
                    char num[12];
                    itoa((int)val, num, 10);
                    strcpy(ptr, num);
                    ptr += strlen(num);
                    break;
                }
                case 'x': case 'X': {
                    unsigned int val = va_arg(args, unsigned int);
                    char hex[11] = "0x00000000";
                    char h[] = "0123456789abcdef";
                    for (int i = 9; i >= 2; i--) {
                        hex[i] = h[val & 0xF];
                        val >>= 4;
                    }
                    strcpy(ptr, hex);
                    ptr += 10;
                    break;
                }
                case 's': {
                    const char* s = va_arg(args, const char*);
                    strcpy(ptr, s);
                    ptr += strlen(s);
                    break;
                }
                case 'c': {
                    char c = (char)va_arg(args, int);
                    *ptr++ = c;
                    break;
                }
                case 'p': {
                    void* p = va_arg(args, void*);
                    char hex[11] = "0x00000000";
                    char h[] = "0123456789abcdef";
                    uint32_t val = (uint32_t)p;
                    for (int i = 9; i >= 2; i--) {
                        hex[i] = h[val & 0xF];
                        val >>= 4;
                    }
                    strcpy(ptr, hex);
                    ptr += 10;
                    break;
                }
                case '%': {
                    *ptr++ = '%';
                    break;
                }
                default:
                    *ptr++ = *format;
                    break;
            }
        } else {
            *ptr++ = *format;
        }
        format++;
    }

    *ptr = '\0';
    va_end(args);

    vga_puts(buf);
    serial_puts(buf);
}

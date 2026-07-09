#include <arcanis/string.h>

size_t arc_strlen(const char* s) {
    size_t len = 0;
    while (s[len]) len++;
    return len;
}

char* arc_strcpy(char* dst, const char* src) {
    char* d = dst;
    while ((*d++ = *src++));
    return dst;
}

char* arc_strncpy(char* dst, const char* src, size_t n) {
    char* d = dst;
    while (n && (*d++ = *src++)) n--;
    while (n--) *d++ = '\0';
    return dst;
}

int arc_strcmp(const char* s1, const char* s2) {
    while (*s1 && (*s1 == *s2)) { s1++; s2++; }
    return *(const unsigned char*)s1 - *(const unsigned char*)s2;
}

int arc_strncmp(const char* s1, const char* s2, size_t n) {
    while (n && *s1 && (*s1 == *s2)) { s1++; s2++; n--; }
    if (n == 0) return 0;
    return *(const unsigned char*)s1 - *(const unsigned char*)s2;
}

char* arc_strcat(char* dst, const char* src) {
    char* d = dst + arc_strlen(dst);
    while ((*d++ = *src++));
    return dst;
}

char* arc_strchr(const char* s, int c) {
    while (*s) {
        if (*s == (char)c) return (char*)s;
        s++;
    }
    return (c == '\0') ? (char*)s : (void*)0;
}

char* arc_strstr(const char* haystack, const char* needle) {
    if (!*needle) return (char*)haystack;
    size_t nlen = arc_strlen(needle);
    while (*haystack) {
        if (arc_strncmp(haystack, needle, nlen) == 0)
            return (char*)haystack;
        haystack++;
    }
    return (void*)0;
}

void* arc_memset(void* s, int c, size_t n) {
    unsigned char* p = (unsigned char*)s;
    while (n--) *p++ = (unsigned char)c;
    return s;
}

void* arc_memcpy(void* dst, const void* src, size_t n) {
    unsigned char* d = (unsigned char*)dst;
    const unsigned char* s = (const unsigned char*)src;
    while (n--) *d++ = *s++;
    return dst;
}

void* arc_memmove(void* dst, const void* src, size_t n) {
    unsigned char* d = (unsigned char*)dst;
    const unsigned char* s = (const unsigned char*)src;
    if (d < s) {
        while (n--) *d++ = *s++;
    } else {
        d += n; s += n;
        while (n--) *--d = *--s;
    }
    return dst;
}

int arc_memcmp(const void* s1, const void* s2, size_t n) {
    const unsigned char* a = (const unsigned char*)s1;
    const unsigned char* b = (const unsigned char*)s2;
    while (n--) {
        if (*a != *b) return *a - *b;
        a++; b++;
    }
    return 0;
}

char* arc_itoa(int32_t value, char* buf, int base) {
    if (base < 2 || base > 36) { buf[0] = '\0'; return buf; }
    char* p = buf;
    char* p1, *p2;
    uint32_t uvalue;
    int negative = 0;
    if (value < 0 && base == 10) { negative = 1; uvalue = (uint32_t)(-value); }
    else { uvalue = (uint32_t)value; }
    do {
        int digit = uvalue % base;
        *p++ = (digit < 10) ? '0' + digit : 'a' + digit - 10;
    } while (uvalue /= base);
    if (negative) *p++ = '-';
    *p = '\0';
    p1 = buf; p2 = p - 1;
    while (p1 < p2) {
        char tmp = *p1; *p1 = *p2; *p2 = tmp;
        p1++; p2--;
    }
    return buf;
}

int arc_atoi(const char* s) {
    int result = 0;
    int sign = 1;
    while (*s == ' ') s++;
    if (*s == '-') { sign = -1; s++; }
    else if (*s == '+') s++;
    while (*s >= '0' && *s <= '9') {
        result = result * 10 + (*s - '0');
        s++;
    }
    return sign * result;
}

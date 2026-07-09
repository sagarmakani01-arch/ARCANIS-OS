#ifndef ARCANIS_STRING_H
#define ARCANIS_STRING_H

#include <stdint.h>
#include <stddef.h>

size_t arc_strlen(const char* s);
char* arc_strcpy(char* dst, const char* src);
char* arc_strncpy(char* dst, const char* src, size_t n);
int arc_strcmp(const char* s1, const char* s2);
int arc_strncmp(const char* s1, const char* s2, size_t n);
char* arc_strcat(char* dst, const char* src);
char* arc_strchr(const char* s, int c);
char* arc_strstr(const char* haystack, const char* needle);
void* arc_memset(void* s, int c, size_t n);
void* arc_memcpy(void* dst, const void* src, size_t n);
void* arc_memmove(void* dst, const void* src, size_t n);
int arc_memcmp(const void* s1, const void* s2, size_t n);
char* arc_itoa(int32_t value, char* buf, int base);
int arc_atoi(const char* s);

#endif

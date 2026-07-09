#ifndef ARCANIS_STRING_H
#define ARCANIS_STRING_H

#include <arcanis/types.h>

size_t strlen(const char* str);
char* strcpy(char* dest, const char* src);
char* strncpy(char* dest, const char* src, size_t n);
int strcmp(const char* s1, const char* s2);
int strncmp(const char* s1, const char* s2, size_t n);
char* strcat(char* dest, const char* src);
char* strchr(const char* str, int c);
char* strrchr(const char* str, int c);
void* memset(void* ptr, int value, size_t num);
void* memcpy(void* dest, const void* src, size_t num);
void* memmove(void* dest, const void* src, size_t num);
int memcmp(const void* ptr1, const void* ptr2, size_t num);
char* itoa(int value, char* str, int base);
int atoi(const char* str);
void reverse(char* str, int length);
void kprintf(const char* format, ...);

#endif

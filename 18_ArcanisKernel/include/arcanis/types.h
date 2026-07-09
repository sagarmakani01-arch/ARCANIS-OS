#ifndef ARCANIS_TYPES_H
#define ARCANIS_TYPES_H

typedef unsigned char       uint8_t;
typedef unsigned short      uint16_t;
typedef unsigned int        uint32_t;
typedef unsigned long long  uint64_t;

typedef signed char         int8_t;
typedef signed short        int16_t;
typedef signed int          int32_t;
typedef signed long long    int64_t;

typedef uint32_t size_t;
typedef int32_t  ssize_t;
typedef int32_t  pid_t;
typedef uint32_t uid_t;
typedef uint32_t gid_t;
typedef uint32_t off_t;

#define NULL ((void*)0)
#define true  1
#define false 0
#define bool  uint8_t

#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define ABS(x)    ((x) < 0 ? -(x) : (x))

#define asm     __asm__
#define inline  __inline__
#define volatile __volatile__

#define KERNEL_BASE 0xC0000000
#define PAGE_SIZE   4096

#endif

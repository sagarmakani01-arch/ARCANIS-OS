#ifndef ARCANIS_DRIVER_H
#define ARCANIS_DRIVER_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#define DRIVER_NAME_MAX     64
#define DRIVER_VERSION_MAX  32
#define DRIVER_MAX_DEVICES  256

typedef enum {
    DRIVER_STATUS_OK = 0,
    DRIVER_STATUS_ERROR,
    DRIVER_STATUS_NOT_READY,
    DRIVER_STATUS_TIMEOUT,
    DRIVER_STATUS_NO_MEMORY,
    DRIVER_STATUS_INVALID_PARAM,
    DRIVER_STATUS_NOT_SUPPORTED,
    DRIVER_STATUS_BUSY
} DriverStatus;

typedef enum {
    DRIVER_TYPE_INPUT = 0,
    DRIVER_TYPE_DISPLAY,
    DRIVER_TYPE_STORAGE,
    DRIVER_TYPE_NETWORK,
    DRIVER_TYPE_BUS,
    DRIVER_TYPE_TIMER,
    DRIVER_TYPE_DMA,
    DRIVER_TYPE_OTHER
} DriverType;

typedef enum {
    DEVICE_STATE_UNKNOWN = 0,
    DEVICE_STATE_INITIALIZING,
    DEVICE_STATE_READY,
    DEVICE_STATE_RUNNING,
    DEVICE_STATE_SUSPENDED,
    DEVICE_STATE_ERROR
} DeviceState;

typedef struct Device Device;
typedef struct Driver Driver;
typedef struct DriverOps DriverOps;
typedef struct DeviceOps DeviceOps;

struct DeviceOps {
    DriverStatus (*open)(Device* dev);
    DriverStatus (*close)(Device* dev);
    DriverStatus (*read)(Device* dev, void* buf, size_t offset, size_t len, size_t* bytes_read);
    DriverStatus (*write)(Device* dev, const void* buf, size_t offset, size_t len, size_t* bytes_written);
    DriverStatus (*ioctl)(Device* dev, uint32_t cmd, void* arg);
};

struct Device {
    char name[DRIVER_NAME_MAX];
    uint32_t id;
    uint32_t vendor_id;
    uint32_t device_id;
    uint32_t class_code;
    uint32_t subclass;
    uint32_t revision;
    DeviceState state;
    Driver* driver;
    void* driver_data;
    DeviceOps* ops;
    uint32_t irq;
    uint64_t mmio_base;
    size_t mmio_size;
};

struct DriverOps {
    DriverStatus (*init)(Driver* drv);
    DriverStatus (*shutdown)(Driver* drv);
    DriverStatus (*probe)(Device* dev);
    DriverStatus (*attach)(Device* dev);
    DriverStatus (*detach)(Device* dev);
};

struct Driver {
    char name[DRIVER_NAME_MAX];
    char version[DRIVER_VERSION_MAX];
    DriverType type;
    uint32_t flags;
    DriverOps* ops;
    Device* devices[DRIVER_MAX_DEVICES];
    uint32_t device_count;
    void* private_data;
    bool initialized;
};

DriverStatus driver_create(Driver* drv, const char* name, DriverType type, DriverOps* ops);
DriverStatus driver_destroy(Driver* drv);
DriverStatus driver_register(Driver* drv);
DriverStatus driver_unregister(Driver* drv);
Driver* driver_find_by_name(const char* name);
Driver* driver_find_by_type(DriverType type);

DriverStatus device_create(Device* dev, const char* name, Driver* drv);
DriverStatus device_destroy(Device* dev);
DriverStatus device_set_state(Device* dev, DeviceState state);

const char* driver_status_str(DriverStatus status);
const char* driver_type_str(DriverType type);
const char* device_state_str(DeviceState state);

#endif
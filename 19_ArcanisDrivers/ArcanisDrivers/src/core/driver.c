#include "drivers/driver.h"
#include <string.h>
#include <stdio.h>

#define MAX_DRIVERS 128

static Driver* g_drivers[MAX_DRIVERS];
static uint32_t g_driver_count = 0;

DriverStatus driver_create(Driver* drv, const char* name, DriverType type, DriverOps* ops) {
    if (!drv || !name || !ops) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    memset(drv, 0, sizeof(Driver));
    strncpy(drv->name, name, DRIVER_NAME_MAX - 1);
    drv->type = type;
    drv->ops = ops;
    drv->initialized = false;
    drv->device_count = 0;

    return DRIVER_STATUS_OK;
}

DriverStatus driver_destroy(Driver* drv) {
    if (!drv) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (drv->initialized && drv->ops && drv->ops->shutdown) {
        drv->ops->shutdown(drv);
    }

    driver_unregister(drv);
    memset(drv, 0, sizeof(Driver));

    return DRIVER_STATUS_OK;
}

DriverStatus driver_register(Driver* drv) {
    if (!drv) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (g_driver_count >= MAX_DRIVERS) {
        return DRIVER_STATUS_NO_MEMORY;
    }

    if (driver_find_by_name(drv->name)) {
        return DRIVER_STATUS_ERROR;
    }

    g_drivers[g_driver_count++] = drv;

    if (drv->ops && drv->ops->init) {
        DriverStatus status = drv->ops->init(drv);
        if (status != DRIVER_STATUS_OK) {
            g_driver_count--;
            return status;
        }
        drv->initialized = true;
    }

    return DRIVER_STATUS_OK;
}

DriverStatus driver_unregister(Driver* drv) {
    if (!drv) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    for (uint32_t i = 0; i < g_driver_count; i++) {
        if (g_drivers[i] == drv) {
            for (uint32_t j = i; j < g_driver_count - 1; j++) {
                g_drivers[j] = g_drivers[j + 1];
            }
            g_driver_count--;
            return DRIVER_STATUS_OK;
        }
    }

    return DRIVER_STATUS_ERROR;
}

Driver* driver_find_by_name(const char* name) {
    if (!name) {
        return NULL;
    }

    for (uint32_t i = 0; i < g_driver_count; i++) {
        if (strcmp(g_drivers[i]->name, name) == 0) {
            return g_drivers[i];
        }
    }

    return NULL;
}

Driver* driver_find_by_type(DriverType type) {
    for (uint32_t i = 0; i < g_driver_count; i++) {
        if (g_drivers[i]->type == type) {
            return g_drivers[i];
        }
    }
    return NULL;
}

DriverStatus device_create(Device* dev, const char* name, Driver* drv) {
    if (!dev || !name || !drv) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    memset(dev, 0, sizeof(Device));
    strncpy(dev->name, name, DRIVER_NAME_MAX - 1);
    dev->driver = drv;
    dev->state = DEVICE_STATE_INITIALIZING;

    if (drv->device_count < DRIVER_MAX_DEVICES) {
        drv->devices[drv->device_count++] = dev;
    }

    return DRIVER_STATUS_OK;
}

DriverStatus device_destroy(Device* dev) {
    if (!dev) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (dev->driver) {
        for (uint32_t i = 0; i < dev->driver->device_count; i++) {
            if (dev->driver->devices[i] == dev) {
                for (uint32_t j = i; j < dev->driver->device_count - 1; j++) {
                    dev->driver->devices[j] = dev->driver->devices[j + 1];
                }
                dev->driver->device_count--;
                break;
            }
        }
    }

    memset(dev, 0, sizeof(Device));
    return DRIVER_STATUS_OK;
}

DriverStatus device_set_state(Device* dev, DeviceState state) {
    if (!dev) {
        return DRIVER_STATUS_INVALID_PARAM;
    }
    dev->state = state;
    return DRIVER_STATUS_OK;
}

const char* driver_status_str(DriverStatus status) {
    switch (status) {
        case DRIVER_STATUS_OK:            return "OK";
        case DRIVER_STATUS_ERROR:         return "Error";
        case DRIVER_STATUS_NOT_READY:     return "Not Ready";
        case DRIVER_STATUS_TIMEOUT:       return "Timeout";
        case DRIVER_STATUS_NO_MEMORY:     return "No Memory";
        case DRIVER_STATUS_INVALID_PARAM: return "Invalid Parameter";
        case DRIVER_STATUS_NOT_SUPPORTED: return "Not Supported";
        case DRIVER_STATUS_BUSY:          return "Busy";
        default:                          return "Unknown";
    }
}

const char* driver_type_str(DriverType type) {
    switch (type) {
        case DRIVER_TYPE_INPUT:   return "Input";
        case DRIVER_TYPE_DISPLAY: return "Display";
        case DRIVER_TYPE_STORAGE: return "Storage";
        case DRIVER_TYPE_NETWORK: return "Network";
        case DRIVER_TYPE_BUS:     return "Bus";
        case DRIVER_TYPE_TIMER:   return "Timer";
        case DRIVER_TYPE_DMA:     return "DMA";
        case DRIVER_TYPE_OTHER:   return "Other";
        default:                  return "Unknown";
    }
}

const char* device_state_str(DeviceState state) {
    switch (state) {
        case DEVICE_STATE_UNKNOWN:      return "Unknown";
        case DEVICE_STATE_INITIALIZING: return "Initializing";
        case DEVICE_STATE_READY:        return "Ready";
        case DEVICE_STATE_RUNNING:      return "Running";
        case DEVICE_STATE_SUSPENDED:    return "Suspended";
        case DEVICE_STATE_ERROR:        return "Error";
        default:                        return "Unknown";
    }
}

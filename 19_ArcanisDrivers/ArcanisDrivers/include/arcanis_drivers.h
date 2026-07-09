#ifndef ARCANIS_DRIVERS_H
#define ARCANIS_DRIVERS_H

#include "drivers/driver.h"
#include "drivers/driver_event.h"
#include "hal/hal.h"
#include "pnp/pnp.h"
#include "utils/driver_memory.h"
#include "utils/driver_ringbuffer.h"

#include "drivers/keyboard.h"
#include "drivers/mouse.h"
#include "drivers/display.h"
#include "drivers/storage.h"
#include "drivers/network.h"

#define ARCANIS_DRIVERS_VERSION_MAJOR 1
#define ARCANIS_DRIVERS_VERSION_MINOR 0
#define ARCANIS_DRIVERS_VERSION_PATCH 0

typedef struct {
    HALContext hal;
    PnPManager pnp;
    MemoryManager memory;
    KeyboardDriver keyboard;
    MouseDriver mouse;
    DisplayDriver display;
    StorageDriver storage;
    NetworkDriver network;
    bool initialized;
} ArcanisDrivers;

DriverStatus arcanis_drivers_init(ArcanisDrivers* ctx);
DriverStatus arcanis_drivers_shutdown(ArcanisDrivers* ctx);
DriverStatus arcanis_drivers_enumerate(ArcanisDrivers* ctx);

const char* arcanis_drivers_version(void);
void arcanis_drivers_print_info(void);

#endif
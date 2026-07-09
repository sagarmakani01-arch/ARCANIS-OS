#ifndef ARCANIS_PNP_H
#define ARCANIS_PNP_H

#include "drivers/driver.h"
#include "drivers/driver_event.h"
#include "hal/hal.h"

#define PNP_MAX_BUS_DEVICES   128
#define PNP_MAX_DRIVERS       64
#define PNP_VENDOR_NAME_MAX   64
#define PNP_DEVICE_NAME_MAX   128

typedef enum {
    BUS_TYPE_PCI = 0,
    BUS_TYPE_ISA,
    BUS_TYPE_USB,
    BUS_TYPE_SCSI,
    BUS_TYPE_SATA,
    BUS_TYPE_NVME,
    BUS_TYPE_VIRTIO,
    BUS_TYPE_CUSTOM
} BusType;

typedef struct {
    uint32_t vendor_id;
    uint32_t device_id;
    uint32_t class_code;
    uint32_t subclass;
    uint32_t revision;
    uint16_t bus;
    uint16_t device;
    uint16_t function;
    uint32_t irq;
    uint64_t bar[6];
    size_t bar_size[6];
    bool enabled;
} PCIDeviceInfo;

typedef struct {
    uint32_t port;
    uint32_t irq;
    bool enabled;
} ISADeviceInfo;

typedef struct {
    uint32_t vendor_id;
    uint32_t product_id;
    uint32_t device_class;
    uint32_t device_subclass;
    uint32_t port;
    uint32_t speed;
} USBDeviceInfo;

typedef struct {
    char vendor_name[PNP_VENDOR_NAME_MAX];
    char device_name[PNP_DEVICE_NAME_MAX];
    BusType bus_type;
    union {
        PCIDeviceInfo pci;
        ISADeviceInfo isa;
        USBDeviceInfo usb;
    } info;
    uint32_t flags;
    bool claimed;
} PnPDevice;

typedef struct {
    DriverType driver_type;
    uint32_t vendor_id;
    uint32_t device_id;
    uint32_t class_code;
    Driver* driver;
    bool active;
} PnPDriverEntry;

typedef struct {
    PnPDevice devices[PNP_MAX_BUS_DEVICES];
    uint32_t device_count;
    PnPDriverEntry drivers[PNP_MAX_DRIVERS];
    uint32_t driver_count;
    EventDispatcher events;
    HALContext* hal;
    bool initialized;
} PnPManager;

DriverStatus pnp_init(PnPManager* pnp, HALContext* hal);
DriverStatus pnp_shutdown(PnPManager* pnp);

DriverStatus pnp_scan_bus(PnPManager* pnp);
DriverStatus pnp_scan_pci(PnPManager* pnp);
DriverStatus pnp_scan_isa(PnPManager* pnp);
DriverStatus pnp_scan_usb(PnPManager* pnp);

DriverStatus pnp_register_driver(PnPManager* pnp, DriverType type, 
                                  uint32_t vendor_id, uint32_t device_id,
                                  uint32_t class_code, Driver* driver);
DriverStatus pnp_unregister_driver(PnPManager* pnp, Driver* driver);

DriverStatus pnp_probe_device(PnPManager* pnp, PnPDevice* dev);
DriverStatus pnp_attach_device(PnPManager* pnp, PnPDevice* dev);
DriverStatus pnp_detach_device(PnPManager* pnp, PnPDevice* dev);

DriverStatus pnp_get_device_info(PnPManager* pnp, uint32_t index, PnPDevice* dev);
uint32_t pnp_get_device_count(PnPManager* pnp);
PnPDevice* pnp_find_device(PnPManager* pnp, uint32_t vendor_id, uint32_t device_id);
PnPDevice* pnp_find_device_by_class(PnPManager* pnp, uint32_t class_code);

DriverStatus pnp_enable_device(PnPManager* pnp, PnPDevice* dev);
DriverStatus pnp_disable_device(PnPManager* pnp, PnPDevice* dev);

const char* pnp_get_vendor_name(uint32_t vendor_id);
const char* pnp_get_device_name(uint32_t vendor_id, uint32_t device_id);
const char* pnp_bus_type_str(BusType type);

#endif
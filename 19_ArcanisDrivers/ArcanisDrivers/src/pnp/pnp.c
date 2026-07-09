#include "pnp/pnp.h"
#include <string.h>
#include <stdio.h>

#define PCI_CONFIG_ADDRESS  0xCF8
#define PCI_CONFIG_DATA     0xCFC

#define PCI_VENDOR_ID       0x00
#define PCI_DEVICE_ID       0x02
#define PCI_COMMAND         0x04
#define PCI_STATUS          0x06
#define PCI_REVISION        0x08
#define PCI_PROG_IF         0x09
#define PCI_SUBCLASS        0x0A
#define PCI_CLASS           0x0B
#define PCI_HEADER_TYPE     0x0E
#define PCI_BAR0            0x10
#define PCI_IRQ_LINE        0x3C

#define PCI_COMMAND_IO_SPACE    0x0001
#define PCI_COMMAND_MEM_SPACE   0x0002
#define PCI_COMMAND_BUS_MASTER  0x0004

#define ISABASE_PORT    0x600
#define ISABASE_IRQ     0x700

typedef struct {
    uint32_t id;
    const char* name;
} VendorEntry;

static const VendorEntry known_vendors[] = {
    {0x8086, "Intel"},
    {0x10DE, "NVIDIA"},
    {0x1002, "AMD"},
    {0x1022, "AMD"},
    {0x10EC, "Realtek"},
    {0x1AF4, "VirtIO"},
    {0x1B36, "Red Hat"},
    {0x1234, "QEMU"},
    {0x1AD7, "Xen"},
    {0x1414, "Microsoft"},
    {0, NULL}
};

static uint32_t pci_config_read(uint16_t bus, uint16_t device, uint16_t function, uint16_t offset, uint32_t size) {
    uint32_t address = (uint32_t)bus << 16 | (uint32_t)device << 11 | (uint32_t)function << 8 | (offset & 0xFC) | 0x80000000;

    #ifdef _WIN32
    __outdword(PCI_CONFIG_ADDRESS, address);
    if (size == 1) return (uint8_t)(__inb(PCI_CONFIG_DATA + (offset & 3)));
    if (size == 2) return (uint16_t)(__inw(PCI_CONFIG_DATA + (offset & 2)));
    return __indl(PCI_CONFIG_DATA);
    #else
    return 0;
    #endif
}

static void pci_config_write(uint16_t bus, uint16_t device, uint16_t function, uint16_t offset, uint32_t value, uint32_t size) {
    uint32_t address = (uint32_t)bus << 16 | (uint32_t)device << 11 | (uint32_t)function << 8 | (offset & 0xFC) | 0x80000000;

    #ifdef _WIN32
    __outdword(PCI_CONFIG_ADDRESS, address);
    if (size == 1) __outb(value, PCI_CONFIG_DATA + (offset & 3));
    else if (size == 2) __outw(value, PCI_CONFIG_DATA + (offset & 2));
    else __outd(value, PCI_CONFIG_DATA);
    #endif
}

DriverStatus pnp_init(PnPManager* pnp, HALContext* hal) {
    if (!pnp || !hal) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    memset(pnp, 0, sizeof(PnPManager));
    pnp->hal = hal;
    event_dispatcher_init(&pnp->events);
    pnp->initialized = true;

    return DRIVER_STATUS_OK;
}

DriverStatus pnp_shutdown(PnPManager* pnp) {
    if (!pnp || !pnp->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    for (uint32_t i = 0; i < pnp->device_count; i++) {
        if (pnp->devices[i].claimed) {
            pnp_detach_device(pnp, &pnp->devices[i]);
        }
    }

    pnp->initialized = false;
    return DRIVER_STATUS_OK;
}

DriverStatus pnp_scan_bus(PnPManager* pnp) {
    if (!pnp || !pnp->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    pnp_scan_pci(pnp);
    pnp_scan_isa(pnp);

    return DRIVER_STATUS_OK;
}

DriverStatus pnp_scan_pci(PnPManager* pnp) {
    if (!pnp || !pnp->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    for (uint16_t bus = 0; bus < 256; bus++) {
        for (uint16_t device = 0; device < 32; device++) {
            for (uint16_t function = 0; function < 8; function++) {
                uint32_t vendor_id = pci_config_read(bus, device, function, PCI_VENDOR_ID, 2);
                if (vendor_id == 0 || vendor_id == 0xFFFF) {
                    if (function == 0) break;
                    continue;
                }

                if (pnp->device_count >= PNP_MAX_BUS_DEVICES) {
                    return DRIVER_STATUS_NO_MEMORY;
                }

                PnPDevice* dev = &pnp->devices[pnp->device_count];
                dev->bus_type = BUS_TYPE_PCI;
                dev->info.pci.vendor_id = vendor_id;
                dev->info.pci.device_id = pci_config_read(bus, device, function, PCI_DEVICE_ID, 2);
                dev->info.pci.class_code = pci_config_read(bus, device, function, PCI_CLASS, 1);
                dev->info.pci.subclass = pci_config_read(bus, device, function, PCI_SUBCLASS, 1);
                dev->info.pci.revision = pci_config_read(bus, device, function, PCI_REVISION, 1);
                dev->info.pci.bus = bus;
                dev->info.pci.device = device;
                dev->info.pci.function = function;
                dev->info.pci.irq = pci_config_read(bus, device, function, PCI_IRQ_LINE, 1);

                for (int i = 0; i < 6; i++) {
                    dev->info.pci.bar[i] = pci_config_read(bus, device, function, PCI_BAR0 + (i * 4), 4);
                }

                snprintf(dev->vendor_name, PNP_VENDOR_NAME_MAX, "%s", pnp_get_vendor_name(vendor_id));
                snprintf(dev->device_name, PNP_DEVICE_NAME_MAX, "PCI Device %04X:%04X", vendor_id, dev->info.pci.device_id);

                dev->claimed = false;
                pnp->device_count++;
            }
        }
    }

    return DRIVER_STATUS_OK;
}

DriverStatus pnp_scan_isa(PnPManager* pnp) {
    if (!pnp || !pnp->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    uint32_t isa_ports[] = {0x60, 0x64, 0x1F0, 0x170, 0x3F8, 0x2F8, 0x3E8, 0x2E8, 0x300, 0};
    uint32_t isa_irqs[]  = {1, 12, 14, 15, 4, 3, 4, 3, 5, 0};

    for (int i = 0; isa_ports[i] != 0; i++) {
        if (pnp->device_count >= PNP_MAX_BUS_DEVICES) {
            return DRIVER_STATUS_NO_MEMORY;
        }

        PnPDevice* dev = &pnp->devices[pnp->device_count];
        dev->bus_type = BUS_TYPE_ISA;
        dev->info.isa.port = isa_ports[i];
        dev->info.isa.irq = isa_irqs[i];
        dev->info.isa.enabled = true;
        dev->claimed = false;

        snprintf(dev->vendor_name, PNP_VENDOR_NAME_MAX, "ISA");
        snprintf(dev->device_name, PNP_DEVICE_NAME_MAX, "ISA Device 0x%03X", isa_ports[i]);

        pnp->device_count++;
    }

    return DRIVER_STATUS_OK;
}

DriverStatus pnp_scan_usb(PnPManager* pnp) {
    (void)pnp;
    return DRIVER_STATUS_NOT_SUPPORTED;
}

DriverStatus pnp_register_driver(PnPManager* pnp, DriverType type,
                                  uint32_t vendor_id, uint32_t device_id,
                                  uint32_t class_code, Driver* driver) {
    if (!pnp || !driver || !pnp->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (pnp->driver_count >= PNP_MAX_DRIVERS) {
        return DRIVER_STATUS_NO_MEMORY;
    }

    PnPDriverEntry* entry = &pnp->drivers[pnp->driver_count];
    entry->driver_type = type;
    entry->vendor_id = vendor_id;
    entry->device_id = device_id;
    entry->class_code = class_code;
    entry->driver = driver;
    entry->active = true;

    pnp->driver_count++;
    return DRIVER_STATUS_OK;
}

DriverStatus pnp_unregister_driver(PnPManager* pnp, Driver* driver) {
    if (!pnp || !driver || !pnp->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    for (uint32_t i = 0; i < pnp->driver_count; i++) {
        if (pnp->drivers[i].driver == driver) {
            pnp->drivers[i].active = false;
            for (uint32_t j = i; j < pnp->driver_count - 1; j++) {
                pnp->drivers[j] = pnp->drivers[j + 1];
            }
            pnp->driver_count--;
            return DRIVER_STATUS_OK;
        }
    }

    return DRIVER_STATUS_ERROR;
}

DriverStatus pnp_probe_device(PnPManager* pnp, PnPDevice* dev) {
    if (!pnp || !dev || !pnp->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    for (uint32_t i = 0; i < pnp->driver_count; i++) {
        PnPDriverEntry* entry = &pnp->drivers[i];
        if (!entry->active || !entry->driver) continue;

        bool match = false;
        if (entry->vendor_id != 0) {
            match = (entry->vendor_id == dev->info.pci.vendor_id);
        } else if (entry->class_code != 0) {
            match = (entry->class_code == dev->info.pci.class_code);
        }

        if (match && entry->driver->ops && entry->driver->ops->probe) {
            Device* device = NULL;
            DriverStatus status = entry->driver->ops->probe(device);
            if (status == DRIVER_STATUS_OK) {
                return DRIVER_STATUS_OK;
            }
        }
    }

    return DRIVER_STATUS_NOT_SUPPORTED;
}

DriverStatus pnp_attach_device(PnPManager* pnp, PnPDevice* dev) {
    if (!pnp || !dev || !pnp->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    DriverEvent event = {
        .type = EVENT_DEVICE_CONNECTED,
        .source = NULL,
        .data = {dev->info.pci.vendor_id, dev->info.pci.device_id, dev->bus_type, 0}
    };

    event_emit(&pnp->events, &event);

    dev->claimed = true;
    return DRIVER_STATUS_OK;
}

DriverStatus pnp_detach_device(PnPManager* pnp, PnPDevice* dev) {
    if (!pnp || !dev || !pnp->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    DriverEvent event = {
        .type = EVENT_DEVICE_DISCONNECTED,
        .source = NULL,
        .data = {dev->info.pci.vendor_id, dev->info.pci.device_id, dev->bus_type, 0}
    };

    event_emit(&pnp->events, &event);

    dev->claimed = false;
    return DRIVER_STATUS_OK;
}

DriverStatus pnp_get_device_info(PnPManager* pnp, uint32_t index, PnPDevice* dev) {
    if (!pnp || !dev || !pnp->initialized || index >= pnp->device_count) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    *dev = pnp->devices[index];
    return DRIVER_STATUS_OK;
}

uint32_t pnp_get_device_count(PnPManager* pnp) {
    return pnp ? pnp->device_count : 0;
}

PnPDevice* pnp_find_device(PnPManager* pnp, uint32_t vendor_id, uint32_t device_id) {
    if (!pnp || !pnp->initialized) {
        return NULL;
    }

    for (uint32_t i = 0; i < pnp->device_count; i++) {
        if (pnp->devices[i].info.pci.vendor_id == vendor_id &&
            pnp->devices[i].info.pci.device_id == device_id) {
            return &pnp->devices[i];
        }
    }

    return NULL;
}

PnPDevice* pnp_find_device_by_class(PnPManager* pnp, uint32_t class_code) {
    if (!pnp || !pnp->initialized) {
        return NULL;
    }

    for (uint32_t i = 0; i < pnp->device_count; i++) {
        if (pnp->devices[i].info.pci.class_code == class_code) {
            return &pnp->devices[i];
        }
    }

    return NULL;
}

DriverStatus pnp_enable_device(PnPManager* pnp, PnPDevice* dev) {
    if (!pnp || !dev || !pnp->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (dev->bus_type == BUS_TYPE_PCI) {
        uint16_t command = pci_config_read(dev->info.pci.bus, dev->info.pci.device,
                                           dev->info.pci.function, PCI_COMMAND, 2);
        command |= PCI_COMMAND_IO_SPACE | PCI_COMMAND_MEM_SPACE | PCI_COMMAND_BUS_MASTER;
        pci_config_write(dev->info.pci.bus, dev->info.pci.device,
                        dev->info.pci.function, PCI_COMMAND, command, 2);
    }

    dev->info.pci.enabled = true;
    return DRIVER_STATUS_OK;
}

DriverStatus pnp_disable_device(PnPManager* pnp, PnPDevice* dev) {
    if (!pnp || !dev || !pnp->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (dev->bus_type == BUS_TYPE_PCI) {
        uint16_t command = pci_config_read(dev->info.pci.bus, dev->info.pci.device,
                                           dev->info.pci.function, PCI_COMMAND, 2);
        command &= ~(PCI_COMMAND_IO_SPACE | PCI_COMMAND_MEM_SPACE | PCI_COMMAND_BUS_MASTER);
        pci_config_write(dev->info.pci.bus, dev->info.pci.device,
                        dev->info.pci.function, PCI_COMMAND, command, 2);
    }

    dev->info.pci.enabled = false;
    return DRIVER_STATUS_OK;
}

const char* pnp_get_vendor_name(uint32_t vendor_id) {
    for (int i = 0; known_vendors[i].name != NULL; i++) {
        if (known_vendors[i].id == vendor_id) {
            return known_vendors[i].name;
        }
    }
    return "Unknown";
}

const char* pnp_get_device_name(uint32_t vendor_id, uint32_t device_id) {
    (void)device_id;
    return pnp_get_vendor_name(vendor_id);
}

const char* pnp_bus_type_str(BusType type) {
    switch (type) {
        case BUS_TYPE_PCI:    return "PCI";
        case BUS_TYPE_ISA:    return "ISA";
        case BUS_TYPE_USB:    return "USB";
        case BUS_TYPE_SCSI:   return "SCSI";
        case BUS_TYPE_SATA:   return "SATA";
        case BUS_TYPE_NVME:   return "NVMe";
        case BUS_TYPE_VIRTIO: return "VirtIO";
        case BUS_TYPE_CUSTOM: return "Custom";
        default:              return "Unknown";
    }
}

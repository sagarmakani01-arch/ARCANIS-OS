/**
 * pci.h — PCI Device Manager
 *
 * PCI bus enumeration, device discovery, and configuration.
 * Supports standard PCI configuration space access.
 */
#ifndef ARCANIS_PCI_H
#define ARCANIS_PCI_H

#include <arcanis/types.h>

#define PCI_MAX_DEVICES   32
#define PCI_MAX_BUSES     256
#define PCI_MAX_FUNCTIONS 8
#define PCI_CONFIG_ADDR   0xCF8
#define PCI_CONFIG_DATA   0xCFC

/* PCI register offsets */
#define PCI_REG_VENDOR_ID     0x00
#define PCI_REG_DEVICE_ID     0x02
#define PCI_REG_COMMAND       0x04
#define PCI_REG_STATUS        0x06
#define PCI_REG_REVISION_ID   0x08
#define PCI_REG_PROG_IF       0x09
#define PCI_REG_SUBCLASS      0x0A
#define PCI_REG_CLASS         0x0B
#define PCI_REG_CACHE_LINE    0x0C
#define PCI_REG_LATENCY       0x0D
#define PCI_REG_HEADER_TYPE   0x0E
#define PCI_REG_BIST          0x0F
#define PCI_REG_BAR0          0x10
#define PCI_REG_BAR1          0x14
#define PCI_REG_BAR2          0x18
#define PCI_REG_BAR3          0x1C
#define PCI_REG_BAR4          0x20
#define PCI_REG_BAR5          0x24
#define PCI_REG_INTERRUPT_LINE 0x3C
#define PCI_REG_INTERRUPT_PIN  0x3D

/* PCI command bits */
#define PCI_CMD_IO_SPACE      0x0001
#define PCI_CMD_MEMORY_SPACE  0x0002
#define PCI_CMD_BUS_MASTER    0x0004
#define PCI_CMD_INTERRUPT     0x0400

/* Known vendor IDs */
#define PCI_VENDOR_INTEL      0x8086
#define PCI_VENDOR_AMD        0x1022
#define PCI_VENDOR_NVIDIA     0x10DE
#define PCI_VENDOR_VIRTIO     0x1AF4
#define PCI_VENDOR_REALTEK    0x10EC

/* Known device classes */
#define PCI_CLASS_STORAGE     0x01
#define PCI_CLASS_NETWORK     0x02
#define PCI_CLASS_DISPLAY     0x03
#define PCI_CLASS_BRIDGE      0x06
#define PCI_CLASS_SERIAL      0x0C

typedef struct {
    uint16_t vendor_id;
    uint16_t device_id;
    uint8_t  bus;
    uint8_t  device;
    uint8_t  function;
    uint8_t  revision;
    uint8_t  prog_if;
    uint8_t  subclass;
    uint8_t  class_code;
    uint8_t  header_type;
    uint32_t bar[6];
    uint32_t bar_size[6];
    uint8_t  interrupt_line;
    uint8_t  interrupt_pin;
    uint16_t command;
    uint16_t status;
    int      enabled;
    int      is_multifunction;
    char     vendor_name[64];
    char     device_name[128];
    char     class_name[64];
} pci_device_t;

typedef struct {
    pci_device_t devices[PCI_MAX_DEVICES];
    uint32_t     num_devices;
    uint32_t     bus_count;
} pci_state_t;

/* Initialize PCI subsystem */
void pci_init(pci_state_t* pci);

/* Bus enumeration */
int  pci_enumerate(pci_state_t* pci);
int  pci_scan_bus(pci_state_t* pci, uint8_t bus);
int  pci_scan_device(pci_state_t* pci, uint8_t bus, uint8_t device, uint8_t function);

/* Configuration space access */
uint32_t pci_config_read(pci_state_t* pci, uint8_t bus, uint8_t device, uint8_t function, uint8_t reg);
void     pci_config_write(pci_state_t* pci, uint8_t bus, uint8_t device, uint8_t function,
                          uint8_t reg, uint32_t value);

/* Device operations */
int      pci_enable_device(pci_state_t* pci, uint32_t index);
int      pci_set_master(pci_state_t* pci, uint32_t index);
uint32_t pci_get_bar(pci_state_t* pci, uint32_t index, uint32_t bar);
uint32_t pci_get_bar_size(pci_state_t* pci, uint32_t index, uint32_t bar);

/* Find devices */
pci_device_t* pci_find_vendor(pci_state_t* pci, uint16_t vendor_id);
pci_device_t* pci_find_device(pci_state_t* pci, uint16_t vendor_id, uint16_t device_id);
pci_device_t* pci_find_class(pci_state_t* pci, uint8_t class_code, uint8_t subclass);
pci_device_t* pci_get_device(pci_state_t* pci, uint32_t index);

/* Lookup tables */
const char* pci_vendor_name(uint16_t vendor_id);
const char* pci_device_name(uint16_t vendor_id, uint16_t device_id);
const char* pci_class_name(uint8_t class_code, uint8_t subclass);

/* Utilities */
void pci_print_devices(pci_state_t* pci);
uint32_t pci_read_bar_size(pci_state_t* pci, uint8_t bus, uint8_t dev, uint8_t func, uint8_t bar);

#endif

/**
 * pci.c — PCI Device Manager Implementation
 *
 * PCI bus enumeration and configuration space access.
 */
#include <arcanis/pci.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

/* Vendor name lookup */
typedef struct { uint16_t id; const char* name; } pci_vendor_entry_t;
static const pci_vendor_entry_t vendor_table[] = {
    { PCI_VENDOR_INTEL,   "Intel Corporation" },
    { PCI_VENDOR_AMD,     "Advanced Micro Devices" },
    { PCI_VENDOR_NVIDIA,  "NVIDIA Corporation" },
    { PCI_VENDOR_VIRTIO,  "VirtIO" },
    { PCI_VENDOR_REALTEK, "Realtek Semiconductor" },
    { 0x1039, "Silicon Integrated Systems" },
    { 0x1102, "Creative Technology" },
    { 0x1106, "VIA Technologies" },
    { 0x1133, "Digi International" },
    { 0x11AB, "Marvell Technology Group" },
    { 0x13F6, "Thermaltake" },
    { 0x14E4, "Broadcom" },
    { 0x15AD, "VMware" },
    { 0x1B36, "Red Hat" },
    { 0x8087, "Intel (USB)" },
    { 0, NULL }
};

/* Device class names */
static const char* class_names[] = {
    "Unclassified",
    "Mass Storage Controller",
    "Network Controller",
    "Display Controller",
    "Multimedia Controller",
    "Memory Controller",
    "Bridge Device",
    "Communication Controller",
    "System Peripheral",
    "Input Device",
    "Docking Station",
    "Processor",
    "Serial Bus Controller",
    "Wireless Controller",
    "Intelligent Controller",
    "Satellite Controller",
    "Encryption Controller",
    "Signal Processing Controller",
    "Processing Accelerator",
    "Non-Essential Instrumentation"
};

void pci_init(pci_state_t* pci) {
    if (!pci) return;
    memset(pci, 0, sizeof(pci_state_t));
}

/* ---- Configuration space access ---- */

static uint32_t pci_calc_addr(uint8_t bus, uint8_t device, uint8_t function, uint8_t reg) {
    return (1 << 31) |
           ((uint32_t)bus << 16) |
           ((uint32_t)(device & 0x1F) << 11) |
           ((uint32_t)(function & 0x07) << 8) |
           (reg & 0xFC);
}

uint32_t pci_config_read(pci_state_t* pci, uint8_t bus, uint8_t device, uint8_t function, uint8_t reg) {
    /* In real implementation: outl(PCI_CONFIG_ADDR, addr); return inl(PCI_CONFIG_DATA); */
    uint32_t addr = pci_calc_addr(bus, device, function, reg);

    /* Simulated response */
    if (reg == PCI_REG_VENDOR_ID && device < 32) {
        /* Return known devices */
        if (bus == 0 && device == 0) return 0x12341AF4; /* VirtIO */
        if (bus == 0 && device == 1) return 0x00108086; /* Intel E1000 */
        if (bus == 0 && device == 2) return  0x11118086; /* Intel VGA */
        if (bus == 0 && device == 3) return 0x200010DE; /* NVIDIA */
        if (bus == 0 && device == 4) return  0x816810EC; /* Realtek RTL8168 */
    }
    return 0;
}

void pci_config_write(pci_state_t* pci, uint8_t bus, uint8_t device, uint8_t function,
                       uint8_t reg, uint32_t value) {
    /* In real implementation: outl(PCI_CONFIG_ADDR, addr); outl(PCI_CONFIG_DATA, value); */
}

/* ---- Device name lookup ---- */

const char* pci_vendor_name(uint16_t vendor_id) {
    for (int i = 0; vendor_table[i].name; i++)
        if (vendor_table[i].id == vendor_id)
            return vendor_table[i].name;
    return "Unknown Vendor";
}

const char* pci_device_name(uint16_t vendor_id, uint16_t device_id) {
    /* In real implementation: lookup from PCI IDs database */
    if (vendor_id == PCI_VENDOR_INTEL) {
        if (device_id == 0x100E) return "PRO/1000 MT Desktop (82540EM)";
        if (device_id == 0x1237) return "440FX - 82441FX PMC";
        if (device_id == 0x7000) return "82371SB PIIX3 ISA";
        if (device_id == 0x7010) return "82371AB/EB/MB PIIX4 IDE";
        if (device_id == 0x7113) return "82371AB/EB/MB PIIX4 ACPI";
        if (device_id == 0x7110) return "82371AB/EB/MB PIIX4 ISA";
    }
    if (vendor_id == PCI_VENDOR_VIRTIO) {
        if (device_id == 0x0001) return "VirtIO Network Card";
        if (device_id == 0x0002) return "VirtIO Block Device";
        if (device_id == 0x0003) return "VirtIO Console";
    }
    if (vendor_id == PCI_VENDOR_NVIDIA && device_id == 0x0200)
        return "NV3 [Riva 128]";
    if (vendor_id == PCI_VENDOR_REALTEK && device_id == 0x8168)
        return "RTL8111/8168/8411 Gigabit Ethernet";
    return "Unknown Device";
}

const char* pci_class_name(uint8_t class_code, uint8_t subclass) {
    if (class_code < 20) return class_names[class_code];
    return "Unknown Class";
}

/* ---- Bus scanning ---- */

int pci_scan_device(pci_state_t* pci, uint8_t bus, uint8_t device, uint8_t function) {
    if (!pci || pci->num_devices >= PCI_MAX_DEVICES) return -1;

    uint32_t vendor_device = pci_config_read(pci, bus, device, function, PCI_REG_VENDOR_ID);
    uint16_t vendor_id = vendor_device & 0xFFFF;
    if (vendor_id == 0xFFFF) return -1; /* No device */

    pci_device_t* dev = &pci->devices[pci->num_devices];
    memset(dev, 0, sizeof(pci_device_t));

    dev->vendor_id = vendor_id;
    dev->device_id = (vendor_device >> 16) & 0xFFFF;
    dev->bus = bus;
    dev->device = device;
    dev->function = function;

    uint32_t class_rev = pci_config_read(pci, bus, device, function, PCI_REG_REVISION_ID);
    dev->revision = class_rev & 0xFF;
    dev->prog_if = (class_rev >> 8) & 0xFF;
    dev->subclass = (class_rev >> 16) & 0xFF;
    dev->class_code = (class_rev >> 24) & 0xFF;

    uint32_t header = pci_config_read(pci, bus, device, function, PCI_REG_HEADER_TYPE);
    dev->header_type = header & 0xFF;
    dev->is_multifunction = (header & 0x80) != 0;

    /* Read BARs */
    for (int i = 0; i < 6; i++) {
        dev->bar[i] = pci_config_read(pci, bus, device, function, PCI_REG_BAR0 + i * 4);
    }

    /* Read interrupt info */
    uint32_t int_info = pci_config_read(pci, bus, device, function, PCI_REG_INTERRUPT_LINE);
    dev->interrupt_line = int_info & 0xFF;
    dev->interrupt_pin = (int_info >> 8) & 0xFF;

    /* Lookup names */
    string_copy(dev->vendor_name, pci_vendor_name(dev->vendor_id), 64);
    string_copy(dev->device_name, pci_device_name(dev->vendor_id, dev->device_id), 128);
    string_copy(dev->class_name, pci_class_name(dev->class_code, dev->subclass), 64);

    dev->enabled = 1;
    pci->num_devices++;

    /* Scan functions for multifunction devices */
    if (dev->is_multifunction) {
        for (int f = 1; f < PCI_MAX_FUNCTIONS; f++) {
            if (f != function)
                pci_scan_device(pci, bus, device, f);
        }
    }

    return 0;
}

int pci_scan_bus(pci_state_t* pci, uint8_t bus) {
    if (!pci) return -1;

    for (uint8_t device = 0; device < 32; device++) {
        pci_scan_device(pci, bus, device, 0);

        /* Check if multifunction */
        if (pci->num_devices > 0) {
            pci_device_t* last = &pci->devices[pci->num_devices - 1];
            if (last->is_multifunction && last->bus == bus && last->device == device) {
                for (int f = 1; f < PCI_MAX_FUNCTIONS; f++)
                    pci_scan_device(pci, bus, device, f);
            }
        }
    }
    return 0;
}

int pci_enumerate(pci_state_t* pci) {
    if (!pci) return -1;

    pci->num_devices = 0;
    pci_scan_bus(pci, 0);

    /* Check if bus 0 has a multifunction device */
    if (pci->num_devices > 0) {
        pci_device_t* first = &pci->devices[0];
        if (first->is_multifunction) {
            pci->bus_count = 1;
        }
    }

    return 0;
}

/* ---- Device operations ---- */

int pci_enable_device(pci_state_t* pci, uint32_t index) {
    if (!pci || index >= pci->num_devices) return -1;
    pci_device_t* dev = &pci->devices[index];

    uint16_t cmd = pci_config_read(pci, dev->bus, dev->device, dev->function, PCI_REG_COMMAND);
    cmd |= PCI_CMD_IO_SPACE | PCI_CMD_MEMORY_SPACE | PCI_CMD_BUS_MASTER;
    pci_config_write(pci, dev->bus, dev->device, dev->function, PCI_REG_COMMAND, cmd);
    dev->command = cmd;
    dev->enabled = 1;
    return 0;
}

int pci_set_master(pci_state_t* pci, uint32_t index) {
    if (!pci || index >= pci->num_devices) return -1;
    pci_device_t* dev = &pci->devices[index];

    uint16_t cmd = pci_config_read(pci, dev->bus, dev->device, dev->function, PCI_REG_COMMAND);
    cmd |= PCI_CMD_BUS_MASTER;
    pci_config_write(pci, dev->bus, dev->device, dev->function, PCI_REG_COMMAND, cmd);
    dev->command = cmd;
    return 0;
}

uint32_t pci_get_bar(pci_state_t* pci, uint32_t index, uint32_t bar) {
    if (!pci || index >= pci->num_devices || bar >= 6) return 0;
    return pci->devices[index].bar[bar];
}

/* ---- Find devices ---- */

pci_device_t* pci_find_vendor(pci_state_t* pci, uint16_t vendor_id) {
    if (!pci) return NULL;
    for (uint32_t i = 0; i < pci->num_devices; i++)
        if (pci->devices[i].vendor_id == vendor_id)
            return &pci->devices[i];
    return NULL;
}

pci_device_t* pci_find_device(pci_state_t* pci, uint16_t vendor_id, uint16_t device_id) {
    if (!pci) return NULL;
    for (uint32_t i = 0; i < pci->num_devices; i++)
        if (pci->devices[i].vendor_id == vendor_id && pci->devices[i].device_id == device_id)
            return &pci->devices[i];
    return NULL;
}

pci_device_t* pci_find_class(pci_state_t* pci, uint8_t class_code, uint8_t subclass) {
    if (!pci) return NULL;
    for (uint32_t i = 0; i < pci->num_devices; i++)
        if (pci->devices[i].class_code == class_code && pci->devices[i].subclass == subclass)
            return &pci->devices[i];
    return NULL;
}

pci_device_t* pci_get_device(pci_state_t* pci, uint32_t index) {
    if (!pci || index >= pci->num_devices) return NULL;
    return &pci->devices[index];
}

/* ---- Print ---- */

void pci_print_devices(pci_state_t* pci) {
    if (!pci) return;
    for (uint32_t i = 0; i < pci->num_devices; i++) {
        pci_device_t* d = &pci->devices[i];
        /* printf("[%02x:%02x.%x] %s: %s (%04x:%04x) %s\n",
                  d->bus, d->device, d->function,
                  d->class_name, d->device_name,
                  d->vendor_id, d->device_id,
                  d->vendor_name); */
    }
}

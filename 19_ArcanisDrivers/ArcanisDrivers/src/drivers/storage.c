#include "drivers/storage.h"
#include <string.h>

static void storage_select_drive(StorageDriver* storage) {
    #ifdef _WIN32
    __outb(0xA0 | (storage->slave << 4), storage->io_base + ATA_REG_DRIVE_HEAD);
    #endif
}

static uint8_t storage_read_status(StorageDriver* storage) {
    #ifdef _WIN32
    return __inb(storage->io_base + ATA_REG_STATUS);
    #else
    return 0;
    #endif
}

static void storage_write_cmd(StorageDriver* storage, uint8_t cmd) {
    #ifdef _WIN32
    __outb(cmd, storage->io_base + ATA_REG_COMMAND);
    #endif
}

static void storage_write_reg(StorageDriver* storage, uint8_t reg, uint8_t value) {
    #ifdef _WIN32
    __outb(value, storage->io_base + reg);
    #endif
}

static uint8_t storage_read_reg(StorageDriver* storage, uint8_t reg) {
    #ifdef _WIN32
    return __inb(storage->io_base + reg);
    #else
    return 0;
    #endif
}

static void storage_write_pio(StorageDriver* storage, uint16_t value) {
    #ifdef _WIN32
    __outw(value, storage->io_base + ATA_REG_DATA);
    #endif
}

static uint16_t storage_read_pio(StorageDriver* storage) {
    #ifdef _WIN32
    return __inw(storage->io_base + ATA_REG_DATA);
    #else
    return 0;
    #endif
}

static void storage_soft_reset(StorageDriver* storage) {
    #ifdef _WIN32
    __outb(0x04, storage->ctrl_base);
    for (volatile int i = 0; i < 1000; i++);
    __outb(0x00, storage->ctrl_base);
    #endif
}

static void storage_irq_handler(void* data) {
    StorageDriver* storage = (StorageDriver*)data;
    if (storage) {
        storage->irq_received = true;
    }
}

DriverStatus storage_init_driver(StorageDriver* storage, HALContext* hal, uint16_t io_base, uint16_t ctrl_base, uint8_t slave) {
    if (!storage || !hal) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    memset(storage, 0, sizeof(StorageDriver));

    driver_create(&storage->driver, "ata_storage", DRIVER_TYPE_STORAGE, NULL);
    device_create(&storage->device, "storage0", &storage->driver);

    storage->io_base = io_base;
    storage->ctrl_base = ctrl_base;
    storage->slave = slave;
    storage->type = STORAGE_TYPE_HDD;
    storage->interface = STORAGE_INTERFACE_PATA;
    storage->irq = (io_base == ATA_PRIMARY_IO) ? ATA_IRQ_PRIMARY : ATA_IRQ_SECONDARY;
    storage->irq_received = false;

    storage_soft_reset(storage);
    storage_select_drive(storage);

    for (volatile int i = 0; i < 10000; i++);

    if (hal->irq.register_handler) {
        hal->irq.register_handler(storage->irq, storage_irq_handler, storage);
    }

    if (hal->irq.enable_irq) {
        hal->irq.enable_irq(storage->irq);
    }

    device_set_state(&storage->device, DEVICE_STATE_RUNNING);
    storage->initialized = true;

    return DRIVER_STATUS_OK;
}

DriverStatus storage_shutdown_driver(StorageDriver* storage) {
    if (!storage || !storage->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    if (storage->irq != 0) {
        #ifdef _WIN32
        if (storage->io_base == ATA_PRIMARY_IO) {
            __outb(0x02, 0xA1);
        } else {
            __outb(0x02, 0xA1);
        }
        #endif
    }

    device_set_state(&storage->device, DEVICE_STATE_SUSPENDED);
    storage->initialized = false;

    return DRIVER_STATUS_OK;
}

DriverStatus storage_identify(StorageDriver* storage) {
    if (!storage || !storage->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    storage_select_drive(storage);
    storage_write_reg(storage, ATA_REG_SECCOUNT, 0);
    storage_write_reg(storage, ATA_REG_LBA_LOW, 0);
    storage_write_reg(storage, ATA_REG_LBA_MID, 0);
    storage_write_reg(storage, ATA_REG_LBA_HIGH, 0);

    storage_write_cmd(storage, ATA_CMD_IDENTIFY);
    uint8_t status = storage_read_status(storage);

    if (status == 0) {
        storage->info.atapi = false;
        return DRIVER_STATUS_NOT_SUPPORTED;
    }

    while ((status & ATA_STATUS_BSY) && !(status & ATA_STATUS_ERR)) {
        status = storage_read_status(storage);
    }

    if (status & ATA_STATUS_ERR) {
        storage_write_reg(storage, ATA_REG_LBA_MID, 0);
        storage_write_reg(storage, ATA_REG_LBA_HIGH, 0);
        storage_write_cmd(storage, ATA_CMD_IDENTIFY_PACKET);

        for (volatile int i = 0; i < 100000; i++);

        status = storage_read_status(storage);
        if (status & ATA_STATUS_ERR) {
            return DRIVER_STATUS_ERROR;
        }

        storage->info.atapi = true;
        storage->type = STORAGE_TYPE_OPTICAL;
        storage->interface = STORAGE_INTERFACE_PATAPI;
    }

    uint16_t identify_data[256];
    for (int i = 0; i < 256; i++) {
        identify_data[i] = storage_read_pio(storage);
    }

    memcpy(storage->info.model, &identify_data[27], 40);
    storage->info.model[40] = '\0';
    for (int i = 0; i < 40; i += 2) {
        char temp = storage->info.model[i];
        storage->info.model[i] = storage->info.model[i + 1];
        storage->info.model[i + 1] = temp;
    }

    memcpy(storage->info.serial, &identify_data[10], 20);
    storage->info.serial[20] = '\0';
    for (int i = 0; i < 20; i += 2) {
        char temp = storage->info.serial[i];
        storage->info.serial[i] = storage->info.serial[i + 1];
        storage->info.serial[i + 1] = temp;
    }

    memcpy(storage->info.firmware, &identify_data[23], 8);
    storage->info.firmware[8] = '\0';
    for (int i = 0; i < 8; i += 2) {
        char temp = storage->info.firmware[i];
        storage->info.firmware[i] = storage->info.firmware[i + 1];
        storage->info.firmware[i + 1] = temp;
    }

    storage->info.sector_size = SECTOR_SIZE;
    storage->info.cylinders = identify_data[1];
    storage->info.heads = identify_data[3];
    storage->info.sectors_per_track = identify_data[6];

    if (identify_data[83] & 0x0400) {
        storage->info.lba48 = true;
        storage->info.size_sectors = ((uint64_t)identify_data[100] << 32) | identify_data[101];
    } else {
        storage->info.lba48 = false;
        storage->info.size_sectors = ((uint32_t)identify_data[61] << 16) | identify_data[60];
    }

    storage->info.removable = (identify_data[0] & 0x0080) != 0;

    return DRIVER_STATUS_OK;
}

DriverStatus storage_read_sectors(StorageDriver* storage, uint32_t lba, uint32_t count, void* buffer) {
    if (!storage || !buffer || !storage->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (count == 0) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    storage_select_drive(storage);
    storage_wait_ready(storage);

    if (storage->info.lba48) {
        storage_write_reg(storage, ATA_REG_SECCOUNT, (count >> 8) & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_LOW, (lba >> 24) & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_MID, (lba >> 32) & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_HIGH, (lba >> 40) & 0xFF);
        storage_write_reg(storage, ATA_REG_SECCOUNT, count & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_LOW, lba & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_MID, (lba >> 8) & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_HIGH, (lba >> 16) & 0xFF);
        storage_write_cmd(storage, ATA_CMD_READ_PIO_EXT);
    } else {
        storage_write_reg(storage, ATA_REG_SECCOUNT, count & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_LOW, lba & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_MID, (lba >> 8) & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_HIGH, (lba >> 16) & 0xFF);
        storage_write_reg(storage, ATA_REG_DRIVE_HEAD, 0xE0 | (storage->slave << 4) | ((lba >> 24) & 0x0F));
        storage_write_cmd(storage, ATA_CMD_READ_PIO);
    }

    uint16_t* ptr = (uint16_t*)buffer;
    for (uint32_t i = 0; i < count; i++) {
        DriverStatus status = storage_wait_drq(storage);
        if (status != DRIVER_STATUS_OK) {
            return status;
        }

        for (int j = 0; j < 256; j++) {
            ptr[i * 256 + j] = storage_read_pio(storage);
        }

        if (i < count - 1) {
            for (volatile int k = 0; k < 1000; k++);
        }
    }

    return DRIVER_STATUS_OK;
}

DriverStatus storage_write_sectors(StorageDriver* storage, uint32_t lba, uint32_t count, const void* buffer) {
    if (!storage || !buffer || !storage->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (count == 0) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    storage_select_drive(storage);
    storage_wait_ready(storage);

    if (storage->info.lba48) {
        storage_write_reg(storage, ATA_REG_SECCOUNT, (count >> 8) & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_LOW, (lba >> 24) & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_MID, (lba >> 32) & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_HIGH, (lba >> 40) & 0xFF);
        storage_write_reg(storage, ATA_REG_SECCOUNT, count & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_LOW, lba & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_MID, (lba >> 8) & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_HIGH, (lba >> 16) & 0xFF);
        storage_write_cmd(storage, ATA_CMD_WRITE_PIO_EXT);
    } else {
        storage_write_reg(storage, ATA_REG_SECCOUNT, count & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_LOW, lba & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_MID, (lba >> 8) & 0xFF);
        storage_write_reg(storage, ATA_REG_LBA_HIGH, (lba >> 16) & 0xFF);
        storage_write_reg(storage, ATA_REG_DRIVE_HEAD, 0xE0 | (storage->slave << 4) | ((lba >> 24) & 0x0F));
        storage_write_cmd(storage, ATA_CMD_WRITE_PIO);
    }

    const uint16_t* ptr = (const uint16_t*)buffer;
    for (uint32_t i = 0; i < count; i++) {
        DriverStatus status = storage_wait_drq(storage);
        if (status != DRIVER_STATUS_OK) {
            return status;
        }

        for (int j = 0; j < 256; j++) {
            storage_write_pio(storage, ptr[i * 256 + j]);
        }

        #ifdef _WIN32
        __outb(0, storage->io_base + ATA_REG_COMMAND);
        #endif

        for (volatile int k = 0; k < 1000; k++);
    }

    return DRIVER_STATUS_OK;
}

DriverStatus storage_get_info(StorageDriver* storage, StorageInfo* info) {
    if (!storage || !info || !storage->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    *info = storage->info;
    return DRIVER_STATUS_OK;
}

uint64_t storage_get_size(StorageDriver* storage) {
    if (!storage || !storage->initialized) {
        return 0;
    }

    return storage->info.size_sectors * storage->info.sector_size;
}

uint32_t storage_get_sector_size(StorageDriver* storage) {
    if (!storage || !storage->initialized) {
        return 0;
    }

    return storage->info.sector_size;
}

DriverStatus storage_wait_ready(StorageDriver* storage) {
    if (!storage) return DRIVER_STATUS_INVALID_PARAM;

    uint32_t timeout = 1000000;
    while (timeout > 0) {
        uint8_t status = storage_read_status(storage);
        if (!(status & ATA_STATUS_BSY) && (status & ATA_STATUS_RDY)) {
            return DRIVER_STATUS_OK;
        }
        timeout--;
    }

    return DRIVER_STATUS_TIMEOUT;
}

DriverStatus storage_wait_drq(StorageDriver* storage) {
    if (!storage) return DRIVER_STATUS_INVALID_PARAM;

    uint32_t timeout = 1000000;
    while (timeout > 0) {
        uint8_t status = storage_read_status(storage);
        if (status & ATA_STATUS_ERR) {
            return DRIVER_STATUS_ERROR;
        }
        if (status & ATA_STATUS_DF) {
            return DRIVER_STATUS_ERROR;
        }
        if (!(status & ATA_STATUS_BSY) && (status & ATA_STATUS_DRQ)) {
            return DRIVER_STATUS_OK;
        }
        timeout--;
    }

    return DRIVER_STATUS_TIMEOUT;
}

DriverStatus storage_wait_irq(StorageDriver* storage) {
    if (!storage) return DRIVER_STATUS_INVALID_PARAM;

    uint32_t timeout = 1000000;
    while (!storage->irq_received && timeout > 0) {
        timeout--;
    }

    if (storage->irq_received) {
        storage->irq_received = false;
        return DRIVER_STATUS_OK;
    }

    return DRIVER_STATUS_TIMEOUT;
}

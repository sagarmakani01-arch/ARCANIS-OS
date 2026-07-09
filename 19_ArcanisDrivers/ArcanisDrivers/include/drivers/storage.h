#ifndef ARCANIS_STORAGE_H
#define ARCANIS_STORAGE_H

#include "drivers/driver.h"

#define ATA_PRIMARY_IO      0x1F0
#define ATA_PRIMARY_CTRL    0x3F6
#define ATA_SECONDARY_IO    0x170
#define ATA_SECONDARY_CTRL  0x376

#define ATA_REG_DATA        0
#define ATA_REG_ERROR       1
#define ATA_REG_SECCOUNT    2
#define ATA_REG_LBA_LOW    3
#define ATA_REG_LBA_MID    4
#define ATA_REG_LBA_HIGH   5
#define ATA_REG_DRIVE_HEAD 6
#define ATA_REG_STATUS     7
#define ATA_REG_COMMAND    7

#define ATA_STATUS_ERR      0x01
#define ATA_STATUS_DRQ      0x08
#define ATA_STATUS_SRV      0x10
#define ATA_STATUS_DF       0x20
#define ATA_STATUS_RDY      0x40
#define ATA_STATUS_BSY      0x80

#define ATA_CMD_READ_PIO        0x20
#define ATA_CMD_READ_PIO_EXT    0x24
#define ATA_CMD_WRITE_PIO       0x30
#define ATA_CMD_WRITE_PIO_EXT   0x34
#define ATA_CMD_IDENTIFY        0xEC
#define ATA_CMD_IDENTIFY_PACKET 0xA1
#define ATA_CMD_PACKET          0xA0

#define ATA_IRQ_PRIMARY      14
#define ATA_IRQ_SECONDARY    15

#define SECTOR_SIZE         512
#define MAX_STORAGE_DEVICES 4

typedef enum {
    STORAGE_TYPE_HDD = 0,
    STORAGE_TYPE_SSD,
    STORAGE_TYPE_OPTICAL,
    STORAGE_TYPE_FLOPPY,
    STORAGE_TYPE_RAMDISK
} StorageType;

typedef enum {
    STORAGE_INTERFACE_PATA = 0,
    STORAGE_INTERFACE_PATAPI,
    STORAGE_INTERFACE_SATA,
    STORAGE_INTERFACE_SATAPI,
    STORAGE_INTERFACE_NVME,
    STORAGE_INTERFACE_VIRTIO
} StorageInterface;

typedef struct {
    char model[41];
    char serial[21];
    char firmware[9];
    uint64_t size_sectors;
    uint32_t sector_size;
    uint16_t cylinders;
    uint16_t heads;
    uint16_t sectors_per_track;
    bool lba48;
    bool removable;
    bool atapi;
} StorageInfo;

typedef struct {
    Driver driver;
    Device device;
    uint16_t io_base;
    uint16_t ctrl_base;
    uint8_t slave;
    StorageType type;
    StorageInterface interface;
    StorageInfo info;
    uint32_t irq;
    bool irq_received;
    bool initialized;
} StorageDriver;

DriverStatus storage_init_driver(StorageDriver* storage, HALContext* hal, uint16_t io_base, uint16_t ctrl_base, uint8_t slave);
DriverStatus storage_shutdown_driver(StorageDriver* storage);

DriverStatus storage_identify(StorageDriver* storage);
DriverStatus storage_read_sectors(StorageDriver* storage, uint32_t lba, uint32_t count, void* buffer);
DriverStatus storage_write_sectors(StorageDriver* storage, uint32_t lba, uint32_t count, const void* buffer);

DriverStatus storage_get_info(StorageDriver* storage, StorageInfo* info);
uint64_t storage_get_size(StorageDriver* storage);
uint32_t storage_get_sector_size(StorageDriver* storage);

DriverStatus storage_wait_ready(StorageDriver* storage);
DriverStatus storage_wait_drq(StorageDriver* storage);
DriverStatus storage_wait_irq(StorageDriver* storage);

#endif
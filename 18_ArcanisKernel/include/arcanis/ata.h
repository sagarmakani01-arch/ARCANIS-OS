#ifndef ARCANIS_ATA_H
#define ARCANIS_ATA_H

#include <arcanis/types.h>

/* ATA I/O ports */
#define ATA_PRIMARY_DATA      0x1F0
#define ATA_PRIMARY_ERROR     0x1F1
#define ATA_PRIMARY_SECCOUNT  0x1F2
#define ATA_PRIMARY_LBA_LO    0x1F3
#define ATA_PRIMARY_LBA_MID   0x1F4
#define ATA_PRIMARY_LBA_HI    0x1F5
#define ATA_PRIMARY_DRIVE     0x1F6
#define ATA_PRIMARY_STATUS    0x1F7
#define ATA_PRIMARY_COMMAND   0x1F7

#define ATA_SECONDARY_DATA    0x170
#define ATA_SECONDARY_ERROR   0x171
#define ATA_SECONDARY_STATUS  0x177

/* Status bits */
#define ATA_SR_BSY   0x80
#define ATA_SR_DRDY  0x40
#define ATA_SR_DRQ   0x08
#define ATA_SR_ERR   0x01

/* Commands */
#define ATA_CMD_READ    0x20
#define ATA_CMD_WRITE   0x30
#define ATA_CMD_IDENTIFY 0xEC

#define ATA_SECTOR_SIZE 512

typedef struct {
    uint16_t base_port;
    uint16_t control_port;
    uint8_t  slave;       /* 0 = master, 1 = slave */
    uint8_t  present;
    uint32_t sectors;
    char     model[41];
} ata_drive_t;

void     ata_initialize(void);
int      ata_read_sectors(ata_drive_t* drive, uint32_t lba, uint32_t count, uint8_t* buf);
int      ata_write_sectors(ata_drive_t* drive, uint32_t lba, uint32_t count, const uint8_t* buf);
ata_drive_t* ata_get_drive(uint8_t index);

#endif

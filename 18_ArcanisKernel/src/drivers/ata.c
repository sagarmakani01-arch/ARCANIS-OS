/**
 * ata.c — ATA/IDE Disk Driver
 *
 * PIO-mode driver for primary/secondary ATA controllers.
 * Supports LBA28 read/write and drive identification.
 */
#include <arcanis/ata.h>
#include <arcanis/io.h>
#include <arcanis/string.h>
#include <arcanis/timer.h>

static ata_drive_t drives[4];

static void ata_delay(uint16_t port) {
    inb(port);
    inb(port);
    inb(port);
    inb(port);
}

static int ata_wait_ready(uint16_t port) {
    uint8_t status;
    int timeout = 100000;
    while (timeout--) {
        status = inb(port + ATA_PRIMARY_STATUS - ATA_PRIMARY_DATA);
        if (!(status & ATA_SR_BSY)) return 0;
    }
    return -1;
}

static int ata_wait_drq(uint16_t port) {
    uint8_t status;
    int timeout = 100000;
    while (timeout--) {
        status = inb(port + ATA_PRIMARY_STATUS - ATA_PRIMARY_DATA);
        if (status & ATA_SR_DRQ) return 0;
        if (status & ATA_SR_ERR) return -1;
    }
    return -1;
}

static void ata_select_drive(uint16_t port, uint8_t slave) {
    outb(port + ATA_PRIMARY_DRIVE - ATA_PRIMARY_DATA, 0xA0 | (slave << 4));
    ata_delay(port);
}

static int ata_identify(uint16_t port, uint8_t slave, ata_drive_t* drive) {
    ata_select_drive(port, slave);
    outb(port + ATA_PRIMARY_COMMAND - ATA_PRIMARY_DATA, ATA_CMD_IDENTIFY);
    ata_delay(port);

    uint8_t status = inb(port + ATA_PRIMARY_STATUS - ATA_PRIMARY_DATA);
    if (status == 0) return -1; /* No drive */

    if (ata_wait_ready(port) != 0) return -1;
    if (ata_wait_drq(port) != 0) return -1;

    uint16_t identify_data[256];
    for (int i = 0; i < 256; i++) {
        identify_data[i] = inw(port + ATA_PRIMARY_DATA);
    }

    /* Extract model name (offset 27-46, swapped bytes) */
    for (int i = 0; i < 20; i++) {
        drive->model[i * 2] = (char)(identify_data[27 + i] & 0xFF);
        drive->model[i * 2 + 1] = (char)(identify_data[27 + i] >> 8);
    }
    drive->model[40] = '\0';

    /* Extract sector count (LBA28) */
    drive->sectors = *(uint32_t*)&identify_data[60];

    drive->base_port = port;
    drive->control_port = port + 0x200;
    drive->slave = slave;
    drive->present = 1;

    return 0;
}

void ata_initialize(void) {
    memset(drives, 0, sizeof(drives));

    /* Try primary controller, master */
    ata_identify(ATA_PRIMARY_DATA, 0, &drives[0]);
    /* Try primary controller, slave */
    ata_identify(ATA_PRIMARY_DATA, 1, &drives[1]);
    /* Try secondary controller, master */
    ata_identify(ATA_SECONDARY_DATA, 0, &drives[2]);
    /* Try secondary controller, slave */
    ata_identify(ATA_SECONDARY_DATA, 1, &drives[3]);
}

int ata_read_sectors(ata_drive_t* drive, uint32_t lba, uint32_t count, uint8_t* buf) {
    if (!drive || !drive->present || !buf) return -1;

    uint16_t port = drive->base_port;

    /* Select drive */
    ata_select_drive(port, drive->slave);

    /* Set sector count */
    outb(port + ATA_PRIMARY_SECCOUNT - ATA_PRIMARY_DATA, (uint8_t)count);

    /* Set LBA address */
    outb(port + ATA_PRIMARY_LBA_LO - ATA_PRIMARY_DATA, (uint8_t)(lba & 0xFF));
    outb(port + ATA_PRIMARY_LBA_MID - ATA_PRIMARY_DATA, (uint8_t)((lba >> 8) & 0xFF));
    outb(port + ATA_PRIMARY_LBA_HI - ATA_PRIMARY_DATA, (uint8_t)((lba >> 16) & 0xFF));
    outb(port + ATA_PRIMARY_DRIVE - ATA_PRIMARY_DATA, 0xE0 | (drive->slave << 4) | ((lba >> 24) & 0x0F));

    /* Send read command */
    outb(port + ATA_PRIMARY_COMMAND - ATA_PRIMARY_DATA, ATA_CMD_READ);

    /* Read sectors */
    for (uint32_t s = 0; s < count; s++) {
        if (ata_wait_ready(port) != 0) return -1;
        if (ata_wait_drq(port) != 0) return -1;

        /* Read 256 words (512 bytes) */
        for (int i = 0; i < 256; i++) {
            uint16_t word = inw(port + ATA_PRIMARY_DATA);
            buf[s * ATA_SECTOR_SIZE + i * 2] = word & 0xFF;
            buf[s * ATA_SECTOR_SIZE + i * 2 + 1] = (word >> 8) & 0xFF;
        }
    }

    return 0;
}

int ata_write_sectors(ata_drive_t* drive, uint32_t lba, uint32_t count, const uint8_t* buf) {
    if (!drive || !drive->present || !buf) return -1;

    uint16_t port = drive->base_port;

    /* Select drive */
    ata_select_drive(port, drive->slave);

    /* Set sector count */
    outb(port + ATA_PRIMARY_SECCOUNT - ATA_PRIMARY_DATA, (uint8_t)count);

    /* Set LBA address */
    outb(port + ATA_PRIMARY_LBA_LO - ATA_PRIMARY_DATA, (uint8_t)(lba & 0xFF));
    outb(port + ATA_PRIMARY_LBA_MID - ATA_PRIMARY_DATA, (uint8_t)((lba >> 8) & 0xFF));
    outb(port + ATA_PRIMARY_LBA_HI - ATA_PRIMARY_DATA, (uint8_t)((lba >> 16) & 0xFF));
    outb(port + ATA_PRIMARY_DRIVE - ATA_PRIMARY_DATA, 0xE0 | (drive->slave << 4) | ((lba >> 24) & 0x0F));

    /* Send write command */
    outb(port + ATA_PRIMARY_COMMAND - ATA_PRIMARY_DATA, ATA_CMD_WRITE);

    /* Write sectors */
    for (uint32_t s = 0; s < count; s++) {
        if (ata_wait_ready(port) != 0) return -1;
        if (ata_wait_drq(port) != 0) return -1;

        /* Write 256 words (512 bytes) */
        for (int i = 0; i < 256; i++) {
            uint16_t word = buf[s * ATA_SECTOR_SIZE + i * 2] | (buf[s * ATA_SECTOR_SIZE + i * 2 + 1] << 8);
            outw(port + ATA_PRIMARY_DATA, word);
        }

        /* Flush */
        outb(port + ATA_PRIMARY_COMMAND - ATA_PRIMARY_DATA, ATA_CMD_WRITE);
    }

    return 0;
}

ata_drive_t* ata_get_drive(uint8_t index) {
    if (index >= 4) return NULL;
    return drives[index].present ? &drives[index] : NULL;
}

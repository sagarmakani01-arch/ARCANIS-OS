#include "drivers/network.h"
#include <string.h>
#include <stdio.h>

#define NE2000_IO_BASE      0x300
#define NE2000_IRQ          10

#define NE2000_CMD          0x00
#define NE2000_PSTART       0x01
#define NE2000_PSTOP        0x02
#define NE2000_BNRY         0x03
#define NE2000_TSR          0x04
#define NE2000_TPSR         0x04
#define NE2000_TBCR0        0x05
#define NE2000_TBCR1        0x06
#define NE2000_ISR          0x07
#define NE2000_RBCR0        0x0A
#define NE2000_RBCR1        0x0B
#define NE2000_RSR          0x0C
#define NE2000_RCR          0x0C
#define NE2000_CURR         0x07
#define NE2000_DCR          0x0E
#define NE2000_IMR          0x0F
#define NE2000_EN0_DUR      0x01

#define NE2000_CMD_STOP     0x01
#define NE2000_CMD_START    0x02
#define NE2000_CMD_TRANS    0x04
#define NE2000_CMD_RREAD    0x08
#define NE2000_CMD_RWRITE   0x10
#define NE2000_CMD_NODMA    0x20

#define NE2000_ISR_PRX      0x01
#define NE2000_ISR_PTX      0x02
#define NE2000_ISR_RXE      0x04
#define NE2000_ISR_TXE      0x08
#define NE2000_ISR_OVW      0x10
#define NE2000_ISR_CDC      0x20
#define NE2000_ISR_RDC      0x40
#define NE2000_ISR_RESET    0x80

static void ne2000_write(NetworkDriver* net, uint16_t reg, uint8_t value) {
    #ifdef _WIN32
    __outb(value, net->io_base + reg);
    #endif
}

static uint8_t ne2000_read(NetworkDriver* net, uint16_t reg) {
    #ifdef _WIN32
    return __inb(net->io_base + reg);
    #else
    return 0;
    #endif
}

static void ne2000_select_page(NetworkDriver* net, uint8_t page) {
    ne2000_write(net, NE2000_CMD, NE2000_CMD_STOP | (page << 6));
}

static void ne2000_read_mac(NetworkDriver* net) {
    ne2000_select_page(net, 1);

    ne2000_write(net, NE2000_RBCR0, 0);
    ne2000_write(net, NE2000_RBCR1, 0);
    ne2000_write(net, NE2000_RSAR0, 0);
    ne2000_write(net, NE2000_RSAR1, 0);
    ne2000_write(net, NE2000_CMD, NE2000_CMD_RREAD | NE2000_CMD_START);

    for (int i = 0; i < NET_MAC_SIZE; i++) {
        net->config.mac[i] = ne2000_read(net, NE2000_EN0_DUR);
    }

    ne2000_select_page(net, 0);
}

static void network_irq_handler(void* data) {
    NetworkDriver* net = (NetworkDriver*)data;
    if (!net || !net->initialized) return;

    uint8_t isr = ne2000_read(net, NE2000_ISR);

    if (isr & NE2000_ISR_PRX) {
        ne2000_write(net, NE2000_ISR, NE2000_ISR_PRX);

        ne2000_select_page(net, 0);
        uint8_t bnry = ne2000_read(net, NE2000_BNRY);
        ne2000_select_page(net, 1);
        uint8_t curr = ne2000_read(net, NE2000_CURR);

        while (bnry != curr) {
            bnry = (bnry + 1) % 128;
            if (bnry == 0) bnry = 1;

            ne2000_select_page(net, 0);
            ne2000_write(net, NE2000_RBCR0, 4);
            ne2000_write(net, NE2000_RBCR1, 0);
            ne2000_write(net, NE2000_RSAR0, bnry);
            ne2000_write(net, NE2000_RSAR1, 0);
            ne2000_write(net, NE2000_CMD, NE2000_CMD_RREAD | NE2000_CMD_START);

            uint8_t header[4];
            for (int i = 0; i < 4; i++) {
                header[i] = ne2000_read(net, NE2000_EN0_DUR);
            }

            uint16_t pkt_len = (header[2] | (header[3] << 8)) - 4;

            if (pkt_len > 0 && pkt_len < NET_MAX_PACKET) {
                ne2000_write(net, NE2000_RBCR0, pkt_len & 0xFF);
                ne2000_write(net, NE2000_RBCR1, (pkt_len >> 8) & 0xFF);
                ne2000_write(net, NE2000_RSAR0, bnry + 4);
                ne2000_write(net, NE2000_RSAR1, 0);
                ne2000_write(net, NE2000_CMD, NE2000_CMD_RREAD | NE2000_CMD_START);

                uint8_t packet[NET_MAX_PACKET];
                for (uint32_t i = 0; i < pkt_len; i++) {
                    packet[i] = ne2000_read(net, NE2000_EN0_DUR);
                }

                if (net->callback) {
                    NetworkEvent event = {
                        .type = NET_EVENT_RX,
                        .data_len = pkt_len
                    };
                    memcpy(event.data, packet, pkt_len);
                    net->callback(&event, net->callback_data);
                }

                net->rx_packets++;
            }
        }

        ne2000_select_page(net, 0);
        ne2000_write(net, NE2000_BNRY, curr - 1);
    }

    if (isr & NE2000_ISR_PTX) {
        ne2000_write(net, NE2000_ISR, NE2000_ISR_PTX);
        net->tx_busy = false;

        if (net->callback) {
            NetworkEvent event = {
                .type = NET_EVENT_TX_COMPLETE,
                .data_len = 0
            };
            net->callback(&event, net->callback_data);
        }
    }

    if (isr & NE2000_ISR_RXE) {
        ne2000_write(net, NE2000_ISR, NE2000_ISR_RXE);
        net->rx_errors++;
    }

    if (isr & NE2000_ISR_TXE) {
        ne2000_write(net, NE2000_ISR, NE2000_ISR_TXE);
        net->tx_errors++;
    }
}

DriverStatus network_init_driver(NetworkDriver* net, HALContext* hal, uint16_t io_base, uint32_t irq) {
    if (!net || !hal) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    memset(net, 0, sizeof(NetworkDriver));

    driver_create(&net->driver, "ne2000_network", DRIVER_TYPE_NETWORK, NULL);
    device_create(&net->device, "net0", &net->driver);

    ringbuffer_init(&net->rx_buffer, net->rx_buffer_data, NET_BUFFER_SIZE);
    ringbuffer_init(&net->tx_buffer, net->tx_buffer_data, NET_BUFFER_SIZE);

    net->hal = hal;
    net->type = NET_TYPE_ETHERNET;
    net->io_base = io_base;
    net->irq = irq;
    net->state = NET_STATE_DOWN;
    net->tx_busy = false;
    net->link_up = false;
    net->link_speed = 10;

    ne2000_write(net, NE2000_CMD, NE2000_CMD_STOP | NE2000_CMD_NODMA);

    ne2000_write(net, NE2000_DCR, 0x58);
    ne2000_write(net, NE2000_RBCR0, 0);
    ne2000_write(net, NE2000_RBCR1, 0);
    ne2000_write(net, NE2000_ISR, 0xFF);
    ne2000_write(net, NE2000_IMR, 0x00);
    ne2000_write(net, NE2000_RCR, 0x20);
    ne2000_write(net, NE2000_TPSR, 0x40);
    ne2000_write(net, NE2000_PSTART, 0x4C);
    ne2000_write(net, NE2000_PSTOP, 0x80);
    ne2000_write(net, NE2000_BNRY, 0x4C);

    ne2000_select_page(net, 1);
    ne2000_write(net, NE2000_CURR, 0x4D);
    ne2000_write(net, NE2000_MAR0, 0x00);
    ne2000_write(net, NE2000_MAR1, 0x00);
    ne2000_write(net, NE2000_MAR2, 0x00);
    ne2000_write(net, NE2000_MAR3, 0x00);
    ne2000_write(net, NE2000_MAR4, 0x00);
    ne2000_write(net, NE2000_MAR5, 0x00);
    ne2000_write(net, NE2000_MAR6, 0x00);
    ne2000_write(net, NE2000_MAR7, 0x00);

    ne2000_select_page(net, 0);
    ne2000_read_mac(net);

    ne2000_write(net, NE2000_RCR, 0x04);
    ne2000_write(net, NE2000_CMD, NE2000_CMD_START | NE2000_CMD_NODMA);
    ne2000_write(net, NE2000_ISR, 0xFF);
    ne2000_write(net, NE2000_IMR, 0x15);

    if (hal->irq.register_handler) {
        hal->irq.register_handler(net->irq, network_irq_handler, net);
    }

    if (hal->irq.enable_irq) {
        hal->irq.enable_irq(net->irq);
    }

    net->state = NET_STATE_UP;
    net->link_up = true;

    device_set_state(&net->device, DEVICE_STATE_RUNNING);
    net->initialized = true;

    return DRIVER_STATUS_OK;
}

DriverStatus network_shutdown_driver(NetworkDriver* net) {
    if (!net || !net->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    ne2000_write(net, NE2000_IMR, 0x00);
    ne2000_write(net, NE2000_CMD, NE2000_CMD_STOP | NE2000_CMD_NODMA);

    if (net->hal->irq.disable_irq) {
        net->hal->irq.disable_irq(net->irq);
    }

    if (net->hal->irq.unregister_handler) {
        net->hal->irq.unregister_handler(net->irq);
    }

    net->state = NET_STATE_DOWN;
    device_set_state(&net->device, DEVICE_STATE_SUSPENDED);
    net->initialized = false;

    return DRIVER_STATUS_OK;
}

DriverStatus network_get_mac(NetworkDriver* net, uint8_t* mac) {
    if (!net || !mac || !net->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    memcpy(mac, net->config.mac, NET_MAC_SIZE);
    return DRIVER_STATUS_OK;
}

DriverStatus network_set_mac(NetworkDriver* net, const uint8_t* mac) {
    if (!net || !mac || !net->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    memcpy(net->config.mac, mac, NET_MAC_SIZE);
    return DRIVER_STATUS_OK;
}

DriverStatus network_set_ip(NetworkDriver* net, uint32_t ip, uint32_t subnet, uint32_t gateway) {
    if (!net || !net->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    net->config.ip = ip;
    net->config.subnet = subnet;
    net->config.gateway = gateway;

    return DRIVER_STATUS_OK;
}

DriverStatus network_get_config(NetworkDriver* net, NetworkConfig* config) {
    if (!net || !config || !net->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    *config = net->config;
    return DRIVER_STATUS_OK;
}

DriverStatus network_send_packet(NetworkDriver* net, const void* data, uint32_t len) {
    if (!net || !data || !net->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (len > NET_MAX_PACKET || net->tx_busy) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    net->tx_busy = true;

    ne2000_write(net, NE2000_RBCR0, len & 0xFF);
    ne2000_write(net, NE2000_RBCR1, (len >> 8) & 0xFF);
    ne2000_write(net, NE2000_RSAR0, 0x00);
    ne2000_write(net, NE2000_RSAR1, 0x40);
    ne2000_write(net, NE2000_CMD, NE2000_CMD_RWRITE | NE2000_CMD_START);

    const uint8_t* pkt = (const uint8_t*)data;
    for (uint32_t i = 0; i < len; i++) {
        ne2000_write(net, NE2000_EN0_DUR, pkt[i]);
    }

    ne2000_write(net, NE2000_TPSR, 0x40);
    ne2000_write(net, NE2000_TBCR0, len & 0xFF);
    ne2000_write(net, NE2000_TBCR1, (len >> 8) & 0xFF);
    ne2000_write(net, NE2000_CMD, NE2000_CMD_TRANS | NE2000_CMD_START);

    net->tx_packets++;

    return DRIVER_STATUS_OK;
}

DriverStatus network_receive_packet(NetworkDriver* net, void* data, uint32_t len, uint32_t* received) {
    if (!net || !data || !net->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    uint32_t read_len = 0;
    ringbuffer_read(&net->rx_buffer, (uint8_t*)data, len, &read_len);

    if (received) {
        *received = read_len;
    }

    return read_len > 0 ? DRIVER_STATUS_OK : DRIVER_STATUS_NOT_READY;
}

DriverStatus network_set_callback(NetworkDriver* net, NetworkCallback callback, void* user_data) {
    if (!net || !net->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    net->callback = callback;
    net->callback_data = user_data;

    return DRIVER_STATUS_OK;
}

NetworkState network_get_state(NetworkDriver* net) {
    return net ? net->state : NET_STATE_DOWN;
}

bool network_is_linked(NetworkDriver* net) {
    return net ? net->link_up : false;
}

uint16_t network_calc_checksum(const void* data, uint32_t len) {
    const uint16_t* ptr = (const uint16_t*)data;
    uint32_t sum = 0;

    while (len > 1) {
        sum += *ptr++;
        len -= 2;
    }

    if (len > 0) {
        sum += *(const uint8_t*)ptr;
    }

    sum = (sum >> 16) + (sum & 0xFFFF);
    sum += (sum >> 16);

    return (uint16_t)(~sum);
}

void network_set_mac_addr(uint8_t* dest, const uint8_t* src) {
    memcpy(dest, src, NET_MAC_SIZE);
}

bool network_cmp_mac(const uint8_t* mac1, const uint8_t* mac2) {
    return memcmp(mac1, mac2, NET_MAC_SIZE) == 0;
}

void network_ip_to_str(uint32_t ip, char* str) {
    if (!str) return;
    sprintf(str, "%d.%d.%d.%d",
            ip & 0xFF,
            (ip >> 8) & 0xFF,
            (ip >> 16) & 0xFF,
            (ip >> 24) & 0xFF);
}

uint32_t network_str_to_ip(const char* str) {
    if (!str) return 0;

    uint32_t ip = 0;
    uint32_t octet = 0;
    int shift = 0;

    while (*str && shift < 32) {
        if (*str >= '0' && *str <= '9') {
            octet = octet * 10 + (*str - '0');
        } else if (*str == '.') {
            ip |= (octet << shift);
            shift += 8;
            octet = 0;
        }
        str++;
    }

    ip |= (octet << shift);
    return ip;
}

#include "arcanis_drivers.h"
#include <stdio.h>
#include <string.h>

static void on_keyboard_event(KeyboardEvent* event, void* user_data) {
    (void)user_data;
    if (event->type == KB_EVENT_KEY_PRESSED) {
        if (event->ctrl && event->alt && event->key == KEY_DELETE) {
            printf("Ctrl+Alt+Delete detected!\n");
        }
    }
}

static void on_mouse_event(MouseEvent* event, void* user_data) {
    (void)user_data;
    if (event->type == MOUSE_EVENT_MOVE) {
        printf("Mouse moved to (%d, %d)\n", event->x, event->y);
    }
}

static void on_network_event(NetworkEvent* event, void* user_data) {
    (void)user_data;
    if (event->type == NET_EVENT_RX && event->data_len >= 14) {
        EthernetHeader* eth = (EthernetHeader*)event->data;
        printf("Packet received: %02X:%02X:%02X:%02X:%02X:%02X -> %02X:%02X:%02X:%02X:%02X:%02X\n",
               eth->src_mac[0], eth->src_mac[1], eth->src_mac[2],
               eth->src_mac[3], eth->src_mac[4], eth->src_mac[5],
               eth->dest_mac[0], eth->dest_mac[1], eth->dest_mac[2],
               eth->dest_mac[3], eth->dest_mac[4], eth->dest_mac[5]);
    }
}

int main(void) {
    ArcanisDrivers ctx;
    DriverStatus status;

    arcanis_drivers_print_info();
    printf("\n");

    printf("Initializing ArcanisDrivers...\n");
    status = arcanis_drivers_init(&ctx);
    if (status != DRIVER_STATUS_OK) {
        printf("Failed to initialize: %s\n", driver_status_str(status));
        return 1;
    }

    printf("\nEnumerating devices...\n");
    arcanis_drivers_enumerate(&ctx);

    printf("\nConfiguring drivers...\n");

    keyboard_set_callback(&ctx.keyboard, on_keyboard_event, &ctx);
    mouse_set_callback(&ctx.mouse, on_mouse_event, &ctx);
    network_set_callback(&ctx.network, on_network_event, &ctx);

    uint32_t width, height, bpp;
    display_get_resolution(&ctx.display, &width, &height, &bpp);
    printf("Display: %ux%u @ %u bpp\n", width, height, bpp);

    StorageInfo storage_info;
    if (storage_get_info(&ctx.storage, &storage_info) == DRIVER_STATUS_OK) {
        printf("Storage: %s (%llu bytes)\n", storage_info.model,
               (unsigned long long)(storage_info.size_sectors * storage_info.sector_size));
    }

    uint8_t mac[NET_MAC_SIZE];
    if (network_get_mac(&ctx.network, mac) == DRIVER_STATUS_OK) {
        char ip_str[16];
        NetworkConfig net_cfg;
        network_get_config(&ctx.network, &net_cfg);
        network_ip_to_str(net_cfg.ip, ip_str);
        printf("Network: MAC %02X:%02X:%02X:%02X:%02X:%02X, IP %s\n",
               mac[0], mac[1], mac[2], mac[3], mac[4], mac[5], ip_str);
    }

    printf("\nDriver subsystem running. Press any key to exit.\n");

    printf("\nShutting down...\n");
    arcanis_drivers_shutdown(&ctx);

    printf("ArcanisDrivers shutdown complete.\n");
    return 0;
}

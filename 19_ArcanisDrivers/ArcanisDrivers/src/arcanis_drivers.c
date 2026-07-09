#include "arcanis_drivers.h"
#include <string.h>
#include <stdio.h>

static uint8_t memory_pool_data[64 * 1024];

static void arcanis_device_event_handler(DriverEvent* event, void* user_data) {
    ArcanisDrivers* ctx = (ArcanisDrivers*)user_data;
    if (!ctx) return;

    switch (event->type) {
        case EVENT_DEVICE_CONNECTED:
            printf("[ArcanisDrivers] Device connected: Vendor 0x%04X, Device 0x%04X\n",
                   event->data[0], event->data[1]);
            break;
        case EVENT_DEVICE_DISCONNECTED:
            printf("[ArcanisDrivers] Device disconnected: Vendor 0x%04X, Device 0x%04X\n",
                   event->data[0], event->data[1]);
            break;
        case EVENT_DEVICE_READY:
            printf("[ArcanisDrivers] Device ready\n");
            break;
        case EVENT_DEVICE_ERROR:
            printf("[ArcanisDrivers] Device error\n");
            break;
        default:
            break;
    }
}

static void arcanis_keyboard_handler(KeyboardEvent* event, void* user_data) {
    (void)user_data;
    if (event->type == KB_EVENT_KEY_PRESSED) {
        printf("[Keyboard] Key pressed: %s\n", key_code_to_string(event->key));
    }
}

static void arcanis_mouse_handler(MouseEvent* event, void* user_data) {
    (void)user_data;
    switch (event->type) {
        case MOUSE_EVENT_MOVE:
            break;
        case MOUSE_EVENT_BUTTON_PRESSED:
            printf("[Mouse] Button pressed: %d\n", event->button);
            break;
        case MOUSE_EVENT_BUTTON_RELEASED:
            printf("[Mouse] Button released: %d\n", event->button);
            break;
        default:
            break;
    }
}

static void arcanis_display_handler(DisplayEvent* event, void* user_data) {
    (void)user_data;
    switch (event->type) {
        case DISPLAY_EVENT_MODE_CHANGED:
            printf("[Display] Mode changed: %ux%u\n", event->width, event->height);
            break;
        case DISPLAY_EVENT_BUFFER_FLUSH:
            break;
        default:
            break;
    }
}

static void arcanis_network_handler(NetworkEvent* event, void* user_data) {
    (void)user_data;
    switch (event->type) {
        case NET_EVENT_RX:
            printf("[Network] Packet received: %u bytes\n", event->data_len);
            break;
        case NET_EVENT_TX_COMPLETE:
            printf("[Network] Transmission complete\n");
            break;
        case NET_EVENT_LINK_UP:
            printf("[Network] Link up\n");
            break;
        case NET_EVENT_LINK_DOWN:
            printf("[Network] Link down\n");
            break;
        default:
            break;
    }
}

DriverStatus arcanis_drivers_init(ArcanisDrivers* ctx) {
    if (!ctx) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    memset(ctx, 0, sizeof(ArcanisDrivers));

    printf("[ArcanisDrivers] Initializing driver subsystem...\n");

    DriverStatus status = hal_init(&ctx->hal);
    if (status != DRIVER_STATUS_OK) {
        printf("[ArcanisDrivers] Failed to initialize HAL: %s\n", driver_status_str(status));
        return status;
    }
    printf("[ArcanisDrivers] HAL initialized\n");

    memory_init(&ctx->memory);
    status = memory_pool_create(&ctx->memory, memory_pool_data, sizeof(memory_pool_data), 64);
    if (status != DRIVER_STATUS_OK) {
        printf("[ArcanisDrivers] Failed to create memory pool: %s\n", driver_status_str(status));
        return status;
    }
    printf("[ArcanisDrivers] Memory pool created\n");

    status = pnp_init(&ctx->pnp, &ctx->hal);
    if (status != DRIVER_STATUS_OK) {
        printf("[ArcanisDrivers] Failed to initialize PnP: %s\n", driver_status_str(status));
        return status;
    }
    printf("[ArcanisDrivers] PnP system initialized\n");

    event_subscribe(&ctx->pnp.events, arcanis_device_event_handler, ctx, NULL);

    status = keyboard_init_driver(&ctx->keyboard, &ctx->hal);
    if (status != DRIVER_STATUS_OK) {
        printf("[ArcanisDrivers] Failed to initialize keyboard driver: %s\n", driver_status_str(status));
    } else {
        keyboard_set_callback(&ctx->keyboard, arcanis_keyboard_handler, ctx);
        printf("[ArcanisDrivers] Keyboard driver initialized\n");
    }

    status = mouse_init_driver(&ctx->mouse, &ctx->hal);
    if (status != DRIVER_STATUS_OK) {
        printf("[ArcanisDrivers] Failed to initialize mouse driver: %s\n", driver_status_str(status));
    } else {
        mouse_set_callback(&ctx->mouse, arcanis_mouse_handler, ctx);
        printf("[ArcanisDrivers] Mouse driver initialized\n");
    }

    status = display_init_driver(&ctx->display, &ctx->hal);
    if (status != DRIVER_STATUS_OK) {
        printf("[ArcanisDrivers] Failed to initialize display driver: %s\n", driver_status_str(status));
    } else {
        display_set_callback(&ctx->display, arcanis_display_handler, ctx);
        printf("[ArcanisDrivers] Display driver initialized\n");
    }

    status = storage_init_driver(&ctx->storage, &ctx->hal, 0x1F0, 0x3F6, 0);
    if (status != DRIVER_STATUS_OK) {
        printf("[ArcanisDrivers] Failed to initialize storage driver: %s\n", driver_status_str(status));
    } else {
        storage_identify(&ctx->storage);
        printf("[ArcanisDrivers] Storage driver initialized\n");
    }

    status = network_init_driver(&ctx->network, &ctx->hal, 0x300, 10);
    if (status != DRIVER_STATUS_OK) {
        printf("[ArcanisDrivers] Failed to initialize network driver: %s\n", driver_status_str(status));
    } else {
        network_set_callback(&ctx->network, arcanis_network_handler, ctx);
        printf("[ArcanisDrivers] Network driver initialized\n");
    }

    ctx->initialized = true;
    printf("[ArcanisDrivers] All drivers initialized successfully\n");

    return DRIVER_STATUS_OK;
}

DriverStatus arcanis_drivers_shutdown(ArcanisDrivers* ctx) {
    if (!ctx || !ctx->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    printf("[ArcanisDrivers] Shutting down driver subsystem...\n");

    network_shutdown_driver(&ctx->network);
    storage_shutdown_driver(&ctx->storage);
    display_shutdown_driver(&ctx->display);
    mouse_shutdown_driver(&ctx->mouse);
    keyboard_shutdown_driver(&ctx->keyboard);

    pnp_shutdown(&ctx->pnp);
    hal_shutdown(&ctx->hal);

    ctx->initialized = false;
    printf("[ArcanisDrivers] Driver subsystem shut down\n");

    return DRIVER_STATUS_OK;
}

DriverStatus arcanis_drivers_enumerate(ArcanisDrivers* ctx) {
    if (!ctx || !ctx->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    printf("[ArcanisDrivers] Enumerating devices...\n");

    DriverStatus status = pnp_scan_bus(&ctx->pnp);
    if (status != DRIVER_STATUS_OK) {
        printf("[ArcanisDrivers] Failed to scan bus: %s\n", driver_status_str(status));
        return status;
    }

    uint32_t count = pnp_get_device_count(&ctx->pnp);
    printf("[ArcanisDrivers] Found %u devices\n", count);

    for (uint32_t i = 0; i < count; i++) {
        PnPDevice dev;
        if (pnp_get_device_info(&ctx->pnp, i, &dev) == DRIVER_STATUS_OK) {
            printf("[ArcanisDrivers] Device %u: %s %s [%s]\n",
                   i, dev.vendor_name, dev.device_name, pnp_bus_type_str(dev.bus_type));
        }
    }

    return DRIVER_STATUS_OK;
}

const char* arcanis_drivers_version(void) {
    static char version[32];
    sprintf(version, "%d.%d.%d",
            ARCANIS_DRIVERS_VERSION_MAJOR,
            ARCANIS_DRIVERS_VERSION_MINOR,
            ARCANIS_DRIVERS_VERSION_PATCH);
    return version;
}

void arcanis_drivers_print_info(void) {
    printf("ArcanisDrivers v%s\n", arcanis_drivers_version());
    printf("Hardware Communication Layers for ArcanisOS\n");
    printf("─────────────────────────────────────────────\n");
    printf("Components:\n");
    printf("  • Driver Framework\n");
    printf("  • Hardware Abstraction Layer (HAL)\n");
    printf("  • Plug-and-Play System\n");
    printf("  • Event System\n");
    printf("  • Memory Management\n");
    printf("─────────────────────────────────────────────\n");
    printf("Drivers:\n");
    printf("  • PS/2 Keyboard\n");
    printf("  • PS/2 Mouse\n");
    printf("  • VGA Display\n");
    printf("  • ATA Storage\n");
    printf("  • NE2000 Network\n");
}

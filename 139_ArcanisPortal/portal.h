#ifndef PORTAL_H
#define PORTAL_H

typedef enum {
    PORTAL_PHYSICAL_AR, PORTAL_AR_VR, PORTAL_VR_SIMULATED, PORTAL_SIMULATED_HOLO, PORTAL_ALL_REALITIES
} PortalType;

typedef struct {
    char id[32];
    char name[64];
    PortalType type;
    int source_layer;
    int target_layer;
    char objects_in_transit[8][32];
    double throughput;
    double stability;
    int active;
    int bidirectional;
} Portal;

typedef struct {
    char id[32];
    char name[64];
    char source_reality[32];
    char target_reality[32];
    double transform_state[16];
    double transition_progress;
    int synced;
} PortalObject;

typedef struct {
    Portal portals[8];
    int portal_count;
    PortalObject objects[32];
    int objects_in_transit;
    int total_transitions;
    double bridge_coherence;
    int cross_reality_physics;
    int auto_sync;
} RealityBridge;

void portal_init(RealityBridge *bridge);
void portal_create(RealityBridge *bridge, const char *name, int src_layer, int dst_layer);
void portal_send_object(RealityBridge *bridge, Portal *portal, PortalObject *object);
void portal_sync(RealityBridge *bridge, Portal *portal);
void portal_bridge_realities(RealityBridge *bridge, int a_layer, int b_layer);
void portal_collapse_to_single(RealityBridge *bridge, int layer);
void portal_show_portals(const RealityBridge *bridge);
void portal_show_objects(const RealityBridge *bridge);
void portal_show_bridge(const RealityBridge *bridge);

#endif

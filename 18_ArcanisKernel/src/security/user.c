/**
 * user.c — Multi-User Authentication System
 *
 * User database, password hashing, authentication.
 * SHA-256 based password hashing with salt.
 */
#include <arcanis/user.h>
#include <arcanis/string.h>

/* Simple SHA-256 for password hashing */
static const uint32_t sha256_k[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};

static uint32_t sha256_rotr(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }

static void sha256_hash(const uint8_t* msg, uint32_t len, uint8_t* hash) {
    uint32_t h[8] = {
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    };

    uint32_t total = len + 9;
    while (total % 64 != 0) total++;
    uint8_t* padded = (uint8_t*)kmalloc(total);
    if (!padded) return;
    memset(padded, 0, total);
    memcpy(padded, msg, len);
    padded[len] = 0x80;
    ((uint32_t*)padded)[(total / 4) - 1] = len * 8;

    for (uint32_t offset = 0; offset < total; offset += 64) {
        uint32_t w[64];
        for (int i = 0; i < 16; i++)
            w[i] = ((uint32_t)padded[offset + i*4] << 24) | ((uint32_t)padded[offset + i*4+1] << 16) |
                    ((uint32_t)padded[offset + i*4+2] << 8) | padded[offset + i*4+3];
        for (int i = 16; i < 64; i++) {
            uint32_t s0 = sha256_rotr(w[i-15],7) ^ sha256_rotr(w[i-15],18) ^ (w[i-15]>>3);
            uint32_t s1 = sha256_rotr(w[i-2],17) ^ sha256_rotr(w[i-2],19) ^ (w[i-2]>>10);
            w[i] = w[i-16] + s0 + w[i-7] + s1;
        }

        uint32_t a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],hh=h[7];
        for (int i = 0; i < 64; i++) {
            uint32_t S1 = sha256_rotr(e,6) ^ sha256_rotr(e,11) ^ sha256_rotr(e,25);
            uint32_t ch = (e & f) ^ (~e & g);
            uint32_t t1 = hh + S1 + ch + sha256_k[i] + w[i];
            uint32_t S0 = sha256_rotr(a,2) ^ sha256_rotr(a,13) ^ sha256_rotr(a,22);
            uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
            uint32_t t2 = S0 + maj;
            hh=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
        }
        h[0]+=a; h[1]+=b; h[2]+=c; h[3]+=d; h[4]+=e; h[5]+=f; h[6]+=g; h[7]+=hh;
    }

    for (int i = 0; i < 8; i++) {
        hash[i*4]   = (h[i] >> 24) & 0xFF;
        hash[i*4+1] = (h[i] >> 16) & 0xFF;
        hash[i*4+2] = (h[i] >> 8) & 0xFF;
        hash[i*4+3] = h[i] & 0xFF;
    }
    kfree(padded);
}

static const char hex_chars[] = "0123456789abcdef";

void user_hash_password(const char* password, char* hash_out) {
    /* Add salt: "arcanis:" + password */
    char salted[128];
    int pass_len = string_length(password);
    string_copy(salted, "arcanis:");
    string_copy(salted + 8, password);

    uint8_t hash[32];
    sha256_hash((const uint8_t*)salted, 8 + pass_len, hash);

    for (int i = 0; i < 32; i++) {
        hash_out[i*2]   = hex_chars[(hash[i] >> 4) & 0x0F];
        hash_out[i*2+1] = hex_chars[hash[i] & 0x0F];
    }
    hash_out[64] = '\0';
}

int user_verify_password(const char* password, const char* hash) {
    char computed[65];
    user_hash_password(password, computed);
    return string_compare(computed, hash) == 0;
}

/* ---- User database ---- */

void user_db_init(user_db_t* db) {
    memset(db, 0, sizeof(user_db_t));
    db->current_uid = 0;

    /* Create root user */
    user_create(db, "root", "toor", USER_ROOT_UID);
    db->users[0].flags = USER_FLAG_ADMIN | USER_FLAG_SYSTEM;
    string_copy(db->users[0].home, "/root");
    string_copy(db->users[0].shell, "/bin/arcanis-sh");

    /* Create default user */
    user_create(db, "user", "user", 1000);
    db->users[1].flags = USER_FLAG_ADMIN;
    string_copy(db->users[1].home, "/home/user");
    string_copy(db->users[1].shell, "/bin/arcanis-sh");
}

int user_create(user_db_t* db, const char* name, const char* password, uint32_t uid) {
    if (!db || !name || !password) return -1;
    if (db->count >= USER_MAX) return -1;
    if (user_find(db, name)) return -1;

    user_t* u = &db->users[db->count];
    u->uid = uid;
    string_copy(u->name, name);
    user_hash_password(password, u->password_hash);
    string_copy(u->home, "/home/");
    string_copy(u->home + 6, name);
    string_copy(u->shell, "/bin/arcanis-sh");
    u->gid = uid;
    u->flags = 0;
    u->failed_logins = 0;
    u->last_login = 0;
    u->in_use = 1;
    db->count++;
    return 0;
}

int user_delete(user_db_t* db, const char* name) {
    if (!db || !name) return -1;
    for (uint32_t i = 0; i < db->count; i++) {
        if (db->users[i].in_use && string_compare(db->users[i].name, name) == 0) {
            if (db->users[i].uid == USER_ROOT_UID) return -1; /* Can't delete root */
            db->users[i].in_use = 0;
            /* Compact array */
            for (uint32_t j = i; j < db->count - 1; j++)
                db->users[j] = db->users[j + 1];
            db->count--;
            return 0;
        }
    }
    return -1;
}

user_t* user_find(user_db_t* db, const char* name) {
    if (!db || !name) return NULL;
    for (uint32_t i = 0; i < db->count; i++) {
        if (db->users[i].in_use && string_compare(db->users[i].name, name) == 0)
            return &db->users[i];
    }
    return NULL;
}

user_t* user_find_by_uid(user_db_t* db, uint32_t uid) {
    if (!db) return NULL;
    for (uint32_t i = 0; i < db->count; i++) {
        if (db->users[i].in_use && db->users[i].uid == uid)
            return &db->users[i];
    }
    return NULL;
}

int user_authenticate(user_db_t* db, const char* name, const char* password) {
    user_t* u = user_find(db, name);
    if (!u) return -1;
    if (u->flags & USER_FLAG_LOCKED) return -2;

    if (user_verify_password(password, u->password_hash)) {
        u->failed_logins = 0;
        db->current_uid = u->uid;
        return 0;
    }
    u->failed_logins++;
    return -1;
}

int user_set_password(user_db_t* db, const char* name, const char* new_password) {
    user_t* u = user_find(db, name);
    if (!u) return -1;
    user_hash_password(new_password, u->password_hash);
    return 0;
}

int user_set_uid(user_db_t* db, const char* name, uint32_t new_uid) {
    user_t* u = user_find(db, name);
    if (!u) return -1;
    u->uid = new_uid;
    return 0;
}

int user_set_flag(user_db_t* db, const char* name, uint32_t flag, int set) {
    user_t* u = user_find(db, name);
    if (!u) return -1;
    if (set) u->flags |= flag;
    else u->flags &= ~flag;
    return 0;
}

int user_list(user_db_t* db, user_t* out, uint32_t max) {
    if (!db) return 0;
    uint32_t count = 0;
    for (uint32_t i = 0; i < db->count && count < max; i++) {
        if (db->users[i].in_use) {
            out[count++] = db->users[i];
        }
    }
    return (int)count;
}

int user_is_admin(user_t* user) {
    return user && (user->flags & USER_FLAG_ADMIN);
}

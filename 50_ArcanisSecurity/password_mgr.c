/**
 * password_mgr.c — Password Manager Implementation
 *
 * Encrypted password storage with master key derivation.
 */
#include <arcanis/password_mgr.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <arcanis/crypto.h>

static const char charset_lower[] = "abcdefghijklmnopqrstuvwxyz";
static const char charset_upper[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
static const char charset_digits[] = "0123456789";
static const char charset_symbols[] = "!@#$%^&*()_+-=[]{}|;:,.<>?";

void pw_init(password_mgr_t* mgr) {
    if (!mgr) return;
    memset(mgr, 0, sizeof(password_mgr_t));
    mgr->master.locked = 1;
    mgr->next_id = 1;
}

/* ---- Key derivation ---- */

void pw_derive_key(const char* password, const uint8_t* salt, uint8_t* key, uint32_t key_len) {
    if (!password || !salt || !key) return;

    /* Simplified PBKDF2-like derivation */
    uint8_t hash[32];
    uint32_t pass_len = string_length(password);

    /* Initial hash: SHA-256(password + salt) */
    /* Simplified: XOR-based derivation */
    for (uint32_t i = 0; i < 32; i++) {
        hash[i] = 0;
        for (uint32_t j = 0; j < pass_len; j++)
            hash[i] ^= password[j] ^ salt[i % PW_SALT_LEN];
        hash[i] ^= i;
    }

    /* Multiple rounds */
    for (uint32_t r = 0; r < PW_HASH_ROUNDS; r++) {
        for (uint32_t i = 0; i < 32; i++) {
            hash[i] = hash[i] ^ hash[(i + 1) % 32];
            hash[i] = (hash[i] << 1) | (hash[i] >> 7);
            hash[i] ^= salt[i % PW_SALT_LEN];
        }
    }

    /* Copy result */
    for (uint32_t i = 0; i < key_len && i < 32; i++)
        key[i] = hash[i];
}

/* ---- Master key ---- */

int pw_set_master(password_mgr_t* mgr, const char* master_password) {
    if (!mgr || !master_password) return -1;

    /* Generate salt */
    for (int i = 0; i < PW_SALT_LEN; i++)
        mgr->master.salt[i] = (uint8_t)(i * 7 + 13); /* Simulated RNG */

    /* Derive key */
    pw_derive_key(master_password, mgr->master.salt, mgr->master.master_key, 32);

    string_copy(mgr->master.master_name, "default", 64);
    mgr->master.locked = 0;
    mgr->master.initialized = 1;
    return 0;
}

int pw_verify_master(password_mgr_t* mgr, const char* master_password) {
    if (!mgr || !master_password) return -1;
    if (!mgr->master.initialized) return -1;

    uint8_t derived_key[32];
    pw_derive_key(master_password, mgr->master.salt, derived_key, 32);

    for (int i = 0; i < 32; i++)
        if (derived_key[i] != mgr->master.master_key[i]) return -1;

    return 0;
}

int pw_change_master(password_mgr_t* mgr, const char* old_pass, const char* new_pass) {
    if (!mgr || !old_pass || !new_pass) return -1;

    if (pw_verify_master(mgr, old_pass) != 0) return -1;
    return pw_set_master(mgr, new_pass);
}

void pw_lock(password_mgr_t* mgr) {
    if (!mgr) return;
    memset(mgr->master.master_key, 0, 32);
    mgr->master.locked = 1;
}

int pw_unlock(password_mgr_t* mgr, const char* master_password) {
    if (!mgr || !master_password) return -1;
    if (pw_verify_master(mgr, master_password) != 0) return -1;
    mgr->master.locked = 0;
    return 0;
}

/* ---- Entry management ---- */

int pw_add_entry(password_mgr_t* mgr, const pw_entry_t* entry) {
    if (!mgr || !entry || mgr->num_entries >= PW_MAX_ENTRIES) return -1;
    if (mgr->master.locked) return -1;

    pw_entry_t* new_entry = &mgr->entries[mgr->num_entries];
    memcpy(new_entry, entry, sizeof(pw_entry_t));

    /* Encrypt password */
    pw_encrypt_entry(new_entry, mgr->master.master_key);

    mgr->num_entries++;
    mgr->dirty = 1;
    return 0;
}

int pw_update_entry(password_mgr_t* mgr, uint32_t id, const pw_entry_t* entry) {
    if (!mgr || !entry) return -1;
    if (mgr->master.locked) return -1;

    for (uint32_t i = 0; i < mgr->num_entries; i++) {
        if (mgr->entries[i].name[0] == id) {
            memcpy(&mgr->entries[i], entry, sizeof(pw_entry_t));
            pw_encrypt_entry(&mgr->entries[i], mgr->master.master_key);
            mgr->dirty = 1;
            return 0;
        }
    }
    return -1;
}

int pw_delete_entry(password_mgr_t* mgr, uint32_t id) {
    if (!mgr) return -1;
    if (mgr->master.locked) return -1;

    for (uint32_t i = 0; i < mgr->num_entries; i++) {
        if (mgr->entries[i].name[0] == id) {
            for (uint32_t j = i; j < mgr->num_entries - 1; j++)
                mgr->entries[j] = mgr->entries[j + 1];
            mgr->num_entries--;
            mgr->dirty = 1;
            return 0;
        }
    }
    return -1;
}

pw_entry_t* pw_find_entry(password_mgr_t* mgr, const char* name) {
    if (!mgr || !name || mgr->master.locked) return NULL;

    for (uint32_t i = 0; i < mgr->num_entries; i++) {
        pw_entry_t entry;
        memcpy(&entry, &mgr->entries[i], sizeof(pw_entry_t));
        pw_decrypt_entry(&entry, mgr->master.master_key);
        if (string_compare(entry.name, name) == 0) {
            memcpy(&mgr->entries[i], &entry, sizeof(pw_entry_t));
            return &mgr->entries[i];
        }
    }
    return NULL;
}

pw_entry_t* pw_find_by_url(password_mgr_t* mgr, const char* url) {
    if (!mgr || !url || mgr->master.locked) return NULL;

    for (uint32_t i = 0; i < mgr->num_entries; i++) {
        pw_entry_t entry;
        memcpy(&entry, &mgr->entries[i], sizeof(pw_entry_t));
        pw_decrypt_entry(&entry, mgr->master.master_key);
        if (string_compare(entry.url, url) == 0) {
            memcpy(&mgr->entries[i], &entry, sizeof(pw_entry_t));
            return &mgr->entries[i];
        }
    }
    return NULL;
}

pw_entry_t* pw_get_entry(password_mgr_t* mgr, uint32_t id) {
    if (!mgr || id >= mgr->num_entries || mgr->master.locked) return NULL;
    return &mgr->entries[id];
}

/* ---- Search ---- */

int pw_search(password_mgr_t* mgr, const char* query, uint32_t* results, uint32_t max_results) {
    if (!mgr || !query || !results || mgr->master.locked) return 0;

    uint32_t count = 0;
    for (uint32_t i = 0; i < mgr->num_entries && count < max_results; i++) {
        pw_entry_t entry;
        memcpy(&entry, &mgr->entries[i], sizeof(pw_entry_t));
        pw_decrypt_entry(&entry, mgr->master.master_key);

        if (string_compare(entry.name, query) == 0 ||
            string_compare(entry.url, query) == 0 ||
            string_compare(entry.username, query) == 0) {
            results[count++] = i;
        }
    }
    return (int)count;
}

/* ---- Import/Export ---- */

int pw_export_csv(password_mgr_t* mgr, const char* filename) {
    if (!mgr || !filename || mgr->master.locked) return -1;

    FILE* f = fopen(filename, "w");
    if (!f) return -1;

    fprintf(f, "name,username,password,url,notes\n");
    for (uint32_t i = 0; i < mgr->num_entries; i++) {
        pw_entry_t entry;
        memcpy(&entry, &mgr->entries[i], sizeof(pw_entry_t));
        pw_decrypt_entry(&entry, mgr->master.master_key);
        fprintf(f, "%s,%s,%s,%s,%s\n",
                entry.name, entry.username, entry.password,
                entry.url, entry.notes);
    }
    fclose(f);
    return 0;
}

int pw_import_csv(password_mgr_t* mgr, const char* filename) {
    if (!mgr || !filename || mgr->master.locked) return -1;

    FILE* f = fopen(filename, "r");
    if (!f) return -1;

    char line[1024];
    fgets(line, 1024, f); /* Skip header */
    while (fgets(line, 1024, f)) {
        pw_entry_t entry;
        memset(&entry, 0, sizeof(pw_entry_t));

        /* Parse CSV line */
        char* p = line;
        char* fields[5];
        for (int i = 0; i < 5; i++) {
            fields[i] = p;
            while (*p && *p != ',') p++;
            if (*p) *p++ = '\0';
        }

        string_copy(entry.name, fields[0], PW_MAX_NAME);
        string_copy(entry.username, fields[1], PW_MAX_USER);
        string_copy(entry.password, fields[2], PW_MAX_PASS);
        string_copy(entry.url, fields[3], PW_MAX_URL);
        string_copy(entry.notes, fields[4], PW_MAX_NOTES);

        pw_add_entry(mgr, &entry);
    }
    fclose(f);
    return 0;
}

/* ---- Password generation ---- */

void pw_generate_password(char* buf, uint32_t len, int use_symbols, int use_upper) {
    if (!buf) return;

    const char* charset = charset_lower;
    uint32_t charset_len = sizeof(charset_lower) - 1;

    if (use_upper) {
        charset = charset_lower;
        charset_len = sizeof(charset_lower) - 1 + sizeof(charset_upper) - 1;
    }
    if (use_symbols) {
        charset_len += sizeof(charset_symbols) - 1;
    }
    charset_len += sizeof(charset_digits) - 1;

    for (uint32_t i = 0; i < len - 1; i++) {
        uint32_t idx = (i * 7 + i * 13 + i * 31) % charset_len;
        if (idx < sizeof(charset_lower) - 1)
            buf[i] = charset_lower[idx];
        else if (idx < sizeof(charset_lower) - 1 + sizeof(charset_digits) - 1)
            buf[i] = charset_digits[idx - (sizeof(charset_lower) - 1)];
        else if (idx < sizeof(charset_lower) - 1 + sizeof(charset_digits) - 1 + sizeof(charset_upper) - 1)
            buf[i] = charset_upper[idx - (sizeof(charset_lower) - 1 + sizeof(charset_digits) - 1)];
        else
            buf[i] = charset_symbols[idx - (sizeof(charset_lower) - 1 + sizeof(charset_digits) - 1 + sizeof(charset_upper) - 1)];
    }
    buf[len - 1] = '\0';
}

/* ---- Encryption ---- */

int pw_encrypt_entry(pw_entry_t* entry, const uint8_t* key) {
    if (!entry || !key) return -1;

    /* Encrypt password field */
    aes_ctx_t ctx;
    aes_init(&ctx, key, AES_256);

    uint8_t iv[16];
    for (int i = 0; i < 16; i++) iv[i] = key[i] ^ i;
    aes_set_iv(&ctx, iv);

    uint8_t padded[256];
    uint32_t padded_len;
    uint32_t pass_len = string_length(entry->password);

    aes_pkcs7_pad((uint8_t*)entry->password, pass_len, padded, &padded_len);

    uint8_t encrypted[256];
    aes_encrypt_cbc(&ctx, padded, padded_len, encrypted);

    /* Store encrypted back */
    for (uint32_t i = 0; i < pass_len; i++)
        entry->password[i] = encrypted[i] ^ key[i % 32];

    return 0;
}

int pw_decrypt_entry(pw_entry_t* entry, const uint8_t* key) {
    if (!entry || !key) return -1;

    /* Decrypt password field */
    uint32_t pass_len = string_length(entry->password);
    for (uint32_t i = 0; i < pass_len; i++)
        entry->password[i] = entry->password[i] ^ key[i % 32];

    return 0;
}

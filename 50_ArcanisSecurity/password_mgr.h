/**
 * password_mgr.h — Password Manager
 *
 * Encrypted password storage with master key derivation.
 * Stores credentials encrypted with AES-CBC.
 */
#ifndef ARCANIS_PASSWORD_MGR_H
#define ARCANIS_PASSWORD_MGR_H

#include <arcanis/types.h>

#define PW_MAX_ENTRIES   128
#define PW_MAX_NAME      64
#define PW_MAX_USER      64
#define PW_MAX_PASS      128
#define PW_MAX_URL       128
#define PW_MAX_NOTES     256
#define PW_SALT_LEN      16
#define PW_HASH_ROUNDS   10000

typedef struct {
    char name[PW_MAX_NAME];
    char username[PW_MAX_USER];
    char password[PW_MAX_PASS];
    char url[PW_MAX_URL];
    char notes[PW_MAX_NOTES];
    uint32_t category;  /* 0=login, 1=credit card, 2=identity, 3=note */
    uint32_t created;
    uint32_t modified;
    int      favorite;
} pw_entry_t;

typedef struct {
    char     master_name[64];
    uint8_t  master_key[32];   /* Derived key */
    uint8_t  salt[PW_SALT_LEN];
    int      locked;
    int      initialized;
} pw_master_t;

typedef struct {
    pw_master_t master;
    pw_entry_t  entries[PW_MAX_ENTRIES];
    uint32_t    num_entries;
    uint32_t    next_id;
    int         dirty;
} password_mgr_t;

/* Initialize password manager */
void pw_init(password_mgr_t* mgr);

/* Master key */
int  pw_set_master(password_mgr_t* mgr, const char* master_password);
int  pw_verify_master(password_mgr_t* mgr, const char* master_password);
int  pw_change_master(password_mgr_t* mgr, const char* old_pass, const char* new_pass);
void pw_lock(password_mgr_t* mgr);
int  pw_unlock(password_mgr_t* mgr, const char* master_password);

/* Entry management */
int  pw_add_entry(password_mgr_t* mgr, const pw_entry_t* entry);
int  pw_update_entry(password_mgr_t* mgr, uint32_t id, const pw_entry_t* entry);
int  pw_delete_entry(password_mgr_t* mgr, uint32_t id);
pw_entry_t* pw_find_entry(password_mgr_t* mgr, const char* name);
pw_entry_t* pw_find_by_url(password_mgr_t* mgr, const char* url);
pw_entry_t* pw_get_entry(password_mgr_t* mgr, uint32_t id);

/* Search */
int  pw_search(password_mgr_t* mgr, const char* query, uint32_t* results, uint32_t max_results);

/* Import/Export */
int  pw_export_csv(password_mgr_t* mgr, const char* filename);
int  pw_import_csv(password_mgr_t* mgr, const char* filename);

/* Password generation */
void pw_generate_password(char* buf, uint32_t len, int use_symbols, int use_upper);

/* Key derivation (simplified PBKDF2) */
void pw_derive_key(const char* password, const uint8_t* salt, uint8_t* key, uint32_t key_len);

/* Encryption/Decryption of entries */
int  pw_encrypt_entry(pw_entry_t* entry, const uint8_t* key);
int  pw_decrypt_entry(pw_entry_t* entry, const uint8_t* key);

#endif

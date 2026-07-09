/**
 * pkg_mgr.c — Package Manager
 *
 * Install, remove, search, upgrade packages from a repository.
 * Declarative dependency resolution.
 */
#include "pkg_mgr.h"
#include <arcanis/string.h>

void pkg_db_init(pkg_db_t* db) {
    memset(db, 0, sizeof(pkg_db_t));
    string_copy(db->repo_url, "https://repo.arcanis.os/packages");
}

int pkg_add(pkg_db_t* db, const char* name, const char* version,
            const char* desc, const char* repo, uint32_t size) {
    if (!db || !name) return -1;
    if (db->count >= PKG_MAX) return -1;
    if (pkg_find(db, name)) return -1;

    package_t* pkg = &db->packages[db->count];
    string_copy(pkg->name, name);
    string_copy(pkg->version, version ? version : "0.1.0");
    string_copy(pkg->description, desc ? desc : "");
    string_copy(pkg->repo, repo ? repo : "");
    pkg->size_bytes = size;
    pkg->status = PKG_AVAILABLE;
    pkg->in_use = 1;
    db->count++;
    return 0;
}

int pkg_remove(pkg_db_t* db, const char* name) {
    if (!db || !name) return -1;
    for (uint32_t i = 0; i < db->count; i++) {
        if (db->packages[i].in_use && string_compare(db->packages[i].name, name) == 0) {
            db->packages[i].in_use = 0;
            /* Compact */
            for (uint32_t j = i; j < db->count - 1; j++)
                db->packages[j] = db->packages[j + 1];
            db->count--;
            return 0;
        }
    }
    return -1;
}

package_t* pkg_find(pkg_db_t* db, const char* name) {
    if (!db || !name) return NULL;
    for (uint32_t i = 0; i < db->count; i++) {
        if (db->packages[i].in_use && string_compare(db->packages[i].name, name) == 0)
            return &db->packages[i];
    }
    return NULL;
}

int pkg_search(pkg_db_t* db, const char* query, package_t* out, uint32_t max) {
    if (!db || !query) return 0;
    uint32_t count = 0;
    for (uint32_t i = 0; i < db->count && count < max; i++) {
        if (!db->packages[i].in_use) continue;
        if (string_compare(db->packages[i].name, query) == 0 ||
            string_compare(db->packages[i].description, query) == 0) {
            out[count++] = db->packages[i];
        }
    }
    return (int)count;
}

int pkg_install(pkg_db_t* db, const char* name) {
    package_t* pkg = pkg_find(db, name);
    if (!pkg) return -1;
    if (pkg->status == PKG_INSTALLED) return 0;
    pkg->status = PKG_INSTALLED;
    return 0;
}

int pkg_upgrade(pkg_db_t* db, const char* name) {
    package_t* pkg = pkg_find(db, name);
    if (!pkg) return -1;
    if (pkg->status != PKG_INSTALLED) return -1;
    pkg->status = PKG_INSTALLED;
    return 0;
}

int pkg_list_installed(pkg_db_t* db, package_t* out, uint32_t max) {
    if (!db) return 0;
    uint32_t count = 0;
    for (uint32_t i = 0; i < db->count && count < max; i++) {
        if (db->packages[i].in_use && db->packages[i].status == PKG_INSTALLED)
            out[count++] = db->packages[i];
    }
    return (int)count;
}

int pkg_list_available(pkg_db_t* db, package_t* out, uint32_t max) {
    if (!db) return 0;
    uint32_t count = 0;
    for (uint32_t i = 0; i < db->count && count < max; i++) {
        if (db->packages[i].in_use && db->packages[i].status == PKG_AVAILABLE)
            out[count++] = db->packages[i];
    }
    return (int)count;
}

void pkg_set_repo(pkg_db_t* db, const char* url) {
    if (db && url) string_copy(db->repo_url, url);
}

#ifndef ARCANIS_PKG_MGR_H
#define ARCANIS_PKG_MGR_H

#include <arcanis/types.h>

#define PKG_MAX       256
#define PKG_NAME_MAX  64
#define PKG_VER_MAX   16
#define PKG_DESC_MAX  128
#define PKG_REPO_MAX  256

typedef enum {
    PKG_AVAILABLE = 0,
    PKG_INSTALLED,
    PKG_UPGRADABLE,
} pkg_status_t;

typedef struct {
    char     name[PKG_NAME_MAX];
    char     version[PKG_VER_MAX];
    char     description[PKG_DESC_MAX];
    char     repo[PKG_REPO_MAX];
    uint32_t size_bytes;
    pkg_status_t status;
    uint8_t  in_use;
} package_t;

typedef struct {
    package_t packages[PKG_MAX];
    uint32_t  count;
    char      repo_url[PKG_REPO_MAX];
} pkg_db_t;

void     pkg_db_init(pkg_db_t* db);
int      pkg_add(pkg_db_t* db, const char* name, const char* version,
                 const char* desc, const char* repo, uint32_t size);
int      pkg_remove(pkg_db_t* db, const char* name);
package_t* pkg_find(pkg_db_t* db, const char* name);
int      pkg_search(pkg_db_t* db, const char* query, package_t* out, uint32_t max);
int      pkg_install(pkg_db_t* db, const char* name);
int      pkg_upgrade(pkg_db_t* db, const char* name);
int      pkg_list_installed(pkg_db_t* db, package_t* out, uint32_t max);
int      pkg_list_available(pkg_db_t* db, package_t* out, uint32_t max);
void     pkg_set_repo(pkg_db_t* db, const char* url);

#endif

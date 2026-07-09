#ifndef ARCANIS_USER_H
#define ARCANIS_USER_H

#include <arcanis/types.h>

#define USER_MAX      32
#define USER_NAME_MAX 32
#define USER_PASS_MAX 64
#define USER_HOME_MAX 128

#define USER_ROOT_UID  0
#define USER_ADMIN_UID 1000

#define USER_FLAG_ADMIN   0x01
#define USER_FLAG_SYSTEM  0x02
#define USER_FLAG_LOCKED  0x04

typedef struct {
    uint32_t uid;
    char     name[USER_NAME_MAX];
    char     password_hash[USER_PASS_MAX];  /* SHA-256 hash */
    char     home[USER_HOME_MAX];
    char     shell[USER_HOME_MAX];
    uint32_t gid;
    uint32_t flags;
    uint32_t failed_logins;
    uint32_t last_login;
    uint8_t  in_use;
} user_t;

typedef struct {
    user_t   users[USER_MAX];
    uint32_t count;
    uint32_t current_uid;
} user_db_t;

void     user_db_init(user_db_t* db);
int      user_create(user_db_t* db, const char* name, const char* password, uint32_t uid);
int      user_delete(user_db_t* db, const char* name);
user_t*  user_find(user_db_t* db, const char* name);
user_t*  user_find_by_uid(user_db_t* db, uint32_t uid);
int      user_authenticate(user_db_t* db, const char* name, const char* password);
int      user_set_password(user_db_t* db, const char* name, const char* new_password);
int      user_set_uid(user_db_t* db, const char* name, uint32_t new_uid);
int      user_set_flag(user_db_t* db, const char* name, uint32_t flag, int set);
int      user_list(user_db_t* db, user_t* out, uint32_t max);
int      user_is_admin(user_t* user);

/* Password hashing (SHA-256 based) */
void     user_hash_password(const char* password, char* hash_out);
int      user_verify_password(const char* password, const char* hash);

#endif

/**
 * dns.h — DNS Resolver
 *
 * DNS query construction, parsing, and caching.
 * Supports A, AAAA, CNAME, MX, TXT record types.
 */
#ifndef ARCANIS_DNS_H
#define ARCANIS_DNS_H

#include <arcanis/types.h>
#include <arcanis/net_stack.h>

#define DNS_PORT         53
#define DNS_MAX_NAME     256
#define DNS_MAX_SERVERS  4
#define DNS_MAX_CACHE    64
#define DNS_MAX_ANSWERS  16
#define DNS_BUF_SIZE     512
#define DNS_DEFAULT_TTL  300

/* DNS record types */
#define DNS_TYPE_A      1
#define DNS_TYPE_NS     2
#define DNS_TYPE_CNAME  5
#define DNS_TYPE_SOA    6
#define DNS_TYPE_MX     15
#define DNS_TYPE_TXT    16
#define DNS_TYPE_AAAA   28

/* DNS classes */
#define DNS_CLASS_IN    1

/* DNS header flags */
#define DNS_FLAG_RD     0x0100  /* Recursion desired */
#define DNS_FLAG_RA     0x8000  /* Recursion available */
#define DNS_FLAG_AA     0x0400  /* Authoritative answer */
#define DNS_FLAG_TC     0x0200  /* Truncated */
#define DNS_FLAG_QR     0x8000  /* Query/Response */

#pragma pack(push, 1)
typedef struct {
    uint16_t id;
    uint16_t flags;
    uint16_t qdcount;
    uint16_t ancount;
    uint16_t nscount;
    uint16_t arcount;
} dns_header_t;

typedef struct {
    uint16_t type;
    uint16_t class;
} dns_question_t;

typedef struct {
    uint16_t type;
    uint16_t class;
    uint32_t ttl;
    uint16_t rdlength;
} dns_rr_t;
#pragma pack(pop)

typedef struct {
    uint32_t ip;
    uint32_t ttl;
    uint32_t timestamp;
} dns_a_record_t;

typedef struct {
    char     name[DNS_MAX_NAME];
    uint16_t type;
    uint16_t class;
    union {
        dns_a_record_t a;
        struct {
            char cname[DNS_MAX_NAME];
        } cname;
        struct {
            char name[DNS_MAX_NAME];
            uint16_t preference;
        } mx;
        struct {
            char text[256];
        } txt;
        struct {
            uint8_t addr[16];
        } aaaa;
    } rdata;
} dns_record_t;

typedef struct {
    char     hostname[DNS_MAX_NAME];
    uint16_t type;
    dns_record_t answers[DNS_MAX_ANSWERS];
    uint32_t num_answers;
    uint32_t timestamp;
    int      valid;
} dns_cache_entry_t;

typedef struct {
    uint32_t servers[DNS_MAX_SERVERS];
    uint32_t num_servers;
    uint32_t local_ip;
    dns_cache_entry_t cache[DNS_MAX_CACHE];
    uint32_t cache_count;
    uint32_t next_id;
} dns_state_t;

/* Initialize DNS resolver */
void dns_init(dns_state_t* dns, uint32_t local_ip);

/* Set DNS server */
void dns_set_server(dns_state_t* dns, uint32_t server_ip);

/* Resolve hostname to IP */
int  dns_resolve(dns_state_t* dns, const char* hostname, uint32_t* ip_out);

/* Build DNS query packet */
int  dns_build_query(dns_state_t* dns, const char* hostname, uint16_t type,
                     uint8_t* buf, uint32_t* buf_len);

/* Parse DNS response */
int  dns_parse_response(dns_state_t* dns, const uint8_t* buf, uint32_t len,
                        dns_record_t* records, uint32_t* num_records);

/* Name encoding/decoding */
int  dns_encode_name(const char* name, uint8_t* buf);
int  dns_decode_name(const uint8_t* buf, uint32_t len, uint32_t offset, char* name);

/* Cache management */
void dns_cache_add(dns_state_t* dns, const char* hostname, uint16_t type,
                   dns_record_t* records, uint32_t num_records);
dns_cache_entry_t* dns_cache_find(dns_state_t* dns, const char* hostname, uint16_t type);
void dns_cache_flush(dns_state_t* dns);
void dns_cache_expire(dns_state_t* dns);

/* Utility */
const char* dns_type_name(uint16_t type);
uint32_t dns_htonl(uint32_t val);
uint16_t dns_htons(uint16_t val);

#endif

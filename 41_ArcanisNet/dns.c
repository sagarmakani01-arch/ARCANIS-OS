/**
 * dns.c — DNS Resolver Implementation
 *
 * DNS query building, response parsing, and caching.
 */
#include <arcanis/dns.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

uint32_t dns_htonl(uint32_t val) {
    return ((val & 0xFF) << 24) | ((val & 0xFF00) << 8) |
           ((val >> 8) & 0xFF00) | ((val >> 24) & 0xFF);
}

uint16_t dns_htons(uint16_t val) {
    return ((val & 0xFF) << 8) | ((val >> 8) & 0xFF);
}

void dns_init(dns_state_t* dns, uint32_t local_ip) {
    if (!dns) return;
    memset(dns, 0, sizeof(dns_state_t));
    dns->local_ip = local_ip;
    dns->next_id = 1;

    /* Default DNS servers */
    dns->servers[0] = dns_htonl(0x08080808); /* Google 8.8.8.8 */
    dns->servers[1] = dns_htonl(0x08080404); /* Google 8.8.4.4 */
    dns->servers[2] = dns_htonl(0x01010101); /* Cloudflare 1.1.1.1 */
    dns->num_servers = 3;
}

void dns_set_server(dns_state_t* dns, uint32_t server_ip) {
    if (!dns || dns->num_servers >= DNS_MAX_SERVERS) return;
    dns->servers[dns->num_servers++] = server_ip;
}

/* ---- Name encoding/decoding ---- */

int dns_encode_name(const char* name, uint8_t* buf) {
    if (!name || !buf) return -1;

    uint32_t offset = 0;
    uint32_t label_start = 0;
    uint32_t i = 0;

    while (1) {
        if (name[i] == '.' || name[i] == '\0') {
            uint32_t label_len = i - label_start;
            if (label_len == 0) break;
            buf[offset++] = (uint8_t)label_len;
            memcpy(buf + offset, name + label_start, label_len);
            offset += label_len;
            label_start = i + 1;
            if (name[i] == '\0') break;
        }
        i++;
    }
    buf[offset++] = 0; /* Root label */
    return (int)offset;
}

int dns_decode_name(const uint8_t* buf, uint32_t len, uint32_t offset, char* name) {
    if (!buf || !name || offset >= len) return -1;

    uint32_t pos = 0;
    uint32_t jumped = 0;
    uint32_t original_offset = offset;
    int name_pos = 0;

    while (offset < len) {
        uint8_t label_len = buf[offset];

        if (label_len == 0) {
            offset++;
            break;
        }

        /* Compression pointer */
        if ((label_len & 0xC0) == 0xC0) {
            if (!jumped) original_offset = offset + 2;
            offset = ((label_len & 0x3F) << 8) | buf[offset + 1];
            jumped = 1;
            continue;
        }

        offset++;
        if (offset + label_len > len) return -1;

        if (name_pos > 0) name[name_pos++] = '.';
        memcpy(name + name_pos, buf + offset, label_len);
        name_pos += label_len;
        offset += label_len;
    }
    name[name_pos] = '\0';

    return jumped ? (int)original_offset : (int)offset;
}

/* ---- Build query ---- */

int dns_build_query(dns_state_t* dns, const char* hostname, uint16_t type,
                     uint8_t* buf, uint32_t* buf_len) {
    if (!dns || !hostname || !buf || !buf_len) return -1;

    uint32_t offset = 0;

    /* DNS header */
    dns_header_t* header = (dns_header_t*)buf;
    header->id = dns_htons(dns->next_id++);
    header->flags = dns_htons(DNS_FLAG_RD);
    header->qdcount = dns_htons(1);
    header->ancount = 0;
    header->nscount = 0;
    header->arcount = 0;
    offset = sizeof(dns_header_t);

    /* Question: hostname */
    int name_len = dns_encode_name(hostname, buf + offset);
    if (name_len < 0) return -1;
    offset += name_len;

    /* Question: type and class */
    dns_question_t* q = (dns_question_t*)(buf + offset);
    q->type = dns_htons(type);
    q->class = dns_htons(DNS_CLASS_IN);
    offset += sizeof(dns_question_t);

    *buf_len = offset;
    return 0;
}

/* ---- Parse response ---- */

int dns_parse_response(dns_state_t* dns, const uint8_t* buf, uint32_t len,
                        dns_record_t* records, uint32_t* num_records) {
    if (!dns || !buf || !records || !num_records) return -1;
    if (len < sizeof(dns_header_t)) return -1;

    const dns_header_t* header = (const dns_header_t*)buf;
    uint16_t ancount = dns_htons(header->ancount);
    uint16_t qdcount = dns_htons(header->qdcount);

    uint32_t offset = sizeof(dns_header_t);
    uint32_t count = 0;

    /* Skip questions */
    for (uint32_t i = 0; i < qdcount; i++) {
        char name[DNS_MAX_NAME];
        int consumed = dns_decode_name(buf, len, offset, name);
        if (consumed < 0) return -1;
        offset = consumed + sizeof(dns_question_t);
    }

    /* Parse answers */
    for (uint32_t i = 0; i < ancount && count < *num_records; i++) {
        if (offset >= len) break;

        dns_record_t* rec = &records[count];
        memset(rec, 0, sizeof(dns_record_t));

        /* Decode name */
        int consumed = dns_decode_name(buf, len, offset, rec->hostname);
        if (consumed < 0) break;
        offset = consumed;

        /* Read RR header */
        if (offset + sizeof(dns_rr_t) > len) break;
        const dns_rr_t* rr = (const dns_rr_t*)(buf + offset);
        rec->type = dns_htons(rr->type);
        rec->class = dns_htons(rr->class);
        uint32_t ttl = dns_htonl(rr->ttl);
        uint16_t rdlength = dns_htons(rr->rdlength);
        offset += sizeof(dns_rr_t);

        /* Parse RDATA */
        if (rec->type == DNS_TYPE_A && rdlength == 4) {
            memcpy(&rec->rdata.a.ip, buf + offset, 4);
            rec->rdata.a.ttl = ttl;
            rec->rdata.a.timestamp = 0;
        } else if (rec->type == DNS_TYPE_CNAME) {
            dns_decode_name(buf, len, offset, rec->rdata.cname.cname);
        } else if (rec->type == DNS_TYPE_MX && rdlength > 2) {
            rec->rdata.mx.preference = dns_htons(*(uint16_t*)(buf + offset));
            dns_decode_name(buf, len, offset + 2, rec->rdata.mx.name);
        } else if (rec->type == DNS_TYPE_TXT) {
            uint8_t txt_len = buf[offset];
            if (txt_len < 256) {
                memcpy(rec->rdata.txt.text, buf + offset + 1, txt_len);
                rec->rdata.txt.text[txt_len] = '\0';
            }
        } else if (rec->type == DNS_TYPE_AAAA && rdlength == 16) {
            memcpy(rec->rdata.aaaa.addr, buf + offset, 16);
        }

        offset += rdlength;
        count++;
    }

    *num_records = count;
    return 0;
}

/* ---- Resolve ---- */

int dns_resolve(dns_state_t* dns, const char* hostname, uint32_t* ip_out) {
    if (!dns || !hostname || !ip_out) return -1;

    /* Check cache first */
    dns_cache_entry_t* cached = dns_cache_find(dns, hostname, DNS_TYPE_A);
    if (cached && cached->num_answers > 0) {
        *ip_out = cached->answers[0].rdata.a.ip;
        return 0;
    }

    /* Build query */
    uint8_t query_buf[DNS_BUF_SIZE];
    uint32_t query_len = 0;
    if (dns_build_query(dns, hostname, DNS_TYPE_A, query_buf, &query_len) != 0)
        return -1;

    /* Send to each DNS server (simulated) */
    for (uint32_t s = 0; s < dns->num_servers; s++) {
        /* In real implementation: send UDP packet to dns->servers[s]:53 */

        /* Simulated response for common domains */
        uint32_t fake_ip = 0;
        if (string_compare(hostname, "google.com") == 0)
            fake_ip = dns_htonl(0xACD95004); /* 142.250.80.4 */
        else if (string_compare(hostname, "github.com") == 0)
            fake_ip = dns_htonl(0x8EF05114); /* 142.81.81.20 */
        else if (string_compare(hostname, "localhost") == 0)
            fake_ip = dns_htonl(0x7F000001); /* 127.0.0.1 */
        else
            fake_ip = dns_htonl(0xC0A80101); /* 192.168.1.1 */

        *ip_out = fake_ip;

        /* Cache the result */
        dns_record_t rec;
        memset(&rec, 0, sizeof(dns_record_t));
        string_copy(rec.hostname, hostname, DNS_MAX_NAME);
        rec.type = DNS_TYPE_A;
        rec.rdata.a.ip = fake_ip;
        rec.rdata.a.ttl = DNS_DEFAULT_TTL;
        dns_cache_add(dns, hostname, DNS_TYPE_A, &rec, 1);

        return 0;
    }

    return -1;
}

/* ---- Cache ---- */

void dns_cache_add(dns_state_t* dns, const char* hostname, uint16_t type,
                   dns_record_t* records, uint32_t num_records) {
    if (!dns || !hostname || !records) return;

    /* Find existing or empty slot */
    for (uint32_t i = 0; i < DNS_MAX_CACHE; i++) {
        dns_cache_entry_t* entry = &dns->cache[i];
        if (!entry->valid || (string_compare(entry->hostname, hostname) == 0 && entry->type == type)) {
            string_copy(entry->hostname, hostname, DNS_MAX_NAME);
            entry->type = type;
            entry->num_records = (num_records > DNS_MAX_ANSWERS) ? DNS_MAX_ANSWERS : num_records;
            for (uint32_t j = 0; j < entry->num_records; j++)
                memcpy(&entry->answers[j], &records[j], sizeof(dns_record_t));
            entry->timestamp = 0; /* Current time */
            entry->valid = 1;
            if (!entry->valid) dns->cache_count++;
            return;
        }
    }
}

dns_cache_entry_t* dns_cache_find(dns_state_t* dns, const char* hostname, uint16_t type) {
    if (!dns || !hostname) return NULL;
    for (uint32_t i = 0; i < DNS_MAX_CACHE; i++) {
        dns_cache_entry_t* entry = &dns->cache[i];
        if (entry->valid && entry->type == type &&
            string_compare(entry->hostname, hostname) == 0)
            return entry;
    }
    return NULL;
}

void dns_cache_flush(dns_state_t* dns) {
    if (!dns) return;
    memset(dns->cache, 0, sizeof(dns->cache));
    dns->cache_count = 0;
}

void dns_cache_expire(dns_state_t* dns) {
    if (!dns) return;
    /* In real implementation: check timestamps and expire */
}

const char* dns_type_name(uint16_t type) {
    switch (type) {
        case DNS_TYPE_A:     return "A";
        case DNS_TYPE_NS:    return "NS";
        case DNS_TYPE_CNAME: return "CNAME";
        case DNS_TYPE_SOA:   return "SOA";
        case DNS_TYPE_MX:    return "MX";
        case DNS_TYPE_TXT:   return "TXT";
        case DNS_TYPE_AAAA:  return "AAAA";
        default:             return "UNKNOWN";
    }
}

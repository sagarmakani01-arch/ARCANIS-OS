/**
 * http.c — HTTP Client Implementation
 *
 * HTTP/1.1 request building and response parsing.
 */
#include <arcanis/http.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>

void http_init(http_client_t* client) {
    if (!client) return;
    memset(client, 0, sizeof(http_client_t));
    client->state = HTTP_STATE_IDLE;
    client->timeout = HTTP_DEFAULT_TIMEOUT;
    client->socket_fd = -1;
}

/* ---- URL parsing ---- */

int http_parse_url(const char* url, char* host, uint16_t* port, char* path) {
    if (!url || !host || !port || !path) return -1;

    const char* p = url;

    /* Skip http:// */
    if (string_compare_n(p, "http://", 7) == 0) p += 7;
    else if (string_compare_n(p, "https://", 8) == 0) {
        p += 8;
        *port = 443;
    } else {
        *port = 80;
    }

    /* Extract host */
    uint32_t i = 0;
    while (*p && *p != ':' && *p != '/' && i < HTTP_MAX_HOST - 1) {
        host[i++] = *p++;
    }
    host[i] = '\0';

    /* Extract port */
    if (*p == ':') {
        p++;
        *port = 0;
        while (*p >= '0' && *p <= '9') {
            *port = *port * 10 + (*p - '0');
            p++;
        }
    } else if (*port == 0) {
        *port = 80;
    }

    /* Extract path */
    if (*p == '/') {
        i = 0;
        while (*p && i < HTTP_MAX_PATH - 1) {
            path[i++] = *p++;
        }
        path[i] = '\0';
    } else {
        string_copy(path, "/", HTTP_MAX_PATH);
    }

    return 0;
}

/* ---- Build request ---- */

static const char* method_str(http_method_t method) {
    switch (method) {
        case HTTP_METHOD_GET:    return "GET";
        case HTTP_METHOD_POST:   return "POST";
        case HTTP_METHOD_HEAD:   return "HEAD";
        case HTTP_METHOD_PUT:    return "PUT";
        case HTTP_METHOD_DELETE: return "DELETE";
        default:                 return "GET";
    }
}

int http_build_request(http_client_t* client, http_method_t method,
                        const char* url, const http_header_t* headers, uint32_t num_headers) {
    if (!client || !url) return -1;

    client->request.method = method;
    http_parse_url(url, client->request.host, &client->request.port, client->request.path);
    string_copy(client->request.url, url, HTTP_MAX_URL);

    /* Copy headers */
    client->request.num_headers = 0;
    for (uint32_t i = 0; i < num_headers && i < HTTP_MAX_HEADERS; i++) {
        memcpy(&client->request.headers[i], &headers[i], sizeof(http_header_t));
        client->request.num_headers++;
    }

    /* Add default headers */
    http_set_header(client, "Host", client->request.host);
    http_set_header(client, "User-Agent", "Arcanis-HTTP/1.0");
    http_set_header(client, "Connection", "close");
    http_set_header(client, "Accept", "*/*");

    return 0;
}

/* ---- Header management ---- */

void http_set_header(http_client_t* client, const char* name, const char* value) {
    if (!client || !name || !value) return;

    /* Update existing */
    for (uint32_t i = 0; i < client->request.num_headers; i++) {
        if (string_compare(client->request.headers[i].name, name) == 0) {
            string_copy(client->request.headers[i].value, value, 256);
            return;
        }
    }

    /* Add new */
    if (client->request.num_headers < HTTP_MAX_HEADERS) {
        http_header_t* h = &client->request.headers[client->request.num_headers++];
        string_copy(h->name, name, HTTP_MAX_HEADER);
        string_copy(h->value, value, 256);
    }
}

const char* http_get_header(http_client_t* client, const char* name) {
    if (!client || !name) return NULL;
    for (uint32_t i = 0; i < client->request.num_headers; i++) {
        if (string_compare(client->request.headers[i].name, name) == 0)
            return client->request.headers[i].value;
    }
    return NULL;
}

/* ---- Send/Receive ---- */

int http_send(http_client_t* client) {
    if (!client) return -1;

    client->state = HTTP_STATE_RESOLVING;

    /* Resolve hostname */
    /* dns_resolve(dns, client->request.host, &client->server_ip); */
    client->server_ip = 0xC0A80101; /* Simulated */

    client->state = HTTP_STATE_CONNECTING;
    /* socket_fd = tcp_connect(client->server_ip, client->request.port); */

    client->state = HTTP_STATE_SENDING;
    /* Build raw HTTP request */
    uint8_t buf[HTTP_BUF_SIZE];
    uint32_t offset = 0;

    /* Request line */
    const char* method = method_str(client->request.method);
    uint32_t method_len = string_length(method);
    memcpy(buf + offset, method, method_len);
    offset += method_len;
    buf[offset++] = ' ';

    uint32_t path_len = string_length(client->request.path);
    memcpy(buf + offset, client->request.path, path_len);
    offset += path_len;

    memcpy(buf + offset, " HTTP/1.1\r\n", 11);
    offset += 11;

    /* Headers */
    for (uint32_t i = 0; i < client->request.num_headers; i++) {
        http_header_t* h = &client->request.headers[i];
        uint32_t name_len = string_length(h->name);
        uint32_t value_len = string_length(h->value);
        memcpy(buf + offset, h->name, name_len);
        offset += name_len;
        buf[offset++] = ':';
        buf[offset++] = ' ';
        memcpy(buf + offset, h->value, value_len);
        offset += value_len;
        buf[offset++] = '\r';
        buf[offset++] = '\n';
    }
    buf[offset++] = '\r';
    buf[offset++] = '\n';

    /* In real implementation: send(buf, offset) */

    client->state = HTTP_STATE_RECEIVING;
    /* recv response */

    /* Simulate a response */
    client->response.status = HTTP_OK;
    string_copy(client->response.status_text, "OK", 64);
    client->response.content_length = 0;
    client->response.chunked = 0;
    client->response.body_len = 0;

    client->state = HTTP_STATE_DONE;
    return 0;
}

/* ---- Parse response ---- */

int http_parse_response(http_client_t* client, const uint8_t* data, uint32_t len) {
    if (!client || !data || len < 12) return -1;

    http_response_t* resp = &client->response;
    const char* p = (const char*)data;

    /* Status line: HTTP/1.1 200 OK */
    if (string_compare_n(p, "HTTP/", 5) != 0) return -1;
    p += 5;
    while (*p && *p != ' ') p++;
    p++; /* skip space */

    /* Parse status code */
    resp->status = 0;
    while (*p >= '0' && *p <= '9')
        resp->status = resp->status * 10 + (*p++ - '0');

    /* Skip status text */
    while (*p && *p != '\r') p++;
    p += 2; /* skip \r\n */

    /* Parse headers */
    resp->num_headers = 0;
    while (*p && *p != '\r' && resp->num_headers < HTTP_MAX_HEADERS) {
        http_header_t* h = &resp->headers[resp->num_headers];

        /* Name */
        uint32_t i = 0;
        while (*p && *p != ':' && i < HTTP_MAX_HEADER - 1)
            h->name[i++] = *p++;
        h->name[i] = '\0';
        p++; /* skip : */
        while (*p == ' ') p++;

        /* Value */
        i = 0;
        while (*p && *p != '\r' && i < 255)
            h->value[i++] = *p++;
        h->value[i] = '\0';
        p += 2; /* skip \r\n */

        /* Check for special headers */
        if (string_compare(h->name, "Content-Length") == 0) {
            resp->content_length = 0;
            const char* v = h->value;
            while (*v >= '0' && *v <= '9')
                resp->content_length = resp->content_length * 10 + (*v++ - '0');
        } else if (string_compare(h->name, "Transfer-Encoding") == 0) {
            resp->chunked = (string_compare(h->value, "chunked") == 0);
        } else if (string_compare(h->name, "Location") == 0) {
            string_copy(resp->redirect_url, h->value, HTTP_MAX_URL);
        } else if (string_compare(h->name, "Connection") == 0) {
            resp->keep_alive = (string_compare(h->value, "keep-alive") == 0);
        }

        resp->num_headers++;
    }

    /* Skip \r\n after headers */
    if (*p == '\r') p += 2;

    /* Body */
    uint32_t body_offset = p - (const char*)data;
    resp->body_len = len - body_offset;
    if (resp->body_len > 0) {
        resp->body = (uint8_t*)kmalloc(resp->body_len + 1);
        if (resp->body) {
            memcpy(resp->body, p, resp->body_len);
            resp->body[resp->body_len] = '\0';
        }
    }

    return 0;
}

/* ---- Convenience methods ---- */

int http_get(http_client_t* client, const char* url) {
    if (!client || !url) return -1;
    http_build_request(client, HTTP_METHOD_GET, url, NULL, 0);
    return http_send(client);
}

int http_post(http_client_t* client, const char* url, const char* content_type,
               const uint8_t* body, uint32_t body_len) {
    if (!client || !url) return -1;
    http_build_request(client, HTTP_METHOD_POST, url, NULL, 0);

    /* Set content-type */
    http_set_header(client, "Content-Type", content_type);

    /* Set content-length */
    char len_str[16];
    uint32_t len = body_len;
    int pos = 0;
    if (len == 0) len_str[pos++] = '0';
    else while (len > 0) { len_str[pos++] = '0' + len % 10; len /= 10; }
    len_str[pos] = '\0';
    /* Reverse */
    for (int i = 0; i < pos / 2; i++) {
        char tmp = len_str[i]; len_str[i] = len_str[pos - 1 - i]; len_str[pos - 1 - i] = tmp;
    }
    http_set_header(client, "Content-Length", len_str);

    client->request.body = (uint8_t*)body;
    client->request.body_len = body_len;

    return http_send(client);
}

int http_head(http_client_t* client, const char* url) {
    if (!client || !url) return -1;
    http_build_request(client, HTTP_METHOD_HEAD, url, NULL, 0);
    return http_send(client);
}

/* ---- Response helpers ---- */

int http_is_redirect(http_client_t* client) {
    if (!client) return 0;
    return client->response.status == HTTP_MOVED_PERMANENTLY ||
           client->response.status == HTTP_FOUND;
}

int http_is_error(http_client_t* client) {
    if (!client) return 1;
    return client->response.status >= 400;
}

const char* http_status_text(http_status_t status) {
    switch (status) {
        case HTTP_CONTINUE:          return "Continue";
        case HTTP_OK:                return "OK";
        case HTTP_MOVED_PERMANENTLY: return "Moved Permanently";
        case HTTP_FOUND:             return "Found";
        case HTTP_NOT_MODIFIED:      return "Not Modified";
        case HTTP_BAD_REQUEST:       return "Bad Request";
        case HTTP_UNAUTHORIZED:      return "Unauthorized";
        case HTTP_FORBIDDEN:         return "Forbidden";
        case HTTP_NOT_FOUND:         return "Not Found";
        case HTTP_SERVER_ERROR:      return "Internal Server Error";
        case HTTP_BAD_GATEWAY:       return "Bad Gateway";
        case HTTP_UNAVAILABLE:       return "Service Unavailable";
        default:                     return "Unknown";
    }
}

void http_close(http_client_t* client) {
    if (!client) return;
    if (client->socket_fd >= 0) {
        /* tcp_close(client->socket_fd); */
        client->socket_fd = -1;
    }
    if (client->response.body) {
        kfree(client->response.body);
        client->response.body = NULL;
    }
    client->connected = 0;
    client->state = HTTP_STATE_IDLE;
}

/**
 * http.h — HTTP Client
 *
 * HTTP/1.1 client with GET, POST, HEAD requests.
 * Supports headers, chunked encoding, and connection reuse.
 */
#ifndef ARCANIS_HTTP_H
#define ARCANIS_HTTP_H

#include <arcanis/types.h>
#include <arcanis/net_stack.h>

#define HTTP_PORT         80
#define HTTP_MAX_URL      256
#define HTTP_MAX_HOST     128
#define HTTP_MAX_PATH     128
#define HTTP_MAX_HEADER   128
#define HTTP_MAX_HEADERS  32
#define HTTP_BUF_SIZE     8192
#define HTTP_MAX_BODY     65536
#define HTTP_DEFAULT_TIMEOUT 5000

typedef enum {
    HTTP_METHOD_GET,
    HTTP_METHOD_POST,
    HTTP_METHOD_HEAD,
    HTTP_METHOD_PUT,
    HTTP_METHOD_DELETE
} http_method_t;

typedef enum {
    HTTP_STATE_IDLE,
    HTTP_STATE_RESOLVING,
    HTTP_STATE_CONNECTING,
    HTTP_STATE_SENDING,
    HTTP_STATE_RECEIVING,
    HTTP_STATE_DONE,
    HTTP_STATE_ERROR
} http_state_t;

typedef enum {
    HTTP_CONTINUE          = 100,
    HTTP_OK                = 200,
    HTTP_MOVED_PERMANENTLY = 301,
    HTTP_FOUND             = 302,
    HTTP_NOT_MODIFIED      = 304,
    HTTP_BAD_REQUEST       = 400,
    HTTP_UNAUTHORIZED      = 401,
    HTTP_FORBIDDEN         = 403,
    HTTP_NOT_FOUND         = 404,
    HTTP_SERVER_ERROR      = 500,
    HTTP_BAD_GATEWAY       = 502,
    HTTP_UNAVAILABLE       = 503
} http_status_t;

typedef struct {
    char     name[HTTP_MAX_HEADER];
    char     value[256];
} http_header_t;

typedef struct {
    http_method_t method;
    char          url[HTTP_MAX_URL];
    char          host[HTTP_MAX_HOST];
    char          path[HTTP_MAX_PATH];
    uint16_t      port;
    http_header_t headers[HTTP_MAX_HEADERS];
    uint32_t      num_headers;
    uint8_t*      body;
    uint32_t      body_len;
} http_request_t;

typedef struct {
    http_status_t status;
    char          status_text[64];
    http_header_t headers[HTTP_MAX_HEADERS];
    uint32_t      num_headers;
    uint8_t*      body;
    uint32_t      body_len;
    uint32_t      content_length;
    int           chunked;
    int           keep_alive;
    char          redirect_url[HTTP_MAX_URL];
} http_response_t;

typedef struct {
    http_state_t    state;
    http_request_t  request;
    http_response_t response;
    uint32_t        socket_fd;
    uint32_t        server_ip;
    uint32_t        timeout;
    int             connected;
    int             error;
    char            error_msg[128];
} http_client_t;

/* Initialize HTTP client */
void http_init(http_client_t* client);

/* Parse URL */
int  http_parse_url(const char* url, char* host, uint16_t* port, char* path);

/* Build request */
int  http_build_request(http_client_t* client, http_method_t method,
                        const char* url, const http_header_t* headers, uint32_t num_headers);

/* Send request and receive response */
int  http_send(http_client_t* client);

/* Parse response */
int  http_parse_response(http_client_t* client, const uint8_t* data, uint32_t len);

/* Convenience methods */
int  http_get(http_client_t* client, const char* url);
int  http_post(http_client_t* client, const char* url, const char* content_type,
               const uint8_t* body, uint32_t body_len);
int  http_head(http_client_t* client, const char* url);

/* Header management */
void http_set_header(http_client_t* client, const char* name, const char* value);
const char* http_get_header(http_client_t* client, const char* name);

/* Response helpers */
int  http_is_redirect(http_client_t* client);
int  http_is_error(http_client_t* client);
const char* http_status_text(http_status_t status);

/* Connection management */
void http_close(http_client_t* client);

#endif

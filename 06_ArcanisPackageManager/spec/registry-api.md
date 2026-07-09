# Arcanis Registry API Specification

Version 1.0.0

## Base URL

`https://registry.arcanis.dev/v1`

## Endpoints

### Get Package Info

```
GET /packages/:name
```

Returns metadata and all versions for a package.

**Response:**
```json
{
  "name": "@arcanis/core",
  "description": "Core Arcanis runtime library",
  "dist-tags": {
    "latest": "1.2.0",
    "beta": "2.0.0-beta.1"
  },
  "versions": {
    "1.0.0": {
      "name": "@arcanis/core",
      "version": "1.0.0",
      "description": "Core Arcanis runtime library",
      "main": "index.js",
      "dependencies": {},
      "files": { "index.js": "..." },
      "checksums": { "index.js": "sha256-hex..." },
      "signature": { "value": "...", "publicKey": "...", "algorithm": "SHA256" }
    }
  },
  "time": {
    "1.0.0": "2026-01-01T00:00:00.000Z"
  }
}
```

### Get Specific Version

```
GET /packages/:name/:version
```

Returns a single version's metadata.

### Search Packages

```
GET /search?q=query&size=20&from=0
```

Returns matching packages.

**Response:**
```json
{
  "objects": [
    {
      "package": {
        "name": "@arcanis/core",
        "version": "1.2.0",
        "description": "Core Arcanis runtime library",
        "keywords": ["arcanis", "core"]
      },
      "score": 0.95
    }
  ],
  "total": 42
}
```

### Publish Package

```
PUT /publish
```

Publishes a new package version. Requires authentication.

**Request:**
```json
{
  "name": "@arcanis/core",
  "version": "1.3.0",
  "description": "Core Arcanis runtime library",
  "main": "index.js",
  "dependencies": {},
  "files": { "index.js": "..." },
  "checksums": { "index.js": "sha256-hex..." },
  "signature": { "value": "...", "publicKey": "...", "algorithm": "SHA256" }
}
```

**Response:**
```json
{
  "ok": true,
  "name": "@arcanis/core",
  "version": "1.3.0"
}
```

### Authentication

```
Authorization: Bearer <token>
```

Tokens are issued per-user or per-organization. Include the token in the `Authorization` header for publish operations.

### Error Responses

```json
{
  "error": "Package not found",
  "status": 404
}
```

```json
{
  "error": "Version already exists",
  "status": 409
}
```

```json
{
  "error": "Invalid manifest",
  "status": 400,
  "details": ["Missing required field: name", "Invalid version format"]
}
```

## Registry Discovery

Registries advertise support via:

```
GET /.well-known/arcanis.txt
```

Must contain `arcanis-registry` to be recognized.

## Rate Limiting

- Anonymous: 60 requests/minute
- Authenticated: 500 requests/minute
- Publish: 10 requests/minute

Rate limit headers:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

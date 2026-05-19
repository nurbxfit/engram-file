# API Rate Limiting Strategy

## Decision

Use a token-bucket algorithm per-user with Redis as the backing store.

## Limits

| Tier      | Requests/min | Burst | Scope     |
|-----------|-------------|-------|-----------|
| Free      | 60          | 10    | per user  |
| Pro       | 300         | 50    | per user  |
| Enterprise| 1000        | 200   | per user  |

## Implementation

- Redis keys: `ratelimit:{userId}:{endpoint_group}` with TTL = 60s.
- Headers returned: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
- Return `429 Too Many Requests` with `Retry-After` header when exceeded.
- Rate limit key is extracted from the JWT `sub` claim (user ID).

## Exemptions

- Health check endpoint (`GET /api/health`) is not rate limited.
- Internal service-to-service calls with `X-Internal-Api-Key` header skip rate limiting.

## Status

Active. Deployed globally in API gateway middleware.

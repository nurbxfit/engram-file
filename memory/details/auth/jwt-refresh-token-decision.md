# JWT Refresh Token Strategy

## Decision

Use short-lived access tokens (15 min) + long-lived refresh tokens (7 days) for API authentication.

## Rationale

- Access tokens in JWTs can be verified statelessly by the API gateway.
- Refresh tokens allow re-authentication without forcing the user to re-login.
- 7-day expiry balances security with UX; refresh token rotation invalidates old tokens on use.

## Implementation Notes

- Store refresh tokens in an HTTP-only, Secure, SameSite=Strict cookie.
- Access tokens in memory (JS variable), never localStorage.
- Endpoint: `POST /api/auth/refresh` — accepts cookie, returns new access token.
- Revoke all user refresh tokens on password change.

## Status

Active. Applied in v2 auth rewrite.

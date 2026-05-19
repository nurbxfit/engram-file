# OAuth2 Social Login Flow

## Pattern

Unified OAuth2 flow supporting Google and GitHub providers via a generic adapter pattern.

## Implementation

```
[User] → [Login Button] → [Provider OAuth URL] → [User grants] → [Callback]
    → [Exchange code for token] → [Find or create user] → [Issue JWT] → [Redirect]
```

### Provider Adapter Interface

- `getAuthUrl(state)` — build provider auth URL with state param
- `exchangeCode(code)` — exchange authorization code for access token
- `getProfile(accessToken)` — fetch user profile from provider

### State Param

OAuth state is an encrypted JWT containing `{ provider, redirectTo, nonce }` with 10min expiry. This prevents CSRF and encodes post-login redirect target.

## Status

Active. Both Google and GitHub adapters implemented.

# Contract: Authentication API

**Base path**: `/api/v1/auth`
**Auth**: Public endpoints (no token required)

---

## POST /api/v1/auth/login

Login with username + password. Returns JWT access token and sets httpOnly refresh cookie.

**Request**
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

**Response 200**
```json
{
  "access_token": "string (JWT, 30min TTL)",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "username": "string",
    "display_name": "string",
    "role": "doctor | staff | admin"
  }
}
```
Sets cookie: `refresh_token` (httpOnly, Secure, SameSite=Strict, 7d TTL)

**Response 401**
```json
{ "error": "invalid_credentials", "message": "用户名或密码错误" }
```

**Response 423**
```json
{ "error": "account_disabled", "message": "账号已停用，请联系管理员" }
```

---

## POST /api/v1/auth/refresh

Refresh access token using httpOnly refresh cookie.

**Request**: No body; reads `refresh_token` cookie automatically.

**Response 200**: Same as login 200 response (new `access_token`, rotated refresh cookie).

**Response 401**
```json
{ "error": "token_expired", "message": "登录已过期，请重新登录" }
```

---

## POST /api/v1/auth/logout

Revoke current access token and clear refresh cookie.

**Auth**: Bearer token required.

**Response 204**: No content. Refresh cookie cleared.

---

## GET /api/v1/auth/me

Get current authenticated user profile.

**Auth**: Bearer token required.

**Response 200**
```json
{
  "id": "uuid",
  "username": "string",
  "display_name": "string",
  "role": "doctor | staff | admin",
  "is_active": true,
  "created_at": "2026-05-17T00:00:00Z"
}
```

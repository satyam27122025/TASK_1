# API Specification & Documentation

Base URL: `http://127.0.0.1:8000`

---

## Health Check Endpoints

### 1. Gateway Health Check
- **URL**: `/health`
- **Method**: `GET`
- **Auth**: None
- **Response (200 OK)**:
```json
{
  "status": "ok",
  "service": "api-gateway"
}
```

### 2. User Service Health Check
- **URL**: `http://127.0.0.1:8001/health/`
- **Method**: `GET`
- **Auth**: None
- **Response (200 OK)**:
```json
{
  "status": "ok",
  "service": "user-service"
}
```

### 3. Notification Service Health Check
- **URL**: `http://127.0.0.1:8002/health/`
- **Method**: `GET`
- **Auth**: None
- **Response (200 OK)**:
```json
{
  "status": "ok",
  "service": "notification-service",
  "nats": "connected"
}
```

---

## User Management Endpoints (Proxied via Gateway)

### 1. User Registration
- **URL**: `/api/users/register/`
- **Method**: `POST`
- **Auth**: None
- **Request Body**:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```
- **Response (201 Created)**:
```json
{
  "message": "User created successfully",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```
- **Error Response (400 Bad Request)**:
```json
{
  "detail": {
    "username": ["A user with that username already exists."],
    "email": ["A user with that email already exists."]
  }
}
```

### 2. User Login
- **URL**: `/api/users/login/`
- **Method**: `POST`
- **Auth**: None
- **Request Body**:
```json
{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```
- **Response (200 OK)**:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
- **Error Response (401 Unauthorized)**:
```json
{
  "detail": {
    "error": "Invalid credentials"
  }
}
```

### 3. Get User Profile
- **URL**: `/api/users/profile/`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <access_token>`
- **Response (200 OK)**:
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com"
}
```
- **Error Response (401 Unauthorized)**:
```json
{
  "detail": "Invalid token signature or payload"
}
```

---

## OpenAPI Interactive Documentation

Interactive Swagger UI documentation for all Gateway endpoints is available out-of-the-box at:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

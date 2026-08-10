# System Architecture Documentation

## Overview

This document describes the design, topology, security boundaries, and message delivery guarantees of the microservices system.

```
+-----------------------------------------------------------------------+
|                                CLIENT                                 |
+-----------------------------------------------------------------------+
                                   |
                                   | HTTP / REST (JWT Bearer Auth)
                                   v
+-----------------------------------------------------------------------+
|                     API GATEWAY (FastAPI :8000)                       |
|   - Rate Limiting                                                     |
|   - Request Validation (Pydantic)                                     |
|   - JWT Signature & Expiration Verification                           |
|   - Error & Timeout Handling (503/504)                                |
+-----------------------------------------------------------------------+
                                   |
                                   | HTTP / REST
                                   v
+-----------------------------------------------------------------------+
|                     USER SERVICE (Django :8001)                       |
|   - User Registration & Authentication (SimpleJWT)                    |
|   - Password Hashing (PBKDF2)                                         |
|   - SQLite Database (db.sqlite3)                                      |
+-----------------------------------------------------------------------+
                                   |
                                   | Asynchronous Event Publish (JetStream)
                                   v
+-----------------------------------------------------------------------+
|                 NATS SERVER (:4222 / JetStream Stream)                |
|   - Stream: USERS                                                     |
|   - Subjects: users.created, users.created.dlq                        |
+-----------------------------------------------------------------------+
                                   |
                                   | Asynchronous Event Push / Pull
                                   v
+-----------------------------------------------------------------------+
|                NOTIFICATION SERVICE (Django :8002)                    |
|   - JetStream Consumer (Durable: notification-service)                 |
|   - Idempotent Processing (event_id dedup)                            |
|   - Explicit Message Acknowledgement (ACK)                            |
|   - Dead-Letter Queue Routing (Max 5 attempts)                        |
|   - SQLite Database (db.sqlite3)                                      |
+-----------------------------------------------------------------------+
```

---

## Communication Patterns

1. **Client <-> API Gateway**: Standard REST HTTP requests. Protected endpoints require `Authorization: Bearer <token>`.
2. **API Gateway <-> User Service**: Synchronous HTTP routing via `httpx.AsyncClient`.
3. **User Service <-> Notification Service**: **Strictly Event-Driven over NATS JetStream**. No REST or WebSockets are used between backend services.

---

## Key Design Decisions & Guarantees

### 1. Reliable Message Delivery & JetStream Persistence
- **Stream**: The `USERS` stream captures all user-related events with file storage persistence enabled.
- **Durable Consumer**: The `notification-service` consumer retains subscription position even during service restarts.
- **Explicit ACK**: Messages are acknowledged **only after** successfully creating and persisting the notification record in the database. If DB saving fails, the message is not ACK-ed, triggering JetStream redelivery.

### 2. Idempotency & Duplicate Protection
- Every published event contains a globally unique `event_id` (UUIDv4).
- The Notification Service checks `Notification.objects.filter(event_id=event_id).exists()` prior to insertion.
- If a duplicate event arrives, the consumer logs an idempotency notice and issues an explicit ACK without writing duplicate records.

### 3. Failure Handling & Dead-Letter Queue (DLQ)
- JetStream redelivers unacknowledged messages automatically.
- Each message metadata contains `num_delivered`. If a message fails processing `5` times continuously, it is automatically forwarded to the Dead-Letter Queue subject `users.created.dlq` and ACK-ed from the main stream to prevent blocking consumer threads.

### 4. Zero-Trust Gateway JWT Authentication
- The API Gateway decodes and validates incoming JWT tokens using the shared secret key (`JWT_SECRET_KEY`) and algorithm (`HS256`).
- Unauthenticated or expired requests are rejected at the Gateway edge (HTTP 401), protecting backend services from unauthorized load.

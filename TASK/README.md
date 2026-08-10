# Internship Assignment - Microservices System

Hi! This is my submission for the microservices internship assignment.

I built a microservices project with three main parts:
1. API Gateway (FastAPI) - Runs on port 8000
2. User Service (Django DRF) - Runs on port 8001
3. Notification Service (Django) - Runs on port 8002
4. NATS Server with JetStream - Runs on port 4222

## System Overview

Client makes HTTP calls to API Gateway (port 8000). The Gateway handles validation, JWT auth, rate limiting, and forwards requests to the User Service (port 8001).

When a user registers, the User Service saves them in SQLite and publishes a users.created event to NATS JetStream.

The Notification Service listens to NATS asynchronously (no REST or WebSockets between backend services), picks up the event, and saves a welcome notification record in its own SQLite database.

## Architecture

Client -> API Gateway (8000) -> User Service (8001) -> NATS JetStream (4222) -> Notification Service (8002)

- API Gateway: FastAPI
- User Service: Django, DRF, SQLite
- Notification Service: Django, SQLite, NATS JetStream consumer
- Message Broker: NATS Server with JetStream enabled

## Requirements & Implementation Details

1. No REST or WebSockets between User & Notification Service:
   User Service only publishes an event to NATS JetStream on users.created. Notification Service runs a background consumer (python manage.py consume_notifications) that pulls messages from NATS.

2. Database Choice:
   Used Django default SQLite database (db.sqlite3) for both Django services as requested.

3. Authentication:
   Used SimpleJWT tokens for login. The API Gateway verifies the JWT Bearer token on protected routes (/api/users/profile/). Secrets are loaded from .env files.

4. NATS Reliability & Idempotency:
   - Every published event gets a unique event_id (UUID).
   - Notification Service checks if the event_id is already in SQLite before saving. If it is a duplicate, it skips saving and ACKs the message.
   - Explicit ACK: The consumer only ACKs the message after saving to SQLite successfully.
   - DLQ (Dead Letter Queue): If processing fails repeatedly (up to 5 attempts), the message gets forwarded to users.created.dlq so it does not block the queue.

## Environment Variables

I created .env files for each service and a .env.example file in the root folder with placeholder credentials:

- user-service/.env
- notification-service/.env
- api-gateway/.env

Real secrets and .sqlite3 files are added to .gitignore.

## How to Run Locally (Windows)

1. Start NATS Server:
nats-server.exe -c nats.conf

2. Start User Service:
cd user-service
.\venv\Scripts\activate
python manage.py migrate
python manage.py runserver 8001

3. Start Notification Service (Web & Consumer):
cd notification-service
.\venv\Scripts\activate
python manage.py migrate
python manage.py runserver 8002

In another terminal:
cd notification-service
.\venv\Scripts\activate
python manage.py consume_notifications

4. Start API Gateway:
cd api-gateway
.\venv\Scripts\activate
uvicorn main:app --host 127.0.0.1 --port 8000

## Health Check Endpoints

- API Gateway: http://127.0.0.1:8000/health
- User Service: http://127.0.0.1:8001/health/
- Notification Service: http://127.0.0.1:8002/health/

## API Endpoints (Gateway)

- GET /health - Gateway status
- POST /api/users/register/ - Register a new user
- POST /api/users/login/ - Login and get JWT access & refresh tokens
- GET /api/users/profile/ - Protected endpoint (Header: Authorization: Bearer <access_token>)
- Swagger Docs: http://127.0.0.1:8000/docs

## Docker Option

I also added a docker-compose.yml file to run everything together if needed:
docker-compose up --build

## Testing

I wrote test scripts to verify everything works:
python test_system.py
python test_idempotency.py

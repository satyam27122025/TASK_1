import os
import time
from collections import defaultdict
from typing import Dict, List, Optional

import httpx
import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

load_dotenv()

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://127.0.0.1:8001")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "shared-super-secret-jwt-key-2026")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

app = FastAPI(
    title="TASK Microservices API Gateway",
    version="1.0.0",
)

request_history: Dict[str, List[float]] = defaultdict(list)


@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    window_start = now - 60.0

    timestamps = [t for t in request_history[client_ip] if t > window_start]
    request_history[client_ip] = timestamps

    if len(timestamps) >= RATE_LIMIT_PER_MINUTE:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )

    request_history[client_ip].append(now)
    response = await call_next(request)
    return response


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    username: str
    password: str


async def verify_jwt_token(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature or payload",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "api-gateway"
    }


@app.post("/api/users/register/", tags=["Users"])
async def register(data: RegisterRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{USER_SERVICE_URL}/api/users/register/",
                json=data.model_dump(),
                timeout=10.0,
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User Service is unavailable",
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="User Service request timed out",
            )

    try:
        content = response.json()
    except Exception:
        content = response.text

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=content,
        )

    return JSONResponse(status_code=response.status_code, content=content)


@app.post("/api/users/login/", tags=["Users"])
async def login(data: LoginRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{USER_SERVICE_URL}/api/users/login/",
                json=data.model_dump(),
                timeout=10.0,
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User Service is unavailable",
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="User Service request timed out",
            )

    try:
        content = response.json()
    except Exception:
        content = response.text

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=content,
        )

    return JSONResponse(status_code=response.status_code, content=content)


@app.get("/api/users/profile/", tags=["Users"])
async def get_profile(
    authorization: str = Header(...),
    token_payload: dict = Depends(verify_jwt_token),
):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{USER_SERVICE_URL}/api/users/profile/",
                headers={"Authorization": authorization},
                timeout=10.0,
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User Service is unavailable",
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="User Service request timed out",
            )

    try:
        content = response.json()
    except Exception:
        content = response.text

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=content,
        )

    return JSONResponse(status_code=response.status_code, content=content)

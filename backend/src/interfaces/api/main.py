import os
import time
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.interfaces.api.routers import auth, agents, conversations, rag

# In-memory rate limit store: {user_id: [timestamp, ...]}
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT_WINDOW = 60  # seconds
_RATE_LIMIT_MAX = 30     # requests per window for conversation endpoint

app = FastAPI(
    title="私立诊所 AI 助手平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.environ.get("NEXT_PUBLIC_API_URL", "http://localhost:3000"),
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000)
    import structlog
    log = structlog.get_logger()
    log.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration_ms,
    )
    return response


# Rate limiting for conversation message endpoint
@app.middleware("http")
async def rate_limit_messages(request: Request, call_next):
    if request.method == "POST" and "/conversations/" in request.url.path and "/messages" in request.url.path:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            import hashlib
            token_hash = hashlib.sha256(auth_header[7:20].encode()).hexdigest()[:12]
            now = time.monotonic()
            window_start = now - _RATE_LIMIT_WINDOW
            hits = _rate_limit_store[token_hash]
            hits[:] = [t for t in hits if t > window_start]
            if len(hits) >= _RATE_LIMIT_MAX:
                return JSONResponse(
                    status_code=429,
                    content={"error": "rate_limit", "message": "请求过于频繁，请稍后再试", "retry_after": 10},
                )
            hits.append(now)
    return await call_next(request)


# Security headers
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"error": "not_found", "message": "Resource not found"})


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc):
    return JSONResponse(status_code=403, content={"error": "forbidden", "message": "Insufficient permissions"})


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    import structlog
    structlog.get_logger().error("unhandled_exception", exc=str(exc))
    return JSONResponse(status_code=500, content={"error": "internal_error", "message": "An unexpected error occurred"})


# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])

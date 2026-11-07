from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.api.routes import router
from backend.app.config import settings


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="GhostCustomer Research and Operational API (Draft v0.2)",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    # Format validation errors cleanly matching contract {"detail": ...}
    errors = exc.errors()
    message = "; ".join(f"{'.'.join(str(loc) for loc in err.get('loc', []))}: {err.get('msg')}" for err in errors)
    return JSONResponse(
        status_code=422,
        content={"detail": message or "Invalid request parameters"},
    )


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {"status": "ok", "service": settings.API_TITLE, "version": settings.API_VERSION}


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "healthy", "version": settings.API_VERSION}


# Mount all contract endpoints under /api
app.include_router(router, prefix=settings.API_PREFIX)

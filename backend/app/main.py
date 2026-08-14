from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.audits import router as audits_router


from app.api.health import router as health_router
from app.core.config import get_settings

from app.api.leases import router as leases_router
from app.api.dashboard import router as dashboard_router


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Backend API for the Automated Lease Audit application.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)

app.include_router(leases_router)

app.include_router(audits_router)
app.include_router(dashboard_router)


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    return {
        "message": "Automated Lease Audit API",
        "documentation": "/docs",
    }
"""API v1 router - aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import admin, applications, auth, compliance, documents, funding, notifications, programs

api_router = APIRouter()

# Auth routes
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Program routes
api_router.include_router(programs.router, prefix="/programs", tags=["programs"])

# Application routes
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])

# Document routes
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

# Compliance routes
api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])

# Funding routes
api_router.include_router(funding.router, prefix="/funding", tags=["funding"])

# Transaction history routes
api_router.include_router(funding.transactions_router, prefix="/transactions", tags=["transactions"])

# Notification routes
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# Admin routes
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])


@api_router.get("/status")
async def api_status():
    """API v1 status endpoint."""
    return {"api_version": "v1", "status": "operational"}

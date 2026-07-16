from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.db import connect_to_db, close_db_connection
from app.api.v1.auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_db()
    yield
    # Shutdown
    await close_db_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": f"Welcome to the {settings.PROJECT_NAME} Backend API"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

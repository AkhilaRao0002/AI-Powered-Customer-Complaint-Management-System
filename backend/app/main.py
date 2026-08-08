# ============================================================
# AIVOA AI - MAIN FASTAPI APPLICATION
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from . import models

from .routes import complaints
from .routes import ai


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AIVOA AI Complaint Management System",
    description=(
        "AI-powered pharmaceutical customer complaint "
        "management and QMS system"
    ),
    version="2.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# DATABASE TABLE CREATION
# ============================================================

# SQLAlchemy checks all models registered with Base
# and creates tables that do not already exist.

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(
    complaints.router
)

app.include_router(
    ai.router
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():

    return {
        "message": (
            "AIVOA AI Complaint Management API "
            "is running"
        )
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, projects, users, sources, knowledge, handovers, system

from app.core.config import settings


app = FastAPI(

    title=settings.APP_NAME,

    version=settings.APP_VERSION,

    description=(
        "Intelligent Knowledge Handover "
        "and Project Continuity Platform"
    )

)


# CORS configuration

app.add_middleware(

    CORSMiddleware,

    allow_origins=settings.allowed_origins,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)


# Register API routers

app.include_router(
    auth.router,
    prefix=settings.API_PREFIX
)

app.include_router(
    users.router,
    prefix=settings.API_PREFIX
)

app.include_router(
    projects.router,
    prefix=settings.API_PREFIX
)

app.include_router(
    sources.router,
    prefix=settings.API_PREFIX
)

app.include_router(
    knowledge.router,
    prefix=settings.API_PREFIX
)

app.include_router(
    handovers.router,
    prefix=settings.API_PREFIX
)

app.include_router(
    system.router,
    prefix=settings.API_PREFIX
)

# Root endpoint

@app.get("/")
def home():

    return {

        "application": "HandoverOS",

        "message": (
            "Preserve Knowledge. "
            "Maintain Continuity."
        ),

        "status": "Running"

    }


# Health check

@app.get("/health")
def health_check():

    return {

        "status": "healthy",

        "application": "HandoverOS"

    }
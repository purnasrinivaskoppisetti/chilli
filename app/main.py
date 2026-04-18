from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# Routers
from app.api import auth, dashboard, purchases, customers

# Database
from app.core.database import init_db


def create_app() -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        await init_db()
        yield
        # Shutdown (optional cleanup)

    app = FastAPI(
        title="Mirchi Cotton Purchase API",
        version="1.0.0",
        description="Backend system for managing mirchi and cotton purchases, billing, and analytics",
        lifespan=lifespan
    )

    configure_middlewares(app)
    register_routes(app)

    return app


# -----------------------------
# MIDDLEWARE
# -----------------------------
def configure_middlewares(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # change in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# -----------------------------
# ROUTES
# -----------------------------
def register_routes(app: FastAPI) -> None:
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
    app.include_router(purchases.router, prefix="/api/purchases", tags=["Purchases"])
    app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])


# Create app
app = create_app()


# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.get("/", tags=["Health"])
async def health_check():
    return {
        "status": "success",
        "message": "Mirchi Cotton Purchase API is running"
    }
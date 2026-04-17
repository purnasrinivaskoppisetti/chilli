# app/core/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.models import Base

# ✅ async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True
)

# ✅ async session
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ✅ dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ✅ create tables function
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
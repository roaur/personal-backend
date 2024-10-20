from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Database URL for psycopg3
DATABASE_URL = "postgresql+psycopg://user:password@postgres/db"

# Create an async engine
engine = create_async_engine(DATABASE_URL, future=True, echo=True)

# Create a session factory for interacting with the database
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency to get a database session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

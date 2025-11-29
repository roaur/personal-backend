from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import logging
import sys
from common.config import settings

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
file_handler = logging.FileHandler("info.log")
file_handler.setFormatter(formatter)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

DATABASE_URL = settings.database_url

print(f"DATABASE CONN: {DATABASE_URL}")
logger.debug("DATABASE CONN: %s", DATABASE_URL)

# Create an async engine
engine = create_async_engine(DATABASE_URL, future=True, echo=False)

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

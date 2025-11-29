import pytest
from httpx import AsyncClient, ASGITransport
import sys
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/common')
from app.main import app

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

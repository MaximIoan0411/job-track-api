import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.database import Base
from app.dependencies import get_db
from app.limiter import limiter
from app.main import app as fastapi_app

import app.models  

settings = get_settings()
TEST_DB_URL = settings.TEST_DATABASE_URL

if not TEST_DB_URL or "test" not in TEST_DB_URL:
    raise RuntimeError(
        "Invalid TEST_DATABASE_URL. Tests aborted to protect the production database."
    )


@pytest_asyncio.fixture(autouse=True)
async def reset_rate_limiter():
    limiter.reset()
    yield


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(test_engine, setup_database):
    session_factory = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(test_engine):
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user_token(client):
    await client.post(
        "/auth/register", json={"email": "user1_fixture@test.com", "password": "parola123"}
    )
    resp = await client.post(
        "/auth/login",
        data={"username": "user1_fixture@test.com", "password": "parola123"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def user2_token(client):
    await client.post(
        "/auth/register", json={"email": "user2_fixture@test.com", "password": "parola123"}
    )
    resp = await client.post(
        "/auth/login",
        data={"username": "user2_fixture@test.com", "password": "parola123"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def make_concurrent_client(test_engine):
    async def _make():
        session_factory = async_sessionmaker(
            bind=test_engine, class_=AsyncSession, expire_on_commit=False
        )

        async def override_get_db():
            async with session_factory() as session:
                yield session

        fastapi_app.dependency_overrides[get_db] = override_get_db
        transport = ASGITransport(app=fastapi_app)
        return AsyncClient(transport=transport, base_url="http://test")

    return _make
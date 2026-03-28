import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app


@pytest.fixture
def db() -> Session:
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    _TestSession = sessionmaker(bind=engine)
    session = _TestSession()
    yield session
    session.close()
    engine.dispose()


# --- Shared fixtures for API integration tests ---


@pytest.fixture(scope="session")
def _api_engine():
    """Single in-memory engine shared across all API tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def _api_session_factory(_api_engine):
    """Session factory bound to the shared API engine."""
    return sessionmaker(bind=_api_engine)


@pytest.fixture(scope="session")
def client(_api_session_factory) -> TestClient:
    """FastAPI test client with database dependency override."""

    def override_get_db():
        session = _api_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def db_session(_api_session_factory) -> Session:
    """Per-test session on the shared API engine for seeding data."""
    session = _api_session_factory()
    yield session
    session.close()


SAMPLE_CSV_TEXT = """\
data,date,time,alertDate,category,category_desc,matrix_id,rid
"באר שבע 288, באר שבע 289",24.07.2014,17:05:26,2014-07-24T17:05:00,1,ירי רקטות וטילים,1,1
אשקלון 256,24.07.2014,17:05:35,2014-07-24T17:06:00,1,ירי רקטות וטילים,1,2
תל אביב,07.10.2023,06:30:00,2023-10-07T06:30:00,1,ירי רקטות וטילים,4,100
תל אביב,07.10.2023,06:30:00,2023-10-07T06:30:00,13,האירוע הסתיים,10,101
"""


SAMPLE_TZOFAR_JSON = """[
    {
        "date": "2024-01-15T10:30:00",
        "name": "תל אביב - מרכז",
        "category": 1,
        "title": "ירי רקטות וטילים"
    },
    {
        "date": "2024-01-15T10:30:00",
        "name": "חולון",
        "category": 1,
        "title": "ירי רקטות וטילים"
    }
]"""

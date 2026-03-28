import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.database import Base


@pytest.fixture
def db() -> Session:
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
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

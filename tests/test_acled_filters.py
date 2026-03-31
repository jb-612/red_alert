"""Tests for ACLED filter utilities."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.api.acled_filters import apply_acled_filters
from backend.database import Base
from backend.models.acled_event import AcledEvent


def _make_event(**overrides: object) -> dict:
    defaults: dict = {
        "event_id_cnty": "IRN001",
        "event_date": date(2026, 3, 1),
        "year": 2026,
        "time_precision": 1,
        "disorder_type": "Political violence",
        "event_type": "Explosions/Remote violence",
        "sub_event_type": "Air/drone strike",
        "actor1": "Military Forces of the United States",
        "country": "Iran, Islamic Republic of",
        "iso": 364,
        "location": "Isfahan",
        "latitude": 32.6539,
        "longitude": 51.6660,
        "fatalities": 0,
    }
    defaults.update(overrides)
    return defaults


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(AcledEvent(**_make_event(event_id_cnty="E1", country="Iran, Islamic Republic of")))
    session.add(AcledEvent(**_make_event(event_id_cnty="E2", country="Iraq", iso=368)))
    session.add(AcledEvent(**_make_event(
        event_id_cnty="E3",
        event_date=date(2026, 3, 15),
        event_type="Violence against civilians",
        sub_event_type="Attack",
        actor1="Military Forces of Iran",
        actor2="Civilians (Iran)",
    )))
    session.commit()
    try:
        yield session
    finally:
        session.close()


class TestApplyAcledFilters:
    def test_no_filters(self, db: Session) -> None:
        stmt = apply_acled_filters(select(AcledEvent), None, None)
        assert len(db.scalars(stmt).all()) == 3

    def test_date_from(self, db: Session) -> None:
        stmt = apply_acled_filters(select(AcledEvent), date(2026, 3, 10), None)
        assert len(db.scalars(stmt).all()) == 1

    def test_date_to(self, db: Session) -> None:
        stmt = apply_acled_filters(select(AcledEvent), None, date(2026, 3, 1))
        assert len(db.scalars(stmt).all()) == 2

    def test_country_filter(self, db: Session) -> None:
        stmt = apply_acled_filters(select(AcledEvent), None, None, countries=["Iraq"])
        assert len(db.scalars(stmt).all()) == 1

    def test_event_type_filter(self, db: Session) -> None:
        stmt = apply_acled_filters(
            select(AcledEvent), None, None, event_types=["Violence against civilians"]
        )
        assert len(db.scalars(stmt).all()) == 1

    def test_sub_event_type_filter(self, db: Session) -> None:
        stmt = apply_acled_filters(
            select(AcledEvent), None, None, sub_event_types=["Air/drone strike"]
        )
        assert len(db.scalars(stmt).all()) == 2

    def test_actor_filter(self, db: Session) -> None:
        stmt = apply_acled_filters(select(AcledEvent), None, None, actor="United States")
        assert len(db.scalars(stmt).all()) == 2

    def test_combined_filters(self, db: Session) -> None:
        stmt = apply_acled_filters(
            select(AcledEvent),
            date(2026, 3, 1),
            date(2026, 3, 1),
            countries=["Iran, Islamic Republic of"],
        )
        assert len(db.scalars(stmt).all()) == 1

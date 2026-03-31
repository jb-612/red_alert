"""Tests for ACLED event models and schemas."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from backend.database import Base
from backend.models.acled_event import AcledEvent
from backend.models.sync_state import SyncState
from backend.schemas.acled import (
    AcledActorCount,
    AcledCountryCount,
    AcledEventListResponse,
    AcledEventResponse,
    AcledEventTypeCount,
    AcledGeoPoint,
    AcledSyncStatus,
    AcledTimelineBucket,
    AcledTimelineResponse,
    UnifiedTimelineBucket,
    UnifiedTimelineResponse,
)


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def _make_event(**overrides: object) -> dict:
    defaults: dict = {
        "event_id_cnty": "IRN12345",
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


class TestAcledEventModel:
    def test_create_event(self, db: Session) -> None:
        event = AcledEvent(**_make_event())
        db.add(event)
        db.commit()

        result = db.scalar(select(AcledEvent).where(AcledEvent.event_id_cnty == "IRN12345"))
        assert result is not None
        assert result.country == "Iran, Islamic Republic of"
        assert result.event_type == "Explosions/Remote violence"
        assert float(result.latitude) == pytest.approx(32.6539, abs=0.001)

    def test_unique_event_id_cnty(self, db: Session) -> None:
        db.add(AcledEvent(**_make_event()))
        db.commit()

        db.add(AcledEvent(**_make_event()))
        with pytest.raises(IntegrityError):
            db.commit()

    def test_different_event_ids_ok(self, db: Session) -> None:
        db.add(AcledEvent(**_make_event(event_id_cnty="IRN001")))
        db.add(AcledEvent(**_make_event(event_id_cnty="IRN002")))
        db.commit()

        count = db.scalar(select(AcledEvent.id).order_by(AcledEvent.id.desc()).limit(1))
        assert count == 2

    def test_nullable_fields(self, db: Session) -> None:
        event = AcledEvent(**_make_event(
            actor2=None,
            assoc_actor_1=None,
            admin1=None,
            notes=None,
            tags=None,
        ))
        db.add(event)
        db.commit()

        result = db.scalar(select(AcledEvent))
        assert result is not None
        assert result.actor2 is None
        assert result.notes is None

    def test_fatalities_default_zero(self, db: Session) -> None:
        data = _make_event()
        del data["fatalities"]
        event = AcledEvent(**data)
        db.add(event)
        db.commit()

        result = db.scalar(select(AcledEvent))
        assert result is not None
        assert result.fatalities == 0


class TestSyncStateModel:
    def test_create_sync_state(self, db: Session) -> None:
        state = SyncState(
            source="acled",
            last_sync_date=date(2026, 3, 15),
            last_sync_at=datetime(2026, 3, 15, 10, 0, 0, tzinfo=UTC),
            events_synced=500,
        )
        db.add(state)
        db.commit()

        result = db.scalar(select(SyncState).where(SyncState.source == "acled"))
        assert result is not None
        assert result.events_synced == 500

    def test_unique_source(self, db: Session) -> None:
        db.add(SyncState(source="acled"))
        db.commit()

        db.add(SyncState(source="acled"))
        with pytest.raises(IntegrityError):
            db.commit()


class TestAcledSchemas:
    def test_event_response_from_orm(self, db: Session) -> None:
        event = AcledEvent(**_make_event(fatalities=5, notes="Test strike"))
        db.add(event)
        db.commit()

        result = db.scalar(select(AcledEvent))
        response = AcledEventResponse.model_validate(result)
        assert response.event_id_cnty == "IRN12345"
        assert response.fatalities == 5
        assert response.country == "Iran, Islamic Republic of"

    def test_event_list_response(self) -> None:
        resp = AcledEventListResponse(
            items=[],
            total=0,
            page=1,
            page_size=50,
        )
        assert resp.total == 0

    def test_geo_point(self) -> None:
        point = AcledGeoPoint(
            location="Isfahan",
            country="Iran",
            lat=32.65,
            lng=51.66,
            count=10,
            fatalities=3,
            event_types=["Air/drone strike", "Armed clash"],
        )
        assert len(point.event_types) == 2

    def test_timeline_bucket(self) -> None:
        bucket = AcledTimelineBucket(period="2026-03-01", count=15, fatalities=3)
        assert bucket.count == 15

    def test_timeline_response(self) -> None:
        resp = AcledTimelineResponse(
            buckets=[AcledTimelineBucket(period="2026-03-01", count=5, fatalities=1)],
            granularity="day",
        )
        assert resp.granularity == "day"

    def test_country_count(self) -> None:
        cc = AcledCountryCount(country="Iran", count=100, fatalities=50)
        assert cc.fatalities == 50

    def test_event_type_count(self) -> None:
        etc = AcledEventTypeCount(
            event_type="Explosions/Remote violence",
            sub_event_type="Air/drone strike",
            count=30,
            fatalities=10,
        )
        assert etc.sub_event_type == "Air/drone strike"

    def test_actor_count(self) -> None:
        ac = AcledActorCount(actor="Military Forces of Iran", count=200, fatalities=80)
        assert ac.actor == "Military Forces of Iran"

    def test_sync_status(self) -> None:
        status = AcledSyncStatus(
            last_sync_date="2026-03-15",
            last_sync_at="2026-03-15T10:00:00Z",
            total_events=5000,
        )
        assert status.total_events == 5000

    def test_unified_timeline_bucket(self) -> None:
        bucket = UnifiedTimelineBucket(
            period="2026-03-01",
            oref_count=50,
            acled_count=10,
            acled_fatalities=3,
        )
        assert bucket.oref_count == 50

    def test_unified_timeline_response(self) -> None:
        resp = UnifiedTimelineResponse(
            buckets=[],
            granularity="week",
        )
        assert resp.granularity == "week"

    def test_schema_field_descriptions(self) -> None:
        fields = AcledEventResponse.model_fields
        assert fields["event_id_cnty"].description is not None
        assert fields["fatalities"].description is not None
        assert fields["country"].description is not None

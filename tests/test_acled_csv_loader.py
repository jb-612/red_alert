"""Tests for ACLED CSV loader."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from backend.ingestion.acled_csv_loader import load_acled_csv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.database import Base
from backend.models.acled_event import AcledEvent

SAMPLE_CSV = dedent("""\
    \ufeffevent_id_cnty,event_date,year,time_precision,disorder_type,event_type,sub_event_type,actor1,assoc_actor_1,inter1,actor2,assoc_actor_2,inter2,interaction,civilian_targeting,iso,region,country,admin1,admin2,admin3,location,latitude,longitude,geo_precision,source,source_scale,notes,fatalities,tags,timestamp
    IRN22059,2023-01-31,2023,1,Political violence,Violence against civilians,Attack,Military Forces of Iran (1989-) Islamic Revolutionary Guard Corps,,1,Civilians (Iran),Baloch Ethnic Group (Iran),7,17,Civilian targeting,364,Middle East,Iran,Sistan and Baluchestan,Iranshahr,Bampur,Bampur,27.1944,60.4559,2,Baloch Campaign,Other,IRGC soldiers fired at a Balochi driver,1,,1675191965
    IRQ50123,2023-02-15,2023,1,Political violence,Explosions/Remote violence,Shelling/artillery/missile attack,Military Forces of the United States,,1,Military Forces of Iran (1989-),,1,11,,368,Middle East,Iraq,Anbar,Al-Qa'im,,Al-Qa'im,34.3764,41.0579,1,Reuters,International,US forces struck Iran-backed militia positions,5,,1676505600
    SYR99001,2023-03-01,2023,1,Political violence,Battles,Armed clash,Syrian Democratic Forces,,3,Islamic State (IS),,2,32,,760,Middle East,Syria,Deir-ez-Zor,Abu Kamal,,Abu Kamal,34.4501,40.9192,1,SOHR,Other,SDF clashed with IS fighters near Abu Kamal,3,,1677628800
""")


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def csv_file(tmp_path: Path) -> Path:
    p = tmp_path / "acled-test.csv"
    p.write_text(SAMPLE_CSV, encoding="utf-8")
    return p


class TestLoadAcledCsv:
    def test_loads_events(self, db: Session, csv_file: Path) -> None:
        count = load_acled_csv(db, str(csv_file))
        assert count == 3

    def test_correct_fields(self, db: Session, csv_file: Path) -> None:
        load_acled_csv(db, str(csv_file))
        event = db.scalar(select(AcledEvent).where(AcledEvent.event_id_cnty == "IRN22059"))
        assert event is not None
        assert event.country == "Iran"
        assert event.event_type == "Violence against civilians"
        assert event.fatalities == 1
        assert float(event.latitude) == pytest.approx(27.1944, abs=0.001)

    def test_theater_classification(self, db: Session, csv_file: Path) -> None:
        load_acled_csv(db, str(csv_file))
        iran = db.scalar(select(AcledEvent).where(AcledEvent.event_id_cnty == "IRN22059"))
        iraq = db.scalar(select(AcledEvent).where(AcledEvent.event_id_cnty == "IRQ50123"))
        assert iran is not None
        assert iraq is not None
        assert iran.theater == "core_me"
        assert iraq.theater == "core_me"

    def test_deduplication(self, db: Session, csv_file: Path) -> None:
        count1 = load_acled_csv(db, str(csv_file))
        count2 = load_acled_csv(db, str(csv_file))
        assert count1 == 3
        assert count2 == 0

    def test_strips_bom(self, db: Session, csv_file: Path) -> None:
        load_acled_csv(db, str(csv_file))
        event = db.scalar(select(AcledEvent).where(AcledEvent.event_id_cnty == "IRN22059"))
        assert event is not None

    def test_empty_csv(self, db: Session, tmp_path: Path) -> None:
        p = tmp_path / "empty.csv"
        p.write_text(
            "event_id_cnty,event_date,year,time_precision,disorder_type,event_type,"
            "sub_event_type,actor1,assoc_actor_1,inter1,actor2,assoc_actor_2,inter2,"
            "interaction,civilian_targeting,iso,region,country,admin1,admin2,admin3,"
            "location,latitude,longitude,geo_precision,source,source_scale,notes,"
            "fatalities,tags,timestamp\n",
            encoding="utf-8",
        )
        count = load_acled_csv(db, str(p))
        assert count == 0

    def test_skips_bad_rows(self, db: Session, tmp_path: Path) -> None:
        bad_csv = dedent("""\
            event_id_cnty,event_date,year,time_precision,disorder_type,event_type,sub_event_type,actor1,assoc_actor_1,inter1,actor2,assoc_actor_2,inter2,interaction,civilian_targeting,iso,region,country,admin1,admin2,admin3,location,latitude,longitude,geo_precision,source,source_scale,notes,fatalities,tags,timestamp
            ,2023-01-31,2023,1,Political violence,Battles,Armed clash,Actor,,1,,,1,11,,364,Middle East,Iran,Tehran,,,Tehran,35.6,51.4,1,Reuters,International,notes,0,,0
            IRN99999,bad-date,2023,1,Political violence,Battles,Armed clash,Actor,,1,,,1,11,,364,Middle East,Iran,Tehran,,,Tehran,35.6,51.4,1,Reuters,International,notes,0,,0
        """)
        p = tmp_path / "bad.csv"
        p.write_text(bad_csv, encoding="utf-8")
        count = load_acled_csv(db, str(p))
        assert count == 0

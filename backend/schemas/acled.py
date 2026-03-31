"""Pydantic response schemas for ACLED conflict event endpoints."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class AcledEventResponse(BaseModel):
    """Single ACLED conflict event."""

    id: int = Field(description="Internal database ID")
    event_id_cnty: str = Field(description="ACLED unique event identifier")
    event_date: date = Field(description="Date the event occurred")
    event_type: str = Field(description="ACLED event type (e.g. Battles, Explosions/Remote violence)")
    sub_event_type: str = Field(description="ACLED sub-event type (e.g. Air/drone strike)")
    actor1: str = Field(description="Primary actor involved")
    actor2: str | None = Field(default=None, description="Secondary actor involved")
    country: str = Field(description="Country where event occurred")
    location: str = Field(description="Specific location name")
    latitude: float = Field(description="Event latitude")
    longitude: float = Field(description="Event longitude")
    fatalities: int = Field(description="Reported fatalities")
    notes: str | None = Field(default=None, description="Event description from ACLED")
    civilian_targeting: str | None = Field(default=None, description="Civilian targeting flag")
    theater: str = Field(description="Conflict theater: core_me, extended_me, maritime, global_terror")

    model_config = {"from_attributes": True}


class AcledEventListResponse(BaseModel):
    """Paginated list of ACLED events."""

    items: list[AcledEventResponse]
    total: int = Field(description="Total matching records")
    page: int
    page_size: int


class AcledGeoPoint(BaseModel):
    """Aggregated conflict event data for a single map location."""

    location: str = Field(description="Location name")
    country: str = Field(description="Country name")
    lat: float = Field(description="Latitude")
    lng: float = Field(description="Longitude")
    count: int = Field(description="Number of events at this location")
    fatalities: int = Field(description="Total fatalities at this location")
    event_types: list[str] = Field(description="Distinct event types at this location")


class AcledTimelineBucket(BaseModel):
    """Single period bucket for ACLED timeline chart."""

    period: str = Field(description="Date bucket (YYYY-MM-DD, YYYY-WNN, or YYYY-MM)")
    count: int = Field(description="Number of events in this period")
    fatalities: int = Field(description="Total fatalities in this period")


class AcledTimelineResponse(BaseModel):
    """Timeline response with bucketed conflict events."""

    buckets: list[AcledTimelineBucket]
    granularity: str = Field(description="day, week, or month")


class AcledCountryCount(BaseModel):
    """Event counts grouped by country."""

    country: str = Field(description="Country name")
    count: int = Field(description="Number of events")
    fatalities: int = Field(description="Total reported fatalities")


class AcledEventTypeCount(BaseModel):
    """Event counts grouped by event type."""

    event_type: str = Field(description="ACLED event type")
    sub_event_type: str | None = Field(default=None, description="ACLED sub-event type")
    count: int = Field(description="Number of events")
    fatalities: int = Field(description="Total fatalities")


class AcledActorCount(BaseModel):
    """Event counts grouped by actor."""

    actor: str = Field(description="Actor name")
    count: int = Field(description="Number of events involving this actor")
    fatalities: int = Field(description="Total fatalities in events involving this actor")


class AcledSyncStatus(BaseModel):
    """Current ACLED sync state."""

    last_sync_date: str | None = Field(description="Last event date synced (YYYY-MM-DD)")
    last_sync_at: str | None = Field(description="When last sync completed (ISO 8601)")
    total_events: int = Field(description="Total ACLED events in database")


class AcledTheaterCount(BaseModel):
    """Event counts grouped by conflict theater."""

    theater: str = Field(description="Theater classification")
    count: int = Field(description="Number of events")
    fatalities: int = Field(description="Total fatalities")


# --- Analytics schemas ---


class AcledAnomalyDay(BaseModel):
    """Single anomalous day in ACLED data."""

    date: str = Field(description="YYYY-MM-DD")
    count: int = Field(description="Event count on this day")
    fatalities: int = Field(description="Fatalities on this day")
    z_score: float = Field(description="Standard deviations from mean")
    direction: str = Field(description="'high' or 'low'")


class AcledAnomalyResponse(BaseModel):
    """Anomaly detection results for ACLED events."""

    mean_daily_count: float
    std_daily_count: float
    threshold: float
    total_days_analyzed: int
    anomalies: list[AcledAnomalyDay]


class AcledEscalationEntry(BaseModel):
    """Week-over-week escalation for a single theater."""

    theater: str = Field(description="Theater classification")
    current_week_count: int = Field(description="Events in most recent week")
    previous_week_count: int = Field(description="Events in prior week")
    change_pct: float | None = Field(description="Percent change (None if prev=0)")
    fatalities_current: int = Field(description="Fatalities in current week")


class AcledEscalationResponse(BaseModel):
    """Escalation tracking across theaters."""

    theaters: list[AcledEscalationEntry]
    period_end: str = Field(description="End date of current week")


class AcledActorProfile(BaseModel):
    """Intelligence profile for a single actor."""

    actor: str = Field(description="Actor name")
    total_events: int = Field(description="Total events involving this actor")
    total_fatalities: int = Field(description="Total fatalities in events involving this actor")
    countries: list[str] = Field(description="Countries where actor is active")
    event_types: list[str] = Field(description="Distinct event types used")
    theaters: list[str] = Field(description="Theaters where actor operates")


class AcledTheaterSeries(BaseModel):
    """Timeline series for a single theater."""

    theater: str = Field(description="Theater classification")
    buckets: list[AcledTimelineBucket] = Field(description="Time-bucketed counts")


class AcledTheaterTimelineResponse(BaseModel):
    """Multi-series timeline, one series per theater."""

    series: list[AcledTheaterSeries]
    granularity: str = Field(description="day, week, or month")


class AcledCivilianCountryImpact(BaseModel):
    """Civilian impact for a single country."""

    country: str = Field(description="Country name")
    civilian_events: int = Field(description="Events targeting civilians")
    civilian_fatalities: int = Field(description="Fatalities in civilian-targeting events")


class AcledCivilianImpactResponse(BaseModel):
    """Civilian impact analysis."""

    total_civilian_events: int = Field(description="Total events with civilian targeting")
    total_civilian_fatalities: int = Field(description="Total fatalities in civilian events")
    by_country: list[AcledCivilianCountryImpact]


# --- Unified timeline (OREF + ACLED) ---


class UnifiedTimelineBucket(BaseModel):
    """Combined OREF + ACLED counts for a single period."""

    period: str = Field(description="Date bucket")
    oref_count: int = Field(description="OREF alert count")
    acled_count: int = Field(description="ACLED conflict event count")
    acled_fatalities: int = Field(description="ACLED fatalities in this period")


class UnifiedTimelineResponse(BaseModel):
    """Unified timeline combining OREF alerts and ACLED conflict events."""

    buckets: list[UnifiedTimelineBucket]
    granularity: str = Field(description="day, week, or month")

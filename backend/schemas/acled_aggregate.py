"""Pydantic schemas for the ACLED aggregate (Explorer overview) endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PulseBucket(BaseModel):
    """A single time bucket in the global aggregate timeline."""

    date: str = Field(description="Bucket start date in ISO format")
    events: int = Field(description="Total events in this bucket")
    fatalities: int = Field(description="Reported fatalities in this bucket")
    exposure: int = Field(description="Population exposure (best estimate)")


class PulseCountry(BaseModel):
    """Aggregate totals for a single country over the queried window."""

    country_id: int = Field(description="ACLED internal country ID")
    country_name: str = Field(description="Country display name")
    theater: str = Field(description="Conflict theater classification")
    events: int = Field(description="Total events for the country")
    fatalities: int = Field(description="Total reported fatalities")
    exposure: int = Field(description="Total population exposure")


class PulseTheater(BaseModel):
    """Aggregate totals rolled up by conflict theater."""

    theater: str = Field(description="Conflict theater key")
    countries: int = Field(description="Number of distinct countries in this theater")
    events: int = Field(description="Total events for the theater")
    fatalities: int = Field(description="Total reported fatalities")
    exposure: int = Field(description="Total population exposure")


class ConflictPulseResponse(BaseModel):
    """Live global conflict pulse assembled from ACLED aggregate rows."""

    latest_update: str | None = Field(
        default=None, description="Latest update date from the source file"
    )
    granularity: str = Field(description="Time granularity: 'day' or 'month'")
    disorder_type: str = Field(description="Disorder type filter applied")
    window_start: str | None = Field(
        default=None, description="First bucket in the timeline (ISO date)"
    )
    window_end: str | None = Field(
        default=None, description="Last bucket in the timeline (ISO date)"
    )
    total_events: int = Field(description="Total events across the window")
    total_fatalities: int = Field(description="Total fatalities across the window")
    total_exposure: int = Field(description="Total population exposure across the window")
    timeline: list[PulseBucket] = Field(description="Global timeline buckets (sorted ascending)")
    top_countries: list[PulseCountry] = Field(description="Top-N countries by event count")
    theater_rollup: list[PulseTheater] = Field(description="Rollup by conflict theater")

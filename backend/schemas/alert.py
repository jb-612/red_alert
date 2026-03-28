from datetime import datetime

from pydantic import BaseModel, Field


class AlertResponse(BaseModel):
    id: int
    alert_datetime: datetime
    location_name: str
    category: int
    category_desc: str | None = None
    source: str

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int = Field(description="Total matching records")
    page: int
    page_size: int


class TimelineBucket(BaseModel):
    period: str = Field(description="Date string for the bucket (YYYY-MM-DD or YYYY-WNN)")
    count: int


class TimelineResponse(BaseModel):
    buckets: list[TimelineBucket]
    granularity: str = Field(description="day, week, or month")


class CategoryCount(BaseModel):
    category: int
    category_desc: str
    count: int


class LocationCount(BaseModel):
    location_name: str
    count: int


class HourlyHeatmapCell(BaseModel):
    hour: int = Field(ge=0, le=23)
    weekday: int = Field(ge=0, le=6, description="0=Monday, 6=Sunday")
    count: int


class PeakDay(BaseModel):
    date: str
    count: int


class MostActiveCategory(BaseModel):
    category: int
    name: str
    name_en: str
    percentage: float


class DateRange(BaseModel):
    from_: str = Field(alias="from")
    to: str

    model_config = {"populate_by_name": True}


class KpiResponse(BaseModel):
    total_alerts: int
    peak_day: PeakDay
    most_active_category: MostActiveCategory
    longest_quiet_days: int
    date_range: DateRange
    unique_locations: int


class GeoPoint(BaseModel):
    location_name: str
    lat: float
    lng: float
    count: int
    categories: list[int] = []


class RegionAnalytics(BaseModel):
    zone_en: str
    total_alerts: int
    top_locations: list[LocationCount]
    category_breakdown: list[CategoryCount]
    timeline: list[TimelineBucket]


# --- Phase 4: Lifestyle Analytics schemas ---


class NightScore(BaseModel):
    date: str = Field(description="Night starting date (YYYY-MM-DD), 22:00 to 06:59")
    peaceful: bool = Field(description="True if zero alerts in the 22:00-06:59 window")


class SleepScoreResponse(BaseModel):
    score: float = Field(description="Percentage of peaceful nights (0-100)")
    total_nights: int = Field(description="Total nights in range")
    peaceful_nights: int = Field(description="Nights with zero alerts 22:00-06:59")
    trend: list[NightScore] = Field(description="Per-night breakdown for trend visualization")


class WeekdayRank(BaseModel):
    weekday: int = Field(ge=0, le=6, description="0=Sunday (Israel week), 6=Saturday")
    weekday_name: str = Field(description="English day name")
    alert_count: int
    rank: int = Field(ge=1, le=7)


class LocationHotHour(BaseModel):
    location_name: str
    peak_hour: int = Field(ge=0, le=23, description="Hour with most alerts")
    alert_count: int


class BestWeekdaysResponse(BaseModel):
    weekdays: list[WeekdayRank] = Field(description="All 7 days ranked by fewest alerts")
    hot_hours: list[LocationHotHour] = Field(description="Peak hour per top location")


class QuietStreak(BaseModel):
    start_date: str = Field(description="First quiet day (YYYY-MM-DD)")
    end_date: str = Field(description="Last quiet day (YYYY-MM-DD)")
    days: int = Field(description="Length of streak in days")


class QuietStreaksResponse(BaseModel):
    current_streak: QuietStreak | None = Field(
        description="Ongoing streak ending at range boundary, or None"
    )
    longest_streak: QuietStreak | None = Field(description="Longest streak in range")
    top_streaks: list[QuietStreak] = Field(description="Top streaks by length, descending")


# --- Phase 5: Comparison + Prediction schemas ---


class AnomalyDay(BaseModel):
    date: str = Field(description="YYYY-MM-DD")
    count: int = Field(description="Alert count on this day")
    z_score: float = Field(description="Standard deviations from mean")
    direction: str = Field(description="'high' or 'low'")


class AnomalyResponse(BaseModel):
    mean_daily_count: float
    std_daily_count: float
    threshold: float
    total_days_analyzed: int
    anomalies: list[AnomalyDay]


class PeriodSummary(BaseModel):
    from_date: str
    to_date: str
    total_alerts: int
    unique_locations: int
    top_categories: list[CategoryCount]
    top_locations: list[LocationCount]
    timeline: list[TimelineBucket]


class ComparisonDelta(BaseModel):
    total_alerts_delta: int
    total_alerts_pct: float | None = Field(
        description="Percentage change, None if period A has 0 alerts"
    )
    unique_locations_delta: int


class ComparisonResponse(BaseModel):
    period_a: PeriodSummary
    period_b: PeriodSummary
    delta: ComparisonDelta


class PrealertLocationStat(BaseModel):
    location_name: str
    total_prealerts: int = Field(description="Total cat 14 alerts")
    followed_by_actual: int = Field(description="Cat 14 followed by cat 1 within window")
    probability: float = Field(description="0.0-1.0")


class PrealertCorrelationResponse(BaseModel):
    window_minutes: int
    overall_total_prealerts: int
    overall_followed: int
    overall_probability: float
    locations: list[PrealertLocationStat]

"""Constants for ACLED conflict data ingestion."""

from __future__ import annotations

# --- Theater classifications ---

THEATER_CORE_ME = "core_me"
THEATER_EXTENDED_ME = "extended_me"
THEATER_MARITIME = "maritime"
THEATER_GLOBAL_TERROR = "global_terror"

# --- Country → default theater mapping ---

COUNTRY_THEATER_MAP: dict[str, str] = {
    # Core Middle East
    "Iran, Islamic Republic of": THEATER_CORE_ME,
    "Israel": THEATER_CORE_ME,
    "Iraq": THEATER_CORE_ME,
    "Syrian Arab Republic": THEATER_CORE_ME,
    "Lebanon": THEATER_CORE_ME,
    "Yemen": THEATER_CORE_ME,
    "United Arab Emirates": THEATER_CORE_ME,
    "Bahrain": THEATER_CORE_ME,
    "Kuwait": THEATER_CORE_ME,
    "Jordan": THEATER_CORE_ME,
    "Saudi Arabia": THEATER_CORE_ME,
    "Palestine": THEATER_CORE_ME,
    "Oman": THEATER_CORE_ME,
    "Qatar": THEATER_CORE_ME,
    # Extended ME
    "Cyprus": THEATER_EXTENDED_ME,
    "Turkey": THEATER_EXTENDED_ME,
    "Azerbaijan": THEATER_EXTENDED_ME,
    # Global terror / Western targets
    "United States": THEATER_GLOBAL_TERROR,
    "United Kingdom": THEATER_GLOBAL_TERROR,
    "France": THEATER_GLOBAL_TERROR,
    "Germany": THEATER_GLOBAL_TERROR,
    "Netherlands": THEATER_GLOBAL_TERROR,
    "Belgium": THEATER_GLOBAL_TERROR,
    "Spain": THEATER_GLOBAL_TERROR,
    "Italy": THEATER_GLOBAL_TERROR,
    "Sweden": THEATER_GLOBAL_TERROR,
    "India": THEATER_GLOBAL_TERROR,
    "Sri Lanka": THEATER_GLOBAL_TERROR,
}

ACLED_TARGET_COUNTRIES: list[str] = list(COUNTRY_THEATER_MAP.keys())

# Keywords that override country-based theater to maritime
MARITIME_KEYWORDS: list[str] = [
    "strait",
    "hormuz",
    "gulf",
    "naval",
    "ship",
    "vessel",
    "tanker",
    "carrier",
    "destroyer",
    "frigate",
    "port",
    "diego garcia",
    "sea",
    "maritime",
    "waterway",
    "blockade",
]

# --- Event type filters ---

ACLED_CONFLICT_EVENT_TYPES: list[str] = [
    "Battles",
    "Explosions/Remote violence",
    "Violence against civilians",
]

ACLED_CONFLICT_SUBTYPES: list[str] = [
    "Shelling/artillery/missile attack",
    "Air/drone strike",
    "Armed clash",
    "Remote explosive/landmine/IED",
    "Disrupted weapons use",
    "Attack",
    "Sexual violence",
    "Abduction/forced disappearance",
]

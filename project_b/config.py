"""
Configuration module for the NYC 311 Data Quality Engine.
Provides default domain values, detector settings, and pipeline parameters,
all of which can be customized per-environment or per-tenant.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional


@dataclass
class DomainConfig:
    """
    Configurable domain rules for NYC 311 data validation.
    Allows adjusting valid categories, bounding boxes, and cross-column mappings
    without hardcoding brittle assumptions.
    """
    # NYC 5 Boroughs
    valid_boroughs: Set[str] = field(
        default_factory=lambda: {
            "BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND", "UNSPECIFIED"
        }
    )

    # Standard NYC service agencies
    valid_agencies: Set[str] = field(
        default_factory=lambda: {
            "NYPD", "HPD", "DOT", "DSNY", "DEP", "DOB", "DPR", "TLC", "DOHMH", "FDNY", "DHS", "EDC"
        }
    )

    # Standard statuses
    valid_statuses: Set[str] = field(
        default_factory=lambda: {
            "Open", "Closed", "Pending", "In Progress", "Assigned", "Draft"
        }
    )

    # NYC Geographic bounding box (approximate inclusive bounds for 5 boroughs)
    min_latitude: float = 40.48
    max_latitude: float = 40.95
    min_longitude: float = -74.30
    max_longitude: float = -73.65

    # NYC ZIP Code range (typically 10001 to 11697)
    min_zip: int = 10001
    max_zip: int = 11697

    # Configurable agency to allowed complaint types.
    # Note: If an agency is not in this mapping or if validation is relaxed,
    # it is treated as permissible unless explicitly contradictory.
    agency_complaint_map: Dict[str, Set[str]] = field(
        default_factory=lambda: {
            "NYPD": {"Noise - Residential", "Noise - Street/Sidewalk", "Noise - Commercial", "Noise - Vehicle", "Illegal Parking", "Blocked Driveway", "Traffic Signal Condition", "Abandoned Vehicle"},
            "HPD": {"HEAT/HOT WATER", "PLUMBING", "PAINT/PLASTER", "WATER LEAK", "DOOR/WINDOW", "GENERAL CONSTRUCTION", "ELECTRIC", "APPLIANCE"},
            "DOT": {"Street Condition", "Street Light Condition", "Sidewalk Condition", "Traffic Signal Condition", "Pothole"},
            "DSNY": {"Dirty Condition", "Missed Collection", "Sanitation Condition", "Graffiti", "Derelict Vehicles"},
            "DEP": {"Water System", "Sewer", "Noise", "Air Quality", "Lead"},
            "DOB": {"Building/Use", "Elevator", "General Construction", "Boiler"},
            "DPR": {"Damaged Tree", "Overgrown Tree/Branches", "Maintenance or Facility", "Dead Tree"},
            "TLC": {"Taxi Complaint", "For Hire Vehicle Complaint", "Lost Property"},
        }
    )

    # Configurable Borough to typical ZIP prefixes
    borough_zip_prefixes: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "MANHATTAN": ["100", "101", "102"],
            "STATEN ISLAND": ["103"],
            "BRONX": ["104"],
            "BROOKLYN": ["112"],
            "QUEENS": ["110", "111", "113", "114", "116"],
        }
    )


@dataclass
class StatisticalConfig:
    """Configurable thresholds for statistical anomaly detection."""
    z_score_threshold: float = 3.0
    iqr_multiplier: float = 1.5
    rare_category_frequency_threshold: float = 0.005  # Categories appearing in < 0.5% of reference rows
    distribution_shift_threshold: float = 0.20        # Threshold for PSI / proportion deviation


@dataclass
class MLConfig:
    """Configurable hyperparameters for machine learning detection."""
    contamination: float = 0.05
    n_estimators: int = 100
    random_state: int = 42
    score_threshold_percentile: float = 5.0  # Lowest 5th percentile considered anomalies


@dataclass
class LLMConfig:
    """Configurable settings for LLM-based detection."""
    model_name: str = "gemini-3.5-flash-lite"
    batch_size: int = 5
    max_rows_to_sample: int = 30     # Strictly limit LLM evaluation to protect cost and latency
    timeout_seconds: int = 20
    offline_mode: bool = False       # Force offline/mock mode even if API key is present
    cost_per_million_input_tokens: float = 0.075
    cost_per_million_output_tokens: float = 0.300


@dataclass
class PipelineConfig:
    """Master pipeline configuration."""
    enable_rules: bool = True
    enable_statistical: bool = True
    enable_ml: bool = True
    enable_llm: bool = True
    deduplicate_alerts: bool = True
    min_confidence_threshold: float = 0.40
    domain: DomainConfig = field(default_factory=DomainConfig)
    statistical: StatisticalConfig = field(default_factory=StatisticalConfig)
    ml: MLConfig = field(default_factory=MLConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)

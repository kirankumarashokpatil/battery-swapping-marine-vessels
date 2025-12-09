from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd
import math
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fixed_path_dp import (
    FixedPathInputs,
    FixedPathOptimizer,
    Segment,
    SegmentOption,
    Station,
    VesselType,
    VesselSpecs,
)

# Import cold-ironing reference if available
try:
    from cold_ironing_reference import VesselTypeHotelling, get_gt_range_info
    COLD_IRONING_AVAILABLE = True
except ImportError:
    COLD_IRONING_AVAILABLE = False

# Import new authentication system
try:
    # Try relative imports first (for Streamlit app execution)
    from .auth_system import get_auth_system
    from .auth_ui import show_login_page, show_user_profile, show_logout_button
except ImportError:
    # Fall back to absolute imports (for direct execution/testing)
    from auth_system import get_auth_system
    from auth_ui import show_login_page, show_user_profile, show_logout_button


def compute_segment_energy(
    distance_nm: float,
    current_knots: float,
    mode: str = "laden",
    base_consumption_laden: float = 245.0,
    base_consumption_unladen: float = 207.0,
    boat_speed_laden: float = 5.0,
    boat_speed_unladen: float = 6.0
) -> Tuple[float, float]:
    """
    Unified energy + travel time calculation. Used by optimizer AND all diagnostics.
    Returns (energy_kwh, travel_time_hr)
    """
    m = (mode or "laden").lower()
    
    # Select mode parameters
    if m == "unladen":
        base_per_nm = base_consumption_unladen
        boat_speed_knots = boat_speed_unladen
    else:  # laden or default
        base_per_nm = base_consumption_laden
        boat_speed_knots = boat_speed_laden
    
    # Travel time (ground speed)
    ground_speed = boat_speed_knots + current_knots
    if ground_speed <= 0:
        raise ValueError(f"Ground speed non-positive: speed={boat_speed_knots}, current={current_knots}")
    
    travel_time_hr = distance_nm / ground_speed
    
    # Energy consumption (corrected zero-flow logic)
    base_energy = distance_nm * base_per_nm
    if current_knots == 0:
        multiplier = 1.0
    elif current_knots < 0:  # Upstream (head current)
        multiplier = 1.2
    else:  # Downstream (tailwind)
        multiplier = 0.8
    
    energy_kwh = base_energy * multiplier
    
    # DEBUG LOGGING
    print(f"DEBUG_CALC: {mode} | dist={distance_nm} | current={current_knots} | speed={boat_speed_knots} | cons={base_per_nm} | mul={multiplier} | energy={energy_kwh}")

    
    return energy_kwh, travel_time_hr


@st.cache_data
def load_default_config() -> Dict:
    import random
    
    # Default route uses real port names (Zhao Qing ⇄ Guangzhou Nansha ⇄ HK Tsing Yi C)
    distances = {
        "Zhao Qing-Guangzhou Nansha": 114.0,
        "Guangzhou Nansha-HK Tsing Yi C": 40.0,
        "HK Tsing Yi C-Guangzhou Nansha": 40.0,
        "Guangzhou Nansha-Zhao Qing": 114.0,
    }
    
    
    # Currents for our route - default to zero for other legs and set these legs per request
    currents = {key: 0.0 for key in distances.keys()}
    currents.update({
        "Zhao Qing-Guangzhou Nansha": 0,
        "Guangzhou Nansha-HK Tsing Yi C": 0,
        "HK Tsing Yi C-Guangzhou Nansha": 0,
        "Guangzhou Nansha-Zhao Qing": 0,
    })
    
    # No remaining segments/currents to randomize for this compact default scenario
    
    # Generate randomized station configs
    stations = {
        "Zhao Qing": {
            "docking_time_hr": 0.0,  # Origin - no stop
            "swap_operation_time_hr": 0.5,
            "allow_swap": False,
            "charging_allowed": False,
            "charging_power_kw": 0.0,
            "available_batteries": 17,
            "total_batteries": 17,
        },
        "Guangzhou Nansha": {
            "docking_time_hr": 2.0,  # If mandatory stop: 2 hours for passenger ops
            "swap_operation_time_hr": 0.5,  # Battery swap: 30 minutes
            "operating_hours": [6.0, 22.0],
            "available_batteries": 17,
            "total_batteries": 17,
            "allow_swap": True,
            "charging_allowed": True,
            "charging_power_kw": 250.0,
            "base_charging_fee": 25.0,  # UK realistic: £10-£50 per session
            "energy_cost_per_kwh": 0.25,  # UK realistic: £0.16-£0.40/kWh (typical £0.25)
            "base_service_fee": 15.0,  # UK realistic: £8-£40 per container (typical £15)
            "swap_cost": 0.0,
            "degradation_fee_per_kwh": 0.03,
            "background_charging_power_kw": 2000.0,
            "background_charging_allowed": True,
        },
        "HK Tsing Yi C": {
            "docking_time_hr": 4.0,  # If mandatory: 4 hours for unloading (per reference image)
            "swap_operation_time_hr": 0.75,  # Battery swap: 45 minutes
            "operating_hours": [0.0, 24.0],
            "available_batteries": 17,
            "total_batteries": 17,
            "allow_swap": True,
            "charging_allowed": True,
            "charging_power_kw": 500.0,
            "base_charging_fee": 30.0,  # UK realistic: £10-£50 per session
            "energy_cost_per_kwh": 0.30,  # UK realistic: higher at busy ports
            "base_service_fee": 20.0,  # UK realistic: £8-£40 per container
            "swap_cost": 0.0,
            "degradation_fee_per_kwh": 0.03,
            "background_charging_power_kw": 500.0,
            "background_charging_allowed": True,
        },
        "D": {
            "docking_time_hr": 2.0,  # If mandatory: 2 hours
            "swap_operation_time_hr": 0.5,  # Battery swap: 30 minutes
            "operating_hours": [8.0, 20.0],
            "available_batteries": 17,
            "total_batteries": 17,
            "allow_swap": True,
            "charging_allowed": True,
            "charging_power_kw": 350.0,
            "base_charging_fee": 20.0,  # UK realistic: £10-£50 per session
            "energy_cost_per_kwh": 0.22,  # UK realistic: £0.16-£0.40/kWh
            "base_service_fee": 18.0,  # UK realistic: £8-£40 per container
            "swap_cost": 0.0,
            "degradation_fee_per_kwh": 0.03,
        },
        "E": {
            "docking_time_hr": 0.0,  # Pass-through only
            "swap_operation_time_hr": 0.5,
            "allow_swap": False,
            "charging_allowed": False,
            "charging_power_kw": 0.0,
        },
    }
    
    # We don't need many stations for this default; any others remain as placeholders
    station_names = ["F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S"]
    for station in station_names:
        if station in ["K", "P"]:  # Make some stations non-swap for variety
            stations[station] = {
                "docking_time_hr": 0.0,
                "allow_swap": False,
                "charging_allowed": False,
                "charging_power_kw": 0.0,
            }
        else:
            # Some stations are 24/7, others have limited hours
            is_24_7 = random.random() > 0.75
            # Default to 17 batteries for each station in the simplified default scenario
            batteries_available = 17
            
            # Energy pricing logic:
            # - 24/7 stations charge premium (15-20% higher)
            # - Large stations (8+ batteries) have economies of scale (lower rates)
            # - Small stations (3-5 batteries) charge more
            # - Base rate varies by location: 0.08-0.13 £/kWh
            base_rate = random.uniform(0.08, 0.13)
            if is_24_7:
                energy_rate = base_rate * random.uniform(1.15, 1.25)  # 24/7 premium
            elif batteries_available >= 8:
                energy_rate = base_rate * random.uniform(0.90, 1.00)  # Large facility discount
            else:
                energy_rate = base_rate * random.uniform(1.05, 1.15)  # Small facility markup
            
            # Charging infrastructure
            charging_power = random.choice([0.0, 250.0, 350.0, 500.0, 750.0])  # Some stations have no charging
            
            stations[station] = {
                "docking_time_hr": round(random.uniform(1.5, 3.0), 2),  # Mandatory stop duration if needed
                "swap_operation_time_hr": round(random.uniform(0.25, 1.0), 2),  # Battery swap: 15 min - 1 hour
                "operating_hours": [0.0, 24.0] if is_24_7 else [random.randint(5, 9), random.randint(16, 23)],
                "available_batteries": batteries_available,
                "total_batteries": batteries_available,
                "allow_swap": True,
                "charging_allowed": charging_power > 0,
                "charging_power_kw": charging_power,
                "base_charging_fee": round(random.uniform(10.0, 50.0), 1) if charging_power > 0 else 0.0,  # UK realistic: £10-£50
                "energy_cost_per_kwh": round(energy_rate, 3),
                "base_service_fee": round(random.uniform(8.0, 40.0), 1),  # UK realistic: £8-£40 per container
                "swap_cost": 0.0,
                "degradation_fee_per_kwh": 0.03,
            }
    
    # T is always destination (no swap)
    stations["T"] = {
        "docking_time_hr": 0.0,
        "allow_swap": False,
        "charging_allowed": False,
        "charging_power_kw": 0.0,
    }
    
    # Default battery: based on container count (12 containers × container size) as default UX
    min_soc_fraction = 0.2
    default_num_containers = 12
    container_capacity_kwh = 2460.0
    battery_capacity_kwh = round(container_capacity_kwh * default_num_containers, 1)
    # Default initial SoC: start full (100%); so initial_soc - min_soc = usable_expected_kwh
    initial_soc_fraction = 1.0
    initial_soc_kwh = round(battery_capacity_kwh * initial_soc_fraction, 1)

    return {
        "route": ["Zhao Qing", "Guangzhou Nansha", "HK Tsing Yi C", "Guangzhou Nansha", "Zhao Qing"],
        "distances_nm": distances,
        "currents_knots": currents,
        # Default vessel behavior derived from the reference table:
        "boat_speed_laden": 5.0,
        "boat_speed_unladen": 6.0,
        "base_consumption_laden": 245.0,
        "base_consumption_unladen": 207.0,
        # Default battery settings:
        "battery_capacity_kwh": battery_capacity_kwh,  # Default based on container count (container_capacity_kwh × num_containers)
        "battery_container_capacity_kwh": 2460.0,  # Standard 20-foot ISO container capacity
        "initial_soc_kwh": initial_soc_kwh,  # Start with full battery (100%)
        "minimum_soc_fraction": min_soc_fraction,  # Industry standard 20% reserve
        "vessel_charging_power_kw": 1000.0,  # Default acceptance capacity for vessel charging
        "energy_cost_per_kwh": 0.12,
        "time_cost_per_hr": 25.0,
        "soc_step_kwh": 20.0,  # Adjusted for containerized battery capacity (2460 kWh)
        "start_time_hr": 6.0,
        "stations": stations,
        "num_containers": default_num_containers,
    }



def build_segment_option(
    segment_name: str,
    distance_nm: float,
    current_knots: float,
    mode: str = "laden",
    boat_speed: float = 5.0,
    boat_speed_laden: float = 5.0,
    boat_speed_unladen: float = 6.0,
    base_consumption: float = 245.0,
    base_consumption_laden: float = 245.0,
    base_consumption_unladen: float = 207.0,
) -> SegmentOption:
    # Delegate to unified computation
    energy_kwh, travel_time_hr = compute_segment_energy(
        distance_nm=distance_nm,
        current_knots=current_knots,
        mode=mode,
        base_consumption_laden=base_consumption_laden,
        base_consumption_unladen=base_consumption_unladen,
        boat_speed_laden=boat_speed_laden,
        boat_speed_unladen=boat_speed_unladen
    )
    
    return SegmentOption(
        label=segment_name,
        travel_time_hr=travel_time_hr,
        energy_kwh=energy_kwh,
    )



def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, str) and not value.strip():
            return default
        return float(str(value))
    except (TypeError, ValueError):
        return default


def _safe_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if not text:
        return default
    return text in {"true", "1", "yes", "y"}


def _safe_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def _pairwise(iterable: Iterable[str]) -> Iterable[Tuple[str, str]]:
    iterator = iter(iterable)
    prev = next(iterator, None)
    for current in iterator:
        if prev is None:
            break
        yield prev, current
        prev = current


def build_inputs(config: Dict) -> FixedPathInputs:
    # Respect per-vessel route if present (vessel_route is per-vessel override)
    route = config.get("vessel_route", config["route"]) if isinstance(config.get("vessel_route"), list) else config["route"]
    distances = config["distances_nm"]
    currents = config["currents_knots"]
    # Derive per-mode speeds & consumption; keep a derived general 'boat_speed_knots' for compatibility
    boat_speed_unladen = float(config.get("boat_speed_unladen", 0.0))
    boat_speed_laden = float(config.get("boat_speed_laden", boat_speed_unladen))
    # Derived 'boat_speed_knots' is conservatively set to unladen speed (used where a single speed may be expected)
    boat_speed_knots = boat_speed_unladen
    base_consumption_laden = float(config.get("base_consumption_laden", 0.0))
    base_consumption_unladen = float(config.get("base_consumption_unladen", base_consumption_laden))

    segments: List[Segment] = []
    # Build mapping for per-vessel segments attributes (laden/must_stop)
    vessel_segment_flags = { (str(s.get("start")).strip(), str(s.get("end")).strip()): s for s in config.get("vessel_segments", []) }
    for start, end in _pairwise(route):
        key = f"{start}-{end}"
        if key not in distances or key not in currents:
            raise ValueError(f"Missing data for segment {key}")
        seg_flags = vessel_segment_flags.get((start, end), {})
        # Convert underlying segment mode to 'laden'/'unladen'; default to 'unladen' for initial runs
        mode = str(seg_flags.get("mode", "unladen")).lower()
        option = build_segment_option(
            segment_name=f"{start}->{end}",
            distance_nm=float(distances[key]),
            current_knots=float(currents[key]),
            mode=mode,
            boat_speed=boat_speed_laden,
            boat_speed_laden=boat_speed_laden,
            boat_speed_unladen=boat_speed_unladen,
            base_consumption=base_consumption_laden,
            base_consumption_laden=base_consumption_laden,
            base_consumption_unladen=base_consumption_unladen,
        )
        segments.append(Segment(start=start, end=end, options=[option]))

    stations: List[Station] = []
    # Build set of arrival stations that should be mandatory stops for this vessel
    arrival_mandatory_stops = {s.get("end") for s in config.get("vessel_segments", []) if s.get("must_stop")}
    # Build mapping of arrival docking times per station for this vessel
    arrival_docking_times = {s.get("end"): float(s.get("docking_time_hr")) for s in config.get("vessel_segments", []) if s.get("docking_time_hr") is not None}
    arrival_force_swaps = {s.get("end"): bool(s.get("force_swap")) for s in config.get("vessel_segments", []) if s.get("force_swap") is not None}
    for name in route:
        station_cfg = config.get("stations", {}).get(name, {})
        operating = station_cfg.get("operating_hours")
        operating_tuple = None
        if operating:
            if len(operating) != 2:
                raise ValueError(f"Station {name} operating_hours must have two values")
            operating_tuple = (float(operating[0]), float(operating[1]))
        
        # Determine docking time for this station for this vessel run
        _docking_override = arrival_docking_times.get(name)
        if _docking_override is None:
            _docking_override = station_cfg.get("docking_time_hr")
        if _docking_override is None:
            _docking_override = 0.0
        dock_time_val = float(_docking_override)
        stations.append(
            Station(
                name=name,
                docking_time_hr=dock_time_val,
                swap_operation_time_hr=float(station_cfg.get("swap_operation_time_hr", 0.5)),
                # Station-level mandatory stop removed from UI; set based on per-vessel arrival flags
                mandatory_stop=(name in arrival_mandatory_stops),
                operating_hours=operating_tuple,
                available_batteries=_safe_int(station_cfg.get("available_batteries")),
                total_batteries=_safe_int(station_cfg.get("total_batteries")),
                allow_swap=_safe_bool(station_cfg.get("allow_swap", True), default=True),
                # Station force swap is also per-vessel schedule-driven
                force_swap=(bool(arrival_force_swaps.get(name)) if name in arrival_force_swaps else bool(station_cfg.get("force_swap", False))),
                partial_swap_allowed=_safe_bool(station_cfg.get("partial_swap_allowed", False), default=False),
                energy_cost_per_kwh=float(station_cfg.get("energy_cost_per_kwh", 0.25)),  # UK realistic: £0.16-£0.40/kWh
                # Charging infrastructure
                charging_power_kw=float(station_cfg.get("charging_power_kw", 0.0)),
                charging_efficiency=float(station_cfg.get("charging_efficiency", 0.95)),
                charging_allowed=_safe_bool(station_cfg.get("charging_allowed", False), default=False),
                background_charging_power_kw=float(station_cfg.get("background_charging_power_kw", 0.0)),
                background_charging_allowed=_safe_bool(station_cfg.get("background_charging_allowed", False), default=False),
                # Simplified pricing components
                swap_cost=float(station_cfg.get("swap_cost", 0.0)),
                base_service_fee=float(station_cfg.get("base_service_fee", 8.0)),
                degradation_fee_per_kwh=float(station_cfg.get("degradation_fee_per_kwh", 0.0)),
                base_charging_fee=float(station_cfg.get("base_charging_fee", 0.0)),
            )
        )

    battery_capacity = float(config["battery_capacity_kwh"])
    battery_container_capacity = float(config.get("battery_container_capacity_kwh", 2460.0))  # Default to standard container
    initial_soc = float(config.get("initial_soc_kwh", battery_capacity))
    min_soc_fraction = float(config.get("minimum_soc_fraction", 0.0))
    min_soc = battery_capacity * min_soc_fraction
    final_soc_value = config.get("final_soc_min_kwh")
    if final_soc_value is not None:
        final_soc_min = float(final_soc_value)
    else:
        final_fraction = config.get("final_soc_fraction")
        final_soc_min = (
            battery_capacity * float(final_fraction)
            if final_fraction is not None
            else min_soc
        )

    # Parse vessel specs if present
    vessel_specs = None
    if "vessel_type" in config and "vessel_gt" in config:
        vessel_type_str = config["vessel_type"]
        vessel_gt = float(config["vessel_gt"])
        # Convert string to VesselType enum
        vessel_type = next((vt for vt in VesselType if vt.value == vessel_type_str), VesselType.CARGO_CONTAINER)
        vessel_specs = VesselSpecs(vessel_type=vessel_type, gross_tonnage=vessel_gt)
    
    return FixedPathInputs(
        stations=stations,
        segments=segments,
        battery_capacity_kwh=battery_capacity,
        battery_container_capacity_kwh=battery_container_capacity,
        initial_soc_kwh=initial_soc,
        final_soc_min_kwh=final_soc_min,
        min_soc_kwh=min_soc,
        energy_cost_per_kwh=float(config["energy_cost_per_kwh"]),
        soc_step_kwh=float(config["soc_step_kwh"]),
        start_time_hr=float(config["start_time_hr"]),
        vessel_specs=vessel_specs,
        vessel_charging_power_kw=float(config.get("vessel_charging_power_kw", 1e9)),
    )


def config_to_form_frames(config: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    route = config["route"]
    segment_rows: List[Dict[str, object]] = []
    for start, end in _pairwise(route):
        key = f"{start}-{end}"
        current_value = config["currents_knots"].get(key, 0.0)
        
        # Convert to absolute value and direction
        flow_speed = abs(current_value)
        direction = "Upstream" if current_value < 0 else "Downstream"
        
        segment_rows.append(
            {
                "Start": start,
                "End": end,
                "Distance (NM)": config["distances_nm"].get(key, 0.0),
                "Flow Speed (knots)": flow_speed,
                "Direction": direction,
            }
        )
    segments_df = pd.DataFrame(segment_rows)

    station_rows: List[Dict[str, object]] = []
    for name in route:
        station_cfg = config.get("stations", {}).get(name, {})
        operating = station_cfg.get("operating_hours")
        station_rows.append(
            {
                "Station": name,
                "Allow Swap": station_cfg.get("allow_swap", True),
                "Swap Cost": station_cfg.get("swap_cost", 0.0),
                "Swap Time (hr)": station_cfg.get("swap_time_hr", 0.0),
                "Queue Time (hr)": station_cfg.get("queue_time_hr", 0.0),
                "Open Hour": operating[0] if operating else 0.0,
                "Close Hour": operating[1] if operating else 24.0,
                "Charged Batteries": station_cfg.get("available_batteries", pd.NA),
                "Total Batteries": station_cfg.get("total_batteries", station_cfg.get("available_batteries", pd.NA)),
                "Energy Cost (£/kWh)": station_cfg.get("energy_cost_per_kwh", 0.25),  # UK realistic
                "Background Charge (kW)": station_cfg.get("background_charging_power_kw", 0.0),
                "Background Charging": station_cfg.get("background_charging_allowed", False),
            }
        )
    stations_df = pd.DataFrame(station_rows)
    if not stations_df.empty:
        # Normalize and cast battery columns
        if "Charged Batteries" in stations_df.columns:
            stations_df["Charged Batteries"] = stations_df["Charged Batteries"].astype("Int64")
        if "Total Batteries" in stations_df.columns:
            stations_df["Total Batteries"] = stations_df["Total Batteries"].astype("Int64")
    return segments_df, stations_df


def form_frames_to_config(
    route_text: str,
    segments_df: pd.DataFrame,
    stations_df: pd.DataFrame,  # <-- Receives the station data now
    params: Dict[str, float],
    default_config: Dict | None = None,  # <-- Add default config to merge pricing
    vessel_segments_df: pd.DataFrame | None = None,
    vessel_route_text: str | None = None,
) -> Dict:
    # route_text is the vessel route (subset of global stations) if provided;
    # fall back to the global route if not provided
    if not route_text or not str(route_text).strip():
        # if vessel_route_text provided, use that as route
        if vessel_route_text:
            route_text = vessel_route_text
        else:
            raise ValueError("Route must contain at least two stops")
    stops = [stop.strip() for stop in str(route_text).split(",") if stop.strip()]
    # Validate vessel route stops against the station list provided by stations_df
    valid_stations = set(stations_df["Station"].astype(str).tolist()) if not stations_df.empty else set()
    invalid_stations = [s for s in stops if s not in valid_stations]
    if invalid_stations:
        raise ValueError(f"Vessel route contains stations not present in station configuration: {invalid_stations}")
    if len(stops) < 2:
        raise ValueError("Route must contain at least two stops")

    segment_records = segments_df.to_dict(orient="records")
    if len(segment_records) != len(stops) - 1:
        raise ValueError("Number of segment rows must equal number of route legs")

    distances: Dict[str, float] = {}
    currents: Dict[str, float] = {}
    for row, (start, end) in zip(segment_records, _pairwise(stops)):
        key = f"{start}-{end}"
        distances[key] = _safe_float(row.get("Distance (NM)"))
        
        flow_speed = _safe_float(row.get("Flow Speed (knots)"), 0.0)
        direction = row.get("Direction", "Downstream")
        currents[key] = -flow_speed if direction == "Upstream" else flow_speed

    station_cfg: Dict[str, Dict[str, object]] = {}
    
    # Get default pricing from default_config if available
    default_stations = {}
    if default_config:
        default_stations = default_config.get("stations", {})
    
    # --- THIS IS THE NEW, CORRECTED LOGIC ---
    # Read the station records from the stations_df DataFrame
    station_records = stations_df.to_dict(orient="records")
    for record in station_records:
        name = record.get("Station")
        if not name:
            continue
            
        # Get default pricing for this station
        default_station_pricing = default_stations.get(name, {})
            
        open_hour = _safe_float(record.get("Open Hour"), 0.0)
        close_hour = _safe_float(record.get("Close Hour"), 24.0)
            
        cfg: Dict[str, object] = {
            # Station-level mandatory/force swap removed from UI; use per-vessel segment flags instead (vessel_segments)
            "allow_swap": _safe_bool(record.get("Allow Swap"), default=True),
            "partial_swap_allowed": _safe_bool(record.get("Partial Swap"), default=False),
            "charging_allowed": _safe_bool(record.get("Charging Allowed"), default=False),
            # We'll determine background charging power with multiple fallbacks
            # Primary source: the explicit Background Charge value from the UI
            # Secondary: defaults from default_config (if available)
            # Tertiary: station's regular charging power
            # Final sensible default: 500kW if charging is allowed, otherwise 0.0
            # Note: we initialize a placeholder here and then compute the real value below
            "background_charging_allowed": False,
            "background_charging_power_kw": 0.0,
            "docking_time_hr": _safe_float(record.get("Docking Time (hr)"), 0.0),
            "swap_operation_time_hr": _safe_float(record.get("Swap Operation Time (hr)"), 0.5),
            "charging_power_kw": _safe_float(record.get("Charging Power (kW)"), 0.0),
            "operating_hours": [open_hour, close_hour],
            "energy_cost_per_kwh": _safe_float(record.get("Energy Cost (£/kWh)"), 0.09),
            
            # Read hybrid pricing from form if present, otherwise use defaults
            # This ensures pricing is preserved even if not shown in UI
            "base_service_fee": _safe_float(
                record.get("Base Service Fee"), 
                default_station_pricing.get("base_service_fee", 8.0)  # Default service fee
            ),
            "swap_cost": 0.0,  # No longer used - base_service_fee is now the per-container cost
            "degradation_fee_per_kwh": _safe_float(
                record.get("Battery Wear Fee"), 
                default_station_pricing.get("degradation_fee_per_kwh", 0.03)  # Default degradation £0.03/kWh
            ),
            "base_charging_fee": _safe_float(
                record.get("Charging Fee (£)"), 
                default_station_pricing.get("base_charging_fee", 10.0)  # Default charging fee
            ),
        }
        
        available = record.get("Charged Batteries")
        # Handle the 999 placeholder for 'unlimited'
        if available == 999:
             cfg["available_batteries"] = None
        else:
            available_int = _safe_int(available)
            if available_int is not None:
                cfg["available_batteries"] = available_int
        # Read total battery stock if provided
        total_stock = None
        total_val = record.get("Total Batteries")
        if total_val is not None:
            total_int = _safe_int(total_val)
            if total_int is not None:
                total_stock = total_int
        # If not provided, default to current charged/available value
        if total_stock is None:
            total_stock = cfg.get("available_batteries")
        cfg["total_batteries"] = total_stock
        # CRITICAL FIX: Properly read background charging power with intelligent fallbacks
        bg_power_from_ui = record.get("Background Charge (kW)", None)

        # Try to get a valid value through multiple sources
        if bg_power_from_ui is not None and str(bg_power_from_ui).strip() != "":
            bg_power = _safe_float(bg_power_from_ui, 0.0)
            if bg_power <= 0:
                bg_power = None
        else:
            bg_power = None

        # First fallback: check default_station_pricing (from prior loaded config)
        if bg_power is None or bg_power <= 0:
            bg_power = default_station_pricing.get("background_charging_power_kw", None)

        # Second fallback: use the station's regular charging power (they should match)
        if bg_power is None or bg_power <= 0:
            charging_power_val = _safe_float(record.get("Charging Power (kW)"), 0.0)
            if charging_power_val is not None and charging_power_val > 0:
                bg_power = charging_power_val

        # Third fallback: sensible default based on charging availability
        if bg_power is None or bg_power <= 0:
            if _safe_bool(record.get("Charging Allowed"), default=False):
                bg_power = 500.0  # Default background charging if charging is allowed
            else:
                bg_power = 0.0

        # FINAL: Store the value and ensure it's a valid float
        cfg["background_charging_power_kw"] = float(bg_power) if bg_power else 0.0
        cfg["background_charging_allowed"] = _safe_bool(
            record.get("Background Charging"), 
            default=(float(bg_power) > 0 if bg_power else False)
        )

        # ALSO ensure total_grid_power supports the charging capacity
        cfg["total_grid_power_kw"] = max(
            float(bg_power) if bg_power else 0.0,
            _safe_float(cfg.get("total_grid_power_kw", 0.0), 0.0)
        )
                
        station_cfg[name] = cfg

    for stop in stops:
        station_cfg.setdefault(stop, {})

    config = {
        "route": stops,
        "distances_nm": distances,
        "currents_knots": currents,
        # Legacy 'boat_speed_knots' and 'base_consumption_per_nm' removed from scenario export.
        # Use per-mode fields: 'boat_speed_laden', 'boat_speed_unladen', 'base_consumption_laden', 'base_consumption_unladen'
        "battery_capacity_kwh": params["battery_capacity"],
        "battery_container_capacity_kwh": params.get("battery_container_capacity", 2460.0),
        "initial_soc_kwh": params.get("initial_soc_kwh", params["battery_capacity"]),
        "minimum_soc_fraction": params["minimum_soc"],
        "energy_cost_per_kwh": 0.09,  # Default fallback (actual costs are per-station)
        "soc_step_kwh": params["soc_step"],
        "start_time_hr": params["start_time"],
        "stations": station_cfg,
        "vessel_type": params.get("vessel_type", "Cargo/Container"),
        "vessel_gt": params.get("vessel_gt", 2000),
        # Per-vessel speeds/consumption (laden/unladen)
        "boat_speed_laden": params.get("boat_speed_laden", params.get("boat_speed")),
        "boat_speed_unladen": params.get("boat_speed_unladen", params.get("boat_speed")),
        "base_consumption_laden": params.get("base_consumption_laden", params.get("base_consumption")),
        "base_consumption_unladen": params.get("base_consumption_unladen", params.get("base_consumption")),
        # Add per-vessel segment flags if present
        "vessel_route": [s for s in stops],
                "vessel_segments": [] if vessel_segments_df is None else [
                    {"start": str(r.get("From")), "end": str(r.get("To (Arrival)")), "mode": ("laden" if bool(r.get("Laden", True)) else "unladen"), "must_stop": bool(r.get("Must Stop", False)), "force_swap": bool(r.get("Force Swap", False)), "docking_time_hr": _safe_float(r.get("Docking (hr)"), default=0.0)}
                    for r in vessel_segments_df.to_dict(orient="records")
                ],
                "vessel_charging_power_kw": params.get("vessel_charging_power", 1000.0),
    }
    return config


def run_optimizer(config: Dict) -> Tuple[pd.DataFrame, Dict[str, object]]:
    inputs = build_inputs(config)
    optimizer = FixedPathOptimizer(inputs)
    result = optimizer.solve()

    steps_rows: List[Dict[str, object]] = []
    soc_profile: List[Tuple[str, float]] = []
    # Build vessel segment flag map for display
    vessel_segment_map = { (str(s.get("start")).strip(), str(s.get("end")).strip()): s for s in config.get("vessel_segments", []) }
    for step in result.steps:
        raw_parts = tuple(part.strip() for part in step.segment_label.split('->')) if step.segment_label else None
        start_end_tuple = (raw_parts[0], raw_parts[1]) if raw_parts is not None and len(raw_parts) == 2 else None
        # Get flow direction for this segment
        segment_key = step.segment_label.replace('->', '-')
        current = config.get('currents_knots', {}).get(segment_key, 0)
        flow_direction = "⬆️ Upstream" if current < 0 else "⬇️ Downstream"
        
        steps_rows.append(
            {
                "Station": step.station_name,
                "Segment": step.segment_label,
                "Flow": flow_direction,
                "Operation": step.operation_type,
                "Swap": step.swap_taken,
                "Charged": step.charging_taken,
                "Containers": step.num_containers_swapped,
                "Energy Charged (kWh)": step.energy_charged_kwh,
                "Arrival (hr)": step.arrival_time_hr,
                "Departure (hr)": step.departure_time_hr,
                "Berth Time (hr)": step.station_docking_time_hr,  # Total time at berth (includes all operations)
                "Scheduled Docking (hr)": vessel_segment_map.get(start_end_tuple, {}).get('docking_time_hr', step.station_docking_time_hr) if start_end_tuple else step.station_docking_time_hr,
                "Travel (hr)": step.travel_time_hr,
                "SoC Before (kWh)": step.soc_before_kwh,
                "SoC After Operation (kWh)": step.soc_after_operation_kwh,
                "SoC After Segment (kWh)": step.soc_after_segment_kwh,
                "Charged Before (BC)": getattr(step, "station_charged_before", None),
                "Charged After (BC)": getattr(step, "station_charged_after", None),
                "Total Before (BC)": getattr(step, "station_total_before", None),
                "Total After (BC)": getattr(step, "station_total_after", None),
                "Precharged (BC)": getattr(step, "containers_precharged", 0),
                "Charged During Stop (BC)": getattr(step, "containers_charged_during_stop", 0),
                "Incremental Cost": step.incremental_cost,
                "Cumulative Cost": step.cumulative_cost,
                "Hotelling Energy (kWh)": step.hotelling_energy_kwh,
                "Hotelling Power (kW)": step.hotelling_power_kw,
                # Add per-segment flags for display
                "Laden": (vessel_segment_map.get(start_end_tuple, {}).get('mode', 'laden').lower() == 'laden') if start_end_tuple else True,
                "Must Stop (Arrival)": vessel_segment_map.get(start_end_tuple, {}).get('must_stop', False) if start_end_tuple else False,
                "Force Swap (Arrival)": vessel_segment_map.get(start_end_tuple, {}).get('force_swap', False) if start_end_tuple else False,
            }
        )
        soc_profile.append((step.station_name, step.soc_before_kwh))
    if result.steps:
        terminal_segment = result.steps[-1].segment_label
        terminal_stop = terminal_segment.split("->")[-1]
        soc_profile.append((terminal_stop, result.steps[-1].soc_after_segment_kwh))

    totals = {
        "total_cost": result.total_cost,
        "total_time": result.total_time_hr,
        "finish_time": result.finish_time_hr,
        "soc_profile": soc_profile,
    }

    steps_df = pd.DataFrame(steps_rows)
    return steps_df, totals


def render_results(steps_df: pd.DataFrame, totals: Dict[str, object], config: Dict) -> None:
    st.success("✅ Optimisation Complete!")
    st.markdown("---")

    # Helper to safely coerce dataframe cell values to float (handles None / pd.NA)
    def _safe_float_from_row(r, key, fallback=0.0):
        v = r.get(key, fallback)
        try:
            if pd.isna(v):
                return float(fallback)
            return float(v)
        except Exception:
            try:
                return float(str(v))
            except Exception:
                return float(fallback)

    # --- CALCULATE TRUE COST BREAKDOWN ONCE ---
    # This matches the optimizer's actual hybrid pricing model
    total_swap_service_cost = 0.0
    total_energy_charging_cost = 0.0
    total_degradation = 0.0
    total_hotelling_cost = 0.0
    battery_cap = config.get('battery_capacity_kwh', 2460.0)
    
    swap_cost_details = []  # Store individual swap costs for table
    
    if not steps_df.empty:
        for idx, row in steps_df.iterrows():
            if row['Swap']:
                station_name = row['Station']
                station_config = config.get('stations', {}).get(station_name, {})
                soc_before_swap = _safe_float_from_row(row, 'SoC Before (kWh)')
                num_containers = row.get('Containers', 1)
                arrival_time = row['Arrival (hr)']
                
                # Use ACTUAL ΔSoC from optimizer steps, not assumed full charge
                actual_energy_charged = _safe_float_from_row(row, 'SoC After Operation (kWh)') - _safe_float_from_row(row, 'SoC Before (kWh)')
                # For swaps, we charge the difference unless specified otherwise
                energy_needed = actual_energy_charged
                
                # Simplified hybrid pricing components
                # Service fee = per-container handling cost
                base_service_fee = station_config.get('base_service_fee', 80.0)
                service_fee = base_service_fee * num_containers
                
                energy_charging = energy_needed * station_config.get('energy_cost_per_kwh', 0.09)
                degradation_fee = station_config.get('degradation_fee_per_kwh', 0.0) * energy_needed
                
                # Hotelling energy cost
                hotelling_energy = row.get('Hotelling Energy (kWh)', 0.0)
                hotelling_cost = hotelling_energy * station_config.get('energy_cost_per_kwh', 0.09)
                
                # Calculate total cost
                total_cost_this_swap = service_fee + energy_charging + degradation_fee + hotelling_cost
                
                # Accumulate totals
                total_swap_service_cost += service_fee
                total_energy_charging_cost += energy_charging
                total_degradation += degradation_fee
                total_hotelling_cost += hotelling_cost
                
                # Store details for table
                swap_cost_details.append({
                    'station_name': station_name,
                    'num_containers': num_containers,
                    'soc_before': soc_before_swap,
                    'energy_needed': energy_needed,
                    'service_fee': service_fee,
                    'energy_charging': energy_charging,
                    'degradation_fee': degradation_fee,
                    'hotelling_energy': hotelling_energy,
                    'hotelling_cost': hotelling_cost,
                    'total_cost': total_cost_this_swap,
                    'energy_rate': station_config.get('energy_cost_per_kwh', 0.09),
                    'total_batteries': station_config.get('total_batteries'),
                    'swap_time': station_config.get('swap_time_hr', 0),
                    'partial_swap_allowed': station_config.get('partial_swap_allowed', False),
                    'berth_time': row.get('Berth Time (hr)', 0),
                    'charged_before': row.get('Charged Before (BC)'),
                    'charged_after': row.get('Charged After (BC)'),
                    'precharged': row.get('Precharged (BC)'),
                })
    
    # Total of all swap-related costs
    total_all_swap_costs = float(
        total_swap_service_cost + 
        total_energy_charging_cost + 
        total_degradation +
        total_hotelling_cost
    )
    
    # Time cost and other non-swap costs
    total_time_and_other_costs = float(str(totals['total_cost'])) - total_all_swap_costs
    # --- END COST BREAKDOWN ---

    # Key Metrics Row
    st.markdown("### 📊 Journey Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(
            "💰 Total Cost", 
            f"£{totals['total_cost']:,.2f}",
            help="Total cost including energy, operations, and fees"
        )
    with col2:
        st.metric(
            "⏱️ Travel Time", 
            f"{totals['total_time']:.2f} hrs",
            help="Total journey time including docking and travel"
        )
    with col3:
        # Calculate total berth time (time spent at stations)
        total_berth_hours = 0.0
        if not steps_df.empty:
            for _, row in steps_df.iterrows():
                # Add berth time for all stations where vessel stops
                berth_time = row.get('Berth Time (hr)', 0.0)
                if berth_time > 0:
                    total_berth_hours += berth_time
        
        st.metric(
            "⚓ Total Berth Time", 
            f"{total_berth_hours:.2f} hrs",
            help="Total hours spent at berth (includes swaps, charges, mandatory stops, passenger/cargo operations)"
        )
    with col4:
        st.metric(
            "🕐 Arrival Time", 
            f"{totals['finish_time']:.2f} hrs",
            help="Clock time when journey completes"
        )
    with col5:
        swaps_count = steps_df[steps_df['Swap'] == True].shape[0] if not steps_df.empty else 0
        charges_count = steps_df[steps_df['Charged'] == True].shape[0] if not steps_df.empty else 0
        st.metric(
            "🔋 Operations", 
            f"{swaps_count}S / {charges_count}C",
            help=f"Swaps: {swaps_count}, Charges: {charges_count}"
        )
    # Show Start SoC and Min SoC for clarity
    battery_cap = config.get('battery_capacity_kwh', 0)
    start_soc = config.get('initial_soc_kwh', battery_cap)
    min_soc_frac = config.get('minimum_soc_fraction', 0.0)
    start_pct = 100 * start_soc / (battery_cap if battery_cap > 0 else 1)
    st.markdown(f"**Start SoC:** {start_soc:,.0f} kWh ({start_pct:.0f}%) — **Min SoC (reserve):** {min_soc_frac*100:.1f}% ({battery_cap*min_soc_frac:,.0f} kWh)")

    st.markdown("---")

    if not steps_df.empty:
        # Enhanced summary with swap breakdown
        st.markdown("### 🔋 Battery Swap Summary")
        if swap_cost_details:
            swap_col1, swap_col2, swap_col3 = st.columns(3)
            
            with swap_col1:
                st.metric(
                    "🔄 Total Swaps",
                    len(swap_cost_details),
                    help="Number of battery swaps during journey"
                )
            
            with swap_col2:
                st.metric(
                    "💵 Swap Costs",
                    f"£{total_all_swap_costs:.2f}",
                    help="Total of all swap-related costs (service + energy + degradation + hotelling)"
                )
            
            with swap_col3:
                avg_swap_cost = total_all_swap_costs / len(swap_cost_details) if swap_cost_details else 0
                st.metric(
                    "📊 Avg Swap Cost",
                    f"£{avg_swap_cost:.2f}",
                    help="Average total cost per swap including all fees"
                )
            
            # Detailed swap table with COMPLETE cost breakdown
            st.markdown("#### 📍 Swap Locations & Details")
            swap_table_data = []
            total_containers_swapped = 0
            
            for detail in swap_cost_details:
                total_containers_swapped += detail['num_containers']
                
                # Determine swap mode
                total_num_containers = int(battery_cap / config.get('battery_container_capacity_kwh', 2460))
                swap_mode = "🔄 Partial" if (detail['partial_swap_allowed'] and detail['num_containers'] < total_num_containers) else "📦 Full Set"
                
                soc_before_pct = (detail['soc_before'] / battery_cap) * 100
                
                swap_table_data.append({
                    'Station': detail['station_name'],
                    'Total Batteries': detail.get('total_batteries', pd.NA),
                    'Mode': swap_mode,
                    'Containers': detail['num_containers'],
                    'Berth Time': f"{detail['berth_time']:.2f} hr",
                    'Returned SoC': f"{detail['soc_before']:.0f} kWh ({soc_before_pct:.0f}%)",
                    'Energy Charged': f"{detail['energy_needed']:.0f} kWh",
                    'Charged Before': detail.get('charged_before', pd.NA),
                    'Charged After': detail.get('charged_after', pd.NA),
                    'Hotelling': f"{detail['hotelling_energy']:.0f} kWh" if detail['hotelling_energy'] > 0 else "—",
                    'Precharged': detail.get('precharged', 0),
                    'Service Fee': f"£{detail['service_fee']:.2f}",
                    'Energy Cost': f"£{detail['energy_charging']:.2f}",
                    'Hotelling Cost': f"£{detail['hotelling_cost']:.2f}" if detail['hotelling_cost'] > 0 else "—",
                    'Battery Wear': f"£{detail['degradation_fee']:.2f}",
                    'Total': f"£{detail['total_cost']:.2f}",
                })
            
            if swap_table_data:
                swap_df = pd.DataFrame(swap_table_data)
                
                # Get vessel info for display
                vessel_type_display = config.get('vessel_type', 'Cargo/Container')
                vessel_gt_display = config.get('vessel_gt', 2000)
                
                hotelling_info = ""
                if total_hotelling_cost > 0:
                    hotelling_info = f"\n\n⚡ **Hotelling Energy**: {vessel_type_display} ({vessel_gt_display:,.0f} GT) consumed energy for onboard services (HVAC, lighting, etc.) during berth time. Total hotelling cost: £{total_hotelling_cost:.2f}"
                
                # Calculate partial vs full swap info
                total_num_containers = int(battery_cap / config.get('battery_container_capacity_kwh', 2460))
                partial_swap_stations = [d for d in swap_cost_details if d['partial_swap_allowed']]
                swap_mode_info = ""
                if partial_swap_stations:
                    swap_mode_info = f"\n\n🔄 **Partial Swap Active**: Swapping only depleted containers (vs. full set of {total_num_containers} BC). This reduces service fees significantly!"
                
                berth_time_info = "\n\n⏱️ **Berth Time**: Total time vessel is docked at station, includes swap operations, passenger boarding/offloading, cargo operations, and any mandatory stop requirements."
                
                st.info(f"""
                📦 **Total Battery Containers Swapped**: {total_containers_swapped} BC across {len(swap_cost_details)} station(s)
                
                💡 **Cost Breakdown**:
                • **Service Fee**: £{total_swap_service_cost:.2f} - Swap operations (scales with # containers)
                • **Energy Cost**: £{total_energy_charging_cost:.2f} - Electricity for charging (SoC-based billing)
                • **Battery Wear**: £{total_degradation:.2f} - Battery degradation/cycling cost
                • **Hotelling**: £{total_hotelling_cost:.2f} - Onboard services energy (HVAC, lights, pumps, etc.){hotelling_info}{swap_mode_info}{berth_time_info}
                """)
                
                st.dataframe(
                    swap_df,
                    width='stretch',
                    hide_index=True
                )
        else:
            st.info("✨ **No battery swaps needed!** The journey can be completed on a single charge.")
        
        st.markdown("---")
        
        # Two-column layout for details and chart
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            st.markdown("### 🛤️ Detailed Journey Plan")
            
            # Don't convert booleans to text - keep them as-is for CheckboxColumn
            display_df = steps_df.copy()
            # Normalize station inventory columns for better UI:
            # Replace None/NaN with a readable dash and turn counts to integers
            inv_cols = [
                'Charged Before (BC)', 'Charged After (BC)',
                'Total Before (BC)', 'Total After (BC)',
                'Precharged (BC)', 'Charged During Stop (BC)'
            ]
            for col in inv_cols:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: '—' if pd.isna(x) or x is None else int(x))
            
            st.dataframe(
                display_df,
                width='stretch',
                column_config={
                    "Station": st.column_config.TextColumn("Station", width="small"),
                    "Segment": st.column_config.TextColumn("Segment", width="medium"),
                    "Flow": st.column_config.TextColumn("Flow", width="small"),
                    "Operation": st.column_config.TextColumn("Operation", width="small"),
                    "Swap": st.column_config.CheckboxColumn("Swap?", width="small"),
                    "Charged": st.column_config.CheckboxColumn("Charged?", width="small"),
                    "Arrival (hr)": st.column_config.NumberColumn("Arrival", format="%.2f hr"),
                    "Departure (hr)": st.column_config.NumberColumn("Departure", format="%.2f hr"),
                    "Berth Time (hr)": st.column_config.NumberColumn("Berth Time", format="%.2f hr", help="Total time at berth including all operations"),
                    "Travel (hr)": st.column_config.NumberColumn("Travel", format="%.2f hr"),
                    "SoC Before (kWh)": st.column_config.NumberColumn("SoC Before", format="%.1f kWh"),
                    "SoC After Operation (kWh)": st.column_config.NumberColumn("SoC After Op", format="%.1f kWh"),
                    "SoC After Segment (kWh)": st.column_config.NumberColumn("SoC After Travel", format="%.1f kWh"),
                    "Scheduled Docking (hr)": st.column_config.NumberColumn("Scheduled Docking", format="%.2f hr"),
                    "Incremental Cost": st.column_config.NumberColumn("Step Cost", format="£%.2f"),
                    "Cumulative Cost": st.column_config.NumberColumn("Total Cost", format="£%.2f"),
                    "Charged Before (BC)": st.column_config.TextColumn("Charged Before", width="small"),
                    "Charged After (BC)": st.column_config.TextColumn("Charged After", width="small"),
                    "Total Before (BC)": st.column_config.TextColumn("Total Before", width="small"),
                    "Total After (BC)": st.column_config.TextColumn("Total After", width="small"),
                    "Precharged (BC)": st.column_config.TextColumn("Precharged", width="small"),
                    "Charged During Stop (BC)": st.column_config.TextColumn("Charged During Stop", width="small"),
                    "Laden": st.column_config.CheckboxColumn("Laden", width="small"),
                    "Must Stop (Arrival)": st.column_config.CheckboxColumn("Must Stop (Arrival)", width="small"),
                    "Force Swap (Arrival)": st.column_config.CheckboxColumn("Force Swap (Arrival)", width="small"),
                },
                hide_index=True
            )
        
        with col_right:
            st.markdown("### 📈 State of Charge Profile")
            
            # Build timeline-based SoC profile
            soc_timeline_data = []
            for idx, row in steps_df.iterrows():
                arrival_time = row['Arrival (hr)']
                departure_time = row['Departure (hr)']
                soc_before = row['SoC Before (kWh)']
                soc_after_op = row['SoC After Operation (kWh)']
                station = row['Station']
                
                # Add arrival point
                soc_timeline_data.append({
                    'Time (hr)': arrival_time,
                    'SoC (kWh)': soc_before,
                    'Station': station,
                    'Event': 'Arrival'
                })
                
                # Add departure point (after swap/charge operations)
                soc_timeline_data.append({
                    'Time (hr)': departure_time,
                    'SoC (kWh)': soc_after_op,
                    'Station': station,
                    'Event': 'Departure'
                })
            
            # Add final arrival at destination
            if len(steps_df) > 0:
                last_row = steps_df.iloc[-1]
                final_soc = last_row['SoC After Segment (kWh)']
                final_time = last_row['Departure (hr)'] + last_row['Travel (hr)']
                final_station = last_row['Segment'].split('->')[-1].strip()
                
                soc_timeline_data.append({
                    'Time (hr)': final_time,
                    'SoC (kWh)': final_soc,
                    'Station': final_station,
                    'Event': 'Final Arrival'
                })
            
            soc_timeline_df = pd.DataFrame(soc_timeline_data)
            
            # Create line chart with time axis
            st.line_chart(
                soc_timeline_df.set_index('Time (hr)')[['SoC (kWh)']], 
                height=400
            )
            
            st.markdown("### 💡 Quick Insights")
            avg_soc = soc_timeline_df["SoC (kWh)"].mean()
            min_soc = soc_timeline_df["SoC (kWh)"].min()
            max_soc = soc_timeline_df["SoC (kWh)"].max()
            total_journey_time = soc_timeline_df["Time (hr)"].max() - soc_timeline_df["Time (hr)"].min()
            
            st.info(f"""
            - **Journey Time**: {total_journey_time:.2f} hours
            - **Average SoC**: {avg_soc:.1f} kWh
            - **Minimum SoC**: {min_soc:.1f} kWh
            - **Maximum SoC**: {max_soc:.1f} kWh
            """)
        
        st.markdown("---")
        # Station inventory timeline
        st.markdown("### 🧭 Station Inventory Timeline")
        # Show vessel info for clarity
        vessel_type_display = config.get('vessel_type', None)
        vessel_gt_display = config.get('vessel_gt', None)
        if vessel_type_display is not None or vessel_gt_display is not None:
            st.markdown(f"**Vessel:** {vessel_type_display} ({vessel_gt_display} GT)")
        st.caption("Note: '—' indicates value is not available or unlimited; numeric values are displayed where computed.")
        station_timeline = []
        for idx, row in steps_df.iterrows():
            st_cfg = config.get('stations', {}).get(row['Station'], {})
            def fmt_inv(col, cfg_key):
                val = row.get(col)
                if pd.isna(val) or val is None:
                    # If station config shows None (unlimited), display 'Unlimited'
                    if st_cfg.get(cfg_key) is None:
                        return 'Unlimited'
                    return '—'
                return val
            station_timeline.append({
                'Time (hr)': row['Arrival (hr)'],
                'Station': row['Station'],
                'Operation': row['Operation'],
                'Containers Swapped': row['Containers'],
                'Energy Charged (kWh)': row['Energy Charged (kWh)'],
                'Charged Before (BC)': fmt_inv('Charged Before (BC)', 'available_batteries'),
                'Charged After (BC)': fmt_inv('Charged After (BC)', 'available_batteries'),
                'Total Before (BC)': fmt_inv('Total Before (BC)', 'total_batteries'),
                'Total After (BC)': fmt_inv('Total After (BC)', 'total_batteries'),
                'Precharged (BC)': row.get('Precharged (BC)'),
                'Charged During Stop (BC)': row.get('Charged During Stop (BC)'),
                'Laden': row.get('Laden', True),
                'Force Swap (Arrival)': row.get('Force Swap (Arrival)', False),
            })
        station_timeline_df = pd.DataFrame(station_timeline)
        if not station_timeline_df.empty:
            st.dataframe(station_timeline_df, width='stretch', hide_index=True)
            # Build a compact station summary
            station_summary = {}
            for _, row in station_timeline_df.iterrows():
                name = row['Station']
                summary = station_summary.setdefault(name, {
                    'initial_charged': None,
                    'final_charged': None,
                    'total_swapped': 0,
                    'total_precharged': 0,
                    'total_charged_during_stop': 0,
                    'total_force_swaps': 0,
                })
                if summary['initial_charged'] is None:
                    summary['initial_charged'] = row['Charged Before (BC)'] if row['Charged Before (BC)'] != '—' else None
                summary['final_charged'] = row['Charged After (BC)']
                summary['total_swapped'] += int(row['Containers Swapped']) if not pd.isna(row['Containers Swapped']) else 0
                summary['total_precharged'] += int(row['Precharged (BC)']) if not pd.isna(row['Precharged (BC)']) and row['Precharged (BC)'] != '—' else 0
                summary['total_charged_during_stop'] += int(row['Charged During Stop (BC)']) if not pd.isna(row['Charged During Stop (BC)']) and row['Charged During Stop (BC)'] != '—' else 0
                summary['total_force_swaps'] += 1 if bool(row.get('Force Swap (Arrival)', False)) else 0

            summary_rows = []
            for name, s in station_summary.items():
                st_cfg = config.get('stations', {}).get(name, {})
                init_val = '—' if s['initial_charged'] is None else int(s['initial_charged'])
                if s['initial_charged'] is None and st_cfg.get('available_batteries') is None:
                    init_val = 'Unlimited'
                final_val = '—' if s['final_charged'] is None or s['final_charged'] == '—' else int(s['final_charged'])
                if (s['final_charged'] is None or s['final_charged']=='—') and st_cfg.get('available_batteries') is None:
                    final_val = 'Unlimited'
                summary_rows.append({
                    'Station': name,
                    'Initial Charged (BC)': init_val,
                    'Final Charged (BC)': final_val,
                    'Total Swapped (BC)': s['total_swapped'],
                    'Total Precharged (BC)': s['total_precharged'],
                    'Total Charged During Stops (BC)': s['total_charged_during_stop'],
                    'Total Forced Swaps (BC)': s['total_force_swaps'],
                })
            summary_df = pd.DataFrame(summary_rows)
            if not summary_df.empty:
                st.markdown('#### 🔢 Station Summary')
                if vessel_type_display is not None or vessel_gt_display is not None:
                    st.caption(f"Vessel: {vessel_type_display} ({vessel_gt_display} GT)")
                st.caption("Note: '—' indicates value is not available or unlimited; counts are integers when computed.")
                st.dataframe(summary_df, width='stretch', hide_index=True)
        
        # Visualization Section
        st.markdown("### 📊 Decision Analysis Visualizations")
        
        viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs([
            "🔋 Energy Balance", 
            "💰 Cost Breakdown", 
            "📊 Segment Analysis",
            "🔄 Swap Decisions"
        ])
        
        with viz_tab1:
            st.markdown("#### Energy Balance Per Segment")
            
            # Build energy balance data
            energy_data = []
            cumulative_energy = 0
            battery_cap = config['battery_capacity_kwh']
            min_soc_kwh = battery_cap * config.get('minimum_soc_fraction', 0.2)
            
            # Note: _safe_float_from_row is defined at start of render_results; use it here

            for idx, row in steps_df.iterrows():
                segment = row['Segment']
                # Use departure SoC (after any swap/charge operation) to compute travel energy
                if 'SoC After Operation (kWh)' in row:
                    soc_departure = _safe_float_from_row(row, 'SoC After Operation (kWh)')
                else:
                    soc_departure = _safe_float_from_row(row, 'SoC Before (kWh)')
                soc_after = _safe_float_from_row(row, 'SoC After Segment (kWh)')
                # Energy consumed during travel = SoC at departure - SoC at arrival
                energy_consumed = soc_departure - soc_after
                
                cumulative_energy += energy_consumed
                
                energy_data.append({
                    'Segment': segment,
                    'Energy Consumed (kWh)': energy_consumed,
                    'SoC Before (kWh)': soc_departure,
                    'SoC After (kWh)': soc_after,
                    'Cumulative Energy (kWh)': cumulative_energy,
                    'Swapped': '✅' if row['Swap'] else '—'
                })
            
            energy_df = pd.DataFrame(energy_data)
            
            # Bar chart: Energy consumed per segment
            st.markdown("**Energy Consumption by Segment**")
            chart_data = energy_df[['Segment', 'Energy Consumed (kWh)']].set_index('Segment')
            st.bar_chart(chart_data, height=300)
            
            # Show table with details
            st.dataframe(
                energy_df,
                width='stretch',
                column_config={
                    "Segment": st.column_config.TextColumn("Segment", width="medium"),
                    "Energy Consumed (kWh)": st.column_config.NumberColumn("Energy Used", format="%.1f kWh"),
                    "SoC Before (kWh)": st.column_config.NumberColumn("SoC Before", format="%.1f kWh"),
                    "SoC After (kWh)": st.column_config.NumberColumn("SoC After", format="%.1f kWh"),
                    "Cumulative Energy (kWh)": st.column_config.NumberColumn("Cumulative", format="%.1f kWh"),
                    "Swapped": st.column_config.TextColumn("Swap", width="small"),
                },
                hide_index=True
            )
            
            # Explanation
            st.info(f"""
            **📌 Energy Analysis:**
            - Battery Capacity: {battery_cap:.1f} kWh
            - Minimum SoC Threshold: {min_soc_kwh:.1f} kWh
            - Total Energy Consumed: {cumulative_energy:.1f} kWh
            - Segments with Swaps: {energy_df['Swapped'].str.contains('✅').sum()}
            
            **Why Swaps Were Needed:**
            If SoC After falls below {min_soc_kwh:.1f} kWh or segment energy exceeds remaining capacity, a swap is required.
            
            **Note on how "Energy Used" is calculated:**
            - The energy consumed per segment is computed as **SoC at departure (after any swap/charging)** minus **SoC at arrival**, i.e., it represents the true energy used for travel and excludes energy added by swaps/charging before departure.
            """)
        
        with viz_tab2:
            st.markdown("#### Cost Structure Analysis")
            
            # Extract cost components with ACTUAL energy charged
            cost_breakdown = []
            total_swap_service_cost = 0
            total_energy_charging_cost = 0
            total_degradation = 0
            
            for idx, row in steps_df.iterrows():
                if row['Swap']:
                    station_name = row['Station']
                    station_config = config.get('stations', {}).get(station_name, {})
                    
                    # Get actual energy needed (not full battery!)
                    soc_before_swap = row['SoC Before (kWh)']
                    energy_needed = battery_cap - soc_before_swap  # Only charge what's missing
                    
                    # Get number of containers swapped
                    num_containers = row.get('Containers', 10)
                    
                    # Simplified service fee = cost per container
                    base_service_fee = station_config.get('base_service_fee', 80.0)
                    service_fee = base_service_fee * num_containers
                    
                    energy_cost_per_kwh = station_config.get('energy_cost_per_kwh', 0.09)
                    energy_charging = energy_needed * energy_cost_per_kwh
                    degradation_fee = station_config.get('degradation_fee_per_kwh', 0.0) * energy_needed
                    
                    total_swap_service_cost += service_fee
                    total_energy_charging_cost += energy_charging
                    total_degradation += degradation_fee
                    
                    # Build cost breakdown with simplified columns
                    swap_row = {
                        'Station': station_name,
                        'Containers': num_containers,
                        'Energy Charged (kWh)': f"{energy_needed:.0f}",
                        'Service Fee': f"£{service_fee:.2f}",
                        'Energy Cost': f"£{energy_charging:.2f}",
                        'Battery Wear': f"£{degradation_fee:.2f}" if degradation_fee > 0 else "—",
                        'Total': f"£{service_fee + energy_charging + degradation_fee:.2f}",
                        'Rate': f"£{energy_cost_per_kwh:.3f}/kWh"
                    }
                    
                    cost_breakdown.append(swap_row)
            
            if cost_breakdown:
                cost_df = pd.DataFrame(cost_breakdown)
                
                # Simplified cost components chart
                st.markdown("**💰 Total Cost Breakdown**")
                
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    # Main cost categories
                    main_costs = {
                        'Service Fee': total_swap_service_cost,
                        'Energy Charging': total_energy_charging_cost,
                    }
                    
                    # Add hotelling if present
                    if total_hotelling_cost > 0:
                        main_costs['Hotelling Energy'] = total_hotelling_cost
                    
                    # Add degradation if used
                    if total_degradation > 0:
                        main_costs['Battery Wear'] = total_degradation
                    
                    main_df = pd.DataFrame(list(main_costs.items()), columns=['Category', 'Cost (£)'])
                    st.bar_chart(main_df.set_index('Category'), height=250)
                
                with col_chart2:
                    st.markdown("**💵 Cost Summary**")
                    st.metric("Service Fees", f"£{total_swap_service_cost:.2f}")
                    st.metric("Energy Charging", f"£{total_energy_charging_cost:.2f}")
                    if total_hotelling_cost > 0:
                        st.metric("Hotelling Energy", f"£{total_hotelling_cost:.2f}")
                    if total_degradation > 0:
                        st.metric("Battery Wear", f"£{total_degradation:.2f}")
                    
                    grand_total_swap = (total_swap_service_cost + total_energy_charging_cost + 
                                       total_degradation + total_hotelling_cost)
                    st.metric("**Grand Total**", f"£{grand_total_swap:.2f}", 
                             help="Total of all swap-related costs including hotelling")
                
                # Detailed cost table
                st.markdown("---")
                st.markdown("**📋 Detailed Swap Costs by Station**")
                st.dataframe(
                    cost_df,
                    width='stretch',
                    hide_index=True
                )
                
                hotelling_note = ""
                if total_hotelling_cost > 0:
                    hotelling_note = f"\n- **Hotelling Energy**: £{total_hotelling_cost:.2f} - Energy consumed for onboard services (HVAC, lighting, etc.) during dwell time at berth"
                
                st.info(f"""
                **💡 Cost Breakdown Explanation:**
                - **Service Fees**: £{total_swap_service_cost:.2f} - Swap operations (scales with # containers swapped)
                - **Energy Charging**: £{total_energy_charging_cost:.2f} - Actual electricity cost for energy recharged{hotelling_note}
                - **Battery Wear**: £{total_degradation:.2f} - Battery degradation/cycling cost
                - **Total Swap Costs**: £{grand_total_swap:.2f}
                
                **Note**: Service fee includes physical handling + operations and scales with the number of containers swapped.
                Energy cost is based on **actual kWh charged** from current SoC to 100%.
                """)
            else:
                st.info("✨ **No swaps performed!** Zero swap costs - journey completed on initial charge.")
        
        with viz_tab3:
            st.markdown("#### Segment-by-Segment Analysis")
            
            # Build simpler, clearer analysis
            segment_analysis = []
            for idx, row in steps_df.iterrows():
                segment = row['Segment']
                swapped = row['Swap']
                # Use departure SoC (after any swap/charging) as available energy for the segment
                # Convert to float safely using helper
                soc_departure = _safe_float_from_row(row, 'SoC After Operation (kWh)') if 'SoC After Operation (kWh)' in row else _safe_float_from_row(row, 'SoC Before (kWh)')
                soc_after = _safe_float_from_row(row, 'SoC After Segment (kWh)')
                
                # Get segment details
                segment_key = segment.replace('->', '-')
                distance = config.get('distances_nm', {}).get(segment_key, 0)
                current = config.get('currents_knots', {}).get(segment_key, 0)
                # Use conservative (Laden) consumption by default for route analysis
                base_consumption = config.get('base_consumption_laden', config.get('base_consumption_unladen', 220))
                
                # Calculate actual energy consumed for travel: departure SoC - arrival SoC
                energy_consumed = soc_departure - soc_after
                
                # Calculate what was required for this segment using the same energy model
                energy_required, _ = compute_segment_energy(
                    distance_nm=distance,
                    current_knots=current,
                    mode='laden' if row.get('Laden', True) else 'unladen',
                    base_consumption_laden=config.get('base_consumption_laden', config.get('base_consumption', 245.0)),
                    base_consumption_unladen=config.get('base_consumption_unladen', config.get('base_consumption', 207.0)),
                    boat_speed_laden=config.get('boat_speed_laden', config.get('boat_speed', 5.0)),
                    boat_speed_unladen=config.get('boat_speed_unladen', config.get('boat_speed', 6.0)),
                )
                
                # Status indicators
                if swapped:
                    status = "🔋 Swapped before segment"
                    battery_status = f"Recharged to {battery_cap:.0f} kWh"
                elif soc_after < (battery_cap * 0.2):
                    status = "⚠️ Low battery after segment"
                    battery_status = f"Dropped to {soc_after:.0f} kWh"
                else:
                    status = "✅ Sufficient battery"
                    battery_status = f"Ended at {soc_after:.0f} kWh"
                
                flow_direction = "⬆️ Upstream (harder)" if current < 0 else "⬇️ Downstream (easier)"
                
                segment_analysis.append({
                    'Laden': row.get('Laden', True),
                    'Segment': segment,
                    'Distance': f"{distance:.1f} NM",
                    'Flow': flow_direction,
                    'Required': f"{energy_required:.0f} kWh",
                    'Available': f"{soc_departure:.0f} kWh",
                    'Used': f"{energy_consumed:.0f} kWh",
                    'Remaining': f"{soc_after:.0f} kWh",
                    'Status': status
                })
            
            segment_df = pd.DataFrame(segment_analysis)
            
            st.markdown("**📊 Journey Breakdown**")
            st.info("""
            This shows what happened at each segment:
            - **Required**: Energy needed for this segment (accounting for river flow)
            - **Available**: Battery charge at start of segment
            - **Used**: Actual energy consumed during travel
            - **Remaining**: Battery charge at end of segment
            """)
            
            st.dataframe(
                segment_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Segment": st.column_config.TextColumn("Segment", width="small"),
                    "Distance": st.column_config.TextColumn("Distance", width="small"),
                    "Flow": st.column_config.TextColumn("River Flow", width="medium"),
                    "Required": st.column_config.TextColumn("Required", width="small"),
                    "Available": st.column_config.TextColumn("Had", width="small"),
                    "Used": st.column_config.TextColumn("Used", width="small"),
                    "Remaining": st.column_config.TextColumn("Left", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="medium"),
                }
            )
            
            # Energy efficiency chart
            st.markdown("**⚡ Energy Efficiency by Segment**")
            
            efficiency_data = []
            for idx, row in steps_df.iterrows():
                segment = row['Segment']
                segment_key = segment.replace('->', '-')
                distance = config.get('distances_nm', {}).get(segment_key, 0)
                soc_departure = _safe_float_from_row(row, 'SoC After Operation (kWh)') if 'SoC After Operation (kWh)' in row else _safe_float_from_row(row, 'SoC Before (kWh)')
                soc_after = _safe_float_from_row(row, 'SoC After Segment (kWh)')
                energy_consumed = soc_departure - soc_after
                
                # Energy per nautical mile
                energy_per_nm = energy_consumed / distance if distance > 0 else 0
                
                efficiency_data.append({
                    'Segment': segment,
                    'kWh per NM': energy_per_nm
                })
            
            efficiency_df = pd.DataFrame(efficiency_data)
            chart_data = efficiency_df.set_index('Segment')
            st.bar_chart(chart_data, height=250)
            
            st.caption("📈 Higher values = more energy consumed (upstream segments use more energy)")
        
        
        with viz_tab4:
            st.markdown("#### Swap Decision Analysis")
            
            if swap_cost_details:
                # Build swap analysis
                swap_analysis = []
                for detail in swap_cost_details:
                    remaining_pct = (detail['soc_before'] / battery_cap) * 100
                    
                    swap_analysis.append({
                        'Station': detail['station_name'],
                        'SoC Before Swap': f"{detail['soc_before']:.1f} kWh ({remaining_pct:.1f}%)",
                        'Charged Before': detail.get('charged_before', pd.NA),
                        'Charged After': detail.get('charged_after', pd.NA),
                        'Energy Rate': f"£{detail['energy_rate']:.3f}/kWh",
                        'Service Fee': f"£{detail['service_fee']:.2f}",
                        'Energy Cost': f"£{detail['energy_charging']:.2f}",
                        'Total Cost': f"£{detail['total_cost']:.2f}",
                        'Decision': '✅ Swapped'
                    })
                
                swap_analysis_df = pd.DataFrame(swap_analysis)
                
                st.dataframe(
                    swap_analysis_df,
                    width='stretch',
                    hide_index=True
                )
                
                avg_soc_before = sum([d['soc_before'] for d in swap_cost_details]) / len(swap_cost_details)
                st.success(f"""
                **✅ Swap Optimization Summary:**
                - Total swaps performed: {len(swap_cost_details)}
                - Average remaining SoC at swap: {avg_soc_before:.1f} kWh ({(avg_soc_before/battery_cap)*100:.1f}%)
                - Optimizer chose these stations to minimize total cost while ensuring journey completion
                - Hybrid pricing model applied: service fees + energy (SoC-based) + location premiums + peak surcharges - discounts
                """)
            else:
                st.info("✨ **No swaps needed!** Battery capacity sufficient for entire journey.")

        st.markdown("---")
        
        # Download buttons
        st.markdown("### 📥 Export Results")
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                "📄 Download Journey Plan (CSV)",
                data=steps_df.to_csv(index=False),
                file_name="journey_plan.csv",
                mime="text/csv",
                width='stretch',
                key="download_journey_csv",
                help="Download detailed journey plan as CSV"
            )
            # Indicate how the default was computed (container size × # containers)
            pass
        
        with col2:
            st.download_button(
                "📋 Download Scenario (JSON)",
                data=json.dumps(config, indent=2),
                file_name="scenario.json",
                mime="application/json",
                width='stretch',
                key="download_scenario_json",
                help="Save scenario configuration for later use"
            )
        
        with col3:
            # Create summary report
            summary = f"""Marine Vessels Journey Summary
{'='*50}
Total Cost: £{totals['total_cost']:.2f}
Total Time: {totals['total_time']:.2f} hours
Arrival Time: {totals['finish_time']:.2f} hours
Battery Swaps: {swaps_count}

Average SoC: {avg_soc:.1f} kWh
Minimum SoC: {min_soc:.1f} kWh
Maximum SoC: {max_soc:.1f} kWh
"""
            st.download_button(
                "📊 Download Summary (TXT)",
                data=summary,
                file_name="journey_summary.txt",
                mime="text/plain",
                width='stretch',
                key="download_summary_txt",
                help="Download summary report as text file"
            )


def main() -> None:
    st.set_page_config(
        page_title="Marine Vessels Battery Swapping",
        layout="wide",
        page_icon="🚢",
        initial_sidebar_state="expanded"
    )
    # Default run button state to avoid UnboundLocalError when used in multiple branches
    run_button = False

    # Initialize authentication system
    auth_system = get_auth_system()

    # Check session validity
    session_token = st.session_state.get('session_token')
    if session_token:
        username = auth_system.validate_session(session_token)
        if username:
            st.session_state.authenticated = True
            st.session_state.username = username
        else:
            # Session expired or invalid
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.session_token = None

    # Authentication check + sidebar UI
    # The sidebar controls Login/Profile and the 'Run Optimisation' button
    with st.sidebar:
        if not st.session_state.get('authenticated', False):
            show_login_page()
        else:
            show_user_profile()
            show_logout_button()

        st.markdown("---")
        st.header("⚙️ Controls")
        # Provide Run button in the sidebar - only actionable when user is authenticated
        sidebar_run_button = st.button(
            "🚀 Run Optimisation",
            type="primary",
            use_container_width=True,
            key="sidebar_run_optimisation_button",
            help="Click to compute the optimal battery swap strategy"
        )
        if not st.session_state.get('authenticated', False):
            # disable run action if not authenticated
            sidebar_run_button = False

    # Main app content (only shown when authenticated)
    st.title("🚢 Marine Vessels Battery Swapping Optimiser")
    st.markdown("---")

    default_config = load_default_config()

    # --- Callback helpers used by Sync/Align buttons to mutate widget-backed state safely ---
    def set_battery_from_containers(vessel_key: str) -> None:
        # Read current containers & container size from session (widget) and update the primary battery capacity
        containers = st.session_state.get(f"num_containers_{vessel_key}", 1)
        cont_size = st.session_state.get(f"battery_container_capacity_{vessel_key}", 2460.0)
        st.session_state[f"battery_capacity_total_{vessel_key}"] = cont_size * containers

    def set_containers_from_battery(vessel_key: str) -> None:
        battery_cap = st.session_state.get(f"battery_capacity_total_{vessel_key}", 0.0)
        cont_size = st.session_state.get(f"battery_container_capacity_{vessel_key}", 2460.0)
        computed = int(math.ceil(battery_cap / cont_size)) if cont_size > 0 else 12
        st.session_state[f"num_containers_{vessel_key}"] = computed

    # align_to_optimizer_callback removed per simplified UX: users edit battery and container count directly
    
    # ========================================
    # VESSEL CONFIGURATION
    # ========================================
    with st.expander("🚢 **VESSEL CONFIGURATION**", expanded=True):
        vessel_type_str = st.selectbox(
            "**Vessel Type**",
            options=[vt.value for vt in VesselType],
            index=3,  # Default to Container vessels
            key="vessel_type_select",
            help="Select vessel type - all other settings will adjust automatically"
        )
        # Convert string back to enum
        vessel_type = next(vt for vt in VesselType if vt.value == vessel_type_str)
        
        # Auto-set defaults based on vessel type
        if vessel_type in [VesselType.CARGO_CONTAINER]:
            default_gt = 5000
            default_containers = 10
            default_consumption = 50.0
            default_speed = 12.0
        elif vessel_type in [VesselType.BULK_CARRIER, VesselType.GENERAL_CARGO]:
            default_gt = 4000
            default_containers = 8
            default_consumption = 40.0
            default_speed = 11.0
        elif vessel_type in [VesselType.TANKER, VesselType.CRUDE_OIL_TANKER]:
            default_gt = 8000
            default_containers = 12
            default_consumption = 70.0
            default_speed = 10.0
        elif vessel_type in [VesselType.PASSENGER_FERRY]:
            default_gt = 2000
            default_containers = 4
            default_consumption = 100.0
            default_speed = 15.0
        elif vessel_type in [VesselType.CRUISE_SHIP]:
            default_gt = 15000
            default_containers = 20
            default_consumption = 150.0
            default_speed = 14.0
        elif vessel_type in [VesselType.SERVICE_VESSELS, VesselType.OFFSHORE_SUPPLY]:
            default_gt = 1500
            default_containers = 3
            default_consumption = 250.0
            default_speed = 8.0
        elif vessel_type in [VesselType.RO_RO]:
            default_gt = 6000
            default_containers = 10
            default_consumption = 60.0
            default_speed = 13.0
        else:  # OTHER, AUTO_CARRIER, etc.
            default_gt = 3000
            default_containers = 6
            default_consumption = 50.0
            default_speed = 10.0
        
        # Auto-calculate recommended docking times based on vessel type
        if vessel_type in [VesselType.CARGO_CONTAINER, VesselType.BULK_CARRIER]:
            recommended_docking_time = 2.0  # hours
        elif vessel_type in [VesselType.TANKER, VesselType.CRUDE_OIL_TANKER]:
            recommended_docking_time = 2.5  # hours
        elif vessel_type in [VesselType.PASSENGER_FERRY]:
            recommended_docking_time = 1.0  # hours - faster turnaround
        elif vessel_type in [VesselType.SERVICE_VESSELS, VesselType.OFFSHORE_SUPPLY]:
            recommended_docking_time = 1.5  # hours
        else:
            recommended_docking_time = 2.0  # hours - default
        
        st.markdown("---")
        
        # SECTION 2: Key Vessel Specs (Side by side for easy comparison)
        st.markdown("### 2️⃣ Vessel Specifications")
        
        # Gross Tonnage - full width
        vessel_gt = st.number_input(
            "**Gross Tonnage (GT)**",
            min_value=100,
            max_value=50000,
            value=default_gt,
            step=100,
            key=f"vessel_gt_{vessel_type.value}",
            help=f"Typical: {default_gt:,} GT"
        )
        
        st.markdown("**Performance Parameters**")
        st.caption("⚠️ Set different Unladen/Laden values to reflect cargo effects on speed and energy consumption.")
        
        # Create 2-column layout for Unladen vs Laden
        col_unladen, col_laden = st.columns(2)
        
        # Initialize session state with correct defaults if not set or if set to 0
        speed_unladen_key = f"vessel_speed_unladen_{vessel_type.value}"
        speed_laden_key = f"vessel_speed_laden_{vessel_type.value}"
        
        if speed_unladen_key not in st.session_state or st.session_state[speed_unladen_key] == 0.0:
            st.session_state[speed_unladen_key] = 6.0
        if speed_laden_key not in st.session_state or st.session_state[speed_laden_key] == 0.0:
            st.session_state[speed_laden_key] = 5.0
        
        with col_unladen:
            st.markdown("**🔵 Unladen (Empty)**")
            boat_speed_unladen = st.number_input(
                "Speed (knots)",
                min_value=3.0,
                max_value=20.0,
                value=6.0,
                step=0.5,
                key=f"vessel_speed_unladen_{vessel_type.value}",
                help="Speed when vessel has no cargo"
            )
            base_consumption_unladen = st.number_input(
                "Energy (kWh/NM)",
                min_value=10.0,
                max_value=500.0,
                value=207.0,
                step=5.0,
                key=f"base_consumption_unladen_{vessel_type.value}",
                help="Energy consumption when unladen"
            )
        
        with col_laden:
            st.markdown("**🟠 Laden (Loaded)**")
            boat_speed_laden = st.number_input(
                "Speed (knots)",
                min_value=3.0,
                max_value=20.0,
                value=5.0,
                step=0.5,
                key=f"vessel_speed_laden_{vessel_type.value}",
                help="Speed when vessel is fully loaded"
            )
            base_consumption_laden = st.number_input(
                "Energy (kWh/NM)",
                min_value=10.0,
                max_value=500.0,
                value=245.0,
                step=5.0,
                key=f"base_consumption_laden_{vessel_type.value}",
                help="Energy consumption when laden"
            )
        
        # Validation: Check if speeds are still 0 (debugging)
        if boat_speed_unladen == 0.0 or boat_speed_laden == 0.0:
            st.error(
                f"⚠️ **CRITICAL ERROR**: Vessel speeds are set to 0!\n\n"
                f"- Unladen Speed: {boat_speed_unladen} knots\n"
                f"- Laden Speed: {boat_speed_laden} knots\n\n"
                f"**This will cause zero energy consumption!**\n\n"
                f"Please manually set the speeds above to:\n"
                f"- Unladen: 6.0 knots\n"
                f"- Laden: 5.0 knots"
            )
        
        # Calculate and display hotelling power
        vessel_specs_temp = VesselSpecs(vessel_type=vessel_type, gross_tonnage=vessel_gt)
        hotelling_power = vessel_specs_temp.get_hotelling_power_kw()
        
        # Key Metrics Display
        st.info(f"⚡ **Hotelling Power:** {hotelling_power:,.0f} kW  |  "
                f"⏱️ **Recommended Docking Time:** {recommended_docking_time} hours")
        
        with st.expander("ℹ️ How Laden/Unladen affects range & charging", expanded=False):
            st.markdown("""
            - **Laden (loaded)**: Higher consumption, potentially lower speed → requires more frequent charging/swaps
            - **Unladen (empty)**: Lower consumption, can travel farther → better range efficiency
            - **Charging**: Station power limits how much energy can be replenished during docking periods
            """)
        
        st.markdown("---")
        
        # SECTION 3: Battery Configuration (Grouped together)
        st.markdown("### 3️⃣ Battery System")
        
        # Configuration inputs
        col1, col2, col3, col4 = st.columns(4)
        
        # Primary UX: user supplies total battery capacity (not usable). This is clearer than
        # asking for containers directly. We'll initialize session defaults so the UI
        # shows a sensible default based on container size (e.g., 12 containers × 2460 kWh).
        # Ensure session state variables exist so number_input default value can be computed
        default_container_size = default_config.get("battery_container_capacity_kwh", 2460.0)
        if f"battery_container_capacity_{vessel_type.value}" not in st.session_state:
            st.session_state[f"battery_container_capacity_{vessel_type.value}"] = default_container_size
        if f"num_containers_{vessel_type.value}" not in st.session_state:
            # Use the per-vessel default if available; otherwise fallback to 12 containers
            st.session_state[f"num_containers_{vessel_type.value}"] = default_config.get("num_containers", 12)
        # Compute a default battery capacity from container size × count
        current_container_size = st.session_state.get(f"battery_container_capacity_{vessel_type.value}", default_container_size)
        current_num_containers = st.session_state.get(f"num_containers_{vessel_type.value}", 12)
        computed_default_battery = float(current_container_size * current_num_containers)
        # If there's no explicit battery_capacity_total set in session, set it to the computed default
        if f"battery_capacity_total_{vessel_type.value}" not in st.session_state:
            st.session_state[f"battery_capacity_total_{vessel_type.value}"] = computed_default_battery
        # Primary UX change: user enters Battery per Container (kWh) instead of total capacity
        with col1:
            battery_container_capacity = st.number_input(
                "**Battery per Container (kWh)**",
                min_value=50.0,
                max_value=5000.0,
                value=float(current_container_size),
                step=10.0,
                key=f"battery_container_capacity_{vessel_type.value}",
                on_change=set_battery_from_containers,
                args=(vessel_type.value,),
                help="Energy capacity per container (kWh). Total capacity = containers × per-container capacity."
            )
            # Compute and set the total battery capacity in session state (not editable directly)
            computed_total = float(battery_container_capacity * current_num_containers)
            st.session_state[f"battery_capacity_total_{vessel_type.value}"] = computed_total
            # Show explanation and computed total
            st.caption(f"Default based on: {current_num_containers} containers × {battery_container_capacity:.0f} kWh = {computed_total:,.0f} kWh")

        # Keep a lightweight read-only display of the optimizer capacity if present
        # Use the computed per-container total if present in session state (keeps the UX consistent)
        optimizer_capacity = st.session_state.get(f"battery_capacity_total_{vessel_type.value}", default_config.get("battery_capacity_kwh", None))
        # Container defaults (for computed syncing) - use session override when present
        current_container_size = st.session_state.get(f"battery_container_capacity_{vessel_type.value}", 2460.0)
        current_num_containers = st.session_state.get(f"num_containers_{vessel_type.value}", 12)
        # Expose these values as local fallbacks for use elsewhere in the view
        battery_container_capacity = current_container_size
        num_containers = current_num_containers
        # Allow user to edit container count directly in the main view (keeps UI simple but editable)
        with col2:
            if optimizer_capacity is not None:
                st.caption(f"Optimiser capacity: {optimizer_capacity:,.0f} kWh (usable={optimizer_capacity * (1 - (st.session_state.get(f'minimum_soc_{vessel_type.value}', 0.2) if f'minimum_soc_{vessel_type.value}' in st.session_state else 0.2) ):.0f} kWh)")
            # If a pending update exists (from a 'Apply recommended containers' button click), apply it
            pending_key = f"pending_num_containers_update_{vessel_type.value}"
            if pending_key in st.session_state:
                st.session_state[f"num_containers_{vessel_type.value}"] = st.session_state.pop(pending_key)
                # Ensure derived capacity is recalculated after applying a pending update
                set_battery_from_containers(vessel_type.value)

            num_containers = st.number_input(
                "**# Containers**",
                min_value=1,
                max_value=200,
                value=current_num_containers,
                step=1,
                key=f"num_containers_{vessel_type.value}",
                on_change=set_battery_from_containers,
                args=(vessel_type.value,),
                help="Number of container battery packs representing the total capacity (editable)"
            )
            # Ensure our local var is in-sync with the session widget
            num_containers = st.session_state.get(f"num_containers_{vessel_type.value}", current_num_containers)
            # Small spacing note
            st.caption("")
            # Offer an option to align the battery capacity and container count with the optimiser default
            needed_containers = int(math.ceil(optimizer_capacity / current_container_size)) if current_container_size > 0 else current_num_containers
            col_align1, col_align2 = st.columns([3,2])
            with col_align1:
                st.caption(f"Optimiser capacity: {optimizer_capacity:,.1f} kWh (usable ≈ {optimizer_capacity * (1 - default_config.get('minimum_soc_fraction', 0.2)):.0f} kWh)")
            with col_align2:
                # Align button removed for simplified UI: users may edit Battery Capacity & Containers directly
                st.markdown("&nbsp;")
        
        with col3:
            minimum_soc = st.number_input(
                "**Min SoC (%)**",
                min_value=0.0,
                max_value=50.0,
                value=20.0,
                step=5.0,
                help="Safety reserve"
            ) / 100.0
        
        with col4:
            initial_soc_fraction = st.number_input(
                "**Start SoC (%)**",
                min_value=0.0,
                max_value=100.0,
                value=100.0,
                step=5.0,
                help="Initial charge"
            ) / 100.0
        
        # Determine actual battery capacity master variable from per-container × #containers
        battery_capacity = float(st.session_state.get(f"battery_capacity_total_{vessel_type.value}", computed_default_battery))
        initial_soc_kwh = battery_capacity * initial_soc_fraction
        
        # Vessel charging power
        vessel_charging_power = st.number_input(
            "**Max Vessel Charging (kW)**",
            min_value=0.0,
            max_value=5000.0,
            value=1000.0,
            step=50.0,
            key=f"vessel_charging_power_{vessel_type.value}",
            help="Maximum charging power the vessel's onboard charger can accept"
        )
        
        # Battery System Summary
        battery_chemistry = "LFP (Lithium Iron Phosphate)"
        energy_density = 120.0
        battery_weight_kg = (battery_capacity * 1000) / energy_density
        battery_weight_tonnes = battery_weight_kg / 1000
        usable_battery = battery_capacity * (1 - minimum_soc)
        
        # Calculate realistic ranges with river flow effects
        usable_range_downstream_unladen = (usable_battery / base_consumption_unladen) / 0.8 if base_consumption_unladen > 0 else 0
        usable_range_downstream_laden = (usable_battery / base_consumption_laden) / 0.8 if base_consumption_laden > 0 else 0
        usable_range_upstream_unladen = (usable_battery / base_consumption_unladen) / 1.2 if base_consumption_unladen > 0 else 0
        usable_range_upstream_laden = (usable_battery / base_consumption_laden) / 1.2 if base_consumption_laden > 0 else 0
        # Still water (zero current) ranges
        usable_range_still_water_unladen = usable_battery / base_consumption_unladen if base_consumption_unladen > 0 else 0
        usable_range_still_water_laden = usable_battery / base_consumption_laden if base_consumption_laden > 0 else 0
        # Expose max ranges for diagnostics and summaries
        max_range_unladen = usable_range_still_water_unladen
        max_range_laden = usable_range_still_water_laden
        
        weight_ratio = (battery_weight_tonnes / vessel_gt) * 100 if vessel_gt > 0 else 0

        # (Per-segment feasibility checks moved to route/params validation section to avoid depending on route variables here)

        # Key metrics display
        st.markdown("**📊 System Overview**")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("**Total Capacity**", f"{battery_capacity/1000:.1f} MWh", 
                     help=f"{battery_capacity:,.0f} kWh")
        with col2:
            st.metric("**Range (Downstream)**", f"{usable_range_downstream_unladen:.0f}/{usable_range_downstream_laden:.0f} NM",
                     help=f"Unladen/Laden downstream ranges (Unladen / Laden)",
                     delta="Best case")
        with col3:
            st.metric("**Range (Still Water)**", f"{usable_range_still_water_unladen:.0f}/{usable_range_still_water_laden:.0f} NM",
                     help=f"Unladen/Laden still water (no current) ranges (Unladen / Laden)")
        with col4:
            st.metric("**Range (Upstream)**", f"{usable_range_upstream_unladen:.0f}/{usable_range_upstream_laden:.0f} NM",
                     help=f"Unladen/Laden upstream ranges (Unladen / Laden)",
                     delta="Worst case",
                     delta_color="inverse")
        with col5:
            st.metric("**Battery Weight**", f"{battery_weight_tonnes:.1f} t",
                     help=f"{weight_ratio:.1f}% of vessel GT")

        # Detailed range analysis in expander
        with st.expander("ℹ️ Detailed Range Analysis", expanded=False):
            
            st.markdown(f"""
            **Usable Battery:** {usable_battery:,.0f} kWh ({(1-minimum_soc)*100:.0f}% of total capacity)
            
            **Unladen (Empty Vessel)**
            - Downstream (⬇️): {usable_range_downstream_unladen:.0f} NM - with river flow (0.8× energy)
            - Still Water: {usable_range_still_water_unladen:.0f} NM - no current (1.0× energy)
            - Upstream (⬆️): {usable_range_upstream_unladen:.0f} NM - against river flow (1.2× energy)
            
            **Laden (Loaded Vessel)**
            - Downstream (⬇️): {usable_range_downstream_laden:.0f} NM
            - Still Water: {usable_range_still_water_laden:.0f} NM
            - Upstream (⬆️): {usable_range_upstream_laden:.0f} NM
            
            ⚠️ **Note:** Actual range per segment depends on vessel load and river flow direction.
            """)
        
        st.markdown("---")
        
        # SECTION 4: Journey Settings (Grouped together)
        # NOTE: 'Departure Time' and 'Journey Settings' are now merged into the
        # Route Configuration expander so users configure route + start time together.
        
        # Initialize container/session defaults (keep UI simple: no advanced controls)
        default_container_size = default_config.get("battery_container_capacity_kwh", 2460.0)
        # Ensure session state variables exist (not shown in UI) so callbacks function
        if f"battery_container_capacity_{vessel_type.value}" not in st.session_state:
            st.session_state[f"battery_container_capacity_{vessel_type.value}"] = default_container_size
        if f"num_containers_{vessel_type.value}" not in st.session_state:
            st.session_state[f"num_containers_{vessel_type.value}"] = default_config.get("num_containers", 12)
        # Refresh local copies of these values
        battery_container_capacity = st.session_state.get(f"battery_container_capacity_{vessel_type.value}", default_container_size)
        num_containers = st.session_state.get(f"num_containers_{vessel_type.value}", 12)

        # Reference Data (Hidden for simplified UI - removed)

    # Interactive Form (always shown)
    if True:
        # ========================================
        # ROUTE CONFIGURATION
        # ========================================
        with st.expander("🗺️ **ROUTE CONFIGURATION**", expanded=True):
            st.markdown("### Journey Planning")
            
            # Departure time and number of stations in one row
            col1, col2 = st.columns([1, 1])
            
            with col1:
                start_time = st.number_input(
                    "**Departure Time (24h)**",
                    min_value=0.0,
                    max_value=23.5,
                    value=8.0,
                    step=0.5,
                    key="departure_time_hr",
                    help="Journey start time"
                )
            
            with col2:
                num_stations = st.number_input(
                    "**Number of Stations**",
                    min_value=2,
                    max_value=20,
                    value=5,
                    step=1,
                    help="Total stations including start and end"
                )
            
            st.info(f"✓ **{num_stations}** stations → **{num_stations-1}** segments to configure")
            
            st.markdown("---")
            
            # Station names in a cleaner grid
            st.markdown("**🏪 Station Names**")
            st.caption("Define the names of each station along your route")
            
            # Fixed SoC step for optimization
            soc_step = 10.0  # kWh precision for state-of-charge calculations
            
            
            # Create rows of 5 columns each
            station_names = []
            for row_start in range(0, num_stations, 5):
                cols = st.columns(5)
                for i in range(5):
                    idx = row_start + i
                    if idx < num_stations:
                        with cols[i]:
                            default_name = default_config["route"][idx] if idx < len(default_config["route"]) else chr(65 + idx)
                            name = st.text_input(
                                f"#{idx+1}",
                                value=default_name,
                                key=f"station_name_{idx}",
                                label_visibility="visible"
                            )
                            station_names.append(name)
            
            route_text = ", ".join(station_names)
            
            st.markdown("---")
            
            # Segment Configuration - cleaner presentation
            st.markdown("**🛤️ Segment Details**")
            st.caption("💡 Upstream = against flow (1.2× energy) | Downstream = with flow (0.8× energy) | Neutral = no flow (1.0× energy)")
            
            # Build segment data based on current stations
            segment_rows = []
            for i in range(len(station_names) - 1):
                start_name = station_names[i]
                end_name = station_names[i + 1]
                key = f"{start_name}-{end_name}"
                
                # Try to get default values if they exist
                default_dist = default_config["distances_nm"].get(key, 40.0)
                
                # Default to zero flow (no current)
                flow_speed = 0.0
                flow_direction = "Downstream"
                
                segment_rows.append({
                    "From": start_name,
                    "To": end_name,
                    "Distance": default_dist,
                    "Flow": flow_speed,
                    "Direction": flow_direction,
                })
            
            segments_df = pd.DataFrame(segment_rows)
            
            segments_df = st.data_editor(
                segments_df,
                width='stretch',
                key="segments_editor",
                column_config={
                    "From": st.column_config.TextColumn("From", width="small", disabled=True),
                    "To": st.column_config.TextColumn("To", width="small", disabled=True),
                    "Distance": st.column_config.NumberColumn(
                        "Distance (NM)",
                        min_value=0.1,
                        max_value=500.0,
                        format="%.1f",
                        help="Distance in Nautical Miles"
                    ),
                    "Flow": st.column_config.NumberColumn(
                        "Flow (knots)",
                        min_value=0.0,
                        max_value=10.0,
                        format="%.1f",
                        help="River/current flow speed"
                    ),
                    "Direction": st.column_config.SelectboxColumn(
                        "Direction",
                        width="medium",
                        options=["Upstream", "Downstream"],
                        help="Upstream=harder, Downstream=easier"
                    ),
                },
                hide_index=True
            )
            
            # Rename columns back for compatibility
            segments_df = segments_df.rename(columns={
                "From": "Start",
                "To": "End",
                "Distance": "Distance (NM)",
                "Flow": "Flow Speed (knots)",
                "Direction": "Direction"
            })

            st.markdown("---")
            
            # Vessel-specific segment configuration
            st.markdown("**🚤 Vessel Segment Configuration**")
            st.caption("⚠️ Configure settings for each segment. 'Docking Time' and 'Must Stop' apply to the ARRIVAL station (the 'To' station).")
            
            # Use station_names to create vessel segment configuration
            vessel_segment_rows = []
            for i in range(len(station_names) - 1):
                a = station_names[i]
                b = station_names[i + 1]
                
                # If departing FROM station C, it's the return journey (unladen)
                if a.upper() == 'C':
                    default_laden = False  # Unladen on return
                else:
                    default_laden = True  # Laden on outward journey
                
                # Special defaults for station C
                if b.upper() == 'C':
                    default_dock = 4.0  # 4 hours at station C
                    default_must_stop = True
                else:
                    # Default: no docking time for arrivals unless explicitly set per segment
                    default_dock = 0.0
                    default_must_stop = False
                vessel_segment_rows.append({
                    "From": a,
                    "To (Arrival)": b,
                    "Laden": default_laden,
                    "Must Stop": default_must_stop,
                    "Force Swap": False,
                    "Docking (hr)": default_dock,
                })
            if not vessel_segment_rows:
                vessel_segments_df = pd.DataFrame(columns=["From", "To (Arrival)", "Laden", "Must Stop", "Force Swap", "Docking (hr)"])
            else:
                vessel_segments_df = pd.DataFrame(vessel_segment_rows)
                vessel_segments_df = st.data_editor(
                    vessel_segments_df,
                    width='stretch',
                    key="vessel_route_segments_editor",
                    column_config={
                        "From": st.column_config.TextColumn("From", width="small", disabled=True),
                        "To (Arrival)": st.column_config.TextColumn("To (Arrival)", width="medium", disabled=True, help="Arrival station where docking occurs"),
                        "Laden": st.column_config.CheckboxColumn("Laden", width="small", help="Is vessel loaded with cargo?"),
                        "Must Stop": st.column_config.CheckboxColumn("Must Stop", width="small", help="Force stop at arrival station"),
                        "Force Swap": st.column_config.CheckboxColumn("Force Swap", width="small", help="Force battery swap at arrival station"),
                        "Docking (hr)": st.column_config.NumberColumn("Docking (hr)", format="%.1f", help="Docking time at arrival station", min_value=0.0, step=0.5),
                    },
                    hide_index=True
                )
                st.caption("💡 Example: Row 'A → C' means traveling from A to C. 'Must Stop' and 'Docking' apply to station C (arrival).")

        # ========================================
        # STATION CONFIGURATION
        # ========================================
        with st.expander("🔋 **STATION SETTINGS**", expanded=True):
            st.markdown("### Configure Swap & Charging Facilities")
            
            # QUICK SETTINGS - Apply to All
            st.markdown("#### ⚡ Quick Apply to All Stations")
            
            # Two quick settings columns - docking time removed (per-vessel schedule only)
            col1, col2 = st.columns(2)
            
            with col1:
                global_charging_power = st.number_input(
                    "**Charging (kW)**",
                    min_value=0.0,
                    max_value=5000.0,
                    value=2000.0,
                    step=50.0,
                    key="global_charging_power",
                    help="Shore power capacity"
                )
                # Optional: global charged battery counts that can be applied to all stations
                global_charged_batteries = st.number_input(
                    "**Charged Batteries (All Stations)**",
                    min_value=0,
                    max_value=100,
                    value=21,
                    step=1,
                    key="global_charged_batteries",
                    help="Apply a uniform initial charged battery count to all stations"
                )
                # Optional: global total batteries
                global_total_batteries = st.number_input(
                    "**Total Batteries (All Stations)**",
                    min_value=0,
                    max_value=100,
                    value=21,
                    step=1,
                    key="global_total_batteries",
                    help="Apply a uniform total battery stock to all stations"
                )
            
            with col2:
                global_partial_swap = st.checkbox(
                    "**Partial Swap**",
                    value=False,
                    key="global_partial_swap",
                    help="Only swap depleted containers (cost-saving)"
                )
            # Option to apply these quick settings to all station widgets
            apply_quick_all = st.button("Apply these settings to all stations", key="quick_apply_all")
            if apply_quick_all:
                # gather station names (it will exist after route configuration). If not present, skip.
                station_names_list = station_names if 'station_names' in locals() else []
                if not station_names_list:
                    st.warning("No station names configured yet. Configure stations first before applying quick settings.")
                else:
                    unique_station_names = list(dict.fromkeys(station_names_list))
                    for idx, sname in enumerate(unique_station_names):
                        # Update charging power for each station widget key (explicitly to correct key)
                        st.session_state[f"charging_power_{idx}_{sname}"] = float(global_charging_power)
                        # Two keys used for partial swap (global vs station level); set both to be safe
                        st.session_state[f"partial_global_{idx}_{sname}"] = bool(global_partial_swap)
                        st.session_state[f"partial_{idx}_{sname}"] = bool(global_partial_swap)
                        # Optional: apply global charged/total battery counts if provided
                        # Apply global charged/total battery counts (use local variables defined above)
                        try:
                            st.session_state[f"charged_batteries_{idx}_{sname}"] = int(global_charged_batteries)
                            st.session_state[f"total_batteries_{idx}_{sname}"] = int(global_total_batteries)
                        except Exception:
                            # Defensive programming: don't let an unexpected type or key cause a crash in the UI
                            pass
                    # Rerun to update the UI with new defaults (safe call)
                    getattr(st, 'experimental_rerun', lambda: None)()
            
            st.markdown("---")
            
            # INDIVIDUAL STATION CONTROLS - More compact tabs
            st.markdown("#### � Individual Station Controls")
            
            # Create tabs for each UNIQUE station (more compact than expanders)
            # Use dict.fromkeys to preserve order while removing duplicates
            unique_station_names = list(dict.fromkeys(station_names))
            station_tabs = st.tabs([f"🏪 {name}" for name in unique_station_names])
            
            station_rows = []
            for idx, (tab, name) in enumerate(zip(station_tabs, unique_station_names)):
                with tab:
                    # Try to get default values if they exist
                    default_swap_settings = default_config.get("swap_settings", {})
                    default_station = dict(default_swap_settings.get(name, {}))
                    # Ensure station charged battery defaults are feasible wrt num_containers
                    # If station supports swaps, make sure station has at least `num_containers` batteries if that is meaningful
                    try:
                        desired_containers = int(num_containers)
                    except Exception:
                        desired_containers = None
                    if default_station.get("allow_swap", True) and desired_containers is not None:
                        # Cap totals to a reasonable upper bound (e.g., 50)
                        cap_batteries = 50
                        total_default = default_station.get("total_batteries", default_station.get("available_batteries", desired_containers))
                        if total_default is None:
                            total_default = desired_containers
                        if total_default < desired_containers:
                            adjusted_total = min(max(total_default, desired_containers), cap_batteries)
                            default_station["total_batteries"] = adjusted_total
                            default_station["available_batteries"] = adjusted_total
                    
                    # Two-column layout for compact presentation
                    col_left, col_right = st.columns(2)
                    
                    with col_left:
                        st.markdown("**⚙️ Operations**")
                        
                        
                        allow_swap = st.checkbox(
                            "Allow Swap",
                            value=default_station.get("allow_swap", True),
                            key=f"allow_{idx}_{name}"
                        )
                        
                        charging_allowed = st.checkbox(
                            "Allow Charging",
                            value=default_station.get("charging_allowed", True),
                            key=f"charging_{idx}_{name}"
                        )
                        
                        # 'Force Swap' is now a per-vessel route setting: remove station-level control
                        
                        # Partial swap: controlled by global setting when enabled
                        if global_partial_swap:
                            st.checkbox(
                                "Partial Swap Allowed",
                                value=True,
                                key=f"partial_global_{idx}_{name}",
                                disabled=True,
                                help="Controlled by global setting"
                            )
                            partial_swap = True
                        else:
                            partial_swap = st.checkbox(
                                "Partial Swap Allowed",
                                value=default_station.get("partial_swap_allowed", False),
                                key=f"partial_{idx}_{name}"
                            )
                        
                        st.markdown("**⏰ Operating Hours**")
                        open_hour = st.number_input(
                            "Opens at (hr)",
                            min_value=0.0,
                            max_value=24.0,
                            value=default_station.get("open_hour", 0.0),
                            step=0.5,
                            key=f"open_{idx}_{name}"
                        )
                        
                        close_hour = st.number_input(
                            "Closes at (hr)",
                            min_value=0.0,
                            max_value=24.0,
                            value=default_station.get("close_hour", 24.0),
                            step=0.5,
                            key=f"close_{idx}_{name}"
                        )
                    
                    with col_right:
                        st.markdown("**⏱️ Operations**")
                        
                        # Station docking time is available as a station default but UI control removed; use Vessel Route editor for per-vessel schedule overrides
                        # Fallback to 0.0 so that pass-through stations default to no docking unless explicitly configured
                        station_default_docking_time = default_station.get("docking_time_hr", 0.0)
                        
                        st.markdown("**🔌 Charging & Batteries**")
                        
                        station_charging_power = st.number_input(
                            "Charging Power (kW)",
                            min_value=0.0,
                            max_value=2000.0,
                            value=default_station.get("charging_power_kw", global_charging_power),
                            step=50.0,
                            key=f"charging_power_{idx}_{name}",
                        )
                        
                        # Show charging capacity info
                        if station_charging_power > 0 and station_default_docking_time > 0:
                            max_energy_charged = station_charging_power * station_default_docking_time * 0.95
                            pct_of_battery = (max_energy_charged / battery_capacity * 100) if battery_capacity > 0 else 0
                            if pct_of_battery < 100:
                                st.caption(f"⚡ Can charge ~{max_energy_charged:.0f} kWh in {station_default_docking_time}h ({pct_of_battery:.1f}% of battery)")
                            else:
                                st.caption(f"⚡ Can fully charge battery in {station_default_docking_time}h")
                            # Containers that can be charged at station during docking
                            if station_charging_power > 0 and battery_container_capacity > 0:
                                containers_chargeable = int(max_energy_charged // battery_container_capacity)
                                if containers_chargeable > 0:
                                    st.caption(f"🔋 Can charge ~{containers_chargeable} container(s) in {station_default_docking_time}h at {station_charging_power} kW")
                        
                        station_charging_fee = st.number_input(
                            "Charging Fee (£)",
                            min_value=0.0,
                            max_value=100.0,
                            value=25.0,  # UK realistic: £10-£50 per session
                            step=5.0,
                            key=f"charging_fee_{idx}_{name}",
                            help="UK realistic: £10-£50 per charging session"
                        )
                        
                        st.markdown("**💰 Swap Costs**")
                        
                        base_service_fee = st.number_input(
                            "Base Service Fee (£)",
                            min_value=0.0,
                            max_value=200.0,
                            value=default_station.get("base_service_fee", 15.0),  # UK realistic: £8-£40 per container
                            step=5.0,
                            key=f"base_service_fee_{idx}_{name}",
                            help="Cost per container swapped (includes handling and operations)"
                        )
                        
                        degradation_fee_per_kwh = st.number_input(
                            "Battery Wear Fee (£/kWh)",
                            min_value=0.0,
                            max_value=0.50,
                            value=default_station.get("degradation_fee_per_kwh", 0.03),  # Default to 0.03 (£0.03/kWh wear cost)
                            step=0.01,
                            format="%.3f",
                            key=f"degradation_fee_{idx}_{name}",
                            help="Battery degradation cost per kWh charged (default £0.03/kWh)"
                        )
                        
                        charged_batteries = st.number_input(
                            "Charged Batteries",
                            min_value=0,
                            max_value=50,
                            value=default_station.get("available_batteries", 17),
                            key=f"charged_batteries_{idx}_{name}",
                            help="Fully charged containers immediately available for swapping"
                        )

                        total_batteries = st.number_input(
                            "Total Battery Stock",
                            min_value=0,
                            max_value=100,
                            value=default_station.get("total_batteries", default_station.get("available_batteries", 17)),
                            key=f"total_batteries_{idx}_{name}",
                            help="Total battery containers kept at station (charged + spare/unavailable)"
                        )
                        
                        st.markdown("**💰 Energy Cost**")
                        energy_cost_station = st.number_input(
                            "£/kWh",
                            min_value=0.0,
                            max_value=1.0,
                            value=default_station.get("energy_cost_per_kwh", 0.25),  # UK realistic: £0.16-£0.40/kWh
                            step=0.01,
                            format="%.3f",
                            key=f"energy_cost_{idx}_{name}",
                            help="UK realistic: £0.16-£0.40/kWh (typical £0.25)"
                        )
                    
                    # Collect data from UI elements
                    # Collect data from UI elements
                    station_rows.append({
                        "Station": name,
                        "Allow Swap": allow_swap,
                        "Partial Swap": partial_swap,
                        "Charging Allowed": charging_allowed,
                        "Charging Power (kW)": station_charging_power,
                        "Charging Fee (£)": station_charging_fee,
                        "Base Service Fee": base_service_fee,
                        "Battery Wear Fee": degradation_fee_per_kwh,
                        "Open Hour": open_hour,
                        "Close Hour": close_hour,
                        "Charged Batteries": charged_batteries,
                        "Total Batteries": total_batteries,
                        "Energy Cost (£/kWh)": energy_cost_station,
                    })
            
            stations_df = pd.DataFrame(station_rows)

    # ======= Per-segment energy feasibility checks (validate route vs battery) ========
    infeasible_segments = []
    if 'segments_df' in locals() and segments_df is not None and not segments_df.empty:
        usable_energy_kwh = battery_capacity - (battery_capacity * minimum_soc)
        for _, r in segments_df.iterrows():
            seg_start = str(r.get('Start'))
            seg_end = str(r.get('End'))
            seg_dist = float(r.get('Distance (NM)', 0.0))
            # Use per-vessel flag if available to choose mode
            mode = 'laden'
            if 'vessel_segments_df' in locals() and vessel_segments_df is not None:
                m = vessel_segments_df.loc[(vessel_segments_df['From'] == seg_start) & (vessel_segments_df['To (Arrival)'] == seg_end)]
                if not m.empty:
                    mode = 'laden' if bool(m.iloc[0].get('Laden', True)) else 'unladen'
            current_knots = float(r.get('Flow Speed (knots)', 0.0))
            seg_energy, _ = compute_segment_energy(seg_dist, current_knots, mode=mode, base_consumption_laden=base_consumption_laden, base_consumption_unladen=base_consumption_unladen, boat_speed_laden=boat_speed_laden, boat_speed_unladen=boat_speed_unladen)
            if seg_energy > usable_energy_kwh:
                # Compute recommended container count to allow this segment without breaching min SoC
                # We need battery_capacity * (1 - min_soc) >= seg_energy -> battery_capacity >= seg_energy / (1 - min_soc)
                needed_total_kwh = seg_energy / (1.0 - (minimum_soc if minimum_soc is not None else 0.0))
                needed_containers = int(math.ceil(needed_total_kwh / battery_container_capacity)) if battery_container_capacity > 0 else None
                infeasible_segments.append((seg_start, seg_end, seg_energy, usable_energy_kwh, needed_containers))
    if infeasible_segments:
        with st.expander("⚠️ Segment Feasibility Issues", expanded=True):
            st.warning("The following segments require more usable energy than your current battery configuration allows. Consider increasing container count, lowering Min SoC, or enabling swaps/charging at intermediate stations.")
            for (a, b, seg_e, usable_e, needed_containers) in infeasible_segments:
                st.markdown(f"- Segment **{a} → {b}**: requires **{seg_e:,.0f} kWh**; usable battery ≈ **{usable_e:,.0f} kWh**.")
                if needed_containers:
                    col_fix1, col_fix2 = st.columns([3,1])
                    with col_fix1:
                        st.caption(f"Recommended containers to allow this segment without breaching min SoC: **{needed_containers}** (current: {num_containers})")
                    with col_fix2:
                        if st.button(f"Apply {needed_containers} containers", key=f"apply_needed_containers_{a}_{b}_{vessel_type.value}"):
                            # Defer setting the widget-bound session_state until widget is recreated to avoid Streamlit errors
                            st.session_state[f"pending_num_containers_update_{vessel_type.value}"] = needed_containers
                            # Rerun if available to refresh UI values
                            getattr(st, 'experimental_rerun', lambda: None)()

    params = {
        # 'boat_speed' retained for backwards compatibility but derived from unladen speed
        "boat_speed": boat_speed_unladen,
        "boat_speed_laden": boat_speed_laden,
        "boat_speed_unladen": boat_speed_unladen,
        # 'base_consumption' retained for backwards compatibility but derived from laden consumption
        "base_consumption": base_consumption_laden,
        "base_consumption_laden": base_consumption_laden,
        "base_consumption_unladen": base_consumption_unladen,
        "battery_capacity": battery_capacity,
        "battery_container_capacity": battery_container_capacity,
        "num_containers": num_containers,
        "initial_soc_kwh": initial_soc_kwh,
        "minimum_soc": minimum_soc,
        "soc_step": soc_step,
        "start_time": start_time,
        "vessel_type": vessel_type.value,
        "vessel_gt": vessel_gt,
        "vessel_charging_power": vessel_charging_power,
    }

    # Use either the sidebar run button (if set) or the main run button (backwards compatibility)
    run_button = sidebar_run_button

    if run_button:
        try:
            with st.status("⚙️ **Preparing optimisation...**", expanded=True) as status:
                st.write("🔍 Validating configuration...")
                # Provide vessel-segment flags and vessel_route_text to form parser
                vessel_route_text_val = st.session_state.get(f"vessel_route_text_{vessel_type.value}", None)
                # Prefer per-vessel route_text if provided, else use global route_text
                input_route_text = vessel_route_text_val or route_text
                
                # Determine segments input and ensure it has physical data (distance/flow)
                if 'vessel_segments_df' in locals() and vessel_segments_df is not None:
                    # If using vessel-specific segments, they might lack physical data. 
                    # Merge it from the global segments_df.
                    segments_input = vessel_segments_df.copy()
                    
                    # Create lookup maps from global segments
                    dist_map = {}
                    flow_map = {}
                    dir_map = {}
                    
                    # Check if global segments_df has data
                    if 'segments_df' in locals() and not segments_df.empty:
                        for _, r in segments_df.iterrows():
                            # Key by Start-End
                            key = (str(r.get('Start')), str(r.get('End')))
                            dist_map[key] = r.get('Distance (NM)', 0.0)
                            flow_map[key] = r.get('Flow Speed (knots)', 0.0)
                            dir_map[key] = r.get('Direction', 'Downstream')
                            
                    # Apply lookups to fill missing physical columns
                    # Note: vessel_segments_df uses 'From'/'To (Arrival)' columns
                    segments_input['Distance (NM)'] = segments_input.apply(
                        lambda x: dist_map.get((str(x['From']), str(x['To (Arrival)'])), 0.0), axis=1
                    )
                    segments_input['Flow Speed (knots)'] = segments_input.apply(
                        lambda x: flow_map.get((str(x['From']), str(x['To (Arrival)'])), 0.0), axis=1
                    )
                    segments_input['Direction'] = segments_input.apply(
                        lambda x: dir_map.get((str(x['From']), str(x['To (Arrival)'])), 'Downstream'), axis=1
                    )
                else:
                    segments_input = segments_df
                
                config = form_frames_to_config(input_route_text, segments_input, stations_df, params, default_config, vessel_segments_df=vessel_segments_df if 'vessel_segments_df' in locals() else None, vessel_route_text=vessel_route_text_val)
                st.write("✅ Configuration validated")
                status.update(label="✅ **Configuration ready**", state="complete")
        except Exception as exc:
            st.error(f"❌ **Invalid scenario configuration:** {exc}")
            st.stop()
    else:
        config = default_config

    if run_button:
        # Create a progress container
        progress_container = st.container()
        
        with progress_container:
            with st.status("� **Running optimisation...**", expanded=True) as status:
                try:
                    # Validate scenario before running
                    st.write("📊 Analyzing route...")
                    route = config.get('route', [])
                    total_distance = sum(config.get('distances_nm', {}).values())
                    battery_capacity = config.get('battery_capacity_kwh', 0)
                    base_consumption = config.get('base_consumption_laden', config.get('base_consumption_unladen', 0))
                    min_soc_fraction = config.get('minimum_soc_fraction', 0)
                    
                    # Echo SoC settings chosen by user (for traceability)
                    initial_soc_val = config.get('initial_soc_kwh', 0.0)
                    min_soc_frac = config.get('minimum_soc_fraction', 0.0)
                    st.info(f"Start SoC: {initial_soc_val:,.0f} kWh ({100*initial_soc_val/config.get('battery_capacity_kwh',1):.0f}% of battery)")
                    st.info(f"Min SoC (reserve): {min_soc_frac*100:.1f}% ({config.get('battery_capacity_kwh',0)*min_soc_frac:,.0f} kWh)")

                    # Calculate theoretical range
                    usable_battery = battery_capacity * (1 - min_soc_fraction)
                    
                    # Calculate realistic range based on route conditions (weighted average)
                    total_energy_laden = 0.0
                    total_energy_unladen = 0.0
                    
                    # Get vessel params
                    bs_laden = config.get('boat_speed_laden', 5.0)
                    bs_unladen = config.get('boat_speed_unladen', 6.0)
                    bc_laden = config.get('base_consumption_laden', 245.0)
                    bc_unladen = config.get('base_consumption_unladen', 207.0)
                    
                    for i in range(len(route) - 1):
                        start = route[i]
                        end = route[i + 1]
                        key = f"{start}-{end}"
                        dist = config.get('distances_nm', {}).get(key, 0)
                        curr = config.get('currents_knots', {}).get(key, 0)
                        
                        # Range Check: Max Range Laden/Unladen
                        e_laden, _ = compute_segment_energy(
                            distance_nm=dist,
                            current_knots=curr,
                            mode="laden",
                            base_consumption_laden=bc_laden,
                            base_consumption_unladen=bc_unladen,
                            boat_speed_laden=bs_laden,
                            boat_speed_unladen=bs_unladen
                        )
                        e_unladen, _ = compute_segment_energy(
                             distance_nm=dist,
                            current_knots=curr,
                            mode="unladen",
                            base_consumption_laden=bc_laden,
                            base_consumption_unladen=bc_unladen,
                            boat_speed_laden=bs_laden,
                            boat_speed_unladen=bs_unladen
                        )
                        
                        total_energy_laden += e_laden
                        total_energy_unladen += e_unladen
                        
                    avg_consumption_laden = total_energy_laden / total_distance if total_distance > 0 else bc_laden
                    avg_consumption_unladen = total_energy_unladen / total_distance if total_distance > 0 else bc_unladen
                    
                    max_range = usable_battery / avg_consumption_laden if avg_consumption_laden > 0 else 0
                    
                    st.write(f"📍 Route: {len(route)} stations, {total_distance:.1f} NM")
                    st.write(f"🔋 Battery: {battery_capacity:,.0f} kWh (range: {max_range:.1f} NM)")
                    
                    # Check if swap stations are available
                    stations_with_swap = [s for s in route if config.get('stations', {}).get(s, {}).get('allow_swap', False)]
                    
                    # Only show warning if route is too long AND no swap stations are available
                    if total_distance > max_range * 1.5 and not stations_with_swap:  # Allow some margin for currents
                        st.warning(f"""
                        ⚠️ **Potential Issue Detected**
                        
                        - **Total Route Distance**: {total_distance:.1f} NM
                        - **Battery Usable Range**: {max_range:.1f} NM
                        - **Number of Segments**: {len(route) - 1}
                        - **Swap Stations Available**: None
                        
                        The route may be too long for the battery capacity. Consider:
                        1. Increasing battery capacity
                        2. Reducing fuel consumption
                        3. Enabling swap stations on the route
                        4. Reducing minimum SoC requirement
                        """)
                    
                    st.write("🧮 Computing optimal strategy...")
                    import time
                    start_time = time.time()
                    
                    steps_df, totals = run_optimizer(config)
                    
                    elapsed_time = time.time() - start_time
                    st.write(f"⚡ Optimization completed in {elapsed_time:.2f} seconds")
                    
                    status.update(label="✅ **Optimisation Complete!**", state="complete")
                    
                    # Show success message
                    st.toast("🚢 Vessel departing!", icon="🚢")
                    st.success(f"""
                    ### 🎉 Optimisation Successful!
                    
                    - **Total Cost:** £{totals['total_cost']:.2f}
                    - **Journey Time:** {totals['total_time']:.2f} hours
                    - **Arrival:** Hour {totals['finish_time']:.2f}
                    - **Computation Time:** {elapsed_time:.2f}s
                    """)
                    
                    render_results(steps_df, totals, config)
                
                except ValueError as exc:
                    status.update(label="❌ **Optimisation Failed**", state="error")
                    error_msg = str(exc)
                    
                    # Check if this is a constraint diagnostics error
                    if "CONSTRAINT VIOLATION DIAGNOSTICS" in error_msg:
                        st.error("❌ **Optimization Failed: No Feasible Solution Found**")
                        
                        # Split the error message to extract diagnostics
                        parts = error_msg.split("CONSTRAINT VIOLATION DIAGNOSTICS:")
                        if len(parts) > 1:
                            diagnostics = parts[1].strip()
                            
                            st.markdown("---")
                            st.markdown("### 🔍 Automated Constraint Analysis")
                            
                            # Display diagnostics in an expandable section
                            with st.expander("📋 **Detailed Diagnostic Report** (Click to view)", expanded=True):
                                st.code(diagnostics, language=None)
                    else:
                        # Fallback to old-style error handling for non-diagnostic errors
                        st.error(f"❌ **No Feasible Solution Found**")
                        st.error(f"**Error Details**: {error_msg}")
                    
                        if "No feasible solution for final SoC requirement" in error_msg:
                            st.markdown("""
                            ### 🔍 Diagnosis
                        
                        The optimizer cannot find a valid solution. This usually means:
                        
                        1. **⚡ Insufficient Battery Range**
                           - Battery capacity is too small for the journey
                           - Energy consumption is too high
                           - Try: Increase battery capacity or reduce consumption
                        
                        2. **🔋 Swap Stations Not Available**
                           - No swap stations on the route, or
                           - Swap stations don't have batteries available, or
                           - Stations are closed during arrival times
                           - Try: Enable swaps at intermediate stations
                        
                        3. **⏰ Operating Hours Conflicts**
                           - Cannot reach swap stations during operating hours
                           - Try: Adjust departure time or station hours
                        
                        4. **🎯 Final SoC Requirement Too High**
                           - Cannot arrive with required minimum charge
                           - Try: Reduce minimum SoC percentage
                        
                        5. **🌊 Strong River Flow**
                           - Traveling upstream (against flow) consuming too much energy
                           - Try: Reduce upstream flow values or increase boat speed
                        """)
                        
                        # Show current configuration summary
                        with st.expander("📋 Current Configuration", expanded=True):
                            col1, col2, col3, col4, col5 = st.columns(5)
                            
                            with col1:
                                st.markdown("**Route Info**")
                                st.write(f"- Stations: {len(route)}")
                                st.write(f"- Segments: {len(route) - 1}")
                                st.write(f"- Total Distance: {total_distance:.1f} NM")
                            
                            with col3:
                                st.metric("**Range (Still Water)**", f"{usable_range_still_water_unladen:.0f}/{usable_range_still_water_laden:.0f} NM",
                                         help=f"Unladen/Laden, still water (no current)")
                            with col2:
                                st.metric("**Range (Downstream)**", f"{usable_range_downstream_unladen:.0f}/{usable_range_downstream_laden:.0f} NM",
                                         help=f"Unladen/Laden, downstream (0.8× energy)",
                                         delta="Best case")
                            with col4:
                                st.metric("**Range (Upstream)**", f"{usable_range_upstream_unladen:.0f}/{usable_range_upstream_laden:.0f} NM",
                                         help=f"Unladen/Laden, upstream (1.2× energy)",
                                         delta="Worst case")
                            
                            with col3:
                                st.markdown("**Energy Info**")
                            with col5:
                                st.metric("**Battery Weight**", f"{battery_weight_tonnes:.1f} t",
                                         help=f"{weight_ratio:.1f}% of vessel GT")
                                energy_deficit = (total_distance * base_consumption_laden) - usable_battery
                                if energy_deficit > 0:
                                    st.error(f"- ⚠️ Deficit: {energy_deficit:.0f} kWh")
                                else:
                                    st.success(f"- ✅ Surplus: {-energy_deficit:.0f} kWh")
                            
                            # Check swap availability
                            stations_with_swap = [s for s in route if config.get('stations', {}).get(s, {}).get('allow_swap', False)]
                            st.markdown("**Swap Stations**")
                            if stations_with_swap:
                                st.write(f"- Available at: {', '.join(stations_with_swap)}")
                            else:
                                st.error("- ⚠️ No swap stations enabled!")
                            
                            # Detailed segment analysis
                            st.markdown("---")
                            st.markdown("**Segment-by-Segment Analysis**")
                            
                            segments_data = []
                            cumulative_distance = 0
                            cumulative_energy = 0
                            
                            for start, end in _pairwise(route):
                                key = f"{start}-{end}"
                                
                                distance = config.get('distances_nm', {}).get(key, 0)
                                current = config.get('currents_knots', {}).get(key, 0)
                                
                                # Use same logic as optimizer
                                segment_energy, _ = compute_segment_energy(
                                    distance_nm=distance,
                                    current_knots=current,
                                    mode="laden",  # Conservative estimate
                                    base_consumption_laden=config.get('base_consumption_laden', 245.0),
                                    base_consumption_unladen=config.get('base_consumption_unladen', 207.0),
                                    boat_speed_laden=config.get('boat_speed_laden', 5.0),
                                    boat_speed_unladen=config.get('boat_speed_unladen', 6.0)
                                )
                                
                                cumulative_distance += distance
                                cumulative_energy += segment_energy
                                
                                flow_direction = "⬆️ Upstream" if current < 0 else "⬇️ Downstream"
                                
                                segments_data.append({
                                    'Segment': f"{start}→{end}",
                                    'Distance': f"{distance:.1f} NM",
                                    'Flow': f"{abs(current):.1f} knots {flow_direction}",
                                    'Energy': f"{segment_energy:.0f} kWh",
                                    'Cumulative': f"{cumulative_energy:.0f} kWh"
                                })
                            
                            seg_df = pd.DataFrame(segments_data)
                            st.dataframe(seg_df, width='stretch', hide_index=True)
                            
                            # Energy balance check
                            st.markdown("---")
                            st.markdown("**Energy Balance Check**")
                            if cumulative_energy > usable_battery:
                                st.error(f"⚠️ **Total energy needed ({cumulative_energy:.0f} kWh) exceeds usable battery ({usable_battery:.0f} kWh)**")
                                st.error(f"Deficit: {cumulative_energy - usable_battery:.0f} kWh - **SWAP REQUIRED!**")
                                if not stations_with_swap:
                                    st.error("❌ **But no swap stations are enabled!**")
                            else:
                                st.success(f"✅ Battery has enough capacity ({usable_battery:.0f} kWh) for total journey ({cumulative_energy:.0f} kWh)")
                    
                except Exception as exc:
                    status.update(label="❌ **Optimisation Failed**", state="error")
                    st.error(f"❌ **Optimisation Failed**")
                    st.exception(exc)
    else:
        # Welcome message when no optimisation has run
        st.info("� **Configure your scenario above and click 'RUN OPTIMISATION' to get started!**")
        
        with st.expander("ℹ️ How to Use This Tool", expanded=False):
            st.markdown("""
            ### Getting Started
            
            1. **Configure Your Scenario**:
               - 🗺️ **Route**: Define the sequence of stations
               - 🛤️ **Segments**: Set distances and river flow between stations (positive = downstream, negative = upstream)
               - 🔋 **Stations**: Configure swap facilities, costs, and operating hours
               - ⚙️ **Parameters**: Set boat specs, battery capacity, and costs
            
            2. **Run Optimisation**: Click the button in the sidebar
            
            3. **Analyze Results**: Review the optimal swap strategy, costs, and timing
            
            4. **Export**: Download journey plans, scenarios, or summaries
            
            ### Tips
            - 💡 Hover over any field for helpful tooltips
            - 🔄 Try different scenarios to compare strategies
            - 📊 Use the SoC chart to visualize battery levels throughout the journey
            - ⚡ See the **Vessel Energy Consumption Reference** in Global Parameters for realistic energy consumption values
            - 📖 Check `ENERGY_CONSUMPTION_REFERENCE.md` for detailed vessel specifications
            """)
        
        with st.expander("📖 Example Scenario", expanded=False):
            st.markdown("""
            **Sample Route**: A → B → C → D → E
            
            - **Total Distance**: 150 NM
            - **Swap Stations**: B, C, D (with varying costs and hours)
            - **Challenge**: Balance swap costs against energy consumption and time
            - **Goal**: Minimize total cost while maintaining minimum battery SoC
            
            The optimizer considers:
            - River flow (downstream/upstream travel)
            - Station operating hours and queue times
            - Energy costs vs swap costs vs time costs
            - Battery availability at each station
            """)


if __name__ == "__main__":
    main()

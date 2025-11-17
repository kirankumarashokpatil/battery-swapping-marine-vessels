from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd
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


@st.cache_data
def load_default_config() -> Dict:
    import random
    
    # Generate randomized distances (25-55 NM range)
    distances = {}
    route_segments = ["A-B", "B-C", "C-D", "D-E", "E-F", "F-G", "G-H", "H-I", "I-J", "J-K", "K-L", "L-M", "M-N", "N-O", "O-P", "P-Q", "Q-R", "R-S", "S-T"]
    
    # Keep first few segments as provided in your data
    distances.update({
        "A-B": 40.0,
        "B-C": 35.0,
        "C-D": 45.0,
        "D-E": 30.0,
    })
    
    # Randomize remaining segments
    for segment in route_segments[4:]:  # Skip first 4
        distances[segment] = round(random.uniform(25.0, 55.0), 1)
    
    # Generate randomized currents (-3.0 to +3.5 knots range)
    currents = {}
    currents.update({
        "A-B": -2.5,  # Upstream (against flow)
        "B-C": -1.8,  # Upstream (against flow)
        "C-D": 3.2,   # Downstream (with flow)
        "D-E": 2.0,   # Downstream (with flow)
    })
    
    # Randomize remaining currents
    for segment in route_segments[4:]:  # Skip first 4
        currents[segment] = round(random.uniform(-3.0, 3.5), 1)
    
    # Generate randomized station configs
    stations = {
        "A": {
            "docking_time_hr": 0.0,  # Origin - no stop
            "swap_operation_time_hr": 0.5,
            "allow_swap": False,
            "charging_allowed": False,
            "charging_power_kw": 0.0,
        },
        "B": {
            "docking_time_hr": 2.0,  # If mandatory stop: 2 hours for passenger ops
            "swap_operation_time_hr": 0.5,  # Battery swap: 30 minutes
            "operating_hours": [6.0, 22.0],
            "available_batteries": 5,
            "allow_swap": True,
            "charging_allowed": True,
            "charging_power_kw": 250.0,
            "base_charging_fee": 25.0,  # UK realistic: £10-£50 per session
            "energy_cost_per_kwh": 0.25,  # UK realistic: £0.16-£0.40/kWh (typical £0.25)
            "base_service_fee": 15.0,  # UK realistic: £8-£40 per container (typical £15)
            "swap_cost": 0.0,
            "degradation_fee_per_kwh": 0.03,
        },
        "C": {
            "docking_time_hr": 3.0,  # If mandatory: 3 hours for major cargo/passenger ops
            "swap_operation_time_hr": 0.75,  # Battery swap: 45 minutes
            "operating_hours": [0.0, 24.0],
            "available_batteries": 4,
            "allow_swap": True,
            "charging_allowed": True,
            "charging_power_kw": 500.0,
            "base_charging_fee": 30.0,  # UK realistic: £10-£50 per session
            "energy_cost_per_kwh": 0.30,  # UK realistic: higher at busy ports
            "base_service_fee": 20.0,  # UK realistic: £8-£40 per container
            "swap_cost": 0.0,
            "degradation_fee_per_kwh": 0.03,
        },
        "D": {
            "docking_time_hr": 2.0,  # If mandatory: 2 hours
            "swap_operation_time_hr": 0.5,  # Battery swap: 30 minutes
            "operating_hours": [8.0, 20.0],
            "available_batteries": 12,
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
    
    # Generate random station configs for F-S (T is destination)
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
            batteries_available = random.randint(3, 12)
            
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
    
    return {
        "route": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T"],
        "distances_nm": distances,
        "currents_knots": currents,
        "boat_speed_knots": 5.0,  # 5 knots - typical for cargo vessels
        "base_consumption_per_nm": 220.0,  # Based on actual data: 207-245 kWh/NM for laden cargo vessels
        "battery_capacity_kwh": 19600.0,  # 10 containers × 1960 kWh = 19.6 MWh total
        "battery_container_capacity_kwh": 1960.0,  # Standard 20-foot ISO container capacity
        "initial_soc_kwh": 19600.0,  # Start with full battery (100%)
        "minimum_soc_fraction": 0.2,  # Industry standard 20% reserve
        "energy_cost_per_kwh": 0.12,
        "time_cost_per_hr": 25.0,
        "soc_step_kwh": 20.0,  # Adjusted for containerized battery capacity (1960 kWh)
        "start_time_hr": 6.0,
        "stations": stations,
    }


def calculate_energy_consumption(
    distance_nm: float,
    current_knots: float,
    boat_speed_knots: float,
    base_consumption_per_nm: float,
) -> float:
    base_energy = distance_nm * base_consumption_per_nm
    multiplier = 1.2 if current_knots < 0 else 0.8
    return base_energy * multiplier


def build_segment_option(
    segment_name: str,
    distance_nm: float,
    current_knots: float,
    boat_speed_knots: float,
    base_consumption_per_nm: float,
) -> SegmentOption:
    ground_speed = boat_speed_knots + current_knots
    if ground_speed <= 0:
        raise ValueError(f"Ground speed becomes non-positive for segment {segment_name}.")
    travel_time_hr = distance_nm / ground_speed
    energy_kwh = calculate_energy_consumption(
        distance_nm,
        current_knots,
        boat_speed_knots,
        base_consumption_per_nm,
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
    route = config["route"]
    distances = config["distances_nm"]
    currents = config["currents_knots"]
    boat_speed = float(config["boat_speed_knots"])
    base_consumption = float(config["base_consumption_per_nm"])

    segments: List[Segment] = []
    for start, end in _pairwise(route):
        key = f"{start}-{end}"
        if key not in distances or key not in currents:
            raise ValueError(f"Missing data for segment {key}")
        option = build_segment_option(
            segment_name=f"{start}->{end}",
            distance_nm=float(distances[key]),
            current_knots=float(currents[key]),
            boat_speed_knots=boat_speed,
            base_consumption_per_nm=base_consumption,
        )
        segments.append(Segment(start=start, end=end, options=[option]))

    stations: List[Station] = []
    for name in route:
        station_cfg = config.get("stations", {}).get(name, {})
        operating = station_cfg.get("operating_hours")
        operating_tuple = None
        if operating:
            if len(operating) != 2:
                raise ValueError(f"Station {name} operating_hours must have two values")
            operating_tuple = (float(operating[0]), float(operating[1]))
        
        stations.append(
            Station(
                name=name,
                docking_time_hr=float(station_cfg.get("docking_time_hr", 2.0)),
                swap_operation_time_hr=float(station_cfg.get("swap_operation_time_hr", 0.5)),
                mandatory_stop=_safe_bool(station_cfg.get("mandatory_stop", False), default=False),
                operating_hours=operating_tuple,
                available_batteries=_safe_int(station_cfg.get("available_batteries")),
                allow_swap=_safe_bool(station_cfg.get("allow_swap", True), default=True),
                force_swap=_safe_bool(station_cfg.get("force_swap", False), default=False),
                partial_swap_allowed=_safe_bool(station_cfg.get("partial_swap_allowed", False), default=False),
                energy_cost_per_kwh=float(station_cfg.get("energy_cost_per_kwh", 0.25)),  # UK realistic: £0.16-£0.40/kWh
                # Charging infrastructure
                charging_power_kw=float(station_cfg.get("charging_power_kw", 0.0)),
                charging_efficiency=float(station_cfg.get("charging_efficiency", 0.95)),
                charging_allowed=_safe_bool(station_cfg.get("charging_allowed", False), default=False),
                # Simplified pricing components
                swap_cost=float(station_cfg.get("swap_cost", 0.0)),
                base_service_fee=float(station_cfg.get("base_service_fee", 8.0)),
                degradation_fee_per_kwh=float(station_cfg.get("degradation_fee_per_kwh", 0.0)),
                base_charging_fee=float(station_cfg.get("base_charging_fee", 0.0)),
            )
        )

    battery_capacity = float(config["battery_capacity_kwh"])
    battery_container_capacity = float(config.get("battery_container_capacity_kwh", 1960.0))  # Default to standard container
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
                "Force Swap": station_cfg.get("force_swap", False),
                "Swap Cost": station_cfg.get("swap_cost", 0.0),
                "Swap Time (hr)": station_cfg.get("swap_time_hr", 0.0),
                "Queue Time (hr)": station_cfg.get("queue_time_hr", 0.0),
                "Open Hour": operating[0] if operating else 0.0,
                "Close Hour": operating[1] if operating else 24.0,
                "Available Batteries": station_cfg.get("available_batteries", pd.NA),
                "Energy Cost (£/kWh)": station_cfg.get("energy_cost_per_kwh", 0.25),  # UK realistic
            }
        )
    stations_df = pd.DataFrame(station_rows)
    if not stations_df.empty:
        stations_df["Available Batteries"] = stations_df["Available Batteries"].astype("Int64")
    return segments_df, stations_df


def form_frames_to_config(
    route_text: str,
    segments_df: pd.DataFrame,
    stations_df: pd.DataFrame,  # <-- Receives the station data now
    params: Dict[str, float],
    default_config: Dict | None = None,  # <-- Add default config to merge pricing
) -> Dict:
    stops = [stop.strip() for stop in route_text.split(",") if stop.strip()]
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
            "mandatory_stop": _safe_bool(record.get("Mandatory Stop"), default=False),
            "allow_swap": _safe_bool(record.get("Allow Swap"), default=True),
            "force_swap": _safe_bool(record.get("Force Swap"), default=False),
            "partial_swap_allowed": _safe_bool(record.get("Partial Swap"), default=False),
            "charging_allowed": _safe_bool(record.get("Charging Allowed"), default=False),
            "docking_time_hr": _safe_float(record.get("Docking Time (hr)"), 2.0),
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
        
        available = record.get("Available Batteries")
        # Handle the 999 placeholder for 'unlimited'
        if available == 999:
             cfg["available_batteries"] = None
        else:
            available_int = _safe_int(available)
            if available_int is not None:
                cfg["available_batteries"] = available_int
                
        station_cfg[name] = cfg

    for stop in stops:
        station_cfg.setdefault(stop, {})

    config = {
        "route": stops,
        "distances_nm": distances,
        "currents_knots": currents,
        "boat_speed_knots": params["boat_speed"],
        "base_consumption_per_nm": params["base_consumption"],
        "battery_capacity_kwh": params["battery_capacity"],
        "battery_container_capacity_kwh": params.get("battery_container_capacity", 1960.0),
        "initial_soc_kwh": params.get("initial_soc_kwh", params["battery_capacity"]),
        "minimum_soc_fraction": params["minimum_soc"],
        "energy_cost_per_kwh": 0.09,  # Default fallback (actual costs are per-station)
        "soc_step_kwh": params["soc_step"],
        "start_time_hr": params["start_time"],
        "stations": station_cfg,
        "vessel_type": params.get("vessel_type", "Cargo/Container"),
        "vessel_gt": params.get("vessel_gt", 2000),
    }
    return config


def run_optimizer(config: Dict) -> Tuple[pd.DataFrame, Dict[str, object]]:
    inputs = build_inputs(config)
    optimizer = FixedPathOptimizer(inputs)
    result = optimizer.solve()

    steps_rows: List[Dict[str, object]] = []
    soc_profile: List[Tuple[str, float]] = []
    for step in result.steps:
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
                "Travel (hr)": step.travel_time_hr,
                "SoC Before (kWh)": step.soc_before_kwh,
                "SoC After Operation (kWh)": step.soc_after_operation_kwh,
                "SoC After Segment (kWh)": step.soc_after_segment_kwh,
                "Incremental Cost": step.incremental_cost,
                "Cumulative Cost": step.cumulative_cost,
                "Hotelling Energy (kWh)": step.hotelling_energy_kwh,
                "Hotelling Power (kW)": step.hotelling_power_kw,
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

    # --- CALCULATE TRUE COST BREAKDOWN ONCE ---
    # This matches the optimizer's actual hybrid pricing model
    total_swap_service_cost = 0.0
    total_energy_charging_cost = 0.0
    total_degradation = 0.0
    total_hotelling_cost = 0.0
    battery_cap = config.get('battery_capacity_kwh', 1960.0)
    
    swap_cost_details = []  # Store individual swap costs for table
    
    if not steps_df.empty:
        for idx, row in steps_df.iterrows():
            if row['Swap']:
                station_name = row['Station']
                station_config = config.get('stations', {}).get(station_name, {})
                soc_before_swap = row['SoC Before (kWh)']
                num_containers = row.get('Containers', 1)
                arrival_time = row['Arrival (hr)']
                
                # Calculate ACTUAL energy charged (SoC-based billing)
                energy_needed = battery_cap - soc_before_swap
                
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
                    'swap_time': station_config.get('swap_time_hr', 0),
                    'partial_swap_allowed': station_config.get('partial_swap_allowed', False),
                    'berth_time': row.get('Berth Time (hr)', 0),
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
                total_num_containers = int(battery_cap / config.get('battery_container_capacity_kwh', 1960))
                swap_mode = "🔄 Partial" if (detail['partial_swap_allowed'] and detail['num_containers'] < total_num_containers) else "📦 Full Set"
                
                soc_before_pct = (detail['soc_before'] / battery_cap) * 100
                
                swap_table_data.append({
                    'Station': detail['station_name'],
                    'Mode': swap_mode,
                    'Containers': detail['num_containers'],
                    'Berth Time': f"{detail['berth_time']:.2f} hr",
                    'Returned SoC': f"{detail['soc_before']:.0f} kWh ({soc_before_pct:.0f}%)",
                    'Energy Charged': f"{detail['energy_needed']:.0f} kWh",
                    'Hotelling': f"{detail['hotelling_energy']:.0f} kWh" if detail['hotelling_energy'] > 0 else "—",
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
                total_num_containers = int(battery_cap / config.get('battery_container_capacity_kwh', 1960))
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
                    "Incremental Cost": st.column_config.NumberColumn("Step Cost", format="£%.2f"),
                    "Cumulative Cost": st.column_config.NumberColumn("Total Cost", format="£%.2f"),
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
            
            for idx, row in steps_df.iterrows():
                segment = row['Segment']
                soc_before = row['SoC Before (kWh)']
                soc_after = row['SoC After Segment (kWh)']
                energy_consumed = soc_before - soc_after
                
                # Check if swap happened
                if row['Swap']:
                    soc_before = battery_cap  # After swap
                    energy_consumed = battery_cap - soc_after
                
                cumulative_energy += energy_consumed
                
                energy_data.append({
                    'Segment': segment,
                    'Energy Consumed (kWh)': energy_consumed,
                    'SoC Before (kWh)': soc_before,
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
                soc_before = row['SoC Before (kWh)']
                soc_after = row['SoC After Segment (kWh)']
                swapped = row['Swap']
                
                # Get segment details
                segment_key = segment.replace('->', '-')
                distance = config.get('distances_nm', {}).get(segment_key, 0)
                current = config.get('currents_knots', {}).get(segment_key, 0)
                base_consumption = config.get('base_consumption_per_nm', 220)
                
                # Calculate actual energy consumed
                energy_consumed = soc_before - soc_after
                
                # Calculate what was required for this segment
                multiplier = 1.2 if current < 0 else 0.8
                energy_required = distance * base_consumption * multiplier
                
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
                    'Segment': segment,
                    'Distance': f"{distance:.1f} NM",
                    'Flow': flow_direction,
                    'Required': f"{energy_required:.0f} kWh",
                    'Available': f"{soc_before:.0f} kWh",
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
                energy_consumed = row['SoC Before (kWh)'] - row['SoC After Segment (kWh)']
                
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
        col1, col2, col3 = st.columns(3)
        
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

    # Authentication check
    if not st.session_state.get('authenticated', False):
        show_login_page()
        return

    # Show user profile/logout in sidebar
    with st.sidebar:
        show_logout_button()

        st.markdown("---")

        # Add profile management
        with st.expander("� Profile", expanded=False):
            show_user_profile()

        st.header("⚙️ Configuration")

        st.markdown("---")

        run_button = st.button(
            "🚀 Run Optimisation",
            type="primary",
            use_container_width=True,
            key="run_optimisation_button",
            help="Click to compute the optimal battery swap strategy"
        )

    # Main app content (only shown when authenticated)
    st.title("🚢 Marine Vessels Battery Swapping Optimiser")
    st.markdown("---")

    default_config = load_default_config()
    
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
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            vessel_gt = st.number_input(
                "**Gross Tonnage (GT)**",
                min_value=100,
                max_value=50000,
                value=default_gt,
                step=100,
                key=f"vessel_gt_{vessel_type.value}",
                help=f"Typical: {default_gt:,} GT"
            )
        
        with col2:
            boat_speed = st.number_input(
                "**Speed (knots)**",
                min_value=3.0,
                max_value=20.0,
                value=default_speed,
                step=0.5,
                key=f"vessel_speed_{vessel_type.value}",
                help=f"Typical: {default_speed} knots"
            )
        
        with col3:
            base_consumption = st.number_input(
                "**Energy (kWh/NM)**",
                min_value=10.0,
                max_value=400.0,
                value=default_consumption,
                step=5.0,
                key=f"base_consumption_{vessel_type.value}",
                help=f"Typical: {default_consumption} kWh/NM"
            )
        
        # Calculate and display hotelling power
        vessel_specs_temp = VesselSpecs(vessel_type=vessel_type, gross_tonnage=vessel_gt)
        hotelling_power = vessel_specs_temp.get_hotelling_power_kw()
        
        # Key Metrics Display
        st.info(f"⚡ **Hotelling Power:** {hotelling_power:,.0f} kW  |  "
                f"⏱️ **Average Docking Time:** {recommended_docking_time} hours")
        
        st.markdown("---")
        
        # SECTION 3: Battery Configuration (Grouped together)
        st.markdown("### 3️⃣ Battery System")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            battery_container_capacity = st.number_input(
                "**Container Size (kWh)**",
                min_value=100.0,
                max_value=5000.0,
                value=1960.0,
                step=50.0,
                help="Standard: 1960 kWh per 20ft container"
            )
        
        with col2:
            num_containers = st.number_input(
                "**# Containers**",
                min_value=1,
                max_value=20,
                value=default_containers,
                step=1,
                key=f"num_containers_{vessel_type.value}",
                help=f"Typical: {default_containers}"
            )
        
        battery_capacity = battery_container_capacity * num_containers
        
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
            initial_soc_kwh = battery_capacity * initial_soc_fraction
        
        # Battery System Summary
        battery_chemistry = "LFP (Lithium Iron Phosphate)"
        energy_density = 120.0
        battery_weight_kg = (battery_capacity * 1000) / energy_density
        battery_weight_tonnes = battery_weight_kg / 1000
        max_range = battery_capacity / base_consumption if base_consumption > 0 else 0
        usable_battery = battery_capacity * (1 - minimum_soc)
        usable_range_still_water = usable_battery / base_consumption if base_consumption > 0 else 0
        
        # Calculate realistic ranges with river flow effects
        usable_range_downstream = (usable_battery / base_consumption) / 0.8 if base_consumption > 0 else 0
        usable_range_upstream = (usable_battery / base_consumption) / 1.2 if base_consumption > 0 else 0
        
        weight_ratio = (battery_weight_tonnes / vessel_gt) * 100 if vessel_gt > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("**Total Capacity**", f"{battery_capacity/1000:.1f} MWh", 
                     help=f"{battery_capacity:,.0f} kWh")
        with col2:
            st.metric("**Range (Downstream)**", f"{usable_range_downstream:.0f} NM",
                     help=f"⬇️ With flow (0.8× energy) | {usable_battery:,.0f} kWh usable",
                     delta="Best case")
        with col3:
            st.metric("**Range (Upstream)**", f"{usable_range_upstream:.0f} NM",
                     help=f"⬆️ Against flow (1.2× energy) | {usable_battery:,.0f} kWh usable",
                     delta="Worst case",
                     delta_color="inverse")
        with col4:
            st.metric("**Battery Weight**", f"{battery_weight_tonnes:.1f} t",
                     help=f"{weight_ratio:.1f}% of vessel GT")
        
        # Range explanation
        st.info(f"""
        📊 **Range Analysis** ({usable_battery:,.0f} kWh usable @ {base_consumption:.0f} kWh/NM):
        • **Downstream (⬇️)**: {usable_range_downstream:.0f} NM - traveling with river flow (0.8× energy)
        • **Still Water**: {usable_range_still_water:.0f} NM - no current (1.0× energy)  
        • **Upstream (⬆️)**: {usable_range_upstream:.0f} NM - against river flow (1.2× energy)
        
        ⚠️ **Important**: Your actual range per segment depends on river flow direction!
        """)
        
        st.markdown("---")
        
        # SECTION 4: Journey Settings (Grouped together)
        st.markdown("### 4️⃣ Journey Settings")
        
        start_time = st.number_input(
            "**Departure Time (24h)**",
            min_value=0.0,
            max_value=23.5,
            value=8.0,
            step=0.5,
            key="departure_time_hr",
            help="Journey start time"
        )
        
        # Hidden - use fixed SoC precision internally
        soc_step = 10.0  # Fixed at 20 kWh for optimal balance
        
        # Advanced Details (Collapsed by default)
        with st.expander("� **Detailed Performance Metrics**", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Battery System:**")
                st.write(f"- Containers: {num_containers} × {battery_container_capacity:.0f} kWh")
                st.write(f"- Total: {battery_capacity:,.0f} kWh ({battery_capacity/1000:.2f} MWh)")
                st.write(f"- Usable: {usable_battery:,.0f} kWh ({(1-minimum_soc)*100:.0f}%)")
                st.write(f"- Weight: {battery_weight_tonnes:.2f} tonnes")
                st.write(f"- Weight/Container: {battery_weight_tonnes/num_containers:.2f} t")
            
            with col2:
                st.markdown("**Vessel Performance:**")
                st.write(f"- Type: {vessel_type.value}")
                st.write(f"- GT: {vessel_gt:,}")
                st.write(f"- Battery/GT: {weight_ratio:.2f}%")
                st.write(f"- Speed: {boat_speed:.1f} knots")
                st.write(f"- Consumption: {base_consumption:.1f} kWh/NM")
                st.write(f"- Hotelling: {hotelling_power:,.0f} kW")
        
        # Reference Data (Hidden for simplified UI - removed)

    # Interactive Form (always shown)
    if True:
        # ========================================
        # ROUTE CONFIGURATION
        # ========================================
        with st.expander("🗺️ **ROUTE CONFIGURATION**", expanded=True):
            st.markdown("### Define Your Journey")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                num_stations = st.number_input(
                    "**Number of Stations**",
                    min_value=2,
                    max_value=20,
                    value=5,
                    step=1,
                    help="Total stations including start and end"
                )
            
            with col2:
                st.info(f"✓ **{num_stations}** stations → **{num_stations-1}** segments to configure")
            
            st.markdown("---")
            
            # Generate station names in a cleaner grid
            st.markdown("**🏪 Station Names**")
            
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
            st.caption("💡 Upstream = against flow (1.2× energy) | Downstream = with flow (0.8× energy)")
            
            # Build segment data based on current stations
            segment_rows = []
            for i in range(len(station_names) - 1):
                start_name = station_names[i]
                end_name = station_names[i + 1]
                key = f"{start_name}-{end_name}"
                
                # Try to get default values if they exist
                default_dist = default_config["distances_nm"].get(key, 40.0)
                default_curr = default_config["currents_knots"].get(key, 0.0)
                
                # Convert to absolute value and direction
                flow_speed = abs(default_curr)
                flow_direction = "Upstream" if default_curr < 0 else "Downstream"
                
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

        # ========================================
        # STATION CONFIGURATION
        # ========================================
        with st.expander("🔋 **STATION SETTINGS**", expanded=True):
            st.markdown("### Configure Swap & Charging Facilities")
            
            # QUICK SETTINGS - Apply to All
            st.markdown("#### ⚡ Quick Apply to All Stations")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                global_docking_time = st.number_input(
                    "**Docking Time (hr)**",
                    min_value=0.0,
                    max_value=12.0,
                    value=recommended_docking_time,
                    step=0.25,
                    key="global_docking_time",
                    help=f"Recommended: {recommended_docking_time}h for {vessel_type.value}"
                )
            
            with col2:
                global_charging_power = st.number_input(
                    "**Charging (kW)**",
                    min_value=0.0,
                    max_value=2000.0,
                    value=250.0,
                    step=50.0,
                    key="global_charging_power",
                    help="Shore power capacity"
                )
            
            with col3:
                global_partial_swap = st.checkbox(
                    "**Partial Swap**",
                    value=False,
                    key="global_partial_swap",
                    help="Only swap depleted containers (cost-saving)"
                )
            
            st.markdown("---")
            
            # INDIVIDUAL STATION CONTROLS - More compact tabs
            st.markdown("#### � Individual Station Controls")
            
            # Create tabs for each station (more compact than expanders)
            station_tabs = st.tabs([f"🏪 {name}" for name in station_names])
            
            station_rows = []
            for idx, (tab, name) in enumerate(zip(station_tabs, station_names)):
                with tab:
                    # Try to get default values if they exist
                    default_swap_settings = default_config.get("swap_settings", {})
                    default_station = default_swap_settings.get(name, {})
                    
                    # Two-column layout for compact presentation
                    col_left, col_right = st.columns(2)
                    
                    with col_left:
                        st.markdown("**⚙️ Operations**")
                        
                        # Mandatory stop - vessel must dock here regardless of battery needs
                        mandatory_stop = st.checkbox(
                            "Mandatory Stop",
                            value=default_station.get("mandatory_stop", idx == 0 or idx == len(station_names) - 1),
                            key=f"mandatory_{name}",
                            help="Vessel MUST dock here (scheduled stop, passenger pickup, etc.). Optimizer will decide what action to take."
                        )
                        
                        allow_swap = st.checkbox(
                            "Allow Swap",
                            value=default_station.get("allow_swap", True),
                            key=f"allow_{name}"
                        )
                        
                        charging_allowed = st.checkbox(
                            "Allow Charging",
                            value=default_station.get("charging_allowed", True),
                            key=f"charging_{name}"
                        )
                        
                        force_swap = st.checkbox(
                            "Force Swap",
                            value=default_station.get("force_swap", False),
                            key=f"force_{name}",
                            help="Require swap for inspection/maintenance"
                        )
                        
                        # Partial swap: controlled by global setting when enabled
                        if global_partial_swap:
                            st.checkbox(
                                "Partial Swap Allowed",
                                value=True,
                                key=f"partial_global_{name}",
                                disabled=True,
                                help="Controlled by global setting"
                            )
                            partial_swap = True
                        else:
                            partial_swap = st.checkbox(
                                "Partial Swap Allowed",
                                value=default_station.get("partial_swap_allowed", False),
                                key=f"partial_{name}"
                            )
                        
                        st.markdown("**⏰ Operating Hours**")
                        open_hour = st.number_input(
                            "Opens at (hr)",
                            min_value=0.0,
                            max_value=24.0,
                            value=default_station.get("open_hour", 0.0),
                            step=0.5,
                            key=f"open_{name}"
                        )
                        
                        close_hour = st.number_input(
                            "Closes at (hr)",
                            min_value=0.0,
                            max_value=24.0,
                            value=default_station.get("close_hour", 24.0),
                            step=0.5,
                            key=f"close_{name}"
                        )
                    
                    with col_right:
                        st.markdown("**⏱️ Operations**")
                        
                        station_docking_time = st.number_input(
                            "Docking Time (hr)",
                            min_value=0.0,
                            max_value=12.0,
                            value=global_docking_time,
                            step=0.25,
                            key=f"docking_time_{name}_{global_docking_time}",
                            help="Duration for operations: battery swap (30 min - 1 hr), charging (variable), or mandatory stop duration. Set to 0.0 for pass-through stations."
                        )
                        
                        st.markdown("**🔌 Charging & Batteries**")
                        
                        station_charging_power = st.number_input(
                            "Charging Power (kW)",
                            min_value=0.0,
                            max_value=2000.0,
                            value=global_charging_power,
                            step=50.0,
                            key=f"charging_power_{name}_{global_charging_power}"
                        )
                        
                        # Show charging capacity info
                        if station_charging_power > 0 and station_docking_time > 0:
                            max_energy_charged = station_charging_power * station_docking_time * 0.95
                            pct_of_battery = (max_energy_charged / battery_capacity * 100) if battery_capacity > 0 else 0
                            if pct_of_battery < 100:
                                st.caption(f"⚡ Can charge ~{max_energy_charged:.0f} kWh in {station_docking_time}h ({pct_of_battery:.1f}% of battery)")
                            else:
                                st.caption(f"⚡ Can fully charge battery in {station_docking_time}h")
                        
                        station_charging_fee = st.number_input(
                            "Charging Fee (£)",
                            min_value=0.0,
                            max_value=100.0,
                            value=25.0,  # UK realistic: £10-£50 per session
                            step=5.0,
                            key=f"charging_fee_{name}",
                            help="UK realistic: £10-£50 per charging session"
                        )
                        
                        st.markdown("**💰 Swap Costs**")
                        
                        base_service_fee = st.number_input(
                            "Base Service Fee (£)",
                            min_value=0.0,
                            max_value=200.0,
                            value=default_station.get("base_service_fee", 15.0),  # UK realistic: £8-£40 per container
                            step=5.0,
                            key=f"base_service_fee_{name}",
                            help="Cost per container swapped (includes handling and operations)"
                        )
                        
                        degradation_fee_per_kwh = st.number_input(
                            "Battery Wear Fee (£/kWh)",
                            min_value=0.0,
                            max_value=0.50,
                            value=default_station.get("degradation_fee_per_kwh", 0.03),  # Default to 0.03 (£0.03/kWh wear cost)
                            step=0.01,
                            format="%.3f",
                            key=f"degradation_fee_{name}",
                            help="Battery degradation cost per kWh charged (default £0.03/kWh)"
                        )
                        
                        batteries = st.number_input(
                            "Battery Stock",
                            min_value=0,
                            max_value=50,
                            value=default_station.get("available_batteries", 7),
                            key=f"batteries_{name}",
                            help="Fully charged containers available"
                        )
                        
                        st.markdown("**💰 Energy Cost**")
                        energy_cost_station = st.number_input(
                            "£/kWh",
                            min_value=0.0,
                            max_value=1.0,
                            value=default_station.get("energy_cost_per_kwh", 0.25),  # UK realistic: £0.16-£0.40/kWh
                            step=0.01,
                            format="%.3f",
                            key=f"energy_cost_{name}",
                            help="UK realistic: £0.16-£0.40/kWh (typical £0.25)"
                        )
                    
                    # Collect data from UI elements
                    station_rows.append({
                        "Station": name,
                        "Mandatory Stop": mandatory_stop,
                        "Allow Swap": allow_swap,
                        "Force Swap": force_swap,
                        "Partial Swap": partial_swap,
                        "Charging Allowed": charging_allowed,
                        "Docking Time (hr)": station_docking_time,
                        "Charging Power (kW)": station_charging_power,
                        "Charging Fee (£)": station_charging_fee,
                        "Base Service Fee": base_service_fee,
                        "Battery Wear Fee": degradation_fee_per_kwh,
                        "Open Hour": open_hour,
                        "Close Hour": close_hour,
                        "Available Batteries": batteries,
                        "Energy Cost (£/kWh)": energy_cost_station,
                    })
            
            stations_df = pd.DataFrame(station_rows)

    params = {
        "boat_speed": boat_speed,
        "base_consumption": base_consumption,
        "battery_capacity": battery_capacity,
        "battery_container_capacity": battery_container_capacity,
        "initial_soc_kwh": initial_soc_kwh,
        "minimum_soc": minimum_soc,
        "soc_step": soc_step,
        "start_time": start_time,
        "vessel_type": vessel_type.value,
        "vessel_gt": vessel_gt,
    }

    if run_button:
        try:
            with st.status("⚙️ **Preparing optimisation...**", expanded=True) as status:
                st.write("🔍 Validating configuration...")
                config = form_frames_to_config(route_text, segments_df, stations_df, params, default_config)
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
                    base_consumption = config.get('base_consumption_per_nm', 0)
                    min_soc_fraction = config.get('minimum_soc_fraction', 0)
                    
                    # Calculate theoretical range
                    usable_battery = battery_capacity * (1 - min_soc_fraction)
                    max_range = usable_battery / base_consumption if base_consumption > 0 else 0
                    
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
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.markdown("**Route Info**")
                                st.write(f"- Stations: {len(route)}")
                                st.write(f"- Segments: {len(route) - 1}")
                                st.write(f"- Total Distance: {total_distance:.1f} NM")
                            
                            with col2:
                                st.markdown("**Battery Info**")
                                st.write(f"- Capacity: {battery_capacity:.0f} kWh")
                                st.write(f"- Usable: {usable_battery:.0f} kWh ({(1-min_soc_fraction)*100:.0f}%)")
                                st.write(f"- Range: {max_range:.1f} NM")
                            
                            with col3:
                                st.markdown("**Energy Info**")
                                st.write(f"- Consumption: {base_consumption:.1f} kWh/NM")
                                st.write(f"- Est. Energy: {total_distance * base_consumption:.0f} kWh")
                                energy_deficit = (total_distance * base_consumption) - usable_battery
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
                            
                            for i in range(len(route) - 1):
                                start = route[i]
                                end = route[i + 1]
                                key = f"{start}-{end}"
                                
                                distance = config.get('distances_nm', {}).get(key, 0)
                                current = config.get('currents_knots', {}).get(key, 0)
                                boat_speed = config.get('boat_speed_knots', 5.0)
                                
                                # Calculate energy for this segment
                                segment_energy = distance * base_consumption
                                if current < 0:  # Upstream
                                    segment_energy *= 1.2
                                else:  # Downstream
                                    segment_energy *= 0.8
                                
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

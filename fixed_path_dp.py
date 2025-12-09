from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any

try:
    from cold_ironing_reference import VesselTypeHotelling
    COLD_IRONING_AVAILABLE = True
except ImportError:
    COLD_IRONING_AVAILABLE = False


class VesselType(Enum):
    """Marine vessel types with corresponding hotelling power characteristics."""
    CRUISE_SHIP = "Cruise ships"
    TANKER = "Chemical Tankers"
    PASSENGER_FERRY = "Ferry"
    CARGO_CONTAINER = "Container vessels"
    GENERAL_CARGO = "Cargo vessels"
    BULK_CARRIER = "Cargo vessels"
    RO_RO = "Cargo vessels"
    AUTO_CARRIER = "Auto Carrier"
    CRUDE_OIL_TANKER = "Crude oil tanker"
    OFFSHORE_SUPPLY = "Offshore Supply"
    SERVICE_VESSELS = "Service Vessels"
    OTHER = "Other"


@dataclass(frozen=True)
class VesselSpecs:
    """Vessel specifications for energy calculations."""
    vessel_type: VesselType
    gross_tonnage: float  # GT
    
    def get_hotelling_power_kw(self) -> float:
        """
        Calculate hotelling power demand (kW) based on vessel type and gross tonnage.
        
        Uses industry-standard cold-ironing reference data when available,
        otherwise falls back to empirical formula.
        
        Based on actual port shore power measurements showing average hotelling
        power by vessel type and GT range.
        """
        # Try to use cold-ironing reference data first (most accurate)
        if COLD_IRONING_AVAILABLE:
            try:
                power = VesselTypeHotelling.get_hotelling_power(
                    self.vessel_type.value,
                    self.gross_tonnage,
                )
                # Reference data returns 0 for some small vessels or unsupported ranges
                # Use fallback formula if we get 0
                if power > 0:
                    return power
            except Exception:
                # If the cold-ironing reference data throws an exception, fall back to the
                # empirical formula below
                pass  # Fall through to empirical formula
        
        # FALLBACK: Use empirical formula (legacy method)
        # Base factors (kW per GT) calibrated to research data
        type_factors = {
            VesselType.CRUISE_SHIP: 0.15,      # Highest energy demand
            VesselType.TANKER: 0.10,           # High demand for pumping, heating
            VesselType.PASSENGER_FERRY: 0.12,  # High HVAC and passenger services
            VesselType.CARGO_CONTAINER: 0.05,  # Moderate - mainly for reefer containers
            VesselType.GENERAL_CARGO: 0.04,    # Lower demand
            VesselType.BULK_CARRIER: 0.03,     # Minimal auxiliary loads
            VesselType.RO_RO: 0.06,            # Moderate - ventilation systems
            VesselType.AUTO_CARRIER: 0.08,     # Moderate-high - ventilation for vehicles
            VesselType.CRUDE_OIL_TANKER: 0.09, # High demand for pumping/heating
            VesselType.OFFSHORE_SUPPLY: 0.12,  # High - dynamic positioning systems
            VesselType.SERVICE_VESSELS: 0.10,  # Variable loads
            VesselType.OTHER: 0.03,            # Conservative estimate
        }
        
        factor = type_factors.get(self.vessel_type, 0.03)
        base_power = self.gross_tonnage * factor
        
        # Apply realistic bounds based on research
        max_power = {
            VesselType.CRUISE_SHIP: 11000,
            VesselType.TANKER: 10000,
            VesselType.PASSENGER_FERRY: 7000,
            VesselType.CARGO_CONTAINER: 5000,
            VesselType.GENERAL_CARGO: 3000,
            VesselType.BULK_CARRIER: 2000,
            VesselType.RO_RO: 4000,
            VesselType.AUTO_CARRIER: 5000,
            VesselType.CRUDE_OIL_TANKER: 10000,
            VesselType.OFFSHORE_SUPPLY: 2000,
            VesselType.SERVICE_VESSELS: 2000,
            VesselType.OTHER: 2000,
        }
        
        min_power = {
            VesselType.CRUISE_SHIP: 1000,
            VesselType.TANKER: 500,
            VesselType.PASSENGER_FERRY: 500,
            VesselType.CARGO_CONTAINER: 200,
            VesselType.GENERAL_CARGO: 100,
            VesselType.BULK_CARRIER: 100,
            VesselType.RO_RO: 200,
            VesselType.AUTO_CARRIER: 200,
            VesselType.CRUDE_OIL_TANKER: 500,
            VesselType.OFFSHORE_SUPPLY: 200,
            VesselType.SERVICE_VESSELS: 100,
            VesselType.OTHER: 100,
        }
        
        max_limit = max_power.get(self.vessel_type, 2000)
        min_limit = min_power.get(self.vessel_type, 100)
        
        return max(min_limit, min(base_power, max_limit))
    
    def get_hotelling_load_percentage(self) -> float:
        """
        Get the percentage of vessel's total battery capacity used per hour during hotelling.
        
        Returns typical load as fraction (e.g., 0.15 for 15% of capacity per hour).
        This is used when battery capacity is known.
        """
        # These are average load factors during hotelling (% of max power)
        load_factors = {
            VesselType.CRUISE_SHIP: 0.70,      # High continuous load (HVAC, services)
            VesselType.TANKER: 0.60,           # Pumping, heating
            VesselType.PASSENGER_FERRY: 0.65,  # Passenger comfort systems
            VesselType.CARGO_CONTAINER: 0.50,  # Reefer containers, lighting
            VesselType.GENERAL_CARGO: 0.40,    # Basic services
            VesselType.BULK_CARRIER: 0.35,     # Minimal services
            VesselType.RO_RO: 0.45,            # Ventilation
            VesselType.OTHER: 0.40,            # Conservative
        }
        
        return load_factors.get(self.vessel_type, 0.40)


@dataclass(frozen=True)
class SegmentOption:
    label: str
    travel_time_hr: float
    energy_kwh: float
    extra_cost: float = 0.0


@dataclass(frozen=True)
class Segment:
    start: str
    end: str
    options: List[SegmentOption]


@dataclass(frozen=True)
class Station:
    name: str
    docking_time_hr: float = 2.0  # Time for MANDATORY stops (passenger ops, cargo, scheduled stops)
    swap_operation_time_hr: float = 0.5  # Time for battery swap operation (typically 30 min - 1 hr). Fixed per-operation, not per-container.
    mandatory_stop: bool = False  # If True, vessel MUST dock for docking_time_hr regardless of battery needs
    allow_swap: bool = True
    force_swap: bool = False
    partial_swap_allowed: bool = False  # If True, can swap only depleted containers; if False, must swap all
    operating_hours: Optional[Tuple[float, float]] = None
    available_batteries: Optional[int] = None
    total_batteries: Optional[int] = None
    energy_cost_per_kwh: float = 0.25  # Station-specific energy pricing (UK realistic: £0.16-£0.40/kWh, typical £0.25)
    
    # Charging Infrastructure
    charging_power_kw: float = 0.0  # Available shore power charging capacity (kW)
    charging_efficiency: float = 1.00  # Charging efficiency (AC/DC conversion losses)
    charging_allowed: bool = False  # Whether charging infrastructure is available
    
    # Hybrid/Custom Pricing Components (UK Realistic Costs)
    swap_cost: float = 0.0  # Per-container swap handling fee (scales with number of containers)
    base_service_fee: float = 15.0  # Base service fee per container (UK realistic: £8-£40, typical £15)
    degradation_fee_per_kwh: float = 0.0  # Charge based on battery wear/degradation
    base_charging_fee: float = 25.0  # Fixed fee for using charging infrastructure (UK realistic: £10-£50, typical £25)
    # Background charging capacity (charging of spare containers when vessel is not present)
    background_charging_power_kw: float = 2000.0  # kW used to charge spare containers between vessel visits
    background_charging_allowed: bool = True  # Whether background charging is available at this station
    # Total grid power available to the station. When vessel is present some of this may be used for vessel charging
    total_grid_power_kw: float = 0.0
    # Minimum SOC threshold (0.0-1.0) to consider a battery available for swapping
    min_swap_soc: float = 1.0


@dataclass(frozen=True)
class FixedPathInputs:
    stations: List[Station]
    segments: List[Segment]
    battery_capacity_kwh: float  # Total battery system capacity
    battery_container_capacity_kwh: float  # Capacity per individual container (default: 2460 kWh)
    initial_soc_kwh: float
    final_soc_min_kwh: float
    energy_cost_per_kwh: float
    min_soc_kwh: float = 0.0
    soc_step_kwh: float = 1.0
    start_time_hr: float = 0.0
    # Inventory mode: 'aggregate' uses bucketed SOC distribution, 'counts' uses simple count-based inventory
    inventory_mode: str = 'counts'
    vessel_specs: Optional[VesselSpecs] = None  # Vessel type and GT for hotelling calculations
    vessel_charging_power_kw: float = 1e9  # Maximum charging power the vessel can accept (kW). Large default means no limit.
    # Time quantization step for last-visit recording (hours). Smaller -> more accuracy, larger -> smaller DP state.
    time_quant_hr: float = 0.25

    def __post_init__(self) -> None:
        if len(self.stations) != len(self.segments) + 1:
            raise ValueError("stations count must be segments + 1")
        if self.initial_soc_kwh > self.battery_capacity_kwh:
            raise ValueError("initial SoC exceeds capacity")
        if self.initial_soc_kwh < self.min_soc_kwh:
            raise ValueError("initial SoC below minimum operating SoC")
        if self.soc_step_kwh <= 0:
            raise ValueError("SoC step must be positive")
        if self.final_soc_min_kwh < 0:
            raise ValueError("final SoC requirement must be non-negative")
        if self.min_soc_kwh < 0:
            raise ValueError("minimum operating SoC must be non-negative")
        if self.min_soc_kwh > self.battery_capacity_kwh:
            raise ValueError("minimum operating SoC exceeds capacity")
        if self.final_soc_min_kwh > self.battery_capacity_kwh:
            raise ValueError("final SoC requirement exceeds capacity")
        if self.final_soc_min_kwh < self.min_soc_kwh:
            raise ValueError("final SoC requirement cannot be below minimum operating SoC")
        for station in self.stations:
            if station.docking_time_hr < 0:
                raise ValueError(f"Station {station.name} docking time must be non-negative")
            if station.available_batteries is not None and station.available_batteries < 0:
                raise ValueError(f"Station {station.name} available batteries cannot be negative")
            if station.total_batteries is not None and station.total_batteries < 0:
                raise ValueError(f"Station {station.name} total batteries cannot be negative")
            if station.charging_power_kw < 0:
                raise ValueError(f"Station {station.name} charging power cannot be negative")
            if station.background_charging_power_kw < 0:
                raise ValueError(f"Station {station.name} background_charging_power_kw cannot be negative")
            if station.total_grid_power_kw < 0:
                raise ValueError(f"Station {station.name} total_grid_power_kw cannot be negative")
            if not (0.0 <= station.charging_efficiency <= 1.0):
                raise ValueError(f"Station {station.name} charging efficiency must be between 0 and 1")
        if self.vessel_charging_power_kw < 0:
            raise ValueError("vessel_charging_power_kw cannot be negative")


@dataclass(frozen=True)
class StepResult:
    station_name: str
    swap_taken: bool
    num_containers_swapped: int  # Number of battery containers swapped at this station
    charging_taken: bool = False  # Whether charging was performed
    energy_charged_kwh: float = 0.0  # Energy charged from shore power
    operation_type: str = "none"  # Operation type: none, swap, charge, hybrid
    arrival_time_hr: float = 0.0
    departure_time_hr: float = 0.0
    station_docking_time_hr: float = 0.0
    soc_before_kwh: float = 0.0
    soc_after_operation_kwh: float = 0.0  # SoC after swap/charge operations
    segment_label: str = ""
    energy_used_kwh: float = 0.0
    travel_time_hr: float = 0.0
    soc_after_segment_kwh: float = 0.0
    incremental_cost: float = 0.0
    cumulative_cost: float = 0.0
    incremental_time_hr: float = 0.0
    cumulative_time_hr: float = 0.0
    hotelling_energy_kwh: float = 0.0  # Energy consumed during dwell time (onboard services)
    hotelling_power_kw: float = 0.0    # Hotelling power demand for this vessel type
    # Station inventory dynamics (before/after this step)
    station_charged_before: Optional[int] = None
    station_charged_after: Optional[int] = None
    station_total_before: Optional[int] = None
    station_total_after: Optional[int] = None
    containers_precharged: int = 0
    containers_charged_during_stop: int = 0
    precharge_energy_kwh: float = 0.0
    # Station-level timeline events for this step; helpful for single/multi-vessel traceability
    station_events: List[Dict[str, Any]] = field(default_factory=list)


# BatteryAggregateState removed: we now use count-only inventory mode (BatteryCountState)


@dataclass
class BatteryCountState:
    """Simple count-based battery state used for a simplified inventory mode.

    charged: number of swap-ready containers (at or above min swap SOC)
    total: total containers at station
    """
    capacity_per_battery_kwh: float
    charged: int = 0
    total: int = 0
    start_empty_soc: float = 0.2
    partial_energy_kwh: float = 0.0

    def add_energy(self, energy_kwh: float, charging_efficiency: float = 1.0, min_swap_soc: float = 1.0) -> float:
        """Add energy to station inventory, convert energy into containers that meet `min_swap_soc`.
        Returns leftover energy (unused) in kWh.
        """
        effective_energy = energy_kwh * charging_efficiency + self.partial_energy_kwh
        per_to_min = max(0.0, (min_swap_soc - self.start_empty_soc) * self.capacity_per_battery_kwh)
        if per_to_min <= 0:
            # Nothing to charge to reach min
            self.partial_energy_kwh = effective_energy
            return 0.0
        can_make = int(effective_energy // per_to_min)
        # Limit by available spare containers
        avail_spares = max(0, self.total - self.charged)
        to_create = min(can_make, avail_spares)
        if to_create > 0:
            self.charged += to_create
            used = to_create * per_to_min
            effective_energy -= used
        # store remainder to partial buffer
        self.partial_energy_kwh = effective_energy
        return 0.0

    def remove_n_highest(self, n: int) -> float:
        """Remove n charged containers (swap out). Return energy removed as if they are full containers.
        This consumes n from charged counts and assumes container is full (1.0) when passed to vessel.
        """
        take = min(self.charged, n)
        self.charged -= take
        return take * self.capacity_per_battery_kwh

    def get_available_for_swap(self, min_soc: float = 1.0) -> int:
        return int(self.charged)

    def get_total_batteries(self) -> int:
        return int(self.total)

    def encode(self) -> int:
        return int(self.charged)

    @classmethod
    def from_bucket_tuple(cls, encoded: Tuple[int, ...], capacity_per_battery_kwh: float):
        # encoded is a bucket tuple; top bucket is charged; total is sum
        charged = int(encoded[-1])
        total = int(sum(encoded))
        return cls(capacity_per_battery_kwh=capacity_per_battery_kwh, charged=charged, total=total)

    def add_depleted_batteries(self, n: int, arrival_soc: float = 0.2) -> None:
        """
        Track returned depleted batteries for recharging.

        When the vessel returns batteries at low SoC (typically 20%), they need to be 
        added back to the station's inventory so they can be recharged during the 
        time between vessel visits.

        Args:
            n: Number of containers returned from vessel
            arrival_soc: State of charge of returned containers (0.0-1.0), typically 0.2
        """
        if n <= 0:
            return

        # Returned containers have some residual charge (arrival_soc)
        # Add this residual energy to the partial_energy_kwh buffer
        residual_energy_per_container = arrival_soc * self.capacity_per_battery_kwh
        total_residual_energy = n * residual_energy_per_container

        # Add residual energy to the buffer for charging
        self.partial_energy_kwh += total_residual_energy

        # Note: We do NOT change self.charged or self.total here
        # The returned containers increase the "pending charge" buffer
        # When add_energy() is called during background charging, it will convert them
        # from partial_energy_kwh to the charged pool


@dataclass(frozen=True)
class OptimisationResult:
    total_cost: float
    total_time_hr: float
    finish_time_hr: float
    steps: List[StepResult]
    # Timeline events recorded per station across the reconstructed path
    station_timelines: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)


@dataclass(frozen=True)
class _Transition:
    prev_level: int
    swapped: bool
    charged: bool
    operation_type: str  # "none", "swap", "charge", "hybrid"
    num_containers_swapped: int
    energy_charged_kwh: float
    total_operation_cost: float
    station_docking_time_hr: float
    soc_after_operation_kwh: float
    option_index: int
    energy_kwh: float
    travel_time_hr: float
    energy_cost: float
    extra_cost: float
    hotelling_energy_kwh: float = 0.0  # Hotelling energy during dwell
    # For inventory-aware DP, store the previous state's encoded inventory tuple
    prev_inventory: Optional[Tuple[int, ...]] = None
    precharge_energy_kwh: float = 0.0

    @property
    def incremental_cost(self) -> float:
        return self.total_operation_cost + self.energy_cost + self.extra_cost

    @property
    def incremental_time(self) -> float:
        return (
            self.station_docking_time_hr
            + self.travel_time_hr
        )


class FixedPathOptimizer:
    def __init__(self, inputs: FixedPathInputs) -> None:
        self.inputs = inputs
        cap_steps = self._to_step(inputs.battery_capacity_kwh)
        self._capacity_steps = cap_steps
        self._soc_levels = cap_steps + 1
        self._min_operating_level = self._to_step(inputs.min_soc_kwh)
        # Time quantization step (hours) used to record the last visit times for inventory state
        self._time_quant_hr = inputs.time_quant_hr
        # Inventory sentinel for unlimited: use -1 to mark unlimited charged counts
        self._UNLIMITED = -1

    def solve(self) -> OptimisationResult:
        inputs = self.inputs
        # Quick feasibility pre-check: compute total energy required vs possible replenishment
        total_segment_energy = sum(opt.energy_kwh for seg in inputs.segments for opt in seg.options)
        required_total_energy = total_segment_energy + inputs.final_soc_min_kwh
        # Compute maximum potential energy that can be provided by station containers (charged + precharge)
        total_container_energy_available = 0.0
        for s in inputs.stations:
            # Skip start station if it's the vessel origin (we only count station supplies at stops)
            # We'll treat None as unlimited which means we cannot pre-check precisely
            containers_available = s.available_batteries if s.available_batteries is not None else None
            containers_total = s.total_batteries if s.total_batteries is not None else None
            if containers_available is None:
                # Station unlimited -> cannot perform accurate pre-check; skip and allow DP to try
                total_container_energy_available = float('inf')
                break
            # Compute possible precharging during docking
            precharge_possible = 0
            precharge_time = s.docking_time_hr if s.mandatory_stop else s.swap_operation_time_hr
            if s.charging_allowed and s.charging_power_kw > 0 and precharge_time > 0:
                energy_can_charge = s.charging_power_kw * precharge_time * s.charging_efficiency
                precharge_possible = int(math.floor(energy_can_charge / inputs.battery_container_capacity_kwh))
            # Bound by total stock if provided
            effective_containers = containers_available + precharge_possible
            if containers_total is not None:
                effective_containers = min(effective_containers, containers_total)
            total_container_energy_available += effective_containers * inputs.battery_container_capacity_kwh

        # Total energy available = initial vehicle SOC + energy from all node containers
        if not math.isinf(total_container_energy_available):
            total_energy_avail = inputs.initial_soc_kwh + total_container_energy_available
            if total_energy_avail < required_total_energy - 1e-9:
                # Fail fast with helpful message
                raise ValueError(
                    "No feasible solution: Total energy (initial SoC + station charged/chargeable containers) "
                    f"<{required_total_energy:.1f} kWh required for journey. Available: {total_energy_avail:.1f} kWh."
                )
        # DP uses (soc_level, inventory_tuple) as state for each station index
        # Inventory tuple: list of charged container counts for each station; -1 denotes unlimited
        num_stations = len(inputs.stations)
        # Build unique station name list for inventory indexing - inventory is station-level (unique by name), not position
        unique_station_names: List[str] = []
        for s in inputs.stations:
            if s.name not in unique_station_names:
                unique_station_names.append(s.name)
        # Inventory tracks unique station names only
        num_inventory_stations = len(unique_station_names)
        name_to_inv_idx: Dict[str, int] = {n: i for i, n in enumerate(unique_station_names)}
        # Warn if this DP will be very large due to many unique stations (inventory state explosion)
        if len(unique_station_names) > 10:
            print(f"WARNING: Inventory-aware DP will track {len(unique_station_names)} stations. This may be slow.")
        # Inventory encoding includes both charged-count and the last-visit quantized time
        # Layout: [charged_0, lastq_0, charged_1, lastq_1, ...]
        def encode_inventory(charged_arr: List[int | None], last_visit_arr: List[int | None]) -> Tuple[int, ...]:
            """Encode either legacy charged-counts or per-station battery distribution encodings.

            New format for each station: [bucket0, bucket1, ..., bucketN, last_visit_q]
            Legacy format is supported where charged_arr contains ints; we will convert to distribution
            with all available in the 1.0 bucket and depleted in a low bucket (0.2 by default).
            """
            enc: List[int] = []
            for idx, (v, t) in enumerate(zip(charged_arr, last_visit_arr)):
                count = v if v is not None and v != self._UNLIMITED else 0
                enc.append(int(count))
                enc.append(t if t is not None else -1)
            return tuple(enc)

        def decode_inventory(tup: Tuple[int, ...]) -> Tuple[List[int], List[int | None]]:
            """Decode inventory tuple into list of per-station charged counts and last visit times.
            Expected format: [charged_0, lastq_0, charged_1, lastq_1, ...]
            """
            if len(tup) != num_inventory_stations * 2:
                raise ValueError("Inventory tuple length mismatch; expected 2 values per station (charged, lastq)")
            charged_counts: List[int] = []
            last_vis: List[int | None] = []
            for i in range(0, len(tup), 2):
                v = tup[i]
                t = tup[i + 1]
                charged_counts.append(int(v))
                last_vis.append(None if int(t) == -1 else int(t))
            return charged_counts, last_vis

        # Initial inventory from inputs
        init_charged = []
        init_last_visit_quant: List[int | None] = []
        for name in unique_station_names:
            s = next(st for st in inputs.stations if st.name == name)
            init_charged.append(s.available_batteries if s.available_batteries is not None else None)
            # default last visit: if station is the starting station, set to the start time; else None
            if s.name == inputs.stations[0].name:
                init_last_visit_quant.append(int(round(inputs.start_time_hr / self._time_quant_hr)))
            else:
                init_last_visit_quant.append(None)
        init_inv_enc = encode_inventory(init_charged, init_last_visit_quant)

        # DP dictionaries per station index
        # dp[idx] maps (soc_level, inv_tuple) -> (best_cost, best_time, battery_source_idx)
        dp: List[Dict[Tuple[int, Tuple[int, ...]], Tuple[float, float, int]]] = [dict() for _ in inputs.stations]
        prev: List[Dict[Tuple[int, Tuple[int, ...]], Optional[_Transition]]] = [dict() for _ in inputs.stations]

        start_level = self._to_step(inputs.initial_soc_kwh)
        # Validate initial inventory encoding
        if len(init_inv_enc) != num_inventory_stations * 2:
            raise RuntimeError(f"Initial inventory encoding length mismatch: got {len(init_inv_enc)} expected {num_inventory_stations*2}")
        dp[0][(start_level, init_inv_enc)] = (0.0, 0.0, 0)  # initial battery source = station 0

        for idx, segment in enumerate(inputs.segments):
                station = inputs.stations[idx]
                next_station = inputs.stations[idx + 1]
                # iterate over all DP states at station idx
                dp_states = list(dp[idx].items())
                for ((level, inv_enc), (base_cost, base_time, battery_source_idx)) in dp_states:
                    soc_before = self._from_step(level)
                    arrival_time_hr = self.inputs.start_time_hr + base_time
                    inv_list, last_visit_list = decode_inventory(inv_enc)
                    # Debugging info
                    # Debugging prints removed — preserved assertion checks below
                    # Debug: ensure decode returned expected lengths
                    if len(inv_list) != num_inventory_stations:
                        raise RuntimeError(f"Decoded inventory length mismatch; inv_list={inv_list} expected length {num_inventory_stations}")
                    # inv_list now contains per-station encodings; create BatteryAggregateState or BatteryCountState objects depending on mode
                    battery_states = []
                    if inputs.inventory_mode == 'counts':
                        for i, enc in enumerate(inv_list):
                            # Identify the corresponding station total to set counts
                            name = unique_station_names[i]
                            st = next((s for s in inputs.stations if s.name == name), None)
                            total_stock = st.total_batteries if st is not None else None
                            if isinstance(enc, tuple):
                                bs = BatteryCountState.from_bucket_tuple(enc, capacity_per_battery_kwh=inputs.battery_container_capacity_kwh)
                                if total_stock is not None:
                                    bs.total = int(total_stock)
                            else:
                                charged_val = int(enc) if enc is not None else 0
                                bs = BatteryCountState(capacity_per_battery_kwh=inputs.battery_container_capacity_kwh, charged=charged_val, total=int(total_stock) if total_stock is not None else charged_val)
                            battery_states.append(bs)
                    # Only counts-mode is supported now; ignore aggregate bucket format
                    candidate_levels = self._candidate_levels(station, level, arrival_time_hr)
                    for (
                        level_after_operation,
                        operation_cost,
                        docking_time,
                        swapped,
                        charged,
                        operation_type,
                        num_containers_swapped,
                        energy_charged_kwh,
                        hotelling_energy,
                        candidate_precharge_energy_kwh,
                    ) in candidate_levels:
                        new_battery_source_idx = idx if swapped else battery_source_idx
                        soc_post_operation = self._from_step(level_after_operation)
                        # precharge energy during this docking provided by the candidate tuple (kWh)
                        # candidate_precharge_energy_kwh is already unpacked from candidate_levels

                        # determine charged_before effective by adding precharge (both during stay and between visits), respecting total_batteries bound
                        inv_idx = name_to_inv_idx.get(station.name, None)
                        if inv_idx is None or inv_idx >= len(battery_states):
                            raise RuntimeError(f"Inventory index out of range for station {station.name}: inv_idx={inv_idx}, battery_states_len={len(battery_states)}, unique_names={unique_station_names}")
                        charged_state = battery_states[inv_idx]
                        charged_before = charged_state.get_available_for_swap(min_soc=station.min_swap_soc)
                        last_visit_q = last_visit_list[name_to_inv_idx[station.name]]
                        # Determine background charging between visits if allowed and we have a quantized last-visit
                        background_precharge_containers = 0
                        # Determine effective background charging power. Prefer explicit background capacity; otherwise use station total grid.
                        bg_power_candidate = 0.0
                        if station.background_charging_allowed:
                            # Use explicit background capacity if provided; only cap by grid when grid is non-zero.
                            if station.background_charging_power_kw and station.background_charging_power_kw > 0:
                                if station.total_grid_power_kw and station.total_grid_power_kw > 0:
                                    bg_power_candidate = min(station.background_charging_power_kw, station.total_grid_power_kw)
                                else:
                                    bg_power_candidate = station.background_charging_power_kw
                            elif station.total_grid_power_kw and station.total_grid_power_kw > 0:
                                bg_power_candidate = station.total_grid_power_kw
                            elif station.charging_power_kw and station.charging_power_kw > 0:
                                # Final fallback
                                bg_power_candidate = station.charging_power_kw
                        if bg_power_candidate > 0 and last_visit_q is not None:
                            last_visit_hr = last_visit_q * self._time_quant_hr
                            time_since_last_visit = max(0.0, arrival_time_hr - last_visit_hr)
                            energy_bg_grid = bg_power_candidate * time_since_last_visit
                            # Apply energy to the battery aggregate to update its distribution
                            # We will clone the battery state for calculation below
                            background_precharge_containers = 0
                        total_stock = station.total_batteries if station.total_batteries is not None else None
                        # simulate precharge (during-docking precharge and background precharge)
                        # Clone battery_state to compute precharge and swaps without mutating original
                        if inputs.inventory_mode == 'counts':
                            # Clone a BatteryCountState
                            bs_clone = BatteryCountState(capacity_per_battery_kwh=inputs.battery_container_capacity_kwh,
                                                         charged=int(getattr(charged_state, 'charged', 0)),
                                                         total=int(getattr(charged_state, 'total', getattr(charged_state, 'charged', 0))),
                                                         start_empty_soc=float(getattr(charged_state, 'start_empty_soc', 0.2)),
                                                         partial_energy_kwh=float(getattr(charged_state, 'partial_energy_kwh', 0.0)))
                        # Only count-mode is supported now; bs_clone constructed as BatteryCountState above
                        # Apply background precharge energy if available
                        if bg_power_candidate > 0 and last_visit_q is not None and time_since_last_visit > 0:
                            bs_clone.add_energy(energy_bg_grid, charging_efficiency=station.charging_efficiency,
                                                min_swap_soc=station.min_swap_soc)
                        # Apply candidate (stay) precharge modeled as 'candidate_precharge_containers' worth of energy
                        if candidate_precharge_energy_kwh and candidate_precharge_energy_kwh > 0:
                            bs_clone.add_energy(candidate_precharge_energy_kwh, charging_efficiency=station.charging_efficiency,
                                                min_swap_soc=station.min_swap_soc)
                        # Charged effective is defined as number of fully charged packs (in 1.0 bucket)
                        # Count batteries available for swapping as those >= 80% SOC
                        charged_effective = bs_clone.get_available_for_swap(min_soc=station.min_swap_soc)
                        if total_stock is not None:
                            charged_effective = min(charged_effective, int(total_stock))

                        # For each travel option, check feasibility and update inventory
                        for option_idx, option in enumerate(segment.options):
                            energy_steps = self._energy_to_steps(option.energy_kwh)
                            if level_after_operation < energy_steps:
                                continue
                            new_level = level_after_operation - energy_steps
                            if new_level < self._min_operating_level:
                                continue

                            # HARD CONSTRAINT: Must maintain minimum operating SoC to continue
                            new_soc_after_travel = self._from_step(new_level)
                            if new_soc_after_travel < self.inputs.min_soc_kwh:
                                # Insufficient energy for this path - skip it
                                continue
                            # At final station, enforce final SoC requirement
                            if idx + 1 == len(self.inputs.stations) - 1:  # Final station
                                if new_soc_after_travel < self.inputs.final_soc_min_kwh:
                                    # Skip solutions that don't meet final SoC requirement
                                    continue
                            travel_time = option.travel_time_hr
                            energy_cost = 0.0
                            new_cost = base_cost + operation_cost + option.extra_cost + energy_cost
                            new_time = base_time + docking_time + travel_time

                            # If swap was requested, ensure charged_effective allows it
                            if swapped:
                                containers_to_swap = num_containers_swapped
                                if charged_effective is not None and charged_effective < containers_to_swap:
                                    # Not enough charged containers for a swap
                                    continue

                            # Build new inventory list
                            # Clone battery_states to produce new state for next step
                            if inputs.inventory_mode == 'counts':
                                new_battery_states = [BatteryCountState(capacity_per_battery_kwh=inputs.battery_container_capacity_kwh,
                                                                       charged=int(getattr(bs,'charged', 0)),
                                                                       total=int(getattr(bs, 'total', getattr(bs, 'charged', 0))),
                                                                       start_empty_soc=float(getattr(bs, 'start_empty_soc', 0.2)),
                                                                       partial_energy_kwh=float(getattr(bs, 'partial_energy_kwh', 0.0))) for bs in battery_states]
                            # Only count-mode is supported now
                            # Apply precharge clone values to the new_battery_states for this station
                            if charged_state is not None:
                                # bs_clone already contains precharge applied
                                new_battery_states[name_to_inv_idx[station.name]] = bs_clone
                            # Update the last visit time for this station to the departure time (arrival + docking)
                            new_last_visit = list(last_visit_list)
                            # departure time
                            departure_time_hr = arrival_time_hr + docking_time
                            new_last_visit[name_to_inv_idx[station.name]] = int(round(departure_time_hr / self._time_quant_hr))
                            # Apply swap: remove high-SOC batteries from station and add depleted batteries
                            if swapped and num_containers_swapped > 0:
                                station_state_for_swap = new_battery_states[name_to_inv_idx[station.name]]
                                removed_energy_kwh = station_state_for_swap.remove_n_highest(num_containers_swapped)
                                # Deteriorated/depleted batteries returned from vessel arrive at lower SOC bucket
                                station_state_for_swap.add_depleted_batteries(num_containers_swapped, arrival_soc=0.2)

                            # Encode the new_battery_states into the inventory tuple
                            enc_buckets = [int(bs.encode()) for bs in new_battery_states]
                            inv_enc_next = encode_inventory([x for x in enc_buckets], new_last_visit)
                            key_next = (new_level, inv_enc_next)
                            current_next = dp[idx+1].get(key_next)
                            old_cost, old_time, _ = current_next if current_next is not None else (math.inf, math.inf, -1)
                            if self._improves(new_cost, new_time, old_cost, old_time):
                                # record this new state
                                dp[idx+1][key_next] = (new_cost, new_time, new_battery_source_idx)
                                prev[idx+1][key_next] = _Transition(
                                    prev_level=level,
                                    swapped=swapped,
                                    charged=charged,
                                    operation_type=operation_type,
                                    num_containers_swapped=num_containers_swapped,
                                    energy_charged_kwh=energy_charged_kwh,
                                    total_operation_cost=operation_cost,
                                    station_docking_time_hr=docking_time,
                                    soc_after_operation_kwh=soc_post_operation,
                                    option_index=option_idx,
                                    energy_kwh=option.energy_kwh,
                                    travel_time_hr=travel_time,
                                    energy_cost=energy_cost,
                                    extra_cost=option.extra_cost,
                                    hotelling_energy_kwh=hotelling_energy,
                                    precharge_energy_kwh=candidate_precharge_energy_kwh,
                                    prev_inventory=inv_enc,
                                )

        best_level, best_inv_enc, best_cost, best_time = self._select_terminal_state(dp)
        steps, station_timelines = self._reconstruct(prev, best_level, best_inv_enc, best_cost, best_time, dp)
        finish_time_hr = self.inputs.start_time_hr + best_time
        return OptimisationResult(
            total_cost=best_cost,
            total_time_hr=best_time,
            finish_time_hr=finish_time_hr,
            steps=steps,
            station_timelines=station_timelines,
        )

    def _candidate_levels(
        self, station: Station, level: int, arrival_time_hr: float
    ) -> List[Tuple[int, float, float, bool, bool, str, int, float, float, float]]:
        """
        Generate all feasible energy operation options at a station.
        
        Returns list of tuples: (level_after_operation, operation_cost, docking_time, 
                                  swapped, charged, operation_type, num_containers_swapped,
                                  energy_charged_kwh, hotelling_energy_kwh)
        """
        options: List[Tuple[int, float, float, bool, bool, str, int, float, float, float]] = []

        if station.force_swap and not station.allow_swap:
            raise ValueError(
                f"Station {station.name} requires swap but swap not allowed"
            )

        current_soc_kwh = self._from_step(level)
        capacity_kwh = self.inputs.battery_capacity_kwh
        
        # Get hotelling power for energy consumption calculations
        hotelling_power_kw = 0.0
        if self.inputs.vessel_specs is not None:
            hotelling_power_kw = self.inputs.vessel_specs.get_hotelling_power_kw()

        # OPTION 1: No operation
        # If mandatory_stop=True: vessel MUST dock but may not need any action
        # If mandatory_stop=False: only dock if optimizer decides to take action
        if not station.force_swap:
            if station.mandatory_stop:
                # Mandatory stop: vessel docks for the specified docking time
                # Hotelling power consumed during docking, but no other operations
                dwell_time_no_op = station.docking_time_hr
                hotelling_energy_no_op = hotelling_power_kw * dwell_time_no_op
            else:
                # Optional stop: pass through without docking if no action needed
                dwell_time_no_op = 0.0
                hotelling_energy_no_op = 0.0
            
            # Subtract hotelling energy that occurs during the dwell time from the SoC
            soc_after_noop_kwh = max(0.0, current_soc_kwh - hotelling_energy_no_op)
            level_after_noop = self._to_step(soc_after_noop_kwh)
            # Precharge during stay when not charging
            vessel_charging_power_used = 0.0
            precharge_noop = 0.0
            if station.background_charging_allowed and dwell_time_no_op > 0:
                bg_max = station.background_charging_power_kw if station.background_charging_power_kw > 0 else station.total_grid_power_kw
                if station.total_grid_power_kw and station.total_grid_power_kw > 0:
                    bg_available = max(0.0, min(bg_max, station.total_grid_power_kw - vessel_charging_power_used))
                else:
                    bg_available = max(0.0, bg_max)
                energy_precharge = bg_available * dwell_time_no_op * station.charging_efficiency
                precharge_noop = energy_precharge
            options.append((level_after_noop, 0.0, dwell_time_no_op, False, False, "none", 0, 0.0, hotelling_energy_no_op, precharge_noop))

        # OPTION 2: Full/Partial Swap Only
        if station.allow_swap:
            # Calculate swap cost based on full vs partial swap mode
            total_num_containers = int(capacity_kwh / self.inputs.battery_container_capacity_kwh)
            if total_num_containers < 1:
                total_num_containers = 1
            
            # Determine allowable containers to swap
            if station.partial_swap_allowed:
                # PARTIAL SWAP: allow swapping any number of depleted containers.
                # Use station.min_swap_soc to compute how many containers are considered 'ready' for swap.
                # A container is considered ready if its per-container SoC >= min_swap_soc.
                per_container_ready_kwh = max(1e-12, station.min_swap_soc * self.inputs.battery_container_capacity_kwh)
                ready_containers = int(current_soc_kwh // per_container_ready_kwh)
                # Cap ready containers at total number of containers onboard
                ready_containers = min(ready_containers, total_num_containers)
                depleted_containers = total_num_containers - ready_containers
                if depleted_containers < 0:
                    depleted_containers = 0
                # If vessel is not fully charged but depleted_containers is zero (fuzzy rounding), allow 1 as a minimal swap
                if current_soc_kwh < capacity_kwh and depleted_containers == 0:
                    depleted_containers = 1
                # Range of swap sizes: from 1..depleted_containers
                candidate_swap_counts = list(range(1, depleted_containers + 1)) if depleted_containers >= 1 else []
            else:
                # FULL SWAP: Always swap the entire battery set only
                candidate_swap_counts = [total_num_containers]

            # Compute available charged containers at time of swap
            initial_charged = station.available_batteries if station.available_batteries is not None else None
            total_stock = station.total_batteries if station.total_batteries is not None else None

            # If no explicit available values are given, treat as 'unlimited'
            def _is_unlimited(val):
                return val is None

            # Pre-swap charging capability: can charge spare containers during docking, accounting for vessel use
            pre_swap_time = station.docking_time_hr if station.mandatory_stop else station.swap_operation_time_hr
            # For swap-only operation vessel is not charging, so vessel_charging_power_used = 0
            vessel_charging_power_used = 0.0
            precharge_energy = 0.0
            if station.background_charging_allowed and pre_swap_time > 0:
                bg_max = station.background_charging_power_kw if station.background_charging_power_kw > 0 else station.total_grid_power_kw
                if station.total_grid_power_kw and station.total_grid_power_kw > 0:
                    bg_available = max(0.0, min(bg_max, station.total_grid_power_kw - vessel_charging_power_used))
                else:
                    bg_available = max(0.0, bg_max)
                energy_can_charge = pre_swap_time * bg_available * station.charging_efficiency
                precharge_energy = energy_can_charge

            if _is_unlimited(initial_charged):
                effective_available = None
            else:
                # Cast to integer safely
                initial_charged_int = int(initial_charged) if initial_charged is not None else 0
                # If total_stock not provided, assume equal to initial_charged
                if _is_unlimited(total_stock):
                    total_stock_val = initial_charged_int
                else:
                    total_stock_val = int(total_stock) if total_stock is not None else initial_charged_int
                effective_available = min(total_stock_val, initial_charged_int + int(precharge_energy // self.inputs.battery_container_capacity_kwh))

            # For each swap size, check availability and compute cost
            for containers_to_swap in candidate_swap_counts:
                # Check if enough batteries are available for this containers_to_swap
                if effective_available is not None and effective_available < containers_to_swap:
                    if station.force_swap:
                        raise ValueError(
                            f"Station {station.name} requires swap of {containers_to_swap} containers "
                            f"but only {station.available_batteries} batteries available"
                        )
                    # Not enough batteries - skip this particular swap size
                    continue
                capacity_level = self._capacity_steps
                
                # Determine berth time: use mandatory stop time if applicable, otherwise swap operation time
                if station.mandatory_stop:
                    swap_time = station.docking_time_hr  # Mandatory stop: must stay for full docking time
                else:
                    swap_time = station.swap_operation_time_hr  # Energy-only stop: quick swap operation
                
                # Simplified swap cost calculation
                # Service fee scales with number of containers (includes handling + operations)
                service_fee_per_container = station.base_service_fee + station.swap_cost
                service_fee = service_fee_per_container * containers_to_swap
                
                # Energy transferred by swap should be based on number of containers swapped
                num_containers_to_swap = containers_to_swap  # keep count as int
                energy_transferred_kwh = containers_to_swap * self.inputs.battery_container_capacity_kwh
                # New energy cost is for the transferred energy only
                energy_cost = energy_transferred_kwh * station.energy_cost_per_kwh
                degradation_cost = energy_transferred_kwh * station.degradation_fee_per_kwh
                
                total_swap_cost = service_fee + energy_cost + degradation_cost
                
                # Add hotelling cost
                hotelling_energy_swap = hotelling_power_kw * swap_time
                hotelling_cost = hotelling_energy_swap * station.energy_cost_per_kwh
                total_swap_cost += hotelling_cost
                
                # After a swap, the vessel returns to full capacity, but hotelling energy during
                # the swap/docking reduces the effective SoC that will be available for the next
                # segment. Subtract the hotelling energy and clamp to [0, capacity_kwh].
                # After swapping containers, the vessel receives charged containers, so SoC increases by energy_transferred
                soc_after_swap_kwh = max(0.0, min(capacity_kwh, current_soc_kwh + energy_transferred_kwh - hotelling_energy_swap))
                level_after_swap = self._to_step(soc_after_swap_kwh)
                options.append((
                    level_after_swap,
                    total_swap_cost,
                    swap_time,
                    True,  # swapped
                    False,  # charged
                    "swap",
                    containers_to_swap,
                    0.0,  # energy_charged_kwh
                    hotelling_energy_swap
                    , precharge_energy))

        # OPTION 3: Charging Only (variable duration)
        if station.charging_allowed and station.charging_power_kw > 0 and not station.force_swap:
            # Discrete charging time options (in hours)
            charge_time_options = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0]
            
            # If mandatory stop, add the docking time as a charging option
            if station.mandatory_stop and station.docking_time_hr not in charge_time_options:
                charge_time_options = sorted(charge_time_options + [station.docking_time_hr])
            
            for charge_time in charge_time_options:
                # Calculate energy charged
                available_charging_kw = min(station.charging_power_kw, self.inputs.vessel_charging_power_kw)
                energy_charged_kwh = min(
                    charge_time * available_charging_kw * station.charging_efficiency,
                    capacity_kwh - current_soc_kwh  # Cannot exceed capacity
                )
                
                if energy_charged_kwh < 1.0:  # Skip trivial charging amounts
                    continue
                
                new_soc_kwh = current_soc_kwh + energy_charged_kwh
                new_level = self._to_step(new_soc_kwh)
                
                # Calculate charging cost
                charging_energy_cost = energy_charged_kwh * station.energy_cost_per_kwh
                base_charging_fee = station.base_charging_fee
                
                # Hotelling energy during charging
                hotelling_energy_charge = hotelling_power_kw * charge_time
                hotelling_cost = hotelling_energy_charge * station.energy_cost_per_kwh
                
                total_charging_cost = charging_energy_cost + base_charging_fee + hotelling_cost
                
                # After charging, account for the hotelling energy consumed during the charge time
                soc_after_charge_kwh = max(0.0, new_soc_kwh - hotelling_energy_charge)
                new_level_after_charge = self._to_step(soc_after_charge_kwh)
                # Compute background precharge during vehicle charging: station total grid minus vessel draw
                vessel_charging_power_used = available_charging_kw
                precharge_during_charge = 0.0
                if station.background_charging_allowed and charge_time > 0:
                    bg_max = station.background_charging_power_kw if station.background_charging_power_kw > 0 else station.total_grid_power_kw
                    # If total_grid_power_kw is zero/absent, don't cap background charging by it.
                    if station.total_grid_power_kw and station.total_grid_power_kw > 0:
                        bg_available = max(0.0, min(bg_max, station.total_grid_power_kw - vessel_charging_power_used))
                    else:
                        bg_available = max(0.0, bg_max)
                    energy_precharge = bg_available * charge_time * station.charging_efficiency
                    precharge_during_charge = energy_precharge

                options.append((
                    new_level_after_charge,
                    total_charging_cost,
                    charge_time,
                    False,  # swapped
                    True,  # charged
                    "charge",
                    0,  # num_containers_swapped
                    energy_charged_kwh,
                    hotelling_energy_charge
                    , precharge_during_charge))

        # OPTION 4: Hybrid (Swap + Charge)
        if station.allow_swap and station.charging_allowed and station.charging_power_kw > 0:
            # Hybrid time options: short charge after swap
            hybrid_charge_times = [0.5, 1.0, 2.0, 3.0, 4.0]
            
            for charge_time in hybrid_charge_times:
                # Determine base time: mandatory stop uses docking time, otherwise swap operation time
                base_time = station.docking_time_hr if station.mandatory_stop else station.swap_operation_time_hr
                total_time = base_time + charge_time
                
                # Calculate swap portion (same as full swap)
                total_num_containers = int(capacity_kwh / self.inputs.battery_container_capacity_kwh)
                if total_num_containers < 1:
                    total_num_containers = 1
                
                # determine candidate swap counts for hybrid options
                if station.partial_swap_allowed:
                    per_container_ready_kwh = max(1e-12, station.min_swap_soc * self.inputs.battery_container_capacity_kwh)
                    ready_containers = int(current_soc_kwh // per_container_ready_kwh)
                    ready_containers = min(ready_containers, total_num_containers)
                    depleted_containers = total_num_containers - ready_containers
                    if depleted_containers < 0:
                        depleted_containers = 0
                    if current_soc_kwh < capacity_kwh and depleted_containers == 0:
                        depleted_containers = 1
                    candidate_swap_counts = list(range(1, depleted_containers + 1)) if depleted_containers >= 1 else []
                else:
                    candidate_swap_counts = [total_num_containers]
                
                # Check if enough batteries are available for hybrid swap (consider charging capability)
                initial_charged = station.available_batteries if station.available_batteries is not None else None
                total_stock = station.total_batteries if station.total_batteries is not None else None
                if initial_charged is None:
                    effective_available = None
                else:
                    initial_charged_int = int(initial_charged)
                    total_stock_val = int(total_stock) if total_stock is not None else initial_charged_int
                    # Pre-swap charging time (if mandatory stop or swap op exists)
                    pre_swap_time = station.docking_time_hr if station.mandatory_stop else station.swap_operation_time_hr
                    precharge = 0
                    if station.charging_allowed and station.charging_power_kw > 0 and pre_swap_time > 0:
                        energy_can_charge = pre_swap_time * station.charging_power_kw * station.charging_efficiency
                        precharge = int(math.floor(energy_can_charge / self.inputs.battery_container_capacity_kwh))
                    effective_available = min(total_stock_val, initial_charged_int + precharge)
                # iterate through candidate swap counts for hybrid
                for containers_to_swap in candidate_swap_counts:
                    if effective_available is not None and effective_available < containers_to_swap:
                        continue  # Skip this hybrid candidate if not enough batteries

                    # After swap, SoC is at capacity (assuming swapping in charged containers)
                    soc_after_swap = capacity_kwh

                    # Then charge (which doesn't add much since already at capacity)
                    # But in partial swap case, there may be room for charging
                    available_charging_kw = min(station.charging_power_kw, self.inputs.vessel_charging_power_kw)
                    energy_charged_kwh = min(
                        charge_time * available_charging_kw * station.charging_efficiency,
                        capacity_kwh - soc_after_swap
                    )

                    # Skip if no meaningful charging happens and this is not a swap
                    if energy_charged_kwh < 0.1 and containers_to_swap == 0:
                        continue

                    final_soc_kwh = soc_after_swap + energy_charged_kwh
                    # After hybrid swap+charge, account for the hotelling energy consumed during the
                    # total time spent at the station (swap + charge portion)
                    hotelling_energy_hybrid = hotelling_power_kw * total_time
                    soc_after_hybrid_kwh = max(0.0, final_soc_kwh - hotelling_energy_hybrid)
                    final_level = self._to_step(soc_after_hybrid_kwh)

                    # Calculate hybrid cost (swap + charge) - simplified
                    service_fee_per_container = station.base_service_fee + station.swap_cost
                    service_fee = service_fee_per_container * containers_to_swap

                    num_containers_to_swap = containers_to_swap  # keep count as int
                    swap_energy_kwh = containers_to_swap * self.inputs.battery_container_capacity_kwh
                    swap_energy_cost = swap_energy_kwh * station.energy_cost_per_kwh
                    degradation_cost = swap_energy_kwh * station.degradation_fee_per_kwh

                    swap_cost = service_fee + swap_energy_cost + degradation_cost
                    charge_cost = energy_charged_kwh * station.energy_cost_per_kwh + station.base_charging_fee

                    # Hotelling for total hybrid time
                    hotelling_energy_hybrid = hotelling_power_kw * total_time
                    hotelling_cost = hotelling_energy_hybrid * station.energy_cost_per_kwh

                    total_hybrid_cost = swap_cost + charge_cost + hotelling_cost

                    # For hybrid: compute precharge during the base swap time + the charge time, background available after vessel power used
                    # Vessel is charging during the charge_time portion
                    vessel_charging_power_used = min(station.charging_power_kw, self.inputs.vessel_charging_power_kw)
                    # background for hybrid: station background power up to station total minus vessel charging power
                    hybrid_precharge = 0.0
                    if station.background_charging_allowed and total_time > 0:
                        bg_max = station.background_charging_power_kw if station.background_charging_power_kw > 0 else station.total_grid_power_kw
                        # During the swap time, vessel charging power is zero; during the charge time vessel uses charging power
                        # We approximate by assuming background available reduces for the charging_time only
                        # Compute energy during swap portion (vessel_charging_power_used = 0)
                        if station.total_grid_power_kw and station.total_grid_power_kw > 0:
                            bg_swap = max(0.0, min(bg_max, station.total_grid_power_kw - 0.0))
                        else:
                            bg_swap = max(0.0, bg_max)
                        energy_swap_precharge = bg_swap * (base_time) * station.charging_efficiency
                        # During charge portion
                        if station.total_grid_power_kw and station.total_grid_power_kw > 0:
                            bg_charge = max(0.0, min(bg_max, station.total_grid_power_kw - vessel_charging_power_used))
                        else:
                            bg_charge = max(0.0, bg_max)
                        energy_charge_precharge = bg_charge * (charge_time) * station.charging_efficiency
                        # Total precharge energy is sum of both parts
                        energy_precharge_total = energy_swap_precharge + energy_charge_precharge
                        hybrid_precharge = energy_precharge_total

                    options.append((
                        final_level,
                        total_hybrid_cost,
                        total_time,
                        True,  # swapped
                        True,  # charged
                        "hybrid",
                        containers_to_swap,
                        energy_charged_kwh,
                        hotelling_energy_hybrid
                        , hybrid_precharge))

        return options



    def _select_terminal_state(
        self,
        dp: List[Dict[Tuple[int, Tuple[int, ...]], Tuple[float, float, int]]],
    ) -> Tuple[int, Tuple[int, ...], float, float]:
        inputs = self.inputs
        final_idx = len(inputs.stations) - 1
        min_level = self._to_step(inputs.final_soc_min_kwh)
        best_level = -1
        best_cost = math.inf
        best_time = math.inf
        # Check all states in dp[final_idx]
        table = dp[final_idx]
        for (level, inv_enc), (cost, time, _) in table.items():
            if level < min_level:
                continue
            if not math.isfinite(cost):
                continue
            if self._improves(cost, time, best_cost, best_time):
                best_cost = cost
                best_time = time
                best_level = level
                best_inv = inv_enc
        if best_level < 0:
            # Provide detailed diagnostics about why no solution was found
            diagnostics = self._diagnose_infeasibility(dp)
            raise ValueError(
                f"No feasible solution found for final SoC requirement.\n\n"
                f"CONSTRAINT VIOLATION DIAGNOSTICS:\n"
                f"{diagnostics}"
            )
        return best_level, best_inv, best_cost, best_time

    def _reconstruct(
        self,
        prev: List[Dict[Tuple[int, Tuple[int, ...]], Optional[_Transition]]],
        level: int,
        inv_enc: Tuple[int, ...],
        best_cost: float,
        best_time: float,
        dp: List[Dict[Tuple[int, Tuple[int, ...]], Tuple[float, float, int]]],
    ) -> Tuple[List[StepResult], Dict[str, List[Dict[str, Any]]]]:
        steps: List[StepResult] = []
        idx = len(self.inputs.stations) - 1
        current_key = (level, inv_enc)
        cumulative_cost = best_cost
        cumulative_time = best_time
        while idx > 0:
            transition = prev[idx].get(current_key)
            if transition is None:
                raise RuntimeError("Missing transition during reconstruction")
            prev_level = transition.prev_level
            prev_inv = transition.prev_inventory
            if prev_inv is None:
                raise RuntimeError("Missing prev_inventory during reconstruction")
            prev_key = (prev_level, prev_inv)
            current_level = current_key[0]
            # (prev_key already set above)
            station = self.inputs.stations[idx - 1]
            segment = self.inputs.segments[idx - 1]
            option = segment.options[transition.option_index]
            soc_before = self._from_step(prev_level)
            soc_after_segment = self._from_step(current_level)
            step_cost = transition.incremental_cost
            step_time = transition.incremental_time
            arrival_elapsed = dp[idx - 1][prev_key][1]
            arrival_time_hr = self.inputs.start_time_hr + arrival_elapsed
            docking_time = transition.station_docking_time_hr
            departure_time_hr = arrival_time_hr + docking_time
            
            # Get hotelling power for display
            hotelling_power_kw = 0.0
            if self.inputs.vessel_specs is not None:
                hotelling_power_kw = self.inputs.vessel_specs.get_hotelling_power_kw()
            
            steps.append(
                StepResult(
                    station_name=station.name,
                    swap_taken=transition.swapped,
                    num_containers_swapped=transition.num_containers_swapped,
                    charging_taken=transition.charged,
                    energy_charged_kwh=transition.energy_charged_kwh,
                    operation_type=transition.operation_type,
                    arrival_time_hr=arrival_time_hr,
                    departure_time_hr=departure_time_hr,
                    station_docking_time_hr=docking_time,
                    soc_before_kwh=soc_before,
                    soc_after_operation_kwh=transition.soc_after_operation_kwh,
                    segment_label=option.label,
                    energy_used_kwh=transition.energy_kwh,
                    travel_time_hr=transition.travel_time_hr,
                    soc_after_segment_kwh=soc_after_segment,
                    incremental_cost=step_cost,
                    cumulative_cost=cumulative_cost,
                    incremental_time_hr=step_time,
                    cumulative_time_hr=cumulative_time,
                    hotelling_energy_kwh=transition.hotelling_energy_kwh,
                    hotelling_power_kw=hotelling_power_kw,
                    precharge_energy_kwh=transition.precharge_energy_kwh,
                    # Inventory placeholders - will be filled in the forward pass
                    station_charged_before=None,
                    station_charged_after=None,
                    station_total_before=None,
                    station_total_after=None,
                    containers_precharged=0,
                    containers_charged_during_stop=0,
                )
            )
            cumulative_cost -= step_cost
            cumulative_time -= step_time
            current_key = prev_key
            idx -= 1
        steps.reverse()

        # Forward-simulate station inventory dynamics to fill in station-level fields
        # Initialize station inventory maps
        container_kwh = self.inputs.battery_container_capacity_kwh
        battery_states_map: Dict[str, Any] = {}
        # Map store last departure time for each station (float in hours); initialized to start_time for origin
        last_departure_map: Dict[str, float | None] = {}
        for s in self.inputs.stations:
            charged = s.available_batteries if s.available_batteries is not None else (s.total_batteries if s.total_batteries is not None else 0)
            total = s.total_batteries if s.total_batteries is not None else charged
            battery_states_map[s.name] = BatteryCountState(capacity_per_battery_kwh=container_kwh, charged=int(charged), total=int(total))
            last_departure_map[s.name] = None
        # Set start station last visit to start time
        start_name = self.inputs.stations[0].name
        last_departure_map[start_name] = self.inputs.start_time_hr

        enriched_steps: List[StepResult] = []
        # Station timelines for the final path reconstructed - used for single-vessel and future multi-vessel
        station_timelines: Dict[str, List[Dict[str, Any]]] = {s.name: [] for s in self.inputs.stations}
        container_kwh = self.inputs.battery_container_capacity_kwh
        # Steps are in chronological order; for each step we can compute pre/post inventory
        for st in steps:
            s_name = st.station_name
            station_obj = next((x for x in self.inputs.stations if x.name == s_name), None)
            if s_name in battery_states_map:
                min_swap = station_obj.min_swap_soc if station_obj is not None else 1.0
                charged_before = battery_states_map[s_name].get_available_for_swap(min_soc=min_swap)
                total_before = battery_states_map[s_name].get_total_batteries()
            else:
                charged_before = None
                total_before = None

            containers_precharged = 0
            containers_charged_during_stop = 0

            station_obj = next((x for x in self.inputs.stations if x.name == s_name), None)
            if station_obj is None:
                # No station object - preserve as-is
                st_full = st
                enriched_steps.append(st_full)
                continue
            assert station_obj is not None
            station_charging_efficiency = station_obj.charging_efficiency

            # Compute background precharging since last visit (between visits)
            background_precharge = 0
            prev_dep = last_departure_map.get(s_name)
            # Determine effective background charging power for the station in forward simulation as well
            bg_power_candidate = 0.0
            if station_obj.background_charging_allowed:
                if station_obj.background_charging_power_kw and station_obj.background_charging_power_kw > 0:
                    bg_power_candidate = station_obj.background_charging_power_kw
                elif station_obj.charging_power_kw and station_obj.charging_power_kw > 0:
                    bg_power_candidate = station_obj.charging_power_kw
            if bg_power_candidate > 0 and prev_dep is not None and battery_states_map.get(s_name) is not None:
                time_since_last_visit = max(0.0, st.arrival_time_hr - prev_dep)
                energy_bg_grid = bg_power_candidate * time_since_last_visit
                before_full = battery_states_map[s_name].get_available_for_swap(min_soc=min_swap)
                battery_states_map[s_name].add_energy(energy_bg_grid, charging_efficiency=station_charging_efficiency,
                                                     min_swap_soc=min_swap)
                after_full = battery_states_map[s_name].get_available_for_swap(min_soc=min_swap)
                background_precharge = max(0, after_full - before_full)

            # Record arrival and background event
            events_for_step: List[Dict[str, Any]] = []
            events_for_step.append({
                "time_hr": st.arrival_time_hr,
                "event": "arrival",
                "charged_before": charged_before,
                "total_before": total_before,
            })
            if background_precharge > 0:
                events_for_step.append({
                    "time_hr": st.arrival_time_hr,
                    "event": "background_precharge",
                    "added": background_precharge,
                })

            # Apply candidate precharge energy from DP plan (kWh) to the station aggregate
            candidate_precharge_energy_kwh = getattr(st, 'precharge_energy_kwh', 0.0)
            candidate_precharge_added = 0
            if candidate_precharge_energy_kwh and battery_states_map.get(s_name) is not None:
                before_full_candidate = battery_states_map[s_name].get_available_for_swap(min_soc=min_swap)
                battery_states_map[s_name].add_energy(candidate_precharge_energy_kwh, charging_efficiency=station_charging_efficiency,
                                                     min_swap_soc=min_swap)
                after_full_candidate = battery_states_map[s_name].get_available_for_swap(min_soc=min_swap)
                candidate_precharge_added = max(0, after_full_candidate - before_full_candidate)
                if candidate_precharge_added > 0:
                    events_for_step.append({
                        "time_hr": st.arrival_time_hr + 0.0002,
                        "event": "precharge_candidate",
                        "energy_kwh": candidate_precharge_energy_kwh,
                        "added": candidate_precharge_added,
                    })

            # Compute maximum containers that can be charged during docking (as spare prep)
            dock_time = st.station_docking_time_hr
            precharge_possible = 0
            if station_obj.charging_allowed and station_obj.charging_power_kw > 0 and dock_time > 0:
                energy_can_charge = dock_time * station_obj.charging_power_kw * station_charging_efficiency
                precharge_possible = int(math.floor(energy_can_charge / container_kwh))

            # Available spare containers that are not charged
            spares = None
            if total_before is not None and charged_before is not None:
                spares = max(0, total_before - charged_before)
            elif total_before is not None and charged_before is None:
                # charged unlimited, though total is finite - treat spares as total
                spares = total_before

            # If precharge possible, actual precharge is bounded by both spares and precharge_possible
            if precharge_possible > 0 or background_precharge > 0 or candidate_precharge_added > 0:
                precharge_from_infrastructure = precharge_possible + background_precharge
                # Limit infra precharge by available spares (excluding candidate additions)
                if spares is None:
                    infra_precharge_applied = precharge_from_infrastructure
                else:
                    infra_precharge_applied = min(precharge_from_infrastructure, max(0, spares - candidate_precharge_added))
                # Total actual precharge counts include candidate additions plus infra additions
                actual_precharge = candidate_precharge_added + infra_precharge_applied
                # Increase charged_before by only the infra_precharge_applied (converted to energy per container)
                if battery_states_map.get(s_name) is not None and infra_precharge_applied > 0:
                    battery_states_map[s_name].add_energy(infra_precharge_applied * container_kwh, charging_efficiency=station_charging_efficiency,
                                                         min_swap_soc=min_swap)
                    # Recompute charged_before using min_swap threshold
                    charged_before = battery_states_map[s_name].get_available_for_swap(min_soc=min_swap)
                containers_precharged = actual_precharge
                if actual_precharge > 0:
                    events_for_step.append({
                        "time_hr": st.arrival_time_hr + 0.0001,
                        "event": "precharge_during_stop",
                        "added": actual_precharge,
                    })

            # Determine post-stop inventory snapshot for reporting
            charged_after = charged_before
            total_after = total_before
            if battery_states_map.get(s_name) is not None:
                charged_after = battery_states_map[s_name].get_available_for_swap(min_soc=min_swap)
                total_after = battery_states_map[s_name].get_total_batteries()

            # Create a new StepResult populated with inventory stats
            new_step = StepResult(
                station_name=st.station_name,
                swap_taken=st.swap_taken,
                num_containers_swapped=st.num_containers_swapped,
                charging_taken=st.charging_taken,
                energy_charged_kwh=st.energy_charged_kwh,
                operation_type=st.operation_type,
                arrival_time_hr=st.arrival_time_hr,
                departure_time_hr=st.departure_time_hr,
                station_docking_time_hr=st.station_docking_time_hr,
                soc_before_kwh=st.soc_before_kwh,
                soc_after_operation_kwh=st.soc_after_operation_kwh,
                segment_label=st.segment_label,
                energy_used_kwh=st.energy_used_kwh,
                travel_time_hr=st.travel_time_hr,
                soc_after_segment_kwh=st.soc_after_segment_kwh,
                incremental_cost=st.incremental_cost,
                cumulative_cost=st.cumulative_cost,
                incremental_time_hr=st.incremental_time_hr,
                cumulative_time_hr=st.cumulative_time_hr,
                hotelling_energy_kwh=st.hotelling_energy_kwh,
                hotelling_power_kw=st.hotelling_power_kw,
                station_charged_before=charged_before if charged_before is None else int(charged_before),
                station_charged_after=charged_after if charged_after is None else int(charged_after),
                station_total_before=total_before if total_before is None else int(total_before),
                station_total_after=total_after if total_after is None else int(total_after),
                containers_precharged=containers_precharged,
                containers_charged_during_stop=containers_charged_during_stop,
                precharge_energy_kwh=getattr(st, 'precharge_energy_kwh', 0.0),
                station_events=events_for_step,
            )
            enriched_steps.append(new_step)
            # Append this step's station events to station timeline
            station_timelines[s_name].extend(events_for_step)

        # Update last departure map for this station
        last_departure_map[s_name] = st.departure_time_hr

        # After processing all steps, append final arrival event for the destination station
        final_station = self.inputs.stations[-1]
        if final_station.name in station_timelines and battery_states_map.get(final_station.name) is not None:
            charged_before_final = battery_states_map[final_station.name].get_available_for_swap(min_soc=final_station.min_swap_soc)
            arrival_time_final = self.inputs.start_time_hr + best_time
            station_timelines[final_station.name].append({
                "time_hr": arrival_time_final,
                "event": "arrival",
                "charged_before": charged_before_final,
                "total_before": battery_states_map[final_station.name].get_total_batteries(),
            })

        return enriched_steps, station_timelines

    def _to_step(self, soc_kwh: float) -> int:
        step = self.inputs.soc_step_kwh
        return int(round(soc_kwh / step))

    def _from_step(self, level: int) -> float:
        return level * self.inputs.soc_step_kwh

    def _energy_to_steps(self, energy_kwh: float) -> int:
        step = self.inputs.soc_step_kwh
        return int(math.ceil(energy_kwh / step))

    @staticmethod
    def _improves(new_cost: float, new_time: float, old_cost: float, old_time: float) -> bool:
        if not math.isfinite(old_cost):
            return True
        if new_cost < old_cost - 1e-9:
            return True
        if abs(new_cost - old_cost) <= 1e-9 and new_time < old_time - 1e-9:
            return True
        return False

    def _diagnose_infeasibility(
        self,
        dp: List[Dict[Tuple[int, Tuple[int, ...]], Tuple[float, float, int]]],
    ) -> str:
        """
        Diagnose why the optimization failed to find a feasible solution.
        Returns a detailed diagnostic report.
        """
        inputs = self.inputs
        diagnostics = []
        
        # 1. Check if we can reach ANY state at the final station
        final_idx = len(inputs.stations) - 1
        # dp[final_idx] maps (level, inv) -> (cost, time, battery_source)
        reachable_final_states = sum(1 for (level, inv), (cost, time, _) in dp[final_idx].items() if math.isfinite(cost))
        
        if reachable_final_states == 0:
            diagnostics.append("❌ CRITICAL: Cannot reach destination at all!")
            diagnostics.append("   → The route is completely infeasible with current constraints.\n")
        else:
            diagnostics.append(f"✓ Can reach destination ({reachable_final_states} possible states)")
            
            # Find the best SoC we can achieve at destination
            best_soc = 0.0
            for (level, inv), (cost, time, _) in dp[final_idx].items():
                if math.isfinite(cost):
                    soc = self._from_step(level)
                    if soc > best_soc:
                        best_soc = soc
            
            required_soc = inputs.final_soc_min_kwh
            diagnostics.append(f"   → Best achievable final SoC: {best_soc:.1f} kWh")
            diagnostics.append(f"   → Required final SoC: {required_soc:.1f} kWh")
            diagnostics.append(f"   → Shortfall: {required_soc - best_soc:.1f} kWh\n")
        
        # 2. Analyze each segment for bottlenecks
        diagnostics.append("SEGMENT ANALYSIS:")
        for idx, segment in enumerate(inputs.segments):
            station = inputs.stations[idx]
            next_station = inputs.stations[idx + 1]
            
            # Count reachable states before and after this segment
            reachable_before = sum(1 for (level, inv), (cost, time, _) in dp[idx].items() if math.isfinite(cost))
            reachable_after = sum(1 for (level, inv), (cost, time, _) in dp[idx + 1].items() if math.isfinite(cost))
            
            diagnostics.append(f"\n  Segment {idx + 1}: {station.name} → {next_station.name}")
            diagnostics.append(f"    States before: {reachable_before}, States after: {reachable_after}")
            
            if reachable_after == 0 and reachable_before > 0:
                diagnostics.append(f"    ❌ BOTTLENECK: Cannot traverse this segment!")
                
                # Analyze why
                option = segment.options[0]  # Assume single option
                energy_needed = option.energy_kwh
                
                diagnostics.append(f"       • Energy required: {energy_needed:.1f} kWh")
                diagnostics.append(f"       • Battery capacity: {inputs.battery_capacity_kwh:.1f} kWh")
                
                if energy_needed > inputs.battery_capacity_kwh:
                    diagnostics.append(f"       ❌ Segment requires MORE energy than battery capacity!")
                    diagnostics.append(f"          SOLUTION: Reduce segment distance or increase battery capacity")
                
                # Check if charging/swapping available at current station
                if not station.allow_swap and not station.charging_allowed:
                    diagnostics.append(f"       ❌ No charging or swapping at {station.name}")
                    diagnostics.append(f"          SOLUTION: Enable swap or charging at this station")
                elif station.allow_swap and station.available_batteries is not None:
                    # Calculate how many containers might be needed
                    total_containers = int(inputs.battery_capacity_kwh / inputs.battery_container_capacity_kwh)
                    # compute effective availability considering charging
                    initial_charged = station.available_batteries if station.available_batteries is not None else None
                    total_stock = station.total_batteries if station.total_batteries is not None else initial_charged
                    if initial_charged is None:
                        effective = None
                    else:
                        precharge = 0
                        if station.charging_allowed and station.charging_power_kw > 0 and station.docking_time_hr > 0:
                            energy_can_charge = station.docking_time_hr * station.charging_power_kw * station.charging_efficiency
                            precharge = int(math.floor(energy_can_charge / self.inputs.battery_container_capacity_kwh))
                        effective = min(int(total_stock) if total_stock is not None else int(initial_charged), int(initial_charged) + precharge)
                    if effective is not None and effective < total_containers:
                        diagnostics.append(f"       ⚠️  Swap allowed but only {effective} batteries effectively available at {station.name}")
                        diagnostics.append(f"          May need up to {total_containers} containers for full swap")
                        diagnostics.append(f"          SOLUTION: Increase total_batteries/charged batteries to {total_containers} or enable partial_swap_allowed")
                elif station.charging_allowed and station.charging_power_kw <= 0:
                    diagnostics.append(f"       ⚠️  Charging enabled but no charging power at {station.name}")
                    diagnostics.append(f"          SOLUTION: Set charging_power_kw > 0")
                
                # Check operating hours
                if station.operating_hours is not None:
                    diagnostics.append(f"       • Operating hours: {station.operating_hours}")
                    diagnostics.append(f"          May be too restrictive for required operations")
            
            elif reachable_after < reachable_before * 0.5:
                diagnostics.append(f"    ⚠️  WARNING: Significant state reduction (bottleneck forming)")
        
        # 3. Check energy requirements vs capacity
        diagnostics.append("\n\nENERGY FEASIBILITY:")
        total_energy_needed = sum(opt.energy_kwh for seg in inputs.segments for opt in seg.options)
        diagnostics.append(f"  Total energy for journey: {total_energy_needed:.1f} kWh")
        diagnostics.append(f"  Battery capacity: {inputs.battery_capacity_kwh:.1f} kWh")
        diagnostics.append(f"  Initial SoC: {inputs.initial_soc_kwh:.1f} kWh")
        diagnostics.append(f"  Final SoC required: {inputs.final_soc_min_kwh:.1f} kWh")
        
        energy_available = inputs.initial_soc_kwh - inputs.final_soc_min_kwh
        if total_energy_needed > energy_available:
            diagnostics.append(f"  ❌ Journey requires {total_energy_needed:.1f} kWh but only {energy_available:.1f} kWh available")
            diagnostics.append(f"     → Must swap or charge at least once")
            
            # Check if any stations support energy replenishment
            swap_stations = []
            for s in inputs.stations:
                if not s.allow_swap:
                    continue
                # compute effective availability
                initial_charged = s.available_batteries if s.available_batteries is not None else None
                total_stock = s.total_batteries if s.total_batteries is not None else initial_charged
                if initial_charged is None:
                    effective = None
                else:
                    precharge = 0
                    if s.charging_allowed and s.charging_power_kw > 0 and s.docking_time_hr > 0:
                        energy_can_charge = s.docking_time_hr * s.charging_power_kw * s.charging_efficiency
                        precharge = int(math.floor(energy_can_charge / self.inputs.battery_container_capacity_kwh))
                    effective = min(int(total_stock) if total_stock is not None else int(initial_charged), int(initial_charged) + precharge)
                if effective is None or effective > 0:
                    swap_stations.append(s.name)
            charge_stations = [s.name for s in inputs.stations if s.charging_allowed and s.charging_power_kw > 0]
            
            if not swap_stations and not charge_stations:
                diagnostics.append(f"     ❌ NO STATIONS with swap or charging capability!")
                diagnostics.append(f"        SOLUTION: Enable swap/charging at intermediate stations")

        # 4. Station container & precharge availability summary
        diagnostics.append("\n\nSTATION CONTAINER AVAILABILITY SUMMARY:")
        total_container_energy_available = 0.0
        overall_unlimited = False
        for s in inputs.stations:
            containers_available = s.available_batteries if s.available_batteries is not None else None
            containers_total = s.total_batteries if s.total_batteries is not None else None
            precharge_possible = 0
            # Precharge possible during docking (charging of vessels/spares while the vessel is present)
            precharge_possible = 0
            if s.charging_allowed and s.charging_power_kw > 0 and s.docking_time_hr > 0:
                energy_can_charge = s.charging_power_kw * s.docking_time_hr * s.charging_efficiency
                precharge_possible = int(math.floor(energy_can_charge / inputs.battery_container_capacity_kwh))
            # Background charging potential (per hour) - helpful diagnostic, not included in precharge_possible
            bg_power = 0
            if s.background_charging_allowed and s.background_charging_power_kw and s.background_charging_power_kw > 0:
                bg_power = s.background_charging_power_kw
            elif s.background_charging_allowed and s.total_grid_power_kw and s.total_grid_power_kw > 0:
                bg_power = s.total_grid_power_kw
            if containers_available is None:
                diagnostics.append(f"  • {s.name}: unlimited charged containers (cannot pre-check)")
                overall_unlimited = True
            else:
                eff_containers = containers_available + precharge_possible
                if containers_total is not None:
                    eff_containers = min(eff_containers, containers_total)
                diagnostics.append(f"  • {s.name}: charged={containers_available}, precharge_possible_dock={precharge_possible}, background_power_kw={bg_power}, total={containers_total}, effective={eff_containers}")
                total_container_energy_available += eff_containers * inputs.battery_container_capacity_kwh
        if not overall_unlimited:
            total_energy_avail = inputs.initial_soc_kwh + total_container_energy_available
            diagnostics.append(f"  → Total additional container energy available: {total_container_energy_available:.1f} kWh")
            diagnostics.append(f"  → Combined energy availability (incl initial SoC): {total_energy_avail:.1f} kWh")
            # Also list swap/charge stations
            swap_stations = [s.name for s in inputs.stations if s.allow_swap and (s.available_batteries is None or s.available_batteries > 0)]
            charge_stations = [s.name for s in inputs.stations if s.charging_allowed and s.charging_power_kw > 0]
            if swap_stations:
                diagnostics.append(f"     ✓ Swap available at: {', '.join(swap_stations)}")
            if charge_stations:
                diagnostics.append(f"     ✓ Charging available at: {', '.join(charge_stations)}")
        
        # 4. Check for impossible constraints combinations
        diagnostics.append("\n\nCONSTRAINT COMPATIBILITY:")
        
        # Check minimum operating SoC vs requirements
        if inputs.min_soc_kwh > inputs.initial_soc_kwh:
            diagnostics.append(f"  ❌ Minimum operating SoC ({inputs.min_soc_kwh:.1f} kWh) > Initial SoC ({inputs.initial_soc_kwh:.1f} kWh)")
            diagnostics.append(f"     SOLUTION: Reduce min_soc_kwh or increase initial_soc_kwh")
        
        if inputs.final_soc_min_kwh > inputs.battery_capacity_kwh:
            diagnostics.append(f"  ❌ Final SoC requirement ({inputs.final_soc_min_kwh:.1f} kWh) > Battery capacity ({inputs.battery_capacity_kwh:.1f} kWh)")
            diagnostics.append(f"     SOLUTION: Reduce final_soc_min_kwh or increase battery_capacity_kwh")
        
        # 5. Suggested actions
        diagnostics.append("\n\nSUGGESTED ACTIONS:")
        diagnostics.append("  1. Enable swap/charging at more intermediate stations")
        diagnostics.append("  2. Increase battery capacity or reduce segment energy requirements")
        diagnostics.append("  3. Relax final SoC requirement (reduce final_soc_min_kwh)")
        diagnostics.append("  4. Check operating hours aren't too restrictive")
        diagnostics.append("  5. Ensure sufficient batteries available at swap stations")
        diagnostics.append("  6. Increase charging power (charging_power_kw) at charging stations")
        diagnostics.append("  7. Adjust docking_time_hr to allow for proper operations")
        
        # Final diagnostics string - sanitize to ASCII-only for console/streamlit safe output
        diag_str = "\n".join(diagnostics)
        # Replace common emojis with ASCII text equivalents
        replacements = {
            "\u274c": "[FAIL]",
            "\u26a0\ufe0f": "[WARNING]",
            "\u2713": "[OK]",
            "\u2192": "->",
            "\u274e": "[*]",
        }
        for k, v in replacements.items():
            diag_str = diag_str.replace(k, v)
        return diag_str


if __name__ == "__main__":
    def calculate_energy_consumption(
        distance_km: float,
        current_kmh: float,
        vessel_speed_kmh: float = 18.0,
        base_consumption_per_km: float = 3.0,
    ) -> float:
        base_energy = distance_km * base_consumption_per_km
        multiplier = 1.25 if current_kmh < 0 else 0.75
        return base_energy * multiplier


# Temporary: BatteryAggregateState will be added below (outside the __main__ block)

    def build_segment_option(
        segment_name: str,
        distance_km: float,
        current_kmh: float,
        vessel_speed_kmh: float = 18.0,
    ) -> SegmentOption:
        ground_speed = vessel_speed_kmh + current_kmh
        if ground_speed <= 0:
            raise ValueError(
                f"Ground speed becomes non-positive for segment {segment_name}."
            )
        travel_time_hr = distance_km / ground_speed
        energy_kwh = calculate_energy_consumption(distance_km, current_kmh, vessel_speed_kmh)
        return SegmentOption(
            label=segment_name,
            travel_time_hr=travel_time_hr,
            energy_kwh=energy_kwh,
        )

    def clock_string(hours: float) -> str:
        total_minutes = int(round(hours * 60))
        day = total_minutes // (24 * 60)
        minutes_into_day = total_minutes - day * 24 * 60
        hour = minutes_into_day // 60
        minute = minutes_into_day % 60
        prefix = f"Day {day} " if day else ""
        return f"{prefix}{hour:02d}:{minute:02d}"

    distances_km = {
        "A-B": 40.0,
        "B-C": 35.0,
        "C-D": 45.0,
        "D-E": 30.0,
    }
    currents_kmh = {
        "A-B": -2.5,
        "B-C": -1.8,
        "C-D": 3.2,
        "D-E": 2.0,
    }

    route = ["A", "B", "C", "D", "E"]
    vessel_speed = 18.0
    segments: List[Segment] = []
    for start, end in zip(route[:-1], route[1:]):
        key = f"{start}-{end}"
        option = build_segment_option(
            segment_name=f"{start}->{end}",
            distance_km=distances_km[key],
            current_kmh=currents_kmh[key],
            vessel_speed_kmh=vessel_speed,
        )
        segments.append(
            Segment(start=start, end=end, options=[option])
        )

    stations = [
        Station(
            name="A", 
            docking_time_hr=0.0,
            allow_swap=False, 
            charging_allowed=False,
            energy_cost_per_kwh=0.09
        ),
        Station(
            name="B",
            docking_time_hr=2.0,
            operating_hours=(6.0, 22.0),
            available_batteries=3,
            total_batteries=3,
            allow_swap=True,
            partial_swap_allowed=True,
            charging_allowed=True,
            charging_power_kw=250.0,
            charging_efficiency=0.95,
            energy_cost_per_kwh=0.09,  # Guangzhou: 0.64 RMB (~$0.09/kWh)
            base_service_fee=25.0,
            base_charging_fee=10.0,
            # Enable background charging: allows station to recharge spare containers while vessel is away
            background_charging_allowed=True,
            background_charging_power_kw=250.0,
            total_grid_power_kw=500.0,
        ),
        Station(
            name="C",
            docking_time_hr=2.5,
            operating_hours=(0.0, 24.0),
            available_batteries=2,
            total_batteries=2,
            allow_swap=True,
            partial_swap_allowed=False,
            charging_allowed=True,
            charging_power_kw=500.0,
            charging_efficiency=0.95,
            energy_cost_per_kwh=0.18,  # Hong Kong: 1.443 HKD (~$0.18/kWh)
            base_service_fee=40.0,
            base_charging_fee=20.0,
            # Enable background charging to support spare container recharges between visits
            background_charging_allowed=True,
            background_charging_power_kw=400.0,
            total_grid_power_kw=700.0,
        ),
        Station(
            name="D",
            docking_time_hr=1.5,
            operating_hours=(8.0, 20.0),
            available_batteries=4,
            total_batteries=4,
            allow_swap=True,
            partial_swap_allowed=True,
            charging_allowed=True,
            charging_power_kw=300.0,
            charging_efficiency=0.95,
            energy_cost_per_kwh=0.09,  # Zhao Qing: 0.62-0.65 RMB (~$0.09/kWh)
            base_service_fee=20.0,
            base_charging_fee=8.0,
            # Enable background charging: Zhao Qing background grid used to recharge spares during long gaps
            background_charging_allowed=True,
            background_charging_power_kw=2000.0,
            total_grid_power_kw=2000.0,
        ),
        Station(
            name="E", 
            docking_time_hr=0.0,
            allow_swap=False, 
            charging_allowed=False,
            energy_cost_per_kwh=0.09
        ),
    ]

    battery_capacity = 300.0
    minimum_fraction = 0.20
    minimum_soc = battery_capacity * minimum_fraction

    inputs = FixedPathInputs(
        stations=stations,
        segments=segments,
        battery_capacity_kwh=battery_capacity,
        battery_container_capacity_kwh=75.0,  # Each container = 75 kWh (4 containers total)
        initial_soc_kwh=battery_capacity,
        final_soc_min_kwh=minimum_soc,
        min_soc_kwh=minimum_soc,
        energy_cost_per_kwh=0.12,
        soc_step_kwh=5.0,
        start_time_hr=6.0,
    )

    optimizer = FixedPathOptimizer(inputs)
    optimisation_result = optimizer.solve()

    print("Optimised Schedule (with Flexible Charging & Hybrid Options)")
    print("=" * 80)
    for step in optimisation_result.steps:
        arrival_clock = clock_string(step.arrival_time_hr)
        departure_clock = clock_string(step.departure_time_hr)
        
        # Build operation description
        if step.operation_type == "none":
            op_desc = "No operation"
        elif step.operation_type == "swap":
            op_desc = f"Swap {step.num_containers_swapped} container(s)"
        elif step.operation_type == "charge":
            op_desc = f"Charge {step.energy_charged_kwh:.1f} kWh"
        elif step.operation_type == "hybrid":
            op_desc = f"Hybrid: Swap {step.num_containers_swapped} + Charge {step.energy_charged_kwh:.1f} kWh"
        else:
            op_desc = "Unknown"
        
        print(
            f"{step.station_name} @ {arrival_clock} → {step.segment_label}\n"
            f"  Operation: {op_desc}\n"
            f"  Docking: {step.station_docking_time_hr:.2f}h | Travel: {step.travel_time_hr:.2f}h\n"
            f"  SoC: {step.soc_before_kwh:.1f} → {step.soc_after_operation_kwh:.1f} → {step.soc_after_segment_kwh:.1f} kWh\n"
            f"  Cost: ${step.incremental_cost:.2f} (cumulative: ${step.cumulative_cost:.2f})\n"
        )

    print("\nTotals")
    print(f"  Total cost: ${optimisation_result.total_cost:.2f}")
    print(f"  Total travel time: {optimisation_result.total_time_hr:.2f} h")
    print(f"  Finish clock time: {clock_string(optimisation_result.finish_time_hr)}")

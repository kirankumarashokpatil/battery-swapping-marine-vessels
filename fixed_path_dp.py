from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

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
                    self.gross_tonnage
                )
                # Reference data returns 0 for some small vessels or unsupported ranges
                # Use fallback formula if we get 0
                if power > 0:
                    return power
            except Exception:
                pass  # Fall through to backup calculation
        
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
    min_docking_time_hr: float = 0.5  # Minimum docking time for port operations (business-driven)
    max_docking_time_hr: Optional[float] = None  # Maximum allowed docking time (port constraints)
    allow_swap: bool = True
    force_swap: bool = False
    partial_swap_allowed: bool = False  # If True, can swap only depleted containers; if False, must swap all
    operating_hours: Optional[Tuple[float, float]] = None
    available_batteries: Optional[int] = None
    energy_cost_per_kwh: float = 0.09  # Station-specific energy pricing (default: Guangzhou/Zhao Qing rate)
    
    # Charging Infrastructure
    charging_power_kw: float = 0.0  # Available shore power charging capacity (kW)
    charging_efficiency: float = 0.95  # Charging efficiency (AC/DC conversion losses)
    charging_allowed: bool = False  # Whether charging infrastructure is available
    
    # Hybrid/Custom Pricing Components (Current Direct-style model)
    base_service_fee: float = 0.0  # Fixed base fee per swap transaction (independent of container count)
    location_premium: float = 0.0  # Location-based markup ($ or % of base cost) for high-demand/strategic ports
    degradation_fee_per_kwh: float = 0.0  # Charge based on battery wear/degradation
    subscription_discount: float = 0.0  # Percentage discount for subscription customers (0.0-1.0)
    base_charging_fee: float = 0.0  # Fixed fee for using charging infrastructure


@dataclass(frozen=True)
class FixedPathInputs:
    stations: List[Station]
    segments: List[Segment]
    battery_capacity_kwh: float  # Total battery system capacity
    battery_container_capacity_kwh: float  # Capacity per individual container (default: 1960 kWh)
    initial_soc_kwh: float
    final_soc_min_kwh: float
    energy_cost_per_kwh: float
    min_soc_kwh: float = 0.0
    soc_step_kwh: float = 1.0
    start_time_hr: float = 0.0
    vessel_specs: Optional[VesselSpecs] = None  # Vessel type and GT for hotelling calculations

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
            if station.min_docking_time_hr < 0:
                raise ValueError(f"Station {station.name} minimum docking time must be non-negative")
            if station.max_docking_time_hr is not None and station.max_docking_time_hr < station.min_docking_time_hr:
                raise ValueError(f"Station {station.name} maximum docking time must be >= minimum")
            if station.available_batteries is not None and station.available_batteries < 0:
                raise ValueError(f"Station {station.name} available batteries cannot be negative")
            if station.charging_power_kw < 0:
                raise ValueError(f"Station {station.name} charging power cannot be negative")
            if not (0.0 <= station.charging_efficiency <= 1.0):
                raise ValueError(f"Station {station.name} charging efficiency must be between 0 and 1")


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


@dataclass(frozen=True)
class OptimisationResult:
    total_cost: float
    total_time_hr: float
    finish_time_hr: float
    steps: List[StepResult]


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

    def solve(self) -> OptimisationResult:
        inputs = self.inputs
        # Track the station index where the current battery was charged for each state
        # dp_battery_source[station][soc_level] = station index where battery was obtained
        dp_cost = [[math.inf] * self._soc_levels for _ in inputs.stations]
        dp_time = [[math.inf] * self._soc_levels for _ in inputs.stations]
        dp_battery_source = [[-1] * self._soc_levels for _ in inputs.stations]
        prev: List[List[Optional[_Transition]]] = [
            [None] * self._soc_levels for _ in inputs.stations
        ]

        start_level = self._to_step(inputs.initial_soc_kwh)
        dp_cost[0][start_level] = 0.0
        dp_time[0][start_level] = 0.0
        dp_battery_source[0][start_level] = 0  # Initial battery from station 0

        for idx, segment in enumerate(inputs.segments):
            station = inputs.stations[idx]
            next_station = inputs.stations[idx + 1]
            for level in range(self._soc_levels):
                base_cost = dp_cost[idx][level]
                if not math.isfinite(base_cost):
                    continue
                base_time = dp_time[idx][level]
                battery_source_idx = dp_battery_source[idx][level]
                soc_before = self._from_step(level)
                arrival_time_hr = self.inputs.start_time_hr + base_time
                candidate_levels = self._candidate_levels(
                    station, level, arrival_time_hr
                )
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
                ) in candidate_levels:
                    # If swapped, battery comes from current station; else keep source
                    new_battery_source_idx = idx if swapped else battery_source_idx
                    battery_source_station = inputs.stations[new_battery_source_idx]
                    
                    soc_post_operation = self._from_step(level_after_operation)
                    for option_idx, option in enumerate(segment.options):
                        energy_steps = self._energy_to_steps(option.energy_kwh)
                        if level_after_operation < energy_steps:
                            continue
                        new_level = level_after_operation - energy_steps
                        if new_level < self._min_operating_level:
                            continue
                        travel_time = option.travel_time_hr
                        # Energy cost is already included in operation_cost at charging station
                        # No additional cost for consuming energy during travel
                        energy_cost = 0.0
                        new_cost = (
                            base_cost
                            + operation_cost
                            + option.extra_cost
                            + energy_cost
                        )
                        new_time = base_time + docking_time + travel_time
                        if self._improves(new_cost, new_time, dp_cost[idx + 1][new_level], dp_time[idx + 1][new_level]):
                            dp_cost[idx + 1][new_level] = new_cost
                            dp_time[idx + 1][new_level] = new_time
                            dp_battery_source[idx + 1][new_level] = new_battery_source_idx
                            prev[idx + 1][new_level] = _Transition(
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
                            )

        best_level, best_cost, best_time = self._select_terminal_state(dp_cost, dp_time)
        steps = self._reconstruct(prev, best_level, best_cost, best_time, dp_cost, dp_time)
        finish_time_hr = self.inputs.start_time_hr + best_time
        return OptimisationResult(
            total_cost=best_cost,
            total_time_hr=best_time,
            finish_time_hr=finish_time_hr,
            steps=steps,
        )

    def _candidate_levels(
        self, station: Station, level: int, arrival_time_hr: float
    ) -> List[Tuple[int, float, float, bool, bool, str, int, float, float]]:
        """
        Generate all feasible energy operation options at a station.
        
        Returns list of tuples: (level_after_operation, operation_cost, docking_time, 
                                  swapped, charged, operation_type, num_containers_swapped,
                                  energy_charged_kwh, hotelling_energy_kwh)
        """
        options: List[Tuple[int, float, float, bool, bool, str, int, float, float]] = []

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

        # OPTION 1: No operation - just minimum docking time for port operations
        if not station.force_swap:
            min_dwell = station.min_docking_time_hr
            hotelling_energy_no_op = hotelling_power_kw * min_dwell
            options.append((level, 0.0, min_dwell, False, False, "none", 0, 0.0, hotelling_energy_no_op))

        # OPTION 2: Full/Partial Swap Only
        if station.allow_swap:
            if station.available_batteries is not None and station.available_batteries < 1:
                if station.force_swap:
                    raise ValueError(
                        f"Station {station.name} requires swap but no batteries available"
                    )
            else:
                capacity_level = self._capacity_steps
                swap_time = station.min_docking_time_hr  # Use minimum docking time for swap
                
                # Calculate swap cost based on full vs partial swap mode
                total_num_containers = int(capacity_kwh / self.inputs.battery_container_capacity_kwh)
                if total_num_containers < 1:
                    total_num_containers = 1
                
                # Determine how many containers need swapping
                if station.partial_swap_allowed:
                    # PARTIAL SWAP: Only swap depleted containers
                    containers_to_swap = total_num_containers - int(current_soc_kwh / self.inputs.battery_container_capacity_kwh)
                    if containers_to_swap < 0:
                        containers_to_swap = 0
                    if current_soc_kwh < capacity_kwh and containers_to_swap == 0:
                        containers_to_swap = 1
                else:
                    # FULL SWAP: Always swap entire battery set
                    containers_to_swap = total_num_containers
                
                # Calculate swap cost
                base_fee = station.base_service_fee
                location_cost = station.location_premium * containers_to_swap
                energy_kwh_needed = capacity_kwh - current_soc_kwh
                energy_cost = energy_kwh_needed * station.energy_cost_per_kwh
                degradation_cost = energy_kwh_needed * station.degradation_fee_per_kwh
                
                subtotal = base_fee + location_cost + energy_cost + degradation_cost
                total_swap_cost = subtotal * (1.0 - station.subscription_discount)
                
                # Add hotelling cost
                hotelling_energy_swap = hotelling_power_kw * swap_time
                hotelling_cost = hotelling_energy_swap * station.energy_cost_per_kwh
                total_swap_cost += hotelling_cost
                
                options.append((
                    capacity_level,
                    total_swap_cost,
                    swap_time,
                    True,  # swapped
                    False,  # charged
                    "swap",
                    containers_to_swap,
                    0.0,  # energy_charged_kwh
                    hotelling_energy_swap
                ))

        # OPTION 3: Charging Only (variable duration)
        if station.charging_allowed and station.charging_power_kw > 0 and not station.force_swap:
            max_dwell = station.max_docking_time_hr if station.max_docking_time_hr is not None else 24.0
            
            # Discrete charging time options (in hours)
            charge_time_options = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0]
            
            for charge_time in charge_time_options:
                if charge_time < station.min_docking_time_hr:
                    continue  # Must meet minimum docking time
                if charge_time > max_dwell:
                    continue  # Cannot exceed maximum docking time
                
                # Calculate energy charged
                energy_charged_kwh = min(
                    charge_time * station.charging_power_kw * station.charging_efficiency,
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
                
                options.append((
                    new_level,
                    total_charging_cost,
                    charge_time,
                    False,  # swapped
                    True,  # charged
                    "charge",
                    0,  # num_containers_swapped
                    energy_charged_kwh,
                    hotelling_energy_charge
                ))

        # OPTION 4: Hybrid (Swap + Charge)
        if station.allow_swap and station.charging_allowed and station.charging_power_kw > 0:
            if station.available_batteries is not None and station.available_batteries < 1:
                pass  # Skip hybrid if no batteries available
            else:
                max_dwell = station.max_docking_time_hr if station.max_docking_time_hr is not None else 24.0
                
                # Hybrid time options: short charge after swap
                hybrid_charge_times = [0.5, 1.0, 2.0, 3.0, 4.0]
                
                for charge_time in hybrid_charge_times:
                    total_time = station.min_docking_time_hr + charge_time
                    if total_time > max_dwell:
                        continue
                    
                    # Calculate swap portion (same as full swap)
                    total_num_containers = int(capacity_kwh / self.inputs.battery_container_capacity_kwh)
                    if total_num_containers < 1:
                        total_num_containers = 1
                    
                    if station.partial_swap_allowed:
                        containers_to_swap = total_num_containers - int(current_soc_kwh / self.inputs.battery_container_capacity_kwh)
                        if containers_to_swap < 0:
                            containers_to_swap = 0
                        if current_soc_kwh < capacity_kwh and containers_to_swap == 0:
                            containers_to_swap = 1
                    else:
                        containers_to_swap = total_num_containers
                    
                    # After swap, SoC is at capacity
                    soc_after_swap = capacity_kwh
                    
                    # Then charge (which doesn't add much since already at capacity)
                    # But in partial swap case, there may be room for charging
                    energy_charged_kwh = min(
                        charge_time * station.charging_power_kw * station.charging_efficiency,
                        capacity_kwh - soc_after_swap
                    )
                    
                    # Skip if no meaningful charging happens
                    if energy_charged_kwh < 0.1 and containers_to_swap == 0:
                        continue
                    
                    final_soc_kwh = soc_after_swap + energy_charged_kwh
                    final_level = self._to_step(final_soc_kwh)
                    
                    # Calculate hybrid cost (swap + charge)
                    base_fee = station.base_service_fee
                    location_cost = station.location_premium * containers_to_swap
                    swap_energy_kwh = capacity_kwh - current_soc_kwh
                    swap_energy_cost = swap_energy_kwh * station.energy_cost_per_kwh
                    degradation_cost = swap_energy_kwh * station.degradation_fee_per_kwh
                    
                    swap_subtotal = base_fee + location_cost + swap_energy_cost + degradation_cost
                    swap_cost = swap_subtotal * (1.0 - station.subscription_discount)
                    
                    charge_cost = energy_charged_kwh * station.energy_cost_per_kwh + station.base_charging_fee
                    
                    # Hotelling for total hybrid time
                    hotelling_energy_hybrid = hotelling_power_kw * total_time
                    hotelling_cost = hotelling_energy_hybrid * station.energy_cost_per_kwh
                    
                    total_hybrid_cost = swap_cost + charge_cost + hotelling_cost
                    
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
                    ))

        return options



    def _select_terminal_state(
        self,
        dp_cost: List[List[float]],
        dp_time: List[List[float]],
    ) -> Tuple[int, float, float]:
        inputs = self.inputs
        final_idx = len(inputs.stations) - 1
        min_level = self._to_step(inputs.final_soc_min_kwh)
        best_level = -1
        best_cost = math.inf
        best_time = math.inf
        for level in range(min_level, self._soc_levels):
            cost = dp_cost[final_idx][level]
            if not math.isfinite(cost):
                continue
            time = dp_time[final_idx][level]
            if self._improves(cost, time, best_cost, best_time):
                best_cost = cost
                best_time = time
                best_level = level
        if best_level < 0:
            # Provide detailed diagnostics about why no solution was found
            diagnostics = self._diagnose_infeasibility(dp_cost, dp_time)
            raise ValueError(
                f"No feasible solution found for final SoC requirement.\n\n"
                f"CONSTRAINT VIOLATION DIAGNOSTICS:\n"
                f"{diagnostics}"
            )
        return best_level, best_cost, best_time

    def _reconstruct(
        self,
        prev: List[List[Optional[_Transition]]],
        level: int,
        best_cost: float,
        best_time: float,
        dp_cost: List[List[float]],
        dp_time: List[List[float]],
    ) -> List[StepResult]:
        steps: List[StepResult] = []
        idx = len(self.inputs.stations) - 1
        current_level = level
        cumulative_cost = best_cost
        cumulative_time = best_time
        while idx > 0:
            transition = prev[idx][current_level]
            if transition is None:
                raise RuntimeError("Missing transition during reconstruction")
            prev_level = transition.prev_level
            station = self.inputs.stations[idx - 1]
            segment = self.inputs.segments[idx - 1]
            option = segment.options[transition.option_index]
            soc_before = self._from_step(prev_level)
            soc_after_segment = self._from_step(current_level)
            step_cost = transition.incremental_cost
            step_time = transition.incremental_time
            arrival_elapsed = dp_time[idx - 1][prev_level]
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
                )
            )
            cumulative_cost -= step_cost
            cumulative_time -= step_time
            current_level = prev_level
            idx -= 1
        steps.reverse()
        return steps

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
        dp_cost: List[List[float]],
        dp_time: List[List[float]],
    ) -> str:
        """
        Diagnose why the optimization failed to find a feasible solution.
        Returns a detailed diagnostic report.
        """
        inputs = self.inputs
        diagnostics = []
        
        # 1. Check if we can reach ANY state at the final station
        final_idx = len(inputs.stations) - 1
        reachable_final_states = sum(1 for cost in dp_cost[final_idx] if math.isfinite(cost))
        
        if reachable_final_states == 0:
            diagnostics.append("❌ CRITICAL: Cannot reach destination at all!")
            diagnostics.append("   → The route is completely infeasible with current constraints.\n")
        else:
            diagnostics.append(f"✓ Can reach destination ({reachable_final_states} possible states)")
            
            # Find the best SoC we can achieve at destination
            best_soc = 0.0
            for level in range(self._soc_levels):
                if math.isfinite(dp_cost[final_idx][level]):
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
            reachable_before = sum(1 for cost in dp_cost[idx] if math.isfinite(cost))
            reachable_after = sum(1 for cost in dp_cost[idx + 1] if math.isfinite(cost))
            
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
                elif station.allow_swap and station.available_batteries is not None and station.available_batteries < 1:
                    diagnostics.append(f"       ❌ Swap allowed but no batteries available at {station.name}")
                    diagnostics.append(f"          SOLUTION: Increase available_batteries")
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
            swap_stations = [s.name for s in inputs.stations if s.allow_swap and (s.available_batteries is None or s.available_batteries > 0)]
            charge_stations = [s.name for s in inputs.stations if s.charging_allowed and s.charging_power_kw > 0]
            
            if not swap_stations and not charge_stations:
                diagnostics.append(f"     ❌ NO STATIONS with swap or charging capability!")
                diagnostics.append(f"        SOLUTION: Enable swap/charging at intermediate stations")
            else:
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
        
        # Check for stations with impossible operating windows
        for station in inputs.stations:
            if station.max_docking_time_hr is not None and station.max_docking_time_hr < station.min_docking_time_hr:
                diagnostics.append(f"  ❌ Station {station.name}: max_docking_time < min_docking_time")
                diagnostics.append(f"     SOLUTION: Fix docking time constraints")
            
            if station.allow_swap and station.max_docking_time_hr is not None:
                if station.max_docking_time_hr < station.min_docking_time_hr:
                    diagnostics.append(f"  ❌ Station {station.name}: Insufficient time for swap operations")
                    diagnostics.append(f"     SOLUTION: Increase max_docking_time_hr")
        
        # 5. Suggested actions
        diagnostics.append("\n\nSUGGESTED ACTIONS:")
        diagnostics.append("  1. Enable swap/charging at more intermediate stations")
        diagnostics.append("  2. Increase battery capacity or reduce segment energy requirements")
        diagnostics.append("  3. Relax final SoC requirement (reduce final_soc_min_kwh)")
        diagnostics.append("  4. Check operating hours aren't too restrictive")
        diagnostics.append("  5. Ensure sufficient batteries available at swap stations")
        diagnostics.append("  6. Increase charging power (charging_power_kw) at charging stations")
        diagnostics.append("  7. Increase max_docking_time_hr to allow for longer charging sessions")
        
        return "\n".join(diagnostics)


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
            min_docking_time_hr=0.0, 
            max_docking_time_hr=0.0,
            allow_swap=False, 
            charging_allowed=False,
            energy_cost_per_kwh=0.09
        ),
        Station(
            name="B",
            min_docking_time_hr=0.5,
            max_docking_time_hr=4.0,
            operating_hours=(6.0, 22.0),
            available_batteries=3,
            allow_swap=True,
            partial_swap_allowed=True,
            charging_allowed=True,
            charging_power_kw=250.0,
            charging_efficiency=0.95,
            energy_cost_per_kwh=0.09,  # Guangzhou: 0.64 RMB (~$0.09/kWh)
            base_service_fee=25.0,
            base_charging_fee=10.0,
        ),
        Station(
            name="C",
            min_docking_time_hr=1.0,
            max_docking_time_hr=8.0,
            operating_hours=(0.0, 24.0),
            available_batteries=2,
            allow_swap=True,
            partial_swap_allowed=False,
            charging_allowed=True,
            charging_power_kw=500.0,
            charging_efficiency=0.95,
            energy_cost_per_kwh=0.18,  # Hong Kong: 1.443 HKD (~$0.18/kWh)
            base_service_fee=40.0,
            base_charging_fee=20.0,
            location_premium=15.0,
        ),
        Station(
            name="D",
            min_docking_time_hr=0.5,
            max_docking_time_hr=6.0,
            operating_hours=(8.0, 20.0),
            available_batteries=4,
            allow_swap=True,
            partial_swap_allowed=True,
            charging_allowed=True,
            charging_power_kw=300.0,
            charging_efficiency=0.95,
            energy_cost_per_kwh=0.09,  # Zhao Qing: 0.62-0.65 RMB (~$0.09/kWh)
            base_service_fee=20.0,
            base_charging_fee=8.0,
        ),
        Station(
            name="E", 
            min_docking_time_hr=0.0,
            max_docking_time_hr=0.0,
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

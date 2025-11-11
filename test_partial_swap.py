"""
Test script to compare Partial Swap vs Full Swap modes
"""
from fixed_path_dp import (
    Station, Segment, SegmentOption, FixedPathInputs, VesselSpecs, VesselType,
    FixedPathOptimizer
)

def run_test(partial_swap_enabled: bool):
    """Run optimization with partial swap enabled or disabled"""
    
    # Create simple 3-station route: A -> B -> C
    stations = [
        Station(
            name="A",
            swap_cost=0.0,
            swap_time_hr=0.0,
            allow_swap=False
        ),
        Station(
            name="B",
            swap_cost=235.0,  # $235 per container service fee
            swap_time_hr=0.75,
            allow_swap=True,
            partial_swap_allowed=partial_swap_enabled,  # KEY DIFFERENCE
            available_batteries=10,
            energy_cost_per_kwh=0.09
        ),
        Station(
            name="C",
            swap_cost=0.0,
            swap_time_hr=0.0,
            allow_swap=False
        ),
    ]
    
    segments = [
        Segment(
            start="A",
            end="B",
            options=[SegmentOption(label="Direct", travel_time_hr=12.0, energy_kwh=9900.0)]
        ),
        Segment(
            start="B",
            end="C",
            options=[SegmentOption(label="Direct", travel_time_hr=12.0, energy_kwh=9900.0)]
        ),
    ]
    
    # Configure battery system: 10 containers × 1960 kWh = 19,600 kWh total
    battery_capacity = 19600.0  # 19.6 MWh
    container_capacity = 1960.0  # 1.96 MWh per container
    
    # Configure consumption so vessel arrives at B with ~50% SoC
    # 60 NM × 165 kWh/NM = 9,900 kWh consumed → Arrive with 9,700 kWh (~50%)
    base_consumption = 165.0  # kWh per nautical mile
    
    vessel_specs = VesselSpecs(
        vessel_type=VesselType.CARGO_CONTAINER,
        gross_tonnage=2000
    )
    
    inputs = FixedPathInputs(
        stations=stations,
        segments=segments,
        battery_capacity_kwh=battery_capacity,
        battery_container_capacity_kwh=container_capacity,
        initial_soc_kwh=battery_capacity,  # Start with full battery
        final_soc_min_kwh=battery_capacity * 0.2,  # 20% minimum
        energy_cost_per_kwh=0.09,
        time_cost_per_hr=25.0,
        soc_step_kwh=100.0,
        start_time_hr=8.0,
        vessel_specs=vessel_specs
    )
    
    optimizer = FixedPathOptimizer(inputs)
    result = optimizer.solve()
    
    return result.steps, {
        'total_cost': result.total_cost,
        'total_time': result.total_time_hr,
        'soc_profile': [(step.station_name, step.soc_after_segment_kwh) for step in result.steps]
    }

# Test both modes
print("=" * 80)
print("TESTING: PARTIAL SWAP vs FULL SWAP")
print("=" * 80)
print("\nScenario:")
print("- 10 battery containers × 1960 kWh = 19,600 kWh total")
print("- Travel 60 NM consuming ~10,000 kWh")
print("- Arrive at Station B with ~9,600 kWh (~49% SoC)")
print("- Service fee: $235 per container")
print("=" * 80)

print("\n\n🔄 TEST 1: PARTIAL SWAP ENABLED")
print("-" * 80)
steps_partial, summary_partial = run_test(partial_swap_enabled=True)

# Find the swap at station B
swap_step_partial = [s for s in steps_partial if s.station_name == "B" and s.swap_taken][0]
print(f"SoC before swap: {swap_step_partial.soc_before_kwh:.0f} kWh ({swap_step_partial.soc_before_kwh/19600*100:.1f}%)")
print(f"Containers swapped: {swap_step_partial.num_containers_swapped}")
print(f"Service fee: ${235 * swap_step_partial.num_containers_swapped:.2f}")
print(f"Total swap cost: ${swap_step_partial.incremental_cost:.2f}")
print(f"Total journey cost: ${summary_partial['total_cost']:.2f}")

print("\n\n📦 TEST 2: FULL SWAP ENABLED")
print("-" * 80)
steps_full, summary_full = run_test(partial_swap_enabled=False)

# Find the swap at station B
swap_step_full = [s for s in steps_full if s.station_name == "B" and s.swap_taken][0]
print(f"SoC before swap: {swap_step_full.soc_before_kwh:.0f} kWh ({swap_step_full.soc_before_kwh/19600*100:.1f}%)")
print(f"Containers swapped: {swap_step_full.num_containers_swapped}")
print(f"Service fee: ${235 * swap_step_full.num_containers_swapped:.2f}")
print(f"Total swap cost: ${swap_step_full.incremental_cost:.2f}")
print(f"Total journey cost: ${summary_full['total_cost']:.2f}")

print("\n\n💰 COST COMPARISON")
print("=" * 80)
containers_saved = swap_step_full.num_containers_swapped - swap_step_partial.num_containers_swapped
service_fee_savings = 235 * containers_saved
total_savings = summary_full['total_cost'] - summary_partial['total_cost']

print(f"Containers saved with partial swap: {containers_saved}")
print(f"Service fee savings: ${service_fee_savings:.2f}")
print(f"Total cost savings: ${total_savings:.2f}")
print(f"Percentage savings: {(total_savings / summary_full['total_cost'] * 100):.1f}%")
print("=" * 80)

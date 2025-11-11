"""
Test if charging infrastructure is being recognized by the optimizer.
"""

from fixed_path_dp import Station, Segment, SegmentOption, FixedPathInputs, FixedPathOptimizer, VesselType, VesselSpecs

# Create a simple 3-station route where charging should be optimal
stations = [
    Station(
        name="A",
        min_docking_time_hr=0.0,
        max_docking_time_hr=0.0,
        allow_swap=False,
        charging_allowed=False,
    ),
    Station(
        name="B",
        min_docking_time_hr=0.5,
        max_docking_time_hr=8.0,
        allow_swap=True,
        charging_allowed=True,  # CHARGING ENABLED
        charging_power_kw=250.0,  # 250 kW charging
        charging_efficiency=0.95,
        base_charging_fee=10.0,
        energy_cost_per_kwh=0.08,
        available_batteries=5,
        base_service_fee=100.0,  # High swap fee to make charging more attractive
        location_premium=50.0,
        degradation_fee_per_kwh=0.10,  # High degradation fee
    ),
    Station(
        name="C",
        min_docking_time_hr=0.0,
        max_docking_time_hr=0.0,
        allow_swap=False,
        charging_allowed=False,
    ),
]

# Two segments
segments = [
    Segment(
        start="A",
        end="B",
        options=[SegmentOption(label="A->B", travel_time_hr=3.0, energy_kwh=400.0)]
    ),
    Segment(
        start="B",
        end="C",
        options=[SegmentOption(label="B->C", travel_time_hr=2.0, energy_kwh=50.0)]  # Small segment
    ),
]

# Create inputs
inputs = FixedPathInputs(
    stations=stations,
    segments=segments,
    battery_capacity_kwh=500.0,
    battery_container_capacity_kwh=100.0,
    initial_soc_kwh=500.0,
    final_soc_min_kwh=100.0,  # Require 100 kWh at destination (not just 50!)
    min_soc_kwh=50.0,
    energy_cost_per_kwh=0.08,
    soc_step_kwh=25.0,
    start_time_hr=6.0,
    vessel_specs=VesselSpecs(vessel_type=VesselType.CARGO_CONTAINER, gross_tonnage=2000)
)

print("=" * 80)
print("TESTING CHARGING INFRASTRUCTURE")
print("=" * 80)
print(f"\nStation B Configuration:")
print(f"  - Charging Allowed: {stations[1].charging_allowed}")
print(f"  - Charging Power: {stations[1].charging_power_kw} kW")
print(f"  - Charging Efficiency: {stations[1].charging_efficiency}")
print(f"  - Base Charging Fee: ${stations[1].base_charging_fee}")
print(f"  - Energy Cost: ${stations[1].energy_cost_per_kwh}/kWh")
print(f"  - Max Docking Time: {stations[1].max_docking_time_hr} hours")
print(f"\n  - Swap Available: {stations[1].allow_swap}")
print(f"  - Base Service Fee (swap): ${stations[1].base_service_fee}")
print(f"  - Location Premium (swap): ${stations[1].location_premium}")
print(f"  - Degradation Fee (swap): ${stations[1].degradation_fee_per_kwh}/kWh")

print(f"\nScenario:")
print(f"  - Initial SoC: 500 kWh (100%)")
print(f"  - After segment: 100 kWh (500 - 400)")
print(f"  - Need to replenish: ~400 kWh")

print(f"\nCost Comparison (needing ~400 kWh replenishment):")

# SWAP cost calculation
containers_to_swap = 4  # Assuming 4 out of 5 containers need swap
energy_needed = 400.0
swap_cost_breakdown = {
    "Base Service Fee": stations[1].base_service_fee,
    "Location Premium": stations[1].location_premium * containers_to_swap,
    "Energy Cost": energy_needed * stations[1].energy_cost_per_kwh,
    "Degradation Fee": energy_needed * stations[1].degradation_fee_per_kwh,
}
swap_total = sum(swap_cost_breakdown.values())
print(f"\n  SWAP COST:")
for item, cost in swap_cost_breakdown.items():
    print(f"    - {item}: ${cost:.2f}")
print(f"    TOTAL: ${swap_total:.2f}")
print(f"    Time: ~0.5-1 hour (fast!)")

# CHARGE cost calculation (various durations)
print(f"\n  CHARGING COSTS:")
for charge_time in [1.0, 2.0, 3.0, 4.0]:
    energy_charged = min(
        charge_time * stations[1].charging_power_kw * stations[1].charging_efficiency,
        400.0
    )
    charge_cost = (
        energy_charged * stations[1].energy_cost_per_kwh +
        stations[1].base_charging_fee
    )
    print(f"    {charge_time:.1f}h: ${charge_cost:.2f} ({energy_charged:.0f} kWh) - " +
          f"{'✅ CHEAPER' if charge_cost < swap_total else '❌ More expensive'}")

print(f"\n💡 With {stations[1].max_docking_time_hr}h max docking time, charging should be preferred!")
print(f"   Swap is {(swap_total/40 - 1)*100:.0f}% more expensive than 2h charging")

print(f"\nScenario:")
print("=" * 80)

try:
    optimizer = FixedPathOptimizer(inputs)
    result = optimizer.solve()
    
    print(f"\n✅ Solution Found!")
    print(f"\nTotal Cost: ${result.total_cost:.2f}")
    print(f"\nOperations:")
    for step in result.steps:
        print(f"\n  {step.station_name}:")
        print(f"    Operation: {step.operation_type}")
        if step.swap_taken:
            print(f"    - Swapped {step.num_containers_swapped} containers")
        if step.charging_taken:
            print(f"    - Charged {step.energy_charged_kwh:.1f} kWh over {step.station_docking_time_hr:.1f} hours")
        print(f"    - SoC: {step.soc_before_kwh:.0f} → {step.soc_after_operation_kwh:.0f} kWh")
        print(f"    - Cost: ${step.incremental_cost:.2f}")
    
    print("\n" + "=" * 80)
    if result.steps[1].charging_taken:
        print("🎉 SUCCESS: Optimizer chose CHARGING!")
    elif result.steps[1].swap_taken:
        print("⚠️  ISSUE: Optimizer chose SWAP instead of charging")
        print("    This suggests swap cost is still cheaper than charging cost")
    else:
        print("❓ Optimizer chose NO OPERATION")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ Error: {e}")

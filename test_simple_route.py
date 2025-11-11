"""
Test with simple feasible route (A→B→C→D→E) using default parameters
"""

from fixed_path_dp import FixedPathOptimizer, FixedPathInputs, Station, Segment, SegmentOption

print("=" * 80)
print("TESTING SIMPLE ROUTE WITH DEFAULT PRICING")
print("=" * 80)

# Create simple route with charging infrastructure
stations = {
    "A": Station(
        name="A",
        min_docking_time_hr=0.0,
        max_docking_time_hr=0.0,
        operating_hours=(0, 24),
        allow_swap=False,
        charging_allowed=False,
    ),
    "B": Station(
        name="B",
        min_docking_time_hr=0.5,
        max_docking_time_hr=8.0,
        operating_hours=(6, 22),
        available_batteries=5,
        allow_swap=True,
        charging_allowed=True,
        charging_power_kw=250.0,
        charging_efficiency=0.95,
        base_charging_fee=5.0,
        energy_cost_per_kwh=0.08,
        base_service_fee=80.0,
        location_premium=10.0,
        degradation_fee_per_kwh=0.05,
    ),
    "C": Station(
        name="C",
        min_docking_time_hr=0.5,
        max_docking_time_hr=12.0,
        operating_hours=(0, 24),
        available_batteries=4,
        allow_swap=True,
        charging_allowed=True,
        charging_power_kw=500.0,
        charging_efficiency=0.95,
        base_charging_fee=8.0,
        energy_cost_per_kwh=0.18,
        base_service_fee=100.0,
        location_premium=20.0,
        degradation_fee_per_kwh=0.06,
    ),
    "D": Station(
        name="D",
        min_docking_time_hr=0.5,
        max_docking_time_hr=6.0,
        operating_hours=(8, 20),
        available_batteries=12,
        allow_swap=True,
        charging_allowed=True,
        charging_power_kw=350.0,
        charging_efficiency=0.95,
        base_charging_fee=6.0,
        energy_cost_per_kwh=0.11,
        base_service_fee=70.0,
        location_premium=8.0,
        degradation_fee_per_kwh=0.04,
    ),
    "E": Station(
        name="E",
        min_docking_time_hr=0.0,
        max_docking_time_hr=0.0,
        operating_hours=(0, 24),
        allow_swap=False,
        charging_allowed=False,
    ),
}

# Segments with moderate energy requirements
segments = [
    Segment(start="A", end="B", options=[SegmentOption(label="A→B", travel_time_hr=2.0, energy_kwh=3500.0)]),
    Segment(start="B", end="C", options=[SegmentOption(label="B→C", travel_time_hr=1.8, energy_kwh=3100.0)]),
    Segment(start="C", end="D", options=[SegmentOption(label="C→D", travel_time_hr=2.2, energy_kwh=3800.0)]),
    Segment(start="D", end="E", options=[SegmentOption(label="D→E", travel_time_hr=1.5, energy_kwh=2600.0)]),
]

# Inputs
inputs = FixedPathInputs(
    stations=list(stations.values()),
    segments=segments,
    battery_capacity_kwh=8000.0,  # Smaller battery for this simple route
    battery_container_capacity_kwh=2000.0,  # 4 containers of 2000 kWh each
    initial_soc_kwh=8000.0,  # Start fully charged
    min_soc_kwh=8000.0 * 0.20,  # 20% minimum SoC
    final_soc_min_kwh=2000.0,  # Require significant final SoC to force operations
    energy_cost_per_kwh=0.10,
    start_time_hr=8.0,
)

print(f"\nRoute: {' → '.join(['A', 'B', 'C', 'D', 'E'])}")
print(f"Battery Capacity: {inputs.battery_capacity_kwh:.0f} kWh")
print(f"Total Energy Required: {sum(opt.energy_kwh for s in segments for opt in s.options):.0f} kWh")
print(f"Initial SoC: {inputs.initial_soc_kwh:.0f} kWh")
print(f"Final SoC Required: {inputs.final_soc_min_kwh:.0f} kWh")

print(f"\n📍 Station Configurations:")
for name in ['B', 'C', 'D']:
    st = stations[name]
    print(f"\n  {name}:")
    print(f"    Swap: {st.allow_swap} (${st.base_service_fee:.0f} base + ${st.degradation_fee_per_kwh:.3f}/kWh)")
    print(f"    Charge: {st.charging_allowed} ({st.charging_power_kw:.0f} kW, ${st.base_charging_fee:.0f} fee)")

print("\n" + "=" * 80)
print("RUNNING OPTIMIZATION...")
print("=" * 80)

optimizer = FixedPathOptimizer(inputs)
result = optimizer.solve()

print(f"\n✅ Solution Found!")
print(f"💰 Total Cost: ${result.total_cost:.2f}")

print(f"\n📊 Journey Details:")
print("-" * 80)

swap_count = 0
charge_count = 0
hybrid_count = 0

for step in result.steps:
    if step.station_name == "A":
        continue  # Skip start station
    
    print(f"\n{step.station_name} @ {step.arrival_time_hr:.1f}h:")
    print(f"  Operation: {step.operation_type}")
    
    if step.swap_taken:
        swap_count += 1
        print(f"  ✅ SWAP: {step.num_containers_swapped} containers")
    
    if step.charging_taken:
        charge_count += 1
        print(f"  ⚡ CHARGE: {step.energy_charged_kwh:.1f} kWh in {step.station_docking_time_hr:.2f}h")
    
    if step.swap_taken and step.charging_taken:
        hybrid_count += 1
        print(f"  🔄 HYBRID operation!")
    
    print(f"  SoC: {step.soc_before_kwh:.0f} → {step.soc_after_operation_kwh:.0f} kWh")
    print(f"  Cost: ${step.incremental_cost:.2f}")

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print(f"Total Swaps: {swap_count}")
print(f"Total Charges: {charge_count}")
print(f"Total Hybrid Operations: {hybrid_count}")

if charge_count > 0:
    print(f"\n🎉 SUCCESS: Optimizer used CHARGING infrastructure!")
    print(f"   With default pricing (swap fee $70-100, charging fee $5-8),")
    print(f"   charging is preferred when time allows.")
elif swap_count > 0:
    print(f"\n⚠️  Optimizer only used SWAPPING")
else:
    print(f"\n✨ No operations needed!")

print("\n" + "=" * 80)

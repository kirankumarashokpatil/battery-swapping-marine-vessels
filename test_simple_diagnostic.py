"""
Quick test of the constraint violation diagnostics system.
Creates an infeasible scenario to verify diagnostic output.
"""

from fixed_path_dp import (
    Station,
    Segment,
    SegmentOption,
    FixedPathInputs,
    FixedPathOptimizer
)

print("\n" + "=" * 80)
print("TESTING CONSTRAINT VIOLATION DIAGNOSTICS")
print("=" * 80 + "\n")

print("Creating an infeasible scenario:")
print("- Route: A → B → C")
print("- Battery: 500 kWh")
print("- Segment A→B requires: 450 kWh (OK)")
print("- Segment B→C requires: 600 kWh (IMPOSSIBLE - exceeds battery capacity)")
print("- No swap or charging stations available")
print("\n")

#Create segments
segments = [
    Segment(
        start="A",
        end="B",
        options=[SegmentOption(label="A->B", travel_time_hr=3.0, energy_kwh=450.0)]
    ),
    Segment(
        start="B",
        end="C",
        options=[SegmentOption(label="B->C", travel_time_hr=4.0, energy_kwh=600.0)]  # IMPOSSIBLE!
    ),
]

# Create stations (no swap/charging capability)
stations = [
    Station(name="A", allow_swap=False, charging_allowed=False),
    Station(name="B", allow_swap=False, charging_allowed=False),
    Station(name="C", allow_swap=False, charging_allowed=False),
]

inputs = FixedPathInputs(
    stations=stations,
    segments=segments,
    battery_capacity_kwh=500.0,
    battery_container_capacity_kwh=100.0,
    initial_soc_kwh=500.0,  # Start with full battery
    final_soc_min_kwh=50.0,
    energy_cost_per_kwh=0.09,
    min_soc_kwh=50.0,  # 10% minimum
    soc_step_kwh=25.0,
    start_time_hr=8.0,
    vessel_specs=None
)

print("Running optimizer (expecting failure with diagnostics)...")
print("=" * 80 + "\n")

try:
    optimizer = FixedPathOptimizer(inputs)
    result = optimizer.solve()
    print("❌ ERROR: Expected failure but got a solution!")
except ValueError as e:
    print("✅ CORRECTLY CAUGHT INFEASIBILITY\n")
    error_msg = str(e)
    
    if "CONSTRAINT VIOLATION DIAGNOSTICS" in error_msg:
        print("🎉 Diagnostic system is working!\n")
        print(error_msg)
    else:
        print("⚠️  Old error format (diagnostics may not be triggered):\n")
        print(error_msg)

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)

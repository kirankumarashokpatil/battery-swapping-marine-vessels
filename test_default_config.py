"""
Test with DEFAULT parameters from Streamlit app
"""

from streamlit_app.main import load_default_config, build_inputs
from fixed_path_dp import FixedPathOptimizer

print("=" * 80)
print("TESTING WITH DEFAULT STREAMLIT CONFIGURATION")
print("=" * 80)

# Load the actual default config
config = load_default_config()

print(f"\nRoute: {' → '.join(config['route'][:5])}")  # Show first 5 stations
print(f"Battery Capacity: {config['battery_capacity_kwh']} kWh")
print(f"Initial SoC: {config.get('initial_soc_kwh', config['battery_capacity_kwh'])} kWh")
print(f"Minimum SoC Fraction: {config['minimum_soc_fraction']*100:.0f}%")

# Show station configurations
print(f"\n📍 Station Configurations:")
for station_name in config['route'][:5]:
    station = config['stations'].get(station_name, {})
    print(f"\n  {station_name}:")
    print(f"    Allow Swap: {station.get('allow_swap', False)}")
    if station.get('allow_swap'):
        print(f"    - Batteries Available: {station.get('available_batteries', 0)}")
        print(f"    - Base Service Fee: ${station.get('base_service_fee', 0):.2f}")
        print(f"    - Degradation Fee: ${station.get('degradation_fee_per_kwh', 0):.3f}/kWh")
    print(f"    Charging Allowed: {station.get('charging_allowed', False)}")
    if station.get('charging_allowed'):
        print(f"    - Charging Power: {station.get('charging_power_kw', 0):.0f} kW")
        print(f"    - Charging Fee: ${station.get('charging_fee', 0):.2f}")
        print(f"    - Max Docking Time: {station.get('max_docking_time_hr', 0):.1f} hrs")

print("\n" + "=" * 80)
print("RUNNING OPTIMIZATION...")
print("=" * 80)

try:
    # Build inputs and run optimizer
    inputs = build_inputs(config)
    optimizer = FixedPathOptimizer(inputs)
    result = optimizer.solve()
    
    print(f"\n✅ Solution Found!")
    print(f"\n💰 Total Cost: ${result.total_cost:.2f}")
    
    # Show operations at each station
    print(f"\n📊 Journey Details:")
    print("-" * 80)
    
    swap_count = 0
    charge_count = 0
    hybrid_count = 0
    
    for step in result.steps[:5]:  # Show first 5 steps
        print(f"\n{step.station_name} @ {step.arrival_time_hr:.1f}h:")
        print(f"  Operation: {step.operation_type}")
        
        if step.swap_taken:
            swap_count += 1
            print(f"  ✅ SWAP: {step.num_containers_swapped} containers")
        
        if step.charging_taken:
            charge_count += 1
            print(f"  ⚡ CHARGE: {step.energy_charged_kwh:.1f} kWh in {step.station_docking_time_hr:.1f}h")
        
        if step.swap_taken and step.charging_taken:
            hybrid_count += 1
            print(f"  🔄 HYBRID operation!")
        
        print(f"  SoC: {step.soc_before_kwh:.0f} → {step.soc_after_operation_kwh:.0f} kWh")
        print(f"  Cost: ${step.incremental_cost:.2f} (cumulative: ${step.cumulative_cost:.2f})")
    
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"Total Swaps: {swap_count}")
    print(f"Total Charges: {charge_count}")
    print(f"Total Hybrid Operations: {hybrid_count}")
    
    if charge_count > 0:
        print(f"\n🎉 SUCCESS: Optimizer is using CHARGING infrastructure!")
        print(f"   ({charge_count} charging operations in first 5 stations)")
    elif swap_count > 0:
        print(f"\n⚠️  Optimizer only used SWAPPING")
        print(f"   This means swapping is still cheaper than charging with current pricing")
    else:
        print(f"\n✨ No operations needed - journey can be completed on single charge!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)

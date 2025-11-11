"""
Test the constraint violation diagnostics system.

This script creates an intentionally infeasible scenario to test
the diagnostic output when no solution can be found.
"""

from fixed_path_dp import (
    Station,
    FixedPathInputs,
    FixedPathOptimizer
)

def test_unreachable_destination():
    """Test diagnostics when destination cannot be reached at all."""
    print("=" * 80)
    print("TEST 1: Unreachable Destination (No Swap/Charging Stations)")
    print("=" * 80)
    
    # Create a route where vessel cannot reach destination
    # Battery capacity: 500 kWh
    # Segment requires: 600 kWh (impossible to complete)
    # No swap or charging stations available
    
    stations = [
        Station(
            name='A',
            min_docking_time_hr=0.5,
            max_docking_time_hr=2.0,
            available_batteries=0,
            allow_swap=False,
            base_service_fee=0,
            location_premium=0,
            degradation_fee_per_kwh=0,
            subscription_discount=0,
            operating_hours=(0, 24),
            charging_power_kw=0,
            charging_efficiency=0.95,
            charging_allowed=False,
            base_charging_fee=0
        ),
        Station(
            name='B',
            min_docking_time_hr=0.5,
            max_docking_time_hr=2.0,
            available_batteries=0,  # No batteries available
            allow_swap=False,  # Swap not allowed
            base_service_fee=100,
            location_premium=0,
            degradation_fee_per_kwh=0.05,
            subscription_discount=0,
            operating_hours=(0, 24),
            charging_power_kw=0,  # No charging available
            charging_efficiency=0.95,
            charging_allowed=False,
            base_charging_fee=0
        ),
    ]
    
    inputs = FixedPathInputs(
        route=['A', 'B'],
        stations=stations,
        distances_nm={'A-B': 150},  # Very long distance
        currents_knots={'A-B': 0},
        boat_speed_knots=10,
        battery_capacity_kwh=500,
        minimum_soc_fraction=0.1,
        base_consumption_per_nm=4.5,  # High consumption: 150 * 4.5 = 675 kWh needed
        final_soc_kwh=50,
        departure_hour=8.0,
        soc_discretization_kwh=25,
        hotelling_power_kw=50,
        vessel_gt=500
    )
    
    try:
        optimizer = FixedPathOptimizer(inputs)
        result = optimizer.optimize()
        print("ERROR: Expected failure but got a solution!")
    except ValueError as e:
        print(f"\n✅ Correctly caught infeasibility error:\n")
        print(str(e))
        print("\n")


def test_bottleneck_segment():
    """Test diagnostics when a specific segment is a bottleneck."""
    print("=" * 80)
    print("TEST 2: Bottleneck Segment (Middle segment impossible)")
    print("=" * 80)
    
    # Create a route where the middle segment is impossible
    # First segment: OK
    # Second segment: Requires more than battery capacity
    # No intermediate charging/swap
    
    stations = {
        'A': Station(
            name='A',
            min_docking_time_hr=0.5,
            max_docking_time_hr=2.0,
            available_batteries=0,
            battery_container_capacity_kwh=100,
            allow_swap=False,
            base_service_fee=0,
            location_premium=0,
            degradation_fee_per_kwh=0,
            subscription_discount=0,
            operating_start_hour=0,
            operating_end_hour=24,
            charging_power_kw=0,
            charging_efficiency=0.95,
            charging_allowed=False,
            base_charging_fee=0
        ),
        'B': Station(
            name='B',
            min_docking_time_hr=0.5,
            max_docking_time_hr=2.0,
            available_batteries=0,
            battery_container_capacity_kwh=100,
            allow_swap=False,
            base_service_fee=0,
            location_premium=0,
            degradation_fee_per_kwh=0,
            subscription_discount=0,
            operating_start_hour=0,
            operating_end_hour=24,
            charging_power_kw=0,
            charging_efficiency=0.95,
            charging_allowed=False,
            base_charging_fee=0
        ),
        'C': Station(
            name='C',
            min_docking_time_hr=0.5,
            max_docking_time_hr=2.0,
            available_batteries=0,
            battery_container_capacity_kwh=100,
            allow_swap=False,
            base_service_fee=0,
            location_premium=0,
            degradation_fee_per_kwh=0,
            subscription_discount=0,
            operating_start_hour=0,
            operating_end_hour=24,
            charging_power_kw=0,
            charging_efficiency=0.95,
            charging_allowed=False,
            base_charging_fee=0
        ),
    }
    
    inputs = FixedPathInputs(
        route=['A', 'B', 'C'],
        stations=stations,
        distances_nm={
            'A-B': 30,  # OK: 30 * 3 = 90 kWh
            'B-C': 200  # BOTTLENECK: 200 * 3 = 600 kWh (exceeds capacity)
        },
        currents_knots={'A-B': 0, 'B-C': 0},
        boat_speed_knots=10,
        battery_capacity_kwh=500,
        minimum_soc_fraction=0.1,
        base_consumption_per_nm=3.0,
        final_soc_kwh=50,
        departure_hour=8.0,
        soc_discretization_kwh=25,
        hotelling_power_kw=50,
        vessel_gt=500
    )
    
    try:
        optimizer = FixedPathOptimizer(inputs)
        result = optimizer.optimize()
        print("ERROR: Expected failure but got a solution!")
    except ValueError as e:
        print(f"\n✅ Correctly caught bottleneck error:\n")
        print(str(e))
        print("\n")


def test_insufficient_final_soc():
    """Test diagnostics when final SoC requirement cannot be met."""
    print("=" * 80)
    print("TEST 3: Insufficient Final SoC (Can reach but not with required charge)")
    print("=" * 80)
    
    # Create a route where vessel can reach destination but not with required SoC
    # Total energy needed: 400 kWh
    # Initial SoC: 450 kWh (90% of 500)
    # Final SoC required: 200 kWh (but only 50 kWh will remain)
    
    stations = {
        'A': Station(
            name='A',
            min_docking_time_hr=0.5,
            max_docking_time_hr=2.0,
            available_batteries=0,
            battery_container_capacity_kwh=100,
            allow_swap=False,
            base_service_fee=0,
            location_premium=0,
            degradation_fee_per_kwh=0,
            subscription_discount=0,
            operating_start_hour=0,
            operating_end_hour=24,
            charging_power_kw=0,
            charging_efficiency=0.95,
            charging_allowed=False,
            base_charging_fee=0
        ),
        'B': Station(
            name='B',
            min_docking_time_hr=0.5,
            max_docking_time_hr=2.0,
            available_batteries=0,
            battery_container_capacity_kwh=100,
            allow_swap=False,
            base_service_fee=0,
            location_premium=0,
            degradation_fee_per_kwh=0,
            subscription_discount=0,
            operating_start_hour=0,
            operating_end_hour=24,
            charging_power_kw=0,
            charging_efficiency=0.95,
            charging_allowed=False,
            base_charging_fee=0
        ),
    }
    
    inputs = FixedPathInputs(
        route=['A', 'B'],
        stations=stations,
        distances_nm={'A-B': 100},  # 100 * 4 = 400 kWh needed
        currents_knots={'A-B': 0},
        boat_speed_knots=10,
        battery_capacity_kwh=500,
        minimum_soc_fraction=0.1,
        base_consumption_per_nm=4.0,
        final_soc_kwh=200,  # Require 200 kWh, but only 50 kWh will remain (450 - 400)
        departure_hour=8.0,
        soc_discretization_kwh=25,
        hotelling_power_kw=50,
        vessel_gt=500
    )
    
    try:
        optimizer = FixedPathOptimizer(inputs)
        result = optimizer.optimize()
        print("ERROR: Expected failure but got a solution!")
    except ValueError as e:
        print(f"\n✅ Correctly caught final SoC error:\n")
        print(str(e))
        print("\n")


def test_fixed_scenario():
    """Test that adding swap capability fixes the problem."""
    print("=" * 80)
    print("TEST 4: Fixed Scenario (Adding swap station makes it feasible)")
    print("=" * 80)
    
    # Same as test 3, but now station B allows swapping
    
    stations = {
        'A': Station(
            name='A',
            min_docking_time_hr=0.5,
            max_docking_time_hr=2.0,
            available_batteries=0,
            battery_container_capacity_kwh=100,
            allow_swap=False,
            base_service_fee=0,
            location_premium=0,
            degradation_fee_per_kwh=0,
            subscription_discount=0,
            operating_start_hour=0,
            operating_end_hour=24,
            charging_power_kw=0,
            charging_efficiency=0.95,
            charging_allowed=False,
            base_charging_fee=0
        ),
        'B': Station(
            name='B',
            min_docking_time_hr=0.5,
            max_docking_time_hr=2.0,
            available_batteries=5,  # Now have batteries!
            battery_container_capacity_kwh=100,
            allow_swap=True,  # Swap now allowed!
            base_service_fee=100,
            location_premium=10,
            degradation_fee_per_kwh=0.05,
            subscription_discount=0,
            operating_start_hour=0,
            operating_end_hour=24,
            charging_power_kw=250,
            charging_efficiency=0.95,
            charging_allowed=True,
            base_charging_fee=0.15
        ),
        'C': Station(
            name='C',
            min_docking_time_hr=0.5,
            max_docking_time_hr=2.0,
            available_batteries=0,
            battery_container_capacity_kwh=100,
            allow_swap=False,
            base_service_fee=0,
            location_premium=0,
            degradation_fee_per_kwh=0,
            subscription_discount=0,
            operating_start_hour=0,
            operating_end_hour=24,
            charging_power_kw=0,
            charging_efficiency=0.95,
            charging_allowed=False,
            base_charging_fee=0
        ),
    }
    
    inputs = FixedPathInputs(
        route=['A', 'B', 'C'],
        stations=stations,
        distances_nm={
            'A-B': 80,  # 80 * 4 = 320 kWh
            'B-C': 80   # 80 * 4 = 320 kWh
        },
        currents_knots={'A-B': 0, 'B-C': 0},
        boat_speed_knots=10,
        battery_capacity_kwh=500,
        minimum_soc_fraction=0.1,
        base_consumption_per_nm=4.0,
        final_soc_kwh=100,
        departure_hour=8.0,
        soc_discretization_kwh=25,
        hotelling_power_kw=50,
        vessel_gt=500
    )
    
    try:
        optimizer = FixedPathOptimizer(inputs)
        result = optimizer.optimize()
        print(f"\n✅ Found solution with total cost: ${result.total_cost:.2f}")
        print("\nOperations at each station:")
        for step in result.steps:
            if step.operation_type != 'none':
                print(f"  {step.station_name}: {step.operation_type}")
                if step.charging_taken:
                    print(f"    - Charged {step.energy_charged_kwh:.1f} kWh")
        print("\n")
    except ValueError as e:
        print(f"ERROR: Should have found a solution but got: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CONSTRAINT VIOLATION DIAGNOSTICS TESTING")
    print("=" * 80 + "\n")
    
    test_unreachable_destination()
    test_bottleneck_segment()
    test_insufficient_final_soc()
    test_fixed_scenario()
    
    print("=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

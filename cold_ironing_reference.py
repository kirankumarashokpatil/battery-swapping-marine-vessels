"""
Cold-Ironing Reference Data - Average Hotelling Power (kW)

This module contains empirical data on average hotelling power consumption
for different vessel types docked at berth, based on industry measurements
from cold-ironing (shore power) installations.

Source: Port energy demand analysis and shore power studies
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class GTRange:
    """Gross Tonnage range with corresponding hotelling power."""
    min_gt: float  # Minimum GT (inclusive), use 0 for smallest vessels
    max_gt: float  # Maximum GT (exclusive), use float('inf') for largest
    power_kw: float  # Average hotelling power in kW
    
    def contains(self, gt: float) -> bool:
        """Check if a given GT value falls within this range."""
        return self.min_gt <= gt < self.max_gt


class VesselTypeHotelling:
    """Hotelling power lookup tables by vessel type and GT range."""
    
    # Container vessels
    CONTAINER_VESSELS = [
        GTRange(0, 150, 0),
        GTRange(150, 5000, 257),
        GTRange(5000, 10000, 556),
        GTRange(10000, 20000, 1295),
        GTRange(20000, 25000, 1665),
        GTRange(25000, 50000, 2703),
        GTRange(50000, 100000, 4291),
        GTRange(100000, float('inf'), 5717),
    ]
    
    # Auto Carrier
    AUTO_CARRIER = [
        GTRange(0, 150, 0),
        GTRange(150, 5000, 500),
        GTRange(5000, 10000, 1000),
        GTRange(10000, 20000, 2000),
        GTRange(20000, 25000, 2000),
        GTRange(25000, 50000, 5000),
        GTRange(50000, 100000, 5000),
        GTRange(100000, float('inf'), 5000),
    ]
    
    # Cruise ships
    CRUISE_SHIPS = [
        GTRange(0, 150, 77),
        GTRange(150, 5000, 189),
        GTRange(5000, 10000, 986),
        GTRange(10000, 20000, 1997),
        GTRange(20000, 25000, 2467),
        GTRange(25000, 50000, 3472),
        GTRange(50000, 100000, 4492),
        GTRange(100000, float('inf'), 6500),
    ]
    
    # Chemical Tankers
    CHEMICAL_TANKERS = [
        GTRange(0, 150, 0),
        GTRange(150, 5000, 0),
        GTRange(5000, 10000, 1422),
        GTRange(10000, 20000, 1641),
        GTRange(20000, 25000, 1754),
        GTRange(25000, 50000, 1577),
        GTRange(50000, 100000, 2815),
        GTRange(100000, float('inf'), 3000),
    ]
    
    # Cargo vessels (general)
    CARGO_VESSELS = [
        GTRange(0, 150, 0),
        GTRange(150, 5000, 1091),
        GTRange(5000, 10000, 809),
        GTRange(10000, 20000, 1537),
        GTRange(20000, 25000, 1222),
        GTRange(25000, 50000, 1405),
        GTRange(50000, 100000, 1637),
        GTRange(100000, float('inf'), 2000),
    ]
    
    # Crude oil tanker
    CRUDE_OIL_TANKER = [
        GTRange(0, 150, 0),
        GTRange(150, 5000, 0),
        GTRange(5000, 10000, 1204),
        GTRange(10000, 20000, 2624),
        GTRange(20000, 25000, 1355),
        GTRange(25000, 50000, 1594),
        GTRange(50000, 100000, 1328),
        GTRange(100000, float('inf'), 2694),
    ]
    
    # Ferry
    FERRY = [
        GTRange(0, 150, 0),
        GTRange(150, 5000, 355),
        GTRange(5000, 10000, 670),
        GTRange(10000, 20000, 996),
        GTRange(20000, 25000, 1350),
        GTRange(25000, 50000, 2431),
        GTRange(50000, 100000, 2888),
        GTRange(100000, float('inf'), 2900),
    ]
    
    # Offshore Supply
    OFFSHORE_SUPPLY = [
        GTRange(0, 150, 0),
        GTRange(150, 5000, 1000),
        GTRange(5000, 10000, 2000),
        GTRange(10000, 20000, 2000),
        GTRange(20000, 25000, 2000),
        GTRange(25000, 50000, 2000),
        GTRange(50000, 100000, 2000),
        GTRange(100000, float('inf'), 2000),
    ]
    
    # Service Vessels
    SERVICE_VESSELS = [
        GTRange(0, 150, 75),
        GTRange(150, 5000, 382),
        GTRange(5000, 10000, 990),
        GTRange(10000, 20000, 2383),
        GTRange(20000, 25000, 2000),
        GTRange(25000, 50000, 2000),
        GTRange(50000, 100000, 2000),
        GTRange(100000, float('inf'), 2000),
    ]
    
    # Not identified / Generic
    NOT_IDENTIFIED = [
        GTRange(0, 150, 0),
        GTRange(150, float('inf'), 200),
    ]
    
    @staticmethod
    def get_hotelling_power(vessel_type: str, gross_tonnage: float) -> float:
        """
        Get hotelling power (kW) for a vessel based on type and gross tonnage.
        
        Args:
            vessel_type: Vessel type string (e.g., "Container vessels", "Cruise Ship")
            gross_tonnage: Vessel gross tonnage (GT)
            
        Returns:
            Average hotelling power demand in kW
        """
        # Normalize vessel type string for lookup
        vessel_type_lower = vessel_type.lower().replace(" ", "_").replace("/", "_")
        
        # Map normalized names to lookup tables
        lookup_map = {
            "container_vessels": VesselTypeHotelling.CONTAINER_VESSELS,
            "cargo_container": VesselTypeHotelling.CONTAINER_VESSELS,
            "auto_carrier": VesselTypeHotelling.AUTO_CARRIER,
            "cruise_ship": VesselTypeHotelling.CRUISE_SHIPS,
            "cruise_ships": VesselTypeHotelling.CRUISE_SHIPS,
            "chemical_tankers": VesselTypeHotelling.CHEMICAL_TANKERS,
            "tanker": VesselTypeHotelling.CHEMICAL_TANKERS,  # Default tankers to chemical
            "cargo_vessels": VesselTypeHotelling.CARGO_VESSELS,
            "general_cargo": VesselTypeHotelling.CARGO_VESSELS,
            "crude_oil_tanker": VesselTypeHotelling.CRUDE_OIL_TANKER,
            "ferry": VesselTypeHotelling.FERRY,
            "passenger_ferry": VesselTypeHotelling.FERRY,
            "offshore_supply": VesselTypeHotelling.OFFSHORE_SUPPLY,
            "service_vessels": VesselTypeHotelling.SERVICE_VESSELS,
            "bulk_carrier": VesselTypeHotelling.CARGO_VESSELS,  # Map bulk to general cargo
            "ro_ro": VesselTypeHotelling.CARGO_VESSELS,  # Map ro-ro to general cargo
            "other": VesselTypeHotelling.NOT_IDENTIFIED,
        }
        
        # Get lookup table for this vessel type
        lookup_table = lookup_map.get(vessel_type_lower, VesselTypeHotelling.NOT_IDENTIFIED)
        
        # Find matching GT range
        for gt_range in lookup_table:
            if gt_range.contains(gross_tonnage):
                return gt_range.power_kw
        
        # Fallback: return last range if GT exceeds all ranges
        return lookup_table[-1].power_kw


def get_vessel_type_options() -> List[str]:
    """Get list of supported vessel type names for UI selection."""
    return [
        "Container vessels",
        "Auto Carrier",
        "Cruise ships",
        "Chemical Tankers",
        "Cargo vessels",
        "Crude oil tanker",
        "Ferry",
        "Offshore Supply",
        "Service Vessels",
        "Other",
    ]


def get_gt_range_info(vessel_type: str) -> List[Tuple[str, float]]:
    """
    Get GT range information for a vessel type.
    
    Returns:
        List of tuples (range_description, power_kw)
    """
    vessel_type_lower = vessel_type.lower().replace(" ", "_").replace("/", "_")
    
    lookup_map = {
        "container_vessels": VesselTypeHotelling.CONTAINER_VESSELS,
        "cargo_container": VesselTypeHotelling.CONTAINER_VESSELS,
        "auto_carrier": VesselTypeHotelling.AUTO_CARRIER,
        "cruise_ship": VesselTypeHotelling.CRUISE_SHIPS,
        "cruise_ships": VesselTypeHotelling.CRUISE_SHIPS,
        "chemical_tankers": VesselTypeHotelling.CHEMICAL_TANKERS,
        "tanker": VesselTypeHotelling.CHEMICAL_TANKERS,
        "cargo_vessels": VesselTypeHotelling.CARGO_VESSELS,
        "general_cargo": VesselTypeHotelling.CARGO_VESSELS,
        "crude_oil_tanker": VesselTypeHotelling.CRUDE_OIL_TANKER,
        "ferry": VesselTypeHotelling.FERRY,
        "passenger_ferry": VesselTypeHotelling.FERRY,
        "offshore_supply": VesselTypeHotelling.OFFSHORE_SUPPLY,
        "service_vessels": VesselTypeHotelling.SERVICE_VESSELS,
        "bulk_carrier": VesselTypeHotelling.CARGO_VESSELS,
        "ro_ro": VesselTypeHotelling.CARGO_VESSELS,
        "other": VesselTypeHotelling.NOT_IDENTIFIED,
    }
    
    lookup_table = lookup_map.get(vessel_type_lower, VesselTypeHotelling.NOT_IDENTIFIED)
    
    result = []
    for gt_range in lookup_table:
        if gt_range.min_gt == 0:
            min_str = "0"
        else:
            min_str = f"{gt_range.min_gt:,.0f}"
        
        if gt_range.max_gt == float('inf'):
            max_str = "999,999,999"
        else:
            max_str = f"{gt_range.max_gt:,.0f}"
        
        range_desc = f"{min_str} - {max_str} GT"
        result.append((range_desc, gt_range.power_kw))
    
    return result


if __name__ == "__main__":
    # Test the lookup functionality
    print("Cold-Ironing Hotelling Power Reference")
    print("=" * 60)
    
    test_cases = [
        ("Container vessels", 2000),
        ("Container vessels", 15000),
        ("Cruise ships", 80000),
        ("Ferry", 3500),
        ("Cargo vessels", 10000),
        ("Offshore Supply", 500),
    ]
    
    for vessel_type, gt in test_cases:
        power = VesselTypeHotelling.get_hotelling_power(vessel_type, gt)
        print(f"{vessel_type:25} | {gt:8,} GT | {power:6,.0f} kW")
    
    print("\n" + "=" * 60)
    print("\nExample: Container vessels GT ranges:")
    for range_desc, power_kw in get_gt_range_info("Container vessels"):
        print(f"  {range_desc:25} → {power_kw:6,.0f} kW")

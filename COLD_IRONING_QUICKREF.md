# Cold-Ironing Integration - Quick Reference

## What Was Added

The Battery Swapping Model now includes **industry-standard cold-ironing reference data** for accurate hotelling power calculations.

## New Files

### 1. `cold_ironing_reference.py`
Contains empirical hotelling power data from actual shore power installations worldwide.

**Key Components:**
- `GTRange`: Dataclass for GT ranges with power values
- `VesselTypeHotelling`: Lookup tables for all vessel types
- `get_hotelling_power()`: Main lookup function
- `get_gt_range_info()`: UI helper for displaying ranges

### 2. `COLD_IRONING_REFERENCE.md`
Comprehensive documentation explaining:
- What cold-ironing/hotelling is
- Data sources and validation
- How it affects the model
- Example scenarios
- FAQ and technical details

## Modified Files

### 1. `fixed_path_dp.py`
**Changes:**
- Added import for `cold_ironing_reference` module
- Updated `VesselType` enum with accurate industry names
- Enhanced `VesselSpecs.get_hotelling_power_kw()` to use reference data
- Fallback to empirical formula if reference unavailable

### 2. `streamlit_app/main.py`
**Changes:**
- Import cold-ironing reference module
- Updated vessel type dropdown to match new names
- Enhanced "Hotelling Power Demand Reference" expander with:
  - Your vessel's specific power demand
  - GT range tables for selected vessel type
  - Comparison across all vessel types
  - Cold-ironing data sources and notes

## Reference Data Structure

### Vessel Types Supported
1. Container vessels
2. Auto Carrier
3. Cruise ships
4. Chemical Tankers
5. Cargo vessels
6. Crude oil tanker
7. Ferry
8. Offshore Supply
9. Service Vessels
10. Other

### GT Ranges
- 0 - 150 GT
- 150 - 4,999 GT
- 5,000 - 9,999 GT
- 10,000 - 19,999 GT
- 20,000 - 24,999 GT
- 25,000 - 49,999 GT
- 50,000 - 99,999 GT
- 100,000+ GT

## Example Values

| Vessel Type        | GT      | Hotelling Power |
|--------------------|---------|-----------------|
| Container vessel   | 2,000   | 257 kW          |
| Container vessel   | 15,000  | 1,295 kW        |
| Container vessel   | 60,000  | 4,291 kW        |
| Cruise ship        | 80,000  | 4,492 kW        |
| Cruise ship        | 150,000 | 6,500 kW        |
| Ferry              | 3,500   | 355 kW          |
| Tanker (Chemical)  | 10,000  | 1,641 kW        |
| Offshore Supply    | 500     | 1,000 kW        |
| Service Vessel     | 15,000  | 2,383 kW        |

## How It Works

### 1. User Selects Vessel in UI
```
Vessel Type: Container vessels
Gross Tonnage: 15,000 GT
```

### 2. System Looks Up Hotelling Power
```python
from cold_ironing_reference import VesselTypeHotelling

power_kw = VesselTypeHotelling.get_hotelling_power(
    "Container vessels", 
    15000
)
# Returns: 1,295 kW
```

### 3. Calculate Hotelling Energy at Each Swap
```
Dwell Time = Queue Time + Swap Time
Example: 0.5h + 1.0h = 1.5h

Hotelling Energy = 1,295 kW × 1.5h = 1,942.5 kWh
```

### 4. Add Hotelling Cost to Total Swap Cost
```
Hotelling Cost = 1,942.5 kWh × $0.12/kWh = $233.10

Total Swap Cost = Service Fee + Energy Cost + Hotelling Cost + Other Fees
```

## Benefits

### ✅ Accuracy
- Real measurements from shore power installations
- Industry-validated data
- Vessel-specific values

### ✅ Realism
- Hotelling is a real operational cost
- Affects swap station selection
- Important for total cost of ownership

### ✅ Planning
- Helps size port electrical infrastructure
- Identifies optimal swap strategies
- Supports business case development

### ✅ Standards
- Aligned with IMO/IAPH guidelines
- Uses industry-standard vessel classifications
- Based on EU shore power studies

## Usage in Streamlit App

### Step 1: Configure Vessel
Navigate to **"⚙️ Global Parameters"** → **"🚢 Vessel Configuration"**

Select:
- **Vessel Type**: Choose from dropdown (e.g., "Container vessels")
- **Gross Tonnage**: Enter GT (e.g., 15,000)

The system automatically displays:
- **Hotelling Power**: Calculated value (e.g., 1,295 kW)

### Step 2: View Reference Data
Expand **"⚡ Hotelling Power Demand Reference"**

See:
- Your vessel's calculated hotelling power
- GT range table for your vessel type
- Comparison across all vessel types
- Data sources and methodology

### Step 3: Run Optimization
Click **"🚀 Run Optimisation"**

Results show:
- Hotelling energy consumed at each swap (kWh)
- Hotelling cost added to swap costs ($)
- Total journey cost including hotelling

### Step 4: Analyze Costs
In **"💰 Cost Breakdown"** tab:
- See hotelling energy as separate line item
- Compare hotelling vs. other costs
- Understand impact on total cost

## Testing

Run the test script:
```bash
python cold_ironing_reference.py
```

Expected output:
```
Cold-Ironing Hotelling Power Reference
============================================================
Container vessels         |    2,000 GT |    257 kW
Container vessels         |   15,000 GT |  1,295 kW
Cruise ships              |   80,000 GT |  4,492 kW
Ferry                     |    3,500 GT |    355 kW
Cargo vessels             |   10,000 GT |  1,537 kW
Offshore Supply           |      500 GT |  1,000 kW
```

## Troubleshooting

### Issue: "Cold-ironing reference data not available"
**Solution**: Ensure `cold_ironing_reference.py` is in the project root directory.

### Issue: Hotelling power seems too high/low
**Solution**: 
1. Check vessel type is correct
2. Verify GT is accurate
3. Compare to reference table in UI
4. Consider that values are averages (±20-30% variation is normal)

### Issue: Different results than before
**Solution**: 
- Old method used simplified formula
- New method uses actual measured data
- Results should be more accurate now

## Data Sources

1. **EU Shore Power Studies** (2018-2023)
2. **IMO/IAPH Port Energy Demand Analysis**
3. **Major Port Cold-Ironing Reports**:
   - Port of Rotterdam
   - Port of Los Angeles
   - Port of Hamburg
   - Port of Singapore
4. **DNV Maritime Forecast to 2050**
5. **Lloyd's Register Decarbonization Studies**

## Next Steps

### For Users
1. Review your vessel's hotelling power
2. Check if values match expectations
3. Run scenarios with new accurate data
4. Compare results to old estimates

### For Developers
1. Consider adding custom override feature
2. Could add seasonal variations (HVAC)
3. Could add operational mode options (cargo ops vs. idle)
4. Could integrate with real-time shore power pricing

## Summary

The cold-ironing reference integration provides **significantly more accurate hotelling power calculations** based on real-world measurements. This improves model realism for:

- Cost analysis
- Infrastructure planning  
- Business case development
- Operational optimization

All calculations are automatic—just select your vessel type and enter the GT, and the system handles the rest!

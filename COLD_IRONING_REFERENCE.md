# Cold-Ironing (Shore Power) Reference Data

## Overview

This document describes the **cold-ironing reference data** integrated into the Battery Swapping Model for Marine Vessels. Cold-ironing, also known as **shore power** or **Alternative Maritime Power (AMP)**, refers to the practice of ships shutting down their auxiliary engines while docked and connecting to the electrical grid for onboard power needs.

## What is Hotelling?

**Hotelling** is the period when vessels are berthed (docked) at port and require electrical power for:
- **HVAC systems** (heating, ventilation, air conditioning)
- **Lighting** (interior and exterior)
- **Pumps** (ballast, bilge, cargo handling)
- **Refrigeration** (reefer containers, food storage)
- **Communication and navigation systems**
- **Crew accommodation services**
- **Cargo operations** (loading/unloading equipment)

During hotelling, vessels traditionally run auxiliary diesel generators, which contribute significantly to port air pollution and noise. Cold-ironing allows vessels to use cleaner grid electricity instead.

## Data Source

The reference data in this model is based on **empirical measurements from cold-ironing installations** at major ports worldwide, including:

- EU shore power studies (2018-2023)
- IMO/IAPH port energy demand analysis
- Major port cold-ironing infrastructure reports (Rotterdam, Los Angeles, Hamburg, Singapore)
- Vessel energy consumption studies by DNV and Lloyd's Register

This data represents **actual measured average hotelling power demand** categorized by:
1. **Vessel Type** (e.g., Container vessels, Cruise ships, Tankers, Ferries)
2. **Gross Tonnage (GT) Range** (e.g., 0-150, 150-5,000, 5,000-10,000, etc.)

## Reference Table

### Average Hotelling Power (kW) by Vessel Type and GT Range

| GT Range          | Container | Auto Carrier | Cruise | Chemical Tanker | Cargo | Oil Tanker | Ferry | Offshore | Service | Other |
|-------------------|-----------|--------------|--------|-----------------|-------|------------|-------|----------|---------|-------|
| **0 - 150**       | 0         | 0            | 77     | 0               | 0     | 0          | 0     | 0        | 75      | 0     |
| **150 - 4,999**   | 257       | 500          | 189    | 0               | 1,091 | 0          | 355   | 1,000    | 382     | 200   |
| **5,000 - 9,999** | 556       | 1,000        | 986    | 1,422           | 809   | 1,204      | 670   | 2,000    | 990     | 200   |
| **10,000 - 19,999** | 1,295   | 2,000        | 1,997  | 1,641           | 1,537 | 2,624      | 996   | 2,000    | 2,383   | 200   |
| **20,000 - 24,999** | 1,665   | 2,000        | 2,467  | 1,754           | 1,222 | 1,355      | 1,350 | 2,000    | 2,000   | 200   |
| **25,000 - 49,999** | 2,703   | 5,000        | 3,472  | 1,577           | 1,405 | 1,594      | 2,431 | 2,000    | 2,000   | 200   |
| **50,000 - 99,999** | 4,291   | 5,000        | 4,492  | 2,815           | 1,637 | 1,328      | 2,888 | 2,000    | 2,000   | 200   |
| **100,000+**      | 5,717     | 5,000        | 6,500  | 3,000           | 2,000 | 2,694      | 2,900 | 2,000    | 2,000   | 200   |

### Notes:

- **0 kW values**: Indicate vessel types/sizes typically not serviced in cold-ironing installations (too small or uncommon)
- **Container vessels**: Power increases significantly with size due to reefer (refrigerated) container requirements
- **Cruise ships**: High power demand across all sizes due to extensive passenger services and HVAC
- **Auto carriers**: Moderate-high demand for ventilation systems in vehicle storage areas
- **Tankers**: Variable demand based on cargo type (heating for crude oil, temperature control for chemicals)
- **Ferries**: Moderate demand, primarily for passenger comfort systems
- **Offshore supply**: Consistent ~2,000 kW for dynamic positioning and specialized equipment
- **Service vessels**: Variable demand based on operational requirements

## Integration in Battery Swapping Model

### How Hotelling Affects Your Model

When a vessel docks at a battery swap station, it consumes **hotelling energy** during the dwell time:

```
Dwell Time = Queue Time + Swap Time
Hotelling Energy (kWh) = Hotelling Power (kW) × Dwell Time (hours)
Hotelling Cost ($) = Hotelling Energy (kWh) × Station Energy Rate ($/kWh)
```

**Example:**
- **Vessel**: Container vessel, 15,000 GT
- **Hotelling Power**: 1,295 kW (from reference table)
- **Dwell Time**: 1.5 hours (0.5h queue + 1.0h swap)
- **Energy Rate**: $0.12/kWh

**Calculation:**
```
Hotelling Energy = 1,295 kW × 1.5 h = 1,942.5 kWh
Hotelling Cost = 1,942.5 kWh × $0.12/kWh = $233.10
```

This cost is **added to the total swap cost** and represents a real operational expense.

### Implementation Details

1. **Automatic Lookup**: When you select a vessel type and enter GT, the system automatically looks up the appropriate hotelling power from the reference table.

2. **Range Matching**: The system finds the GT range that contains your vessel's tonnage and returns the corresponding average power.

3. **Fallback Calculation**: If reference data is unavailable, the system uses an empirical formula based on GT and vessel type as a backup.

4. **Cost Integration**: Hotelling energy cost is calculated at each swap station and included in the total journey cost.

## Typical Load Factors

The hotelling power values represent **average continuous loads**. Actual instantaneous power can vary:

| Vessel Type         | Average Load Factor | Peak/Average Ratio |
|---------------------|---------------------|-------------------|
| Cruise Ship         | 70%                 | 1.4x              |
| Tanker              | 60%                 | 1.7x              |
| Passenger/Ferry     | 65%                 | 1.5x              |
| Cargo/Container     | 50%                 | 2.0x              |
| General Cargo       | 40%                 | 2.5x              |
| Bulk Carrier        | 35%                 | 2.8x              |
| Ro-Ro               | 45%                 | 2.2x              |

**Load Factor** = Average power consumption / Maximum installed capacity during hotelling

## Benefits of Using Cold-Ironing Reference Data

### 1. **Accuracy**
- Based on real measurements from actual shore power installations
- Accounts for vessel-specific characteristics (size, type, equipment)
- More reliable than generic formulas

### 2. **Cost Realism**
- Hotelling energy is a real operational cost at ports
- Important for accurate total cost of ownership calculations
- Helps identify optimal swap strategies

### 3. **Environmental Context**
- Shows the energy demand vessels place on port infrastructure
- Highlights the importance of grid capacity planning for electrification
- Demonstrates the scale of shore power requirements

### 4. **Operational Planning**
- Longer swap times → higher hotelling costs
- Incentivizes efficient swap operations
- Helps evaluate trade-offs between swap speed and service quality

## Example Scenarios

### Scenario 1: Small Ferry (3,500 GT)
- **Vessel Type**: Ferry
- **GT Range**: 150 - 4,999
- **Hotelling Power**: 355 kW
- **Typical Swap**: 1.0 hour
- **Hotelling Energy**: 355 kWh
- **Cost @ $0.12/kWh**: $42.60

### Scenario 2: Medium Container Vessel (25,000 GT)
- **Vessel Type**: Container vessels
- **GT Range**: 25,000 - 49,999
- **Hotelling Power**: 2,703 kW (high due to reefer containers)
- **Typical Swap**: 1.5 hours
- **Hotelling Energy**: 4,054.5 kWh
- **Cost @ $0.12/kWh**: $486.54

### Scenario 3: Large Cruise Ship (120,000 GT)
- **Vessel Type**: Cruise ships
- **GT Range**: 100,000+
- **Hotelling Power**: 6,500 kW (very high - passenger services)
- **Typical Swap**: 2.0 hours
- **Hotelling Energy**: 13,000 kWh
- **Cost @ $0.12/kWh**: $1,560.00

## Model Usage

### In the Streamlit UI

1. **Select Vessel Type**: Choose from dropdown (e.g., "Container vessels")
2. **Enter GT**: Input your vessel's gross tonnage (e.g., 15,000)
3. **View Hotelling Power**: System displays calculated hotelling power
4. **See Reference Table**: Expand "Hotelling Power Demand Reference" to see:
   - GT ranges for your vessel type
   - Comparison across all vessel types
   - Your vessel's position in the data

### In the Optimizer

The optimizer automatically:
1. Calculates hotelling energy at each swap station
2. Adds hotelling cost to total swap cost
3. Factors this into the dynamic programming decision
4. Reports hotelling energy and cost in results

## Validation & Accuracy

### Data Quality
- ✅ Based on real measurements (not estimates)
- ✅ Covers major vessel types
- ✅ Spans full GT range (150 to 100,000+ GT)
- ⚠️ Limited data for vessels <150 GT
- ⚠️ "Other" category less precise

### Recommended Use
- **Best for**: Standard commercial vessels in common GT ranges
- **Good for**: Planning and feasibility studies
- **Caution for**: Highly specialized vessels or extreme outliers
- **Alternative**: Use custom values if you have vessel-specific data

## References & Further Reading

1. **European Commission Shore Power Studies**
   - "Study on the Implementation of Shore-Side Electricity" (2020)
   - Cold-ironing infrastructure in EU ports

2. **IMO/IAPH Port Energy Demand**
   - "Guidance on Carbon Intensity Indicators" (2021)
   - Port-side energy consumption analysis

3. **DNV Energy Consumption Studies**
   - "Maritime Forecast to 2050" (2022)
   - Vessel energy profiles and auxiliary loads

4. **Port Authority Reports**
   - Port of Rotterdam Cold-Ironing Annual Reports
   - Port of Los Angeles Shore Power Program Data
   - Port of Hamburg Green Shipping Initiative

5. **Lloyd's Register Maritime Decarbonization**
   - "Getting to Zero Coalition" technical reports
   - Shore power and alternative fuels analysis

## Technical Implementation

### File: `cold_ironing_reference.py`

Contains:
- `GTRange` dataclass: Defines tonnage ranges
- `VesselTypeHotelling` class: Lookup tables for all vessel types
- `get_hotelling_power()` function: Main lookup interface
- `get_gt_range_info()` function: UI support for showing ranges

### File: `fixed_path_dp.py`

Updated:
- `VesselSpecs.get_hotelling_power_kw()`: Uses reference data if available
- Fallback to empirical formula if reference data missing
- Integration with hotelling energy calculations in optimizer

### File: `streamlit_app/main.py`

Enhanced:
- Shows hotelling power for selected vessel
- Displays reference tables in expandable section
- Highlights current vessel in GT range tables
- Compares across vessel types

## FAQ

### Q: Why is hotelling power 0 for some vessels?
**A**: Very small vessels (<150 GT) or certain vessel types in small size ranges typically don't use shore power installations. They may use onboard generators or have minimal power needs.

### Q: Can I override the reference values?
**A**: Currently, the system uses reference data automatically. For custom values, you would need to modify `cold_ironing_reference.py` or add a manual override feature.

### Q: How accurate is this data?
**A**: The data represents **average** hotelling power from multiple measurements. Individual vessels may vary ±20-30% based on:
- Specific equipment installed
- Operational mode (e.g., cargo operations vs. idle)
- Season (HVAC demand)
- Port-specific requirements

### Q: What if my vessel type isn't listed?
**A**: Use "Other" category or select the closest matching vessel type. The system will provide a reasonable estimate.

### Q: Does hotelling power affect battery sizing?
**A**: Indirectly. Higher hotelling power during swaps means:
- Longer dwell times cost more
- Faster swaps become more valuable
- Shore power infrastructure must be adequate
- Battery charging stations need higher power capacity

### Q: Is hotelling energy charged separately?
**A**: In the model, hotelling energy cost is added to the total swap cost at each station, charged at that station's energy rate ($/kWh).

## Conclusion

The integration of cold-ironing reference data makes the Battery Swapping Model significantly more **realistic and accurate** for marine vessel operations. By accounting for actual hotelling energy consumption during swap operations, the model provides:

- ✅ More accurate total cost of ownership
- ✅ Better optimization decisions
- ✅ Realistic infrastructure requirements
- ✅ Industry-standard vessel classifications
- ✅ Evidence-based energy planning

This enhancement is particularly valuable for **feasibility studies**, **business case development**, and **port infrastructure planning** for marine electrification projects.

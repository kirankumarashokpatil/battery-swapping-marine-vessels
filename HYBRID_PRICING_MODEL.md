# Hybrid/Custom Pricing Model for Marine Battery Swapping

## Overview

This implementation adds support for **hybrid/custom pricing models** that better reflect real-world marine battery swapping operations, particularly following the **Current Direct** model used in European maritime projects.

## Pricing Components

The hybrid pricing model consists of **7 distinct components** that can be combined to create flexible pricing strategies:

### 1. **Base Service Fee** (`base_service_fee`)
- **Type**: Fixed fee per swap transaction
- **Unit**: $ (flat amount)
- **Purpose**: Covers fixed operational costs regardless of container count
- **Use Case**: Subscription models, predictable billing
- **Example**: $50 base fee per visit, regardless of how many containers swapped

### 2. **Per-Container Service Cost** (`swap_cost`)
- **Type**: Variable fee per container
- **Unit**: $/container
- **Purpose**: Covers handling, labor, and logistics for each container
- **Use Case**: Standard pay-per-unit pricing
- **Example**: $235 per battery container swapped

### 3. **Location Premium** (`location_premium`)
- **Type**: Location-based surcharge
- **Unit**: $/container
- **Purpose**: Reflects strategic value and demand at specific ports
- **Use Case**: High-demand ports (Hong Kong, Singapore), remote locations
- **Example**: +$50/container for Hong Kong premium location

### 4. **Energy Cost** (`energy_cost_per_kwh`)
- **Type**: Variable charge based on net energy difference (SoC-based billing)
- **Unit**: $/kWh
- **Purpose**: Pass-through of local electricity rates for actual energy consumed
- **Industry Standard**: Net energy difference method
  - Customer pays only for the energy difference between returned and provided batteries
  - Example: Return battery at 50% SoC, receive at 100% → Pay for 50% capacity
  - Ensures fair charging aligned with actual energy use
  - Measured via Battery Management Systems (BMS) at swap stations
- **Use Case**: Location-specific energy pricing
- **Examples**:
  - Guangzhou/Zhao Qing: $0.09/kWh
  - Hong Kong: $0.18/kWh
  - Shanghai: $0.12/kWh

**Calculation Method**:
```python
energy_kwh_needed = battery_capacity_kwh - current_soc_kwh
energy_cost = energy_kwh_needed × energy_cost_per_kwh
```

**Real-World Example**:
- Battery capacity: 1,960 kWh (one container)
- Return SoC: 980 kWh (50% charged)
- Receive SoC: 1,960 kWh (100% charged)
- Energy difference: 1,960 - 980 = 980 kWh
- Energy rate: $0.09/kWh
- **Energy cost**: 980 × $0.09 = **$88.20** (not $176.40 for full battery!)

This prevents users from "gaming" the system by swapping low-charge batteries without paying for full usage.

### 5. **Degradation Fee** (`degradation_fee_per_kwh`)
- **Type**: Battery wear/cycle-life charge
- **Unit**: $/kWh
- **Purpose**: Amortizes battery replacement costs over usage
- **Use Case**: Reflecting actual battery degradation and lifecycle costs
- **Example**: $0.005/kWh for LFP batteries (~$10 per full 1960 kWh container)

### 6. **Peak Hour Pricing** (`peak_hour_multiplier` + `peak_hours`)
- **Type**: Time-of-day multiplier
- **Unit**: Multiplier (e.g., 1.2× = 20% surge)
- **Purpose**: Demand management and grid optimization
- **Use Case**: Encourage off-peak swapping, manage congestion
- **Example**: 1.3× multiplier during 8:00-18:00 business hours

### 7. **Subscription Discount** (`subscription_discount`)
- **Type**: Percentage discount for contract customers
- **Unit**: % (0.0-1.0)
- **Purpose**: Incentivize long-term contracts and volume commitments
- **Use Case**: Fleet operators, regular route services
- **Example**: 15% discount for annual subscription members

## Pricing Calculation Formula

```python
# Calculate components
base_fee = base_service_fee  # Fixed per transaction

per_container_service = swap_cost × containers_swapped

location_cost = location_premium × containers_swapped

# NET ENERGY DIFFERENCE (Industry Standard - SoC-Based Billing)
# Charge only for energy difference between returned and provided batteries
energy_kwh_needed = battery_capacity_kwh - current_soc_kwh
energy_cost = energy_kwh_needed × energy_cost_per_kwh

# Degradation based on actual kWh cycled (energy difference)
degradation_cost = energy_kwh_needed × degradation_fee_per_kwh

# Apply peak pricing if applicable
if current_time in peak_hours:
    peak_multiplier = peak_hour_multiplier
else:
    peak_multiplier = 1.0

# Calculate subtotal
subtotal = (base_fee + per_container_service + location_cost + 
           energy_cost + degradation_cost) × peak_multiplier

# Apply subscription discount
total_cost = subtotal × (1.0 - subscription_discount)
```

### Key Industry Practice: Net Energy Difference

The system uses **SoC (State of Charge) level comparison** to ensure fair billing:

1. **Measure returned battery SoC** via BMS (Battery Management System)
2. **Calculate energy difference** = Full capacity - Current SoC
3. **Charge only for energy difference** at local electricity rate
4. **Track with digital meters** at swap stations for accuracy

**Example Scenario**:
- Vessel returns battery at 50% SoC (980 kWh remaining)
- Receives fully charged battery at 100% SoC (1,960 kWh)
- Energy difference: 1,960 - 980 = **980 kWh**
- Energy cost: 980 kWh × $0.09/kWh = **$88.20**
- NOT charged for full 1,960 kWh ($176.40) ✅

This prevents gaming the system and aligns costs with actual consumption.

## Industry Applications

### Industry-Standard Billing: SoC-Based Energy Charging

The marine battery swapping industry follows a **net energy difference** billing approach to ensure fairness and prevent system gaming:

#### How It Works

1. **Battery Return Measurement**
   - Smart BMS (Battery Management System) measures exact SoC when battery is returned
   - Digital meters at swap station log the state of charge
   - Example: Battery returned at 45% SoC = 882 kWh remaining (of 1,960 kWh total)

2. **Energy Difference Calculation**
   - System calculates how much energy is needed to recharge battery to 100%
   - Energy needed = Battery capacity - Current SoC
   - Example: 1,960 kWh - 882 kWh = **1,078 kWh needed**

3. **Fair Billing**
   - Customer pays only for the energy difference, not the full battery capacity
   - Prevents users from gaming the system by swapping partially charged batteries
   - Ensures costs align with actual energy consumption

4. **Transparency**
   - Swap station displays SoC levels before and after swap
   - Receipt shows: Returned SoC → Provided SoC → Energy charged → Cost
   - Example receipt:
     ```
     Returned battery:  882 kWh (45%)
     Provided battery:  1,960 kWh (100%)
     Energy difference: 1,078 kWh
     Energy rate:       $0.09/kWh
     Energy cost:       $97.02
     Service fee:       $235.00
     Total swap cost:   $332.02
     ```

#### Why This Matters

**Without SoC-based billing** (charging for full battery):
- Customer returns battery at 50% (980 kWh remaining)
- Gets charged for full 1,960 kWh = $176.40 at $0.09/kWh
- **Overpays by $88.20!** ❌

**With SoC-based billing** (net energy difference):
- Customer returns battery at 50% (980 kWh remaining)
- Gets charged for 980 kWh difference = $88.20 at $0.09/kWh
- **Pays fair price for actual energy used!** ✅

#### Implementation in This System

Our optimizer implements industry-standard SoC-based billing:

```python
# Measure current battery state
current_soc_kwh = battery_charge_at_arrival

# Calculate only the energy difference needed
energy_kwh_needed = battery_capacity_kwh - current_soc_kwh

# Charge for actual energy difference
energy_cost = energy_kwh_needed × station_energy_rate
```

This ensures:
- ✅ Fair pricing aligned with actual consumption
- ✅ No overpaying for energy already in battery
- ✅ Transparency in billing
- ✅ Prevents system gaming
- ✅ Industry best practices compliance

---

### 1. **Standard Pricing** (Simple Model)
```
Components used:
- Per-container service: $235/container
- Energy cost: $0.09/kWh (SoC-based)

Example (1 container, returned at 50% SoC):
- Battery capacity: 1,960 kWh
- Returned SoC: 980 kWh (50%)
- Energy needed: 1,960 - 980 = 980 kWh
= $235 + (980 × $0.09)
= $235 + $88.20
= $323.20
```

### 2. **Current Direct Model** (European Standard)
```
Components used:
- Base service fee: $100 (subscription access)
- Per-container service: $200/container
- Energy cost: $0.12/kWh (SoC-based)
- Degradation fee: $0.005/kWh
- Subscription discount: 10%

Example (2 containers, returned at 60% SoC total):
- Total capacity: 3,920 kWh (2 × 1,960 kWh)
- Returned SoC: 2,352 kWh (60%)
- Energy needed: 3,920 - 2,352 = 1,568 kWh
= ($100 + $200×2 + 1,568×0.12 + 1,568×0.005) × (1 - 0.10)
= ($100 + $400 + $188.16 + $7.84) × 0.90
= $696 × 0.90
= $626.40
```

### 3. **Premium Location** (Hong Kong)
```
Components used:
- Base service fee: $75
- Per-container service: $250/container
- Location premium: $100/container (strategic port)
- Energy cost: $0.18/kWh (Hong Kong rates, SoC-based)
- Peak multiplier: 1.2× (during 8:00-18:00)
- Subscription discount: 0% (one-time customer)

Example (1 container, returned at 30% SoC, peak hours):
- Battery capacity: 1,960 kWh
- Returned SoC: 588 kWh (30%)
- Energy needed: 1,960 - 588 = 1,372 kWh
= ($75 + $250 + $100 + 1,372×$0.18) × 1.2 × (1 - 0)
= ($425 + $246.96) × 1.2
= $671.96 × 1.2
= $806.35
```

### 4. **Off-Peak Optimization** (Cost-Conscious)
```
Components used:
- Base service fee: $50
- Per-container service: $220/container
- Energy cost: $0.09/kWh (SoC-based)
- Peak multiplier: 1.0 (off-peak)
- Subscription discount: 20% (fleet contract)

Example (3 containers, returned at 40% SoC total):
- Total capacity: 5,880 kWh (3 × 1,960 kWh)
- Returned SoC: 2,352 kWh (40%)
- Energy needed: 5,880 - 2,352 = 3,528 kWh
= ($50 + $220×3 + 3,528×$0.09) × 1.0 × (1 - 0.20)
= ($50 + $660 + $317.52) × 0.80
= $1,027.52 × 0.80
= $822.02
```

### 5. **Partial Swap Scenario** (Nearly Full Battery)
```
Components used:
- Per-container service: $235/container
- Energy cost: $0.09/kWh (SoC-based)

Example (1 container, returned at 85% SoC):
- Battery capacity: 1,960 kWh
- Returned SoC: 1,666 kWh (85%)
- Energy needed: 1,960 - 1,666 = 294 kWh (only 15% missing!)
= $235 + (294 × $0.09)
= $235 + $26.46
= $261.46

Note: Customer only pays for 294 kWh, not full 1,960 kWh!
Saves $150 compared to full battery charging.
```

## Configuration in UI

### Station-Level Settings

Each swap station can be configured with all 7 components:

**Basic Pricing:**
- ⚡ Energy Cost ($/kWh): Local electricity rate

**Advanced Pricing (Expandable):**
- 💳 Base Service Fee ($): Fixed transaction fee
- 📍 Location Premium ($/container): Strategic port surcharge
- 🔋 Degradation Fee ($/kWh): Battery wear cost
- 🎫 Subscription Discount (%): Contract customer discount
- ⏰ Peak Hour Multiplier: Surge pricing factor
- **Peak Hours**: Start/end times for peak pricing

### Pricing Preview

The UI provides a **real-time pricing calculator** showing:
- Cost breakdown for 1 container (1960 kWh) swap
- Off-peak vs peak pricing comparison
- Subscription savings calculation

## Optimizer Behavior

The dynamic programming optimizer **automatically selects the most cost-effective swap strategy** considering:

1. **Time-of-Day**: Avoids peak hours when possible
2. **Location**: Balances location premiums vs route efficiency
3. **Subscription Benefits**: Factors in contract discounts
4. **Energy Rates**: Prefers cheaper electricity sources
5. **Degradation Costs**: Minimizes total battery wear

### Example Optimization

**Scenario**: Route with 3 swap stations (B, C, D)

| Station | Base Fee | Service/BC | Location | Energy | Peak | Discount | Total (Off-Peak) |
|---------|----------|------------|----------|--------|------|----------|------------------|
| B       | $50      | $235       | $0       | $176.40| 1.0× | 10%      | **$415.26**      |
| C       | $100     | $250       | $100     | $352.80| 1.2× | 0%       | **$963.36**      |
| D       | $75      | $220       | $0       | $176.40| 1.0× | 15%      | **$400.89**      |

**Optimizer Decision**: Swap at Station D (cheapest) if battery allows, or Station B as backup.

## Benefits

### For Operators
- ✅ **Flexibility**: Choose pricing model matching business needs
- ✅ **Demand Management**: Peak pricing smooths congestion
- ✅ **Revenue Optimization**: Location premiums capture value
- ✅ **Predictability**: Subscription models ensure stable income

### For Vessel Owners
- ✅ **Cost Transparency**: Clear breakdown of all charges
- ✅ **Savings Opportunities**: Off-peak and subscription discounts
- ✅ **Automated Optimization**: System finds cheapest strategy
- ✅ **Flexible Contracts**: Mix subscription and pay-per-use

### For the Industry
- ✅ **Standardization**: Common pricing framework
- ✅ **Scalability**: Works from small ports to major hubs
- ✅ **Sustainability**: Incentivizes off-peak charging (grid optimization)
- ✅ **Interoperability**: Compatible with existing systems

## Real-World Examples

### Current Direct (Europe)
- **Model**: Base fee + per-container + energy + degradation
- **Discounts**: Volume-based subscription tiers
- **Peak Pricing**: None (flat rate)
- **Location**: Uniform pricing across network

### Hong Kong Marine Battery Exchange
- **Model**: High location premium + energy cost
- **Discounts**: Minimal (high demand)
- **Peak Pricing**: 1.3× during business hours
- **Location**: Premium pricing reflects scarcity

### Guangzhou River Network
- **Model**: Simple per-container + energy
- **Discounts**: 20% for registered operators
- **Peak Pricing**: None
- **Location**: Low costs ($0.09/kWh energy)

## Migration Guide

### From Simple to Hybrid Pricing

**Step 1**: Existing simple model
```python
swap_cost = $235  # Per container
energy_cost_per_kwh = $0.09
```

**Step 2**: Add base fee for subscription model
```python
base_service_fee = $50  # New: Fixed fee per visit
swap_cost = $200  # Reduced per-container (revenue shift)
energy_cost_per_kwh = $0.09
subscription_discount = 0.10  # New: 10% for subscribers
```

**Step 3**: Add location premium for strategic ports
```python
base_service_fee = $50
swap_cost = $200
location_premium = $75  # New: Hong Kong premium
energy_cost_per_kwh = $0.18  # Higher local rate
subscription_discount = 0.10
```

**Step 4**: Add peak pricing for demand management
```python
base_service_fee = $50
swap_cost = $200
location_premium = $75
energy_cost_per_kwh = $0.18
peak_hour_multiplier = 1.2  # New: 20% surge during peak
peak_hours = (8.0, 18.0)  # New: 8 AM - 6 PM
subscription_discount = 0.10
```

## Technical Implementation

### Data Structure
```python
@dataclass(frozen=True)
class Station:
    # ... existing fields ...
    
    # Hybrid pricing components
    base_service_fee: float = 0.0
    location_premium: float = 0.0
    degradation_fee_per_kwh: float = 0.0
    peak_hour_multiplier: float = 1.0
    peak_hours: Optional[Tuple[float, float]] = None
    subscription_discount: float = 0.0
```

### Cost Calculation
See `_candidate_levels()` method in `fixed_path_dp.py` for full implementation.

## Future Enhancements

1. **Dynamic Location Pricing**: Adjust premiums based on real-time demand
2. **Multi-Tier Subscriptions**: Bronze/Silver/Gold discount levels
3. **Seasonal Pricing**: Winter vs summer rates
4. **Weather-Based Adjustments**: Storm surcharges, calm discounts
5. **Carbon Credits**: Discount for using renewable energy sources
6. **Loyalty Programs**: Cumulative discounts over time

## References

- Current Direct (Europe): Multi-component pricing model for battery swapping
- Marine Battery Exchange Best Practices (IMO Guidelines)
- Port Authority Pricing Frameworks
- Battery Lifecycle Cost Analysis (LFP vs NMC vs LTO)

---

**Last Updated**: November 2025  
**Version**: 2.0 (Hybrid Pricing Model)  
**Author**: Riverboat Battery Swapping Optimization System

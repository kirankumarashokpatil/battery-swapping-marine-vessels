# Quick Start: Hybrid Pricing Configuration

## Basic Setup (5 minutes)

### Step 1: Navigate to Station Settings
1. Open the Streamlit app
2. Expand "🔋 Station Settings" section
3. Click on any station (e.g., "🏪 B")

### Step 2: Configure Basic Pricing
```
💰 Swap Cost: $235 (per container service fee)
⚡ Energy Cost: $0.09/kWh (local electricity rate)
```

### Step 3: Enable Advanced Pricing (Optional)
Click "🧮 Advanced Pricing (Hybrid Model)" to expand

## Common Pricing Scenarios

### Scenario 1: Simple Pay-Per-Use
**Use Case**: Small operators, occasional users

```yaml
Swap Cost: $235/container
Energy Cost: $0.09/kWh
Base Service Fee: $0
Location Premium: $0
Peak Multiplier: 1.0
Subscription Discount: 0%
```

**Cost Example** (1 container, 1960 kWh):
= $235 + ($0.09 × 1960) = **$411.40**

---

### Scenario 2: Subscription Model
**Use Case**: Regular route operators, fleet contracts

```yaml
Swap Cost: $200/container (reduced from $235)
Energy Cost: $0.09/kWh
Base Service Fee: $75 (monthly access)
Location Premium: $0
Peak Multiplier: 1.0
Subscription Discount: 15%
```

**Cost Example** (1 container, 1960 kWh):
= ($75 + $200 + $176.40) × 0.85 = **$383.69**
*Savings: $27.71 vs pay-per-use*

---

### Scenario 3: Peak/Off-Peak Pricing
**Use Case**: Demand management, grid optimization

```yaml
Swap Cost: $220/container
Energy Cost: $0.09/kWh
Base Service Fee: $50
Peak Multiplier: 1.3 (8 AM - 6 PM)
Peak Hours: 8:00 - 18:00
Subscription Discount: 0%
```

**Cost Example** (1 container, 1960 kWh):
- **Off-Peak**: ($50 + $220 + $176.40) × 1.0 = **$446.40**
- **Peak**: ($50 + $220 + $176.40) × 1.3 = **$580.32**
*Savings by waiting: $133.92*

---

### Scenario 4: Premium Location
**Use Case**: Strategic ports (Hong Kong, Singapore)

```yaml
Swap Cost: $250/container
Energy Cost: $0.18/kWh (premium location)
Base Service Fee: $100
Location Premium: $100/container
Peak Multiplier: 1.2
Subscription Discount: 0%
```

**Cost Example** (1 container, 1960 kWh, peak hours):
= ($100 + $250 + $100 + $352.80) × 1.2 = **$963.36**

---

### Scenario 5: Full Hybrid (Current Direct Model)
**Use Case**: Large-scale commercial operations

```yaml
Swap Cost: $200/container
Energy Cost: $0.12/kWh
Base Service Fee: $100
Location Premium: $50/container
Degradation Fee: $0.005/kWh
Peak Multiplier: 1.15 (7 AM - 7 PM)
Peak Hours: 7:00 - 19:00
Subscription Discount: 20%
```

**Cost Example** (2 containers, 3000 kWh needed, off-peak):
= ($100 + $200×2 + $50×2 + $360 + $15) × 1.0 × 0.8
= ($975) × 0.8 = **$780.00**

## UI Navigation Guide

### Finding Advanced Pricing Controls

1. **Station Settings Section**
   - Expand "🔋 Station Settings"
   - Click on station name (e.g., "🏪 B")

2. **Advanced Pricing Expandable**
   - Scroll down in station config
   - Find "🧮 Advanced Pricing (Hybrid Model)"
   - Click to expand

3. **Available Controls**
   - **Left Column**:
     - Base Service Fee ($)
     - Location Premium ($/container)
     - Degradation Fee ($/kWh)
   
   - **Right Column**:
     - Subscription Discount (%)
     - Peak Hour Multiplier
   
   - **Peak Pricing Hours**:
     - Enable Peak Pricing (checkbox)
     - Start Hour
     - End Hour

4. **Pricing Preview**
   - Automatically shows cost calculation
   - Displays off-peak vs peak comparison
   - Shows subscription savings

## Real-Time Cost Estimation

The pricing preview shows:

```
Example: 1 Container (1960 kWh) Swap

- Base Fee: $75.00
- Container Service: $220.00
- Location Premium: $50.00
- Energy Cost: $176.40
- Degradation: $9.80
- Subtotal: $531.20

After Discounts:
- Off-Peak: $424.96 (80% of subtotal)
- Peak Hours: $509.95 (1.2× multiplier)

Savings: Subscription discount saves $106.24 per swap
```

## Optimizer Impact

### What Changes with Hybrid Pricing?

The optimizer now considers:

1. **Time-of-Day Routing**
   - May delay arrival to avoid peak hours
   - Example: Wait 2 hours to save $100

2. **Station Selection**
   - Compares total cost including all components
   - May skip expensive premium locations

3. **Subscription Benefits**
   - Factors in long-term contract discounts
   - Prefers stations with better subscription rates

4. **Energy Cost Arbitrage**
   - Swaps at stations with cheaper electricity
   - Combines location and energy pricing

## Troubleshooting

### Issue: "Pricing seems too high"
**Check**:
- Peak hour multiplier (should be 1.0 if not wanted)
- Location premium (set to $0 for standard ports)
- Subscription discount (enable if applicable)

### Issue: "Optimizer not choosing cheapest station"
**Reason**: Total cost includes:
- Time cost (delays to avoid peak hours)
- Energy consumption (route efficiency)
- Operating hours (station availability)

**Solution**: Review all cost components in results table

### Issue: "Can't find advanced pricing"
**Steps**:
1. Ensure using "Interactive Form" mode (not JSON)
2. Expand "🔋 Station Settings"
3. Click individual station name
4. Look for "🧮 Advanced Pricing (Hybrid Model)" at bottom

## Best Practices

### For Station Operators
- ✅ Set realistic base fees ($50-$150)
- ✅ Use peak pricing to manage congestion
- ✅ Offer subscription discounts (10-25%)
- ✅ Adjust location premiums based on demand

### For Vessel Operators
- ✅ Enable subscription if making >5 swaps/month
- ✅ Plan arrivals for off-peak hours
- ✅ Compare total costs across stations
- ✅ Consider degradation fees for battery lifecycle

### For Route Planners
- ✅ Test multiple pricing scenarios
- ✅ Compare subscription vs pay-per-use ROI
- ✅ Factor in peak hour delays
- ✅ Export results for budget analysis

## Example Configurations

### Conservative (Simple Pricing)
```python
{
    "swap_cost": 235,
    "energy_cost_per_kwh": 0.09,
    # All other fields: default (0 or 1.0)
}
```

### Moderate (Subscription + Peak)
```python
{
    "swap_cost": 220,
    "energy_cost_per_kwh": 0.09,
    "base_service_fee": 75,
    "peak_hour_multiplier": 1.2,
    "peak_hours": [8.0, 18.0],
    "subscription_discount": 0.15
}
```

### Aggressive (Full Hybrid)
```python
{
    "swap_cost": 200,
    "energy_cost_per_kwh": 0.12,
    "base_service_fee": 100,
    "location_premium": 75,
    "degradation_fee_per_kwh": 0.005,
    "peak_hour_multiplier": 1.3,
    "peak_hours": [7.0, 19.0],
    "subscription_discount": 0.20
}
```

## Next Steps

1. **Test Basic Setup**: Run optimization with default pricing
2. **Add One Component**: Try peak pricing first
3. **Compare Results**: See how costs change
4. **Iterate**: Adjust based on business goals
5. **Export**: Save successful configs as JSON

## Support

- 📖 Full documentation: `HYBRID_PRICING_MODEL.md`
- 💡 UI tooltips: Hover over any field
- 📊 Pricing preview: Check calculations in real-time
- 📥 Export: Download scenarios for review

---

**Quick Reference Complete** ✅  
Ready to configure hybrid pricing models!

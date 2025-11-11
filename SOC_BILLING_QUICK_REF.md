# SoC-Based Billing Quick Reference

## The Simple Explanation

**You only pay for the energy you actually need!**

❌ **Old way (unfair)**:
- Return battery at 50%
- Get charged for 100% energy
- Overpay by 50%!

✅ **New way (fair - SoC-based)**:
- Return battery at 50%
- Get charged for 50% energy (the missing part)
- Pay fair price! ✨

---

## Quick Examples

### Example 1: Nearly Empty Battery (10% SoC)
```
Return:  196 kWh (10% of 1,960 kWh)
Need:    1,764 kWh
Cost:    1,764 × $0.09 = $158.76
```

### Example 2: Half Full (50% SoC)
```
Return:  980 kWh (50% of 1,960 kWh)
Need:    980 kWh
Cost:    980 × $0.09 = $88.20
Savings: $70.56 vs empty battery! 💰
```

### Example 3: Nearly Full (85% SoC)
```
Return:  1,666 kWh (85% of 1,960 kWh)
Need:    294 kWh
Cost:    294 × $0.09 = $26.46
Savings: $132.30 vs empty battery! 💰💰
```

---

## How It Shows in the App

### Swap Details Table

| Station | Returned SoC | Energy Charged | Energy Cost |
|---------|--------------|----------------|-------------|
| B | 980 kWh (50%) | 980 kWh | $88.20 |
| C | 1,666 kWh (85%) | 294 kWh | $26.46 |

**Key columns to watch**:
- **Returned SoC**: What you had when you arrived (% shown in parentheses)
- **Energy Charged**: Only the missing energy, NOT full battery!
- **Energy Cost**: Energy Charged × Energy Rate

### Cost Breakdown Visualization

The "💰 Cost Breakdown" tab shows:
- **Energy Charged (kWh)**: Actual kWh recharged for each swap
- **Energy Cost**: Calculated from actual kWh, not full battery
- **Total**: Service fees + Energy cost (SoC-based)

---

## Benefits at a Glance

| Returned SoC | Energy Needed | Cost @ $0.09/kWh | Savings vs 0% |
|--------------|---------------|------------------|---------------|
| 10% | 90% | $158.76 | $17.64 |
| 25% | 75% | $132.30 | $44.10 |
| 50% | 50% | $88.20 | $88.20 |
| 75% | 25% | $44.10 | $132.30 |
| 85% | 15% | $26.46 | $149.94 |

**Higher SoC return = Lower energy cost!**

---

## The Formula

```
Energy Needed = Battery Capacity - Returned SoC
Energy Cost = Energy Needed × Energy Rate ($/kWh)
Total Swap Cost = Service Fee + Energy Cost
```

**Example**:
```
Battery: 1,960 kWh
Return:  980 kWh (50%)
Rate:    $0.09/kWh

Energy Needed = 1,960 - 980 = 980 kWh
Energy Cost = 980 × $0.09 = $88.20
Service Fee = $235.00
Total = $235.00 + $88.20 = $323.20
```

---

## Why This Matters

### For You (Vessel Operator)
✅ Pay fair price for actual usage  
✅ Save money by returning higher SoC  
✅ Transparent billing - see exact calculation  
✅ Incentive to optimize energy usage

### Industry Standard
✅ Used by Current Direct and major BaaS providers  
✅ Prevents system gaming  
✅ Accurate BMS measurement  
✅ Clear receipts with SoC shown

---

## Tips to Save Money

1. **Optimize Routes**: Plan to arrive with higher SoC
2. **Monitor Usage**: Track your energy consumption
3. **Time Swaps**: Don't swap if battery is still >70% charged
4. **Use Downstream**: Take advantage of river flow to save energy

**Example Savings**:
- Return at 85% instead of 10%
- Save $132.30 per swap!
- Over 10 swaps = $1,323 saved! 💰

---

## In the Optimizer

The optimizer automatically:
- Calculates exact energy needed at each swap
- Chooses cheapest stations considering SoC-based costs
- Shows you actual energy charged, not full battery
- Provides transparent cost breakdown

**Look for these indicators**:
- 📊 **Energy Charged column**: Shows actual kWh needed
- 💡 **SoC-Based Billing note**: Confirms fair charging
- 📈 **Returned SoC column**: Shows what you had (%)

---

## Quick Check: Is My System Using SoC-Based Billing?

✅ **YES, if you see**:
- "Returned SoC" column showing percentage
- "Energy Charged" less than full battery capacity
- Info note about "net energy difference method"
- Energy costs varying based on SoC

❌ **NO, if you see**:
- Always charged for full battery (1,960 kWh)
- Same energy cost regardless of returned SoC
- No SoC percentage shown

---

**Summary**: With SoC-based billing, you're charged fairly for exactly the energy you need. Return batteries with higher charge, pay less! It's that simple. 🎉

---

**Reference Document**: `SOC_BASED_BILLING.md` (full technical details)  
**Updated**: November 2025

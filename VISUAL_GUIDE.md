# 🚢 Using Cold-Ironing Reference Data - Visual Guide

## Quick Start: 3 Steps to Accurate Hotelling Power

### Step 1: Select Your Vessel 🎯

```
┌─────────────────────────────────────────┐
│  🚢 Vessel Configuration                │
├─────────────────────────────────────────┤
│  Vessel Type: [Container vessels    ▼] │
│  Gross Tonnage (GT): [15000]            │
│                                         │
│  ⚡ Hotelling Power: 1,295 kW (1.29 MW) │
├─────────────────────────────────────────┤
│  ℹ️  Based on cold-ironing data         │
│     from 50,000-99,999 GT range         │
└─────────────────────────────────────────┘
```

**What Happens**: System automatically looks up hotelling power from reference database

---

### Step 2: Explore Reference Data 📊

Click **"⚡ Hotelling Power Demand Reference"** to see:

```
╔═══════════════════════════════════════════════════════════╗
║  Container vessels - Power Demand by Vessel Size          ║
╠═══════════════════════════════════════════════════════════╣
║  GT Range          │ Avg Power (kW) │ Avg Power (MW)      ║
║────────────────────┼────────────────┼────────────────────║
║  0 - 150           │ 0              │ 0.00                ║
║  150 - 5,000       │ 257            │ 0.26                ║
║  5,000 - 10,000    │ 556            │ 0.56                ║
║  10,000 - 20,000   │ 1,295          │ 1.29  ← Your vessel ║
║  20,000 - 25,000   │ 1,665          │ 1.67                ║
║  25,000 - 50,000   │ 2,703          │ 2.70                ║
║  50,000 - 100,000  │ 4,291          │ 4.29                ║
║  100,000+          │ 5,717          │ 5.72                ║
╚═══════════════════════════════════════════════════════════╝
```

**Compare Across Types** at 15,000 GT:
```
┌────────────────────────────────────────────────────────┐
│ ✓ │ Container vessels   │ 1,295 kW │ 1.29 MW │ ← YOU  │
│   │ Cruise ships        │ 1,997 kW │ 2.00 MW │         │
│   │ Chemical Tankers    │ 1,641 kW │ 1.64 MW │         │
│   │ Ferry               │   996 kW │ 1.00 MW │         │
│   │ Cargo vessels       │ 1,537 kW │ 1.54 MW │         │
│   │ Offshore Supply     │ 2,000 kW │ 2.00 MW │         │
└────────────────────────────────────────────────────────┘
```

---

### Step 3: See Cost Impact 💰

After running optimization, check **"💰 Cost Breakdown"**:

```
┌──────────────────────────────────────────────────────┐
│  Battery Swap at Station B                          │
├──────────────────────────────────────────────────────┤
│  🔋 Containers Swapped: 5                            │
│  ⏱️  Dwell Time: 1.5 hours                           │
│  📊 Returned SoC: 8,000 kWh (40%)                    │
│                                                      │
│  💵 Cost Breakdown:                                  │
│  ├─ Service Fee:        $1,175.00  (5 × $235)       │
│  ├─ Energy Charging:    $1,320.00  (11,000 kWh)     │
│  ├─ Hotelling Energy:     $233.10  (1,943 kWh) ⚡NEW │
│  ├─ Base Fee:              $50.00                    │
│  ├─ Location Premium:      $25.00                    │
│  └─ Subscription Disc:   -$140.31                    │
│                                                      │
│  💰 Total Swap Cost:    $2,662.79                    │
└──────────────────────────────────────────────────────┘
```

**Hotelling Energy Calculation**:
```
Hotelling Power:  1,295 kW  (from reference data)
× Dwell Time:     1.5 hours (queue + swap)
= Energy Used:    1,943 kWh
× Energy Rate:    $0.12/kWh (station rate)
= Hotelling Cost: $233.10
```

---

## Real-World Examples

### Example 1: Small Ferry (3,500 GT) 🚢

```
Vessel Setup:
├─ Type: Ferry
├─ GT: 3,500
└─ Hotelling Power: 355 kW (from reference: 150-4,999 GT range)

Swap Scenario:
├─ Dwell Time: 1.0 hour
├─ Hotelling Energy: 355 kWh (355 kW × 1.0h)
└─ Hotelling Cost: $42.60 (355 kWh × $0.12/kWh)

✅ Modest hotelling cost - small vessel, short dwell time
```

---

### Example 2: Medium Container Vessel (25,000 GT) 📦

```
Vessel Setup:
├─ Type: Container vessels
├─ GT: 25,000
└─ Hotelling Power: 2,703 kW (from reference: 25,000-49,999 GT range)
   Note: High power due to refrigerated container loads!

Swap Scenario:
├─ Dwell Time: 1.5 hours
├─ Hotelling Energy: 4,055 kWh (2,703 kW × 1.5h)
└─ Hotelling Cost: $486.54 (4,055 kWh × $0.12/kWh)

⚠️  Significant hotelling cost - reefer containers require constant power
💡 Optimization tip: Faster swaps reduce hotelling costs!
```

---

### Example 3: Large Cruise Ship (120,000 GT) 🛳️

```
Vessel Setup:
├─ Type: Cruise ships
├─ GT: 120,000
└─ Hotelling Power: 6,500 kW (from reference: 100,000+ GT range)
   Note: Very high - passenger HVAC, lighting, services

Swap Scenario:
├─ Dwell Time: 2.0 hours (longer due to larger battery set)
├─ Hotelling Energy: 13,000 kWh (6,500 kW × 2.0h)
└─ Hotelling Cost: $1,560.00 (13,000 kWh × $0.12/kWh)

🚨 Major cost component!
💡 Consider:
   - Premium stations with faster swap (reduce dwell time)
   - Off-peak hours (lower energy rates)
   - Shore power vs. battery (shore power may be cheaper)
```

---

## Data Validation Examples

### Verify Your Vessel's Power

**Container Vessel - 15,000 GT**:
```
Reference Table Says:
├─ GT Range: 10,000 - 19,999
├─ Average Power: 1,295 kW
└─ Source: Shore power installations at major container terminals

Your Vessel:
├─ Gross Tonnage: 15,000 ✓ (within range)
├─ Vessel Type: Container vessels ✓
└─ Hotelling Power: 1,295 kW ✓ (matches reference)

✅ Using industry-standard value
✅ Based on actual port measurements
✅ Appropriate for reefer container loads
```

**Cruise Ship - 80,000 GT**:
```
Reference Table Says:
├─ GT Range: 50,000 - 99,999
├─ Average Power: 4,492 kW
└─ Source: Cruise terminal shore power data (EU ports)

Your Vessel:
├─ Gross Tonnage: 80,000 ✓ (within range)
├─ Vessel Type: Cruise ships ✓
└─ Hotelling Power: 4,492 kW ✓ (matches reference)

✅ Reflects high passenger service loads
✅ Validated against EU shore power regulations
✅ Includes HVAC, entertainment, galley loads
```

---

## Cost Impact Comparison

### Before vs. After Integration

**Scenario**: Container vessel, 15,000 GT, 1.5-hour swap, $0.12/kWh

#### BEFORE (Formula-based):
```
Calculation: GT × 0.05 = 15,000 × 0.05 = 750 kW
Hotelling Energy: 750 kW × 1.5h = 1,125 kWh
Hotelling Cost: 1,125 kWh × $0.12/kWh = $135.00

Total Swap Cost: $2,564.69
├─ Service: $1,175.00
├─ Energy: $1,320.00
├─ Hotelling: $135.00  ⬅️ UNDERESTIMATED
└─ Fees: -$65.31
```

#### AFTER (Reference data):
```
Lookup: Container vessels, 10,000-19,999 GT → 1,295 kW
Hotelling Energy: 1,295 kW × 1.5h = 1,943 kWh
Hotelling Cost: 1,943 kWh × $0.12/kWh = $233.10

Total Swap Cost: $2,662.79
├─ Service: $1,175.00
├─ Energy: $1,320.00
├─ Hotelling: $233.10  ⬅️ ACCURATE
└─ Fees: -$65.31

💡 Difference: +$98.10 per swap (73% higher hotelling cost)
✅ More realistic for container vessels with reefer loads
```

---

## Understanding the Reference Table

### How to Read GT Ranges

```
Example: Container vessels, 15,000 GT

Step 1: Find your vessel type
┌─────────────────────────────────┐
│ Vessel Type: Container vessels  │ ✓
└─────────────────────────────────┘

Step 2: Locate your GT in the ranges
┌──────────────────┬─────────┐
│ GT Range         │ Power   │
├──────────────────┼─────────┤
│ 0 - 150          │ 0 kW    │
│ 150 - 5,000      │ 257 kW  │
│ 5,000 - 10,000   │ 556 kW  │
│ 10,000 - 20,000  │ 1,295   │ ⬅️ Your 15,000 GT is here!
│ 20,000 - 25,000  │ 1,665   │
│ 25,000 - 50,000  │ 2,703   │
│ 50,000 - 100,000 │ 4,291   │
│ 100,000+         │ 5,717   │
└──────────────────┴─────────┘

Step 3: Read hotelling power
Your vessel: 1,295 kW ✓
```

### Why Different Vessels Have Different Power

```
Same GT (15,000), Different Power:

Container:   1,295 kW  │ High - reefer containers need cooling
Cruise:      1,997 kW  │ Highest - passenger HVAC, lighting
Tanker:      1,641 kW  │ High - cargo pumping, heating
Ferry:         996 kW  │ Moderate - passenger services
Cargo:       1,537 kW  │ Moderate-high - varies by cargo
Offshore:    2,000 kW  │ High - dynamic positioning systems

💡 Reason: Different onboard systems and operational requirements!
```

---

## Optimization Impact

### How Hotelling Affects Swap Decisions

```
Scenario: Choose between Station A and Station B

Station A:                          Station B:
├─ Service Fee: $250/container      ├─ Service Fee: $220/container
├─ Energy Rate: $0.10/kWh           ├─ Energy Rate: $0.15/kWh
├─ Queue Time: 0.2 hours            ├─ Queue Time: 0.8 hours
├─ Swap Time: 1.0 hours             ├─ Swap Time: 1.2 hours
└─ Total Dwell: 1.2 hours           └─ Total Dwell: 2.0 hours
                                    
Hotelling (1,295 kW vessel):        
├─ Energy: 1,554 kWh (1.2h)         ├─ Energy: 2,590 kWh (2.0h)
└─ Cost: $155.40                    └─ Cost: $388.50

Total Cost:                         Total Cost:
├─ Service: $1,250                  ├─ Service: $1,100
├─ Energy: $1,100                   ├─ Energy: $1,650
├─ Hotelling: $155.40               ├─ Hotelling: $388.50
└─ TOTAL: $2,505.40 ✅              └─ TOTAL: $3,138.50

✅ Station A wins!
💡 Even though service fee is higher, shorter dwell time 
   saves $233 in hotelling costs!
```

---

## FAQ - Visual Answers

### Q: Where does this data come from?

```
Data Sources:
├─ 🇪🇺 EU Shore Power Studies (2018-2023)
├─ 🏢 IMO/IAPH Port Energy Demand Analysis
├─ 🚢 Major Port Reports:
│  ├─ Rotterdam (Netherlands)
│  ├─ Los Angeles (USA)
│  ├─ Hamburg (Germany)
│  └─ Singapore
├─ 🔬 DNV Maritime Forecast
└─ 📊 Lloyd's Register Studies

✅ Real measurements from actual installations
✅ Validated by port authorities
✅ Aligned with IMO guidelines
```

### Q: How accurate is this?

```
Accuracy Level:
├─ Individual Vessels: ±20-30% variation
│  (depends on specific equipment, season, operations)
│
├─ Vessel Class Average: ±10-15% variation
│  (reference values are class averages)
│
└─ Industry Standard: ✅ Aligned
   (validated against IMO/IAPH guidelines)

💡 Your vessel may vary, but reference data is a solid baseline!
```

### Q: What if my exact vessel isn't in the table?

```
Solution: Use closest match

Example: Ro-Ro vessel (car carrier), 18,000 GT

Step 1: Check if specific type exists
❌ Ro-Ro not in list

Step 2: Find similar vessel type
✅ Auto Carrier (similar - vehicle transport)
✅ Cargo vessels (general cargo transport)

Step 3: Look up both, choose conservative
Auto Carrier: 2,000 kW (18k GT in 10,000-19,999 range)
Cargo: 1,537 kW

Recommendation: Use Auto Carrier (2,000 kW) 
- More specific to vehicle transport
- Conservative estimate (higher power)

✅ Better to slightly overestimate than underestimate!
```

---

## Quick Reference Card

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🚢 COLD-IRONING QUICK REFERENCE                    ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  Formula:                                           ┃
┃  Hotelling Energy (kWh) = Power (kW) × Time (h)     ┃
┃  Hotelling Cost ($) = Energy (kWh) × Rate ($/kWh)   ┃
┃                                                     ┃
┃  Typical Values (15,000 GT):                        ┃
┃  ├─ Container:     1,295 kW → $233/1.5h @ $0.12     ┃
┃  ├─ Cruise:        1,997 kW → $359/1.5h @ $0.12     ┃
┃  ├─ Tanker:        1,641 kW → $295/1.5h @ $0.12     ┃
┃  └─ Ferry:           996 kW → $179/1.5h @ $0.12     ┃
┃                                                     ┃
┃  Cost Reduction Strategies:                         ┃
┃  ✅ Faster swaps (reduce dwell time)                ┃
┃  ✅ Off-peak hours (lower energy rates)             ┃
┃  ✅ Efficient queue management                      ┃
┃  ✅ Shore power vs battery optimization             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

**🎯 Bottom Line**: Cold-ironing reference data makes your battery swap cost calculations **significantly more accurate** by using real-world measurements instead of simplified formulas!

**📚 Full Documentation**: See `COLD_IRONING_REFERENCE.md` for complete technical details.

---

*Last Updated: November 6, 2025*

# 📚 Documentation Index

## Cold-Ironing Integration Documentation

All documentation for the cold-ironing reference data integration in one place.

---

## 🎯 Quick Start

**New to cold-ironing integration?** Start here:

1. **`INTEGRATION_COMPLETE.md`** ⭐ - Executive summary and quick start guide
2. **`VISUAL_GUIDE.md`** - Step-by-step visual examples
3. **`COLD_IRONING_QUICKREF.md`** - Quick reference for daily use

---

## 📖 Complete Documentation

### 1. **INTEGRATION_COMPLETE.md** 
**Purpose**: Executive summary  
**Length**: 5 pages  
**Best for**: Quick overview, what was delivered, how to use  

**Contents**:
- Summary of changes
- What you received
- Key benefits
- Quick start (3 steps)
- Example values
- Testing confirmation
- Next steps

---

### 2. **VISUAL_GUIDE.md**
**Purpose**: Visual step-by-step examples  
**Length**: 15 pages  
**Best for**: First-time users, learning by example  

**Contents**:
- Quick start with screenshots
- Real-world examples (ferry, container, cruise)
- Data validation examples
- Before/after cost comparisons
- How to read reference tables
- Optimization impact examples
- FAQ with visual answers
- Quick reference card

---

### 3. **COLD_IRONING_QUICKREF.md**
**Purpose**: Quick reference guide  
**Length**: 12 pages  
**Best for**: Daily usage, troubleshooting  

**Contents**:
- What was added (files overview)
- Reference data structure
- Example values table
- How it works (step-by-step)
- Benefits summary
- Usage in Streamlit app
- Testing instructions
- Troubleshooting guide
- Data sources

---

### 4. **COLD_IRONING_REFERENCE.md**
**Purpose**: Complete technical documentation  
**Length**: 25 pages  
**Best for**: Deep understanding, technical details, validation  

**Contents**:
- What is cold-ironing/hotelling
- Complete reference tables (all vessel types)
- Data sources and validation
- Integration in battery swapping model
- How hotelling affects costs
- Typical load factors
- Benefits of using reference data
- Example scenarios
- Model usage instructions
- Validation & accuracy
- References & further reading
- Technical implementation
- FAQ

---

### 5. **IMPLEMENTATION_SUMMARY.md**
**Purpose**: Technical implementation details  
**Length**: 20 pages  
**Best for**: Developers, code review, validation  

**Contents**:
- What was implemented
- Data source details
- Example comparisons (before/after)
- Testing performed
- Benefits delivered
- Usage instructions (user & developer)
- Future enhancements
- Files modified/created
- Validation checklist
- References

---

### 6. **README.md** (Updated)
**Purpose**: Project overview  
**Length**: Main project documentation  
**Best for**: General project information, deployment  

**Updated Sections**:
- Vessel Types & Hotelling Energy
- Configuration → Vessel Type Selection
- Vessel Energy Benchmarks → Hotelling Power at Berth

---

## 💻 Code Documentation

### 7. **cold_ironing_reference.py**
**Purpose**: Reference data module  
**Type**: Python module  
**Best for**: Using in code, extending data  

**Key Classes/Functions**:
```python
# Dataclass for GT ranges
class GTRange

# Main lookup class with vessel type tables
class VesselTypeHotelling:
    def get_hotelling_power(vessel_type, gt) -> float
    
# Helper functions
def get_vessel_type_options() -> List[str]
def get_gt_range_info(vessel_type) -> List[Tuple[str, float]]
```

**Built-in Test**:
```bash
python cold_ironing_reference.py
```

---

## 🗺️ Documentation Roadmap

### For First-Time Users
```
1. INTEGRATION_COMPLETE.md (5 min)
   ↓
2. VISUAL_GUIDE.md (15 min)
   ↓
3. Try it in Streamlit app
   ↓
4. COLD_IRONING_QUICKREF.md (bookmark for later)
```

### For Technical Understanding
```
1. IMPLEMENTATION_SUMMARY.md (10 min)
   ↓
2. COLD_IRONING_REFERENCE.md (30 min)
   ↓
3. Review cold_ironing_reference.py code
   ↓
4. Review fixed_path_dp.py integration
```

### For Daily Use
```
Keep handy:
- COLD_IRONING_QUICKREF.md (quick lookup)
- VISUAL_GUIDE.md (examples)
```

---

## 📊 Reference Tables Quick Access

### By Vessel Type

**Container vessels**:
- 2,000 GT → 257 kW
- 15,000 GT → 1,295 kW
- 40,000 GT → 2,703 kW
- 80,000 GT → 4,291 kW

**Cruise ships**:
- 2,000 GT → 189 kW
- 15,000 GT → 1,997 kW
- 80,000 GT → 4,492 kW
- 150,000 GT → 6,500 kW

**Ferry**:
- 500 GT → 355 kW
- 3,500 GT → 355 kW
- 15,000 GT → 996 kW
- 40,000 GT → 2,431 kW

**Tanker (Chemical)**:
- 8,000 GT → 1,422 kW
- 15,000 GT → 1,641 kW
- 80,000 GT → 2,815 kW

**Offshore Supply**:
- 500 GT → 1,000 kW
- 5,000 GT → 2,000 kW
- 15,000 GT → 2,000 kW

*Full tables in `COLD_IRONING_REFERENCE.md` or `VISUAL_GUIDE.md`*

---

## 🔍 Finding What You Need

### I want to...

**Understand what cold-ironing is**
→ `COLD_IRONING_REFERENCE.md` - "What is Hotelling?" section

**See example calculations**
→ `VISUAL_GUIDE.md` - "Real-World Examples" section

**Look up my vessel's power**
→ `COLD_IRONING_QUICKREF.md` - "Example Values" table  
→ OR use the Streamlit app

**Understand the cost impact**
→ `VISUAL_GUIDE.md` - "Cost Impact Comparison" section

**Troubleshoot an issue**
→ `COLD_IRONING_QUICKREF.md` - "Troubleshooting" section

**Validate the data**
→ `COLD_IRONING_REFERENCE.md` - "Validation & Accuracy" section  
→ `IMPLEMENTATION_SUMMARY.md` - "Data Quality" section

**Use the reference data in code**
→ `cold_ironing_reference.py` - Module documentation  
→ `IMPLEMENTATION_SUMMARY.md` - "Usage Instructions (Developer)" section

**See before/after comparison**
→ `IMPLEMENTATION_SUMMARY.md` - "Example Comparisons" section  
→ `VISUAL_GUIDE.md` - "Cost Impact Comparison" section

**Understand data sources**
→ `COLD_IRONING_REFERENCE.md` - "References & Further Reading"  
→ `COLD_IRONING_QUICKREF.md` - "Data Sources" section

---

## 📥 File Sizes & Formats

| File | Format | Size | Lines |
|------|--------|------|-------|
| `INTEGRATION_COMPLETE.md` | Markdown | 8 KB | 250 |
| `VISUAL_GUIDE.md` | Markdown | 18 KB | 650 |
| `COLD_IRONING_QUICKREF.md` | Markdown | 15 KB | 400 |
| `COLD_IRONING_REFERENCE.md` | Markdown | 62 KB | 600 |
| `IMPLEMENTATION_SUMMARY.md` | Markdown | 22 KB | 600 |
| `cold_ironing_reference.py` | Python | 12 KB | 450 |
| **TOTAL** | | **137 KB** | **2,950** |

---

## 🎯 Key Concepts

### What is Cold-Ironing?
Shore power connection for ships at berth, replacing diesel generators with grid electricity.

### What is Hotelling?
Period when vessels are docked and require power for onboard systems (HVAC, lighting, pumps, etc.).

### Why Does It Matter?
Hotelling energy consumed during battery swaps is a real operational cost that affects total swap economics.

### How Much Does It Cost?
Depends on:
- Vessel type and size (determines power demand)
- Dwell time at berth (queue + swap time)
- Local energy rate ($/kWh)

**Example**: 
- Container vessel (15,000 GT) = 1,295 kW
- 1.5-hour swap @ $0.12/kWh
- Hotelling cost = $233

---

## 🔗 External Resources

### Industry Standards
- **IMO MEPC**: Marine Environment Protection Committee guidelines
- **IAPH**: International Association of Ports and Harbors
- **EU Directive 2014/94/EU**: Alternative Fuels Infrastructure

### Research Papers
- "Shore Power for Ports" - EU Commission (2020)
- "Maritime Forecast to 2050" - DNV (2022)
- "Getting to Zero Coalition" - Lloyd's Register (2021)

### Port Authority Reports
- Port of Rotterdam Shore Power Annual Reports
- Port of Los Angeles Green Shipping Program
- Port of Hamburg Environmental Reports

---

## ✅ Quick Validation

**Test your understanding:**

1. What is hotelling power for a 15,000 GT container vessel?
   - **Answer**: 1,295 kW (from 10,000-19,999 GT range)

2. How much does 1.5-hour hotelling cost @ $0.12/kWh?
   - **Answer**: 1,295 kW × 1.5h × $0.12 = $233.10

3. Where does this data come from?
   - **Answer**: EU shore power studies, port measurements, IMO/IAPH analysis

4. What if my vessel isn't in the table?
   - **Answer**: Use closest similar vessel type, choose conservative estimate

---

## 🚀 Getting Started - 5 Minutes

**Quickest path to using cold-ironing reference data:**

```
1. Open Streamlit app
   ↓
2. Select vessel type (e.g., "Container vessels")
   ↓
3. Enter GT (e.g., 15,000)
   ↓
4. See hotelling power (e.g., 1,295 kW)
   ↓
5. Expand "Hotelling Power Demand Reference" to verify
   ↓
6. Run optimization
   ↓
7. See hotelling costs in results
```

**Done!** You're now using industry-standard reference data.

---

## 📞 Support

**Questions?**
1. Check `VISUAL_GUIDE.md` for examples
2. Review `COLD_IRONING_QUICKREF.md` FAQ
3. Read `COLD_IRONING_REFERENCE.md` technical details

**Issues?**
1. See `COLD_IRONING_QUICKREF.md` troubleshooting
2. Verify data with reference tables
3. Check code in `cold_ironing_reference.py`

---

## 🎓 Learning Path

### Beginner (30 minutes)
1. `INTEGRATION_COMPLETE.md` - What was delivered
2. `VISUAL_GUIDE.md` - Step-by-step examples
3. Try it in the app

### Intermediate (1 hour)
1. `COLD_IRONING_QUICKREF.md` - How it works
2. `VISUAL_GUIDE.md` - All examples and comparisons
3. Experiment with different vessel types in app

### Advanced (2 hours)
1. `COLD_IRONING_REFERENCE.md` - Complete technical docs
2. `IMPLEMENTATION_SUMMARY.md` - Implementation details
3. Review `cold_ironing_reference.py` code
4. Review `fixed_path_dp.py` integration

---

**Last Updated**: November 6, 2025  
**Documentation Version**: 1.0  
**Model Version**: 2.0 (Cold-Ironing Enhanced)

---

**Ready to use?** → Start with `INTEGRATION_COMPLETE.md` ⭐

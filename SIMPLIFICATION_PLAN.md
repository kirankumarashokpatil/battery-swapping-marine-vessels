# Global Parameters Simplification Plan

## Current Issues
- Multiple redundant sections: "Vessel & Battery Specifications", "Boat Configuration", "Battery Configuration", "Battery System Analysis"
- Repetitive parameters spread across different sections
- Too many nested expanders with complex calculations
- Information overload for users

## Proposed Simplified Structure

###  🚢 Vessel Configuration (Main Inputs)
- Vessel GT
- Boat Speed
- Energy Consumption (kWh/NM)  
- Departure Time

### 🔋 Battery System (Main Inputs)
- Battery Chemistry (dropdown: LFP, NMC, LTO)
- Energy Density (auto-filled based on chemistry, with slider to adjust)
- Container Capacity (kWh per container)
- Number of Containers
- Minimum SoC %
- Initial SoC %
- SoC Precision

### 💰 Cost Settings  
- Time Cost ($/hr)
- (Energy costs moved to station-specific settings)

### 📊 System Analysis (Auto-calculated Display Only)
- Battery Weight
- Weight/GT Ratio
- Maximum Range
- Usable Range

### 📖 Reference Information (Collapsed Expanders)
- Vessel Type Benchmarks (simplified table)
- Battery Chemistry Comparison (simplified table)
- Battery Calculator (optional tool)

## Benefits
1. **Clearer Structure**: Logical grouping of inputs vs outputs
2. **Less Repetition**: Single location for each parameter
3. **Faster Setup**: Essential parameters upfront, details in expanders
4. **Better UX**: Users see what they need to configure immediately

## Implementation Steps
1. Consolidate vessel parameters (GT, speed, consumption, time) into one section
2. Consolidate battery parameters (chemistry, capacity, SoC) into one section
3. Move all calculations to a single "System Analysis" display section
4. Collapse verbose reference information into simple expanders
5. Remove duplicate chemistry selection and vessel type discussions
6. Remove redundant calculators (keep one simplified version if needed)

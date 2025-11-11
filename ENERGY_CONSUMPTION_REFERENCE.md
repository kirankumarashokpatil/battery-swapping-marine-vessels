# Energy Consumption Reference for Electric Vessels

## Overview

Energy consumption per nautical mile (kWh/NM) for each vessel type is calculated by dividing the vessel's typical operational energy use by the distance traveled in a representative mission or route. This lets you compare the efficiency and battery demands across various vessel types and battery chemistries.

---

## Step-by-Step Calculation

- **1. Estimate Total Energy Use:** Use the vessel's typical battery capacity required for a full operational cycle (from practical examples or engineering design studies).[1][2]
- **2. Obtain Typical Route Distance:** Reference standard route lengths for the vessel's operation (e.g., ferry crossing, tug maneuver session).
- **3. Divide Energy by Distance:** Energy consumed per NM = Total Energy Consumed for the trip (kWh) ÷ Distance traveled (NM).

---

## Vessel Examples: Battery Consumed per Nautical Mile

| Vessel Type              | Typical Battery Capacity (kWh) | Typical Route (NM) | Energy Consumption (kWh/NM) | Notes |
|--------------------------|-------------------------------|---------------------|-----------------------------|-------|
| Small electric ferry (Ampere)        | 1,000–1,200 [3]         | 10–12                | 83–100                      | Short, predictable route; frequent shore charging [3][1]  |
| Harbor Tug (Damen RSD-E Tug)         | 2,800 [3]               | 8–12                  | 233–350                     | High peak loads, port maneuvering, energy per NM varies by duty cycle [2] |
| Coastal car/passenger ferry           | 6,000–8,000 [3]         | 30–40                 | 200–267                     | Medium-length routes, faster average speed, more hotel loads [1][2] |
| Offshore support vessel (hybrid)      | 5,000–7,000 [3]         | 50–70                 | 100–140                     | Uses battery during DP/low-load operations; varies with hybrid operation [2] |
| Medium cruise/RoPax ferry (hybrid)    | 10,000–20,000 [3]       | 80–100                | 125–200                     | Batteries cover peak loads and zero-emission port entry [1][3] |
| Inland cargo vessel (electric hybrid) | 3,000–5,000 [3]         | 100–130               | 30–50                       | Steady operations, low variability, optimized for shore charging [3] |

---

## How These Values Are Used

These energy consumption figures (kWh/NM) are essential for:
- **Sizing batteries** for fuel/electric hybrid or full-electric operation.
- **Estimating charging requirements** at ports or during service intervals.
- **Benchmarking efficiency** and comparing operational costs across vessel types and battery chemistries.[2][3][1]

Actual values can vary based on speed, weather, hull condition, and duties (e.g., propulsion versus auxiliary loads). Engineers always use route-specific and duty-specific energy logs to refine these estimates for each vessel class.[1][2]

---

## Containerized Battery Systems for Marine Vessels

### Overview

Modern marine battery swapping systems use **modular, containerized battery packs** designed for rapid portside handling and exchange. These systems enable quick turnaround times for vessels and standardized infrastructure across multiple ports.[4]

### Standard Battery Container Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Energy Capacity per Container** | 1.96 MWh (1,960 kWh) | Modular design for scalability [4] |
| **Physical Dimensions** | 20-foot ISO container | Standard shipping container format |
| | Length: 6.06 m | Facilitates standard handling equipment |
| | Width: 2.44 m | Compatible with existing port infrastructure |
| | Height: 2.59 m | |
| **Weight (LFP Chemistry)** | ~19.6 tonnes | Based on ~100 Wh/kg energy density |
| | (19,600 kg) | Conservative estimate for marine safety |
| **Weight (NMC Chemistry)** | ~9.8–13.1 tonnes | Based on ~150-200 Wh/kg energy density |
| | (9,800–13,066 kg) | Higher energy density, lighter weight |

### Weight Calculation Example

For **LFP (Lithium Iron Phosphate)** chemistry at ~100 Wh/kg:

$$
\text{Weight} = \frac{1,960,000\, \text{Wh}}{100\, \text{Wh/kg}} = 19,600\, \text{kg} = 19.6\, \text{tonnes}
$$

For **NMC (Lithium Nickel Manganese Cobalt)** chemistry at ~150-200 Wh/kg:

$$
\text{Weight} = \frac{1,960,000\, \text{Wh}}{150-200\, \text{Wh/kg}} = 9,800-13,066\, \text{kg} = 9.8-13.1\, \text{tonnes}
$$

### Practical Implementation

**Example Route Configuration:**
- **Route A (Longest Leg)**: 12 battery containers
- **Total Capacity**: 12 × 1.96 MWh = **23.52 MWh (23,520 kWh)**
- **Total Weight (LFP)**: 12 × 19.6 tonnes = **235.2 tonnes**
- **Total Weight (NMC)**: 12 × 10-13 tonnes = **120-156 tonnes**

### Benefits of Containerized Systems

1. **Rapid Swapping**: Standard handling equipment (cranes, forklifts) can exchange containers quickly
2. **Modularity**: Vessels can carry different numbers of containers based on route requirements
3. **Infrastructure Standardization**: Same container format works across multiple ports
4. **Maintenance Flexibility**: Containers can be serviced offline while vessel continues operations
5. **Scalability**: Easy to upgrade capacity by adding more containers

### Application to Battery Swapping Model

When modeling containerized battery swapping:

- **Swap Time**: 0.5-1.0 hours per container (depending on handling equipment)
- **Swap Cost**: Based on container rental/purchase + energy cost
  - Energy cost: 1,960 kWh × $0.12/kWh = **$235 per container**
  - Container amortization: Variable based on ownership model
  - **Typical swap cost**: $150-300 per container

- **Multiple Container Swaps**: For vessels requiring multiple containers, total swap time and cost scale linearly or with slight economies of scale

---

## References

1. [How to Calculate Vessel Fuel Consumption](https://perfomax.io/how-to-calculate-vessel-fuel-consumption/)
2. [Ship Fuel Consumption - Handybulk](https://www.handybulk.com/ship-fuel-consumption/)
3. [Electric Ships: The World's Top Five Projects by Battery Capacity](https://www.ship-technology.com/features/electric-ships-the-world-top-five-projects-by-battery-capacity/)
4. Marine Battery Containerization Case Study - Modular Battery Systems for Long-Range Routes

---

## Application to Current Model

The current model in `fixed_path_dp.py` uses simplified energy consumption calculations. For more realistic vessel modeling, consider:

### Current Implementation
```python
def calculate_energy_consumption(
    distance_km: float,
    current_kmh: float,
    boat_speed_kmh: float = 18.0,
    base_consumption_per_km: float = 3.0,
) -> float:
    base_energy = distance_km * base_consumption_per_km
    multiplier = 1.25 if current_kmh < 0 else 0.75
    return base_energy * multiplier
```

### Recommendations for Enhancement

1. **Use vessel-specific energy consumption rates** from the table above
2. **Convert distances** from kilometers to nautical miles (1 NM ≈ 1.852 km)
3. **Account for operational modes**:
   - Base propulsion loads
   - Hotel/auxiliary loads
   - Peak power requirements
   - Weather and sea state impacts

### Example: Harbor Tug Model
For a harbor tug with 2,800 kWh battery capacity operating an 8-12 NM route:
- Energy consumption: 233–350 kWh/NM
- Recommended battery capacity: 2,800 kWh (covers full route with margin)
- Minimum SoC: 20% (560 kWh reserve)
- Energy per km: ~126-189 kWh/km (after NM conversion)

This would translate to a `base_consumption_per_km` value of approximately **126-189 kWh/km** for harbor tug operations, significantly higher than the current placeholder value of 3.0 kWh/km.

# 🚢 Riverboat Battery Swapping Optimizer

An advanced optimization tool for planning battery swap strategies for electric marine vessels operating on fixed routes. The app uses dynamic programming to find the cost-optimal battery swap schedule while considering energy consumption, hotelling power demand, station operating hours, and various pricing models.

## ✨ Key Features

### 🔋 **Vessel Types & Hotelling Energy**

 - Background: This repository implements a DP model to schedule battery-swaps and charging for marine vessels.
 - New: Station-level background charging support between visits (see BACKGROUND_CHARGING.md for details).
- **Service fees** per battery container swap
### 🗺️ **Route & Battery Management**
- **Partial swap support**: Swap only depleted battery containers (cost optimization)
- **Full swap mode**: Replace entire battery set (standard practice)
- **Modular battery containers**: Configurable 20-foot ISO battery containers (default 1960 kWh each)
- **River current modeling**: Upstream (harder) and downstream (easier) flow adjustments to energy consumption
- **Operating hours constraints**: Station-specific hours with automatic wait time calculation
- **Battery stock limits**: Track available charged batteries at each station

### 📊 **Advanced Analytics**
- **Journey summary**: Total cost, time, arrival time, number of swaps
- **SoC profile visualization**: State of charge across all stations
- **Energy balance analysis**: Per-segment energy consumption and cumulative tracking
- **Cost structure breakdown**: Container services, energy charging, hotelling, fees, surcharges
- **Segment-by-segment analysis**: Energy efficiency metrics, flow impact, swap decisions

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.10+
- pip

### Run Locally

```powershell
# Clone or navigate to repository
cd "c:\Users\kiran\OneDrive\Documents\Natpower UK\Battery Swapping Model for Marine Vessels"

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run streamlit_app/main.py
```

Then open http://localhost:8501 in your browser.

## 🐳 Docker Deployment

### Build and Run with Docker

```powershell
# Build the Docker image
docker build -t riverboat-app .

# Run the container
docker run --rm -p 8501:8501 --name riverboat-app-instance riverboat-app
```

Access the app at http://localhost:8501

### Run on Custom Port

```powershell
# Map to port 8080 on your host
docker run --rm -p 8080:8501 riverboat-app
```

Access at http://localhost:8080

## ☁️ Cloud Deployment Options

### Option 1: Google Cloud Run (Serverless)
```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/riverboat-app

# Deploy to Cloud Run
gcloud run deploy riverboat-app \
  --image gcr.io/YOUR_PROJECT_ID/riverboat-app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Note**: Cloud Run expects apps to listen on `$PORT` (Cloud Run sets this dynamically). To adapt, modify the Dockerfile CMD:
```dockerfile
CMD ["sh", "-c", "streamlit run streamlit_app/main.py --server.port ${PORT:-8501} --server.address 0.0.0.0"]
```

### Option 2: AWS ECS / Fargate
1. Push image to Amazon ECR
2. Create ECS task definition with 1-2 vCPUs, 2-4 GB RAM
3. Create ECS service with load balancer
4. Configure ALB to route traffic to port 8501
5. Set up TLS certificate via AWS Certificate Manager

### Option 3: Azure Container Instances
```bash
# Login to Azure
az login

# Create resource group
az group create --name riverboat-rg --location eastus

# Deploy container
az container create \
  --resource-group riverboat-rg \
  --name riverboat-app \
  --image YOUR_REGISTRY/riverboat-app:latest \
  --dns-name-label riverboat-app \
  --ports 8501
```

### Option 4: Render / Fly.io / Railway
These platforms support Docker directly:

**Render**:
1. Connect GitHub repository
2. Select "Web Service"
3. Choose "Docker"
4. Render auto-detects Dockerfile and deploys

**Fly.io**:
```bash
fly launch
fly deploy
```

**Railway**:
1. Connect GitHub repo
2. Railway auto-deploys on push to main

### Option 5: VPS (DigitalOcean, Linode, AWS EC2)
```bash
# Install Docker on VPS
# Copy files to VPS
# Build and run container
docker-compose up -d  # if using docker-compose

# Set up reverse proxy (nginx) with TLS
# Example nginx config:
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }
}
```

## 🌐 Deployment Requirements

| Requirement | Details |
|------------|---------|
| **Container** | Docker image built from Dockerfile |
| **Port** | 8501 (customizable via env vars) |
| **Memory** | 1-2 GB minimum (scale to 4 GB for heavy concurrent use) |
| **CPU** | 1 vCPU minimum (scale to 2+ for better performance) |
| **Domain & DNS** | Point A/CNAME record to hosting IP or platform endpoint |
| **TLS/SSL** | Use Let's Encrypt (certbot) or platform-managed TLS |
| **Environment Vars** | None required currently (future: API keys, DB credentials) |
| **Health Check** | HTTP GET to port 8501 (Streamlit auto-responds) |
| **Logging** | Docker stdout/stderr (use platform logs or centralized logging) |

## 🔧 Configuration

### Vessel Type Selection
Choose from 10+ vessel categories with **actual cold-ironing reference data**:

| Vessel Type | GT Range Examples | Hotelling Power Examples |
|-------------|-------------------|--------------------------|
| **Container vessels** | 2,000 GT: 257 kW | 15,000 GT: 1,295 kW | 60,000 GT: 4,291 kW |
| **Cruise ships** | 80,000 GT: 4,492 kW | 150,000 GT: 6,500 kW |
| **Auto Carrier** | 15,000 GT: 2,000 kW | 40,000 GT: 5,000 kW |
| **Chemical Tankers** | 10,000 GT: 1,641 kW | 80,000 GT: 2,815 kW |
| **Cargo vessels** | 3,000 GT: 1,091 kW | 15,000 GT: 1,537 kW |
| **Crude oil tanker** | 15,000 GT: 2,624 kW | 80,000 GT: 1,328 kW |
| **Ferry** | 3,500 GT: 355 kW | 30,000 GT: 2,431 kW |
| **Offshore Supply** | 500 GT: 1,000 kW | 15,000 GT: 2,000 kW |
| **Service Vessels** | 500 GT: 382 kW | 15,000 GT: 2,383 kW |
| **Other** | Any GT: 200 kW (default) |

**Data Source**: Cold-ironing (shore power) measurements from major ports worldwide
- Port of Rotterdam, Los Angeles, Hamburg, Singapore
- EU Shore Power Studies (2018-2023)
- IMO/IAPH Port Energy Demand Analysis

See `COLD_IRONING_REFERENCE.md` for complete documentation.

### Battery Configuration
- **Battery Chemistry**: LFP (120 Wh/kg), NMC (200 Wh/kg), LTO (90 Wh/kg)
- **Container Capacity**: 100-5000 kWh per container (default: 1960 kWh)
- **Number of Containers**: 1-20 containers
- **Total Capacity**: Automatically calculated
- **Minimum SoC**: Reserve battery percentage (typically 20%)

### Pricing Model
Configure per-station pricing components:
- **Swap Cost**: Physical handling fee per container ($180-$320 typical)
- **Energy Cost**: $/kWh at station (e.g., $0.09 Guangzhou, $0.18 Hong Kong)
- **Base Service Fee**: Fixed fee per transaction
- **Location Premium**: Strategic port surcharge
- **Degradation Fee**: Battery wear cost per kWh
- **Peak Hour Multiplier**: Surge pricing during peak hours
- **Subscription Discount**: Percentage discount for members

## 📈 Understanding Results

### Journey Summary
- **Total Cost**: All costs (swaps + time + hotelling)
- **Travel Time**: Including swaps, queues, and waiting
- **Arrival Time**: Clock time when journey completes
- **Battery Swaps**: Number of swap operations

### Swap Breakdown
For each swap station:
- **Mode**: Partial (some containers) or Full Set (all containers)
- **Returned SoC**: Battery charge when arriving
- **Energy Charged**: kWh needed to reach 100%
- **Hotelling**: Energy for onboard services during dwell
- **Total Cost**: All fees + energy + hotelling

### Cost Structure
- **Container Service**: Physical swap handling
- **Energy Charging**: Electricity for battery recharge
- **Hotelling Energy**: Onboard auxiliary systems during berth
- **Base Fees, Location Premiums, Degradation**: Additional charges
- **Peak Surcharges**: Time-of-day pricing
- **Discounts**: Subscription savings

## 📊 Vessel Energy Benchmarks

### Propulsion Energy (kWh/NM)
| Vessel Type | kWh/NM | Notes |
|------------|--------|-------|
| Small Ferry | 83-100 | Short routes, frequent charging |
| Harbor Tug | 233-350 | High peak loads, maneuvering |
| Coastal Ferry | 200-267 | Medium routes, faster speeds |
| Inland Cargo | 30-50 | Steady operations, optimized |

### Hotelling Power at Berth (Cold-Ironing Data)

**Industry-Standard Reference Values** (measured from actual shore power installations):

| Vessel Type | Small Vessels | Medium Vessels | Large Vessels | Very Large Vessels |
|-------------|---------------|----------------|---------------|--------------------|
| **Container** | 257 kW (2,000 GT) | 1,295 kW (15,000 GT) | 2,703 kW (40,000 GT) | 5,717 kW (150,000 GT) |
| **Cruise** | 189 kW (2,000 GT) | 1,997 kW (15,000 GT) | 4,492 kW (80,000 GT) | 6,500 kW (150,000 GT) |
| **Tanker** | — | 1,641 kW (10,000 GT) | 2,815 kW (80,000 GT) | 3,000 kW (150,000 GT) |
| **Ferry** | 355 kW (3,500 GT) | 996 kW (15,000 GT) | 2,888 kW (80,000 GT) | 2,900 kW (150,000 GT) |
| **Offshore** | 1,000 kW (500 GT) | 2,000 kW (all ranges) | — | — |

**What is Cold-Ironing?**
Cold-ironing (shore power) is when ships connect to the electrical grid while at berth instead of running auxiliary diesel generators. The power values above represent measured average hotelling demand for onboard systems (HVAC, lighting, pumps, refrigeration, etc.).

**Complete Reference**: See `COLD_IRONING_REFERENCE.md` for:
- Full GT range tables for all 10 vessel types
- Data sources and validation methodology
- How hotelling costs affect swap strategy
- Example calculations and scenarios

## 🛠️ Advanced Features

### Partial Swap Optimization
When enabled at a station, the optimizer can swap only the depleted battery containers instead of the entire set, reducing costs when some containers still have charge.

### Peak Hour Pricing
Define peak hours (e.g., 8:00-18:00) at each station with surge multipliers (e.g., 1.2× during peak).

### Operating Hours Constraints
The optimizer automatically schedules swaps within station operating hours or calculates wait time if arriving outside hours.

### River Flow Modeling
- **Upstream** (negative current): 1.2× energy consumption
- **Downstream** (positive current): 0.8× energy consumption

## 🔒 Security & Best Practices

- Use TLS/HTTPS for all production deployments
- Keep dependencies updated: `pip list --outdated`
- Pin specific versions after testing: `pip freeze > requirements.txt`
- Use environment variables for secrets (future: API keys, DB credentials)
- Enable rate limiting and DDoS protection at reverse proxy or platform level
- Regular backups of configuration JSON files

## 📝 Exporting Results

The app provides three export formats:
1. **Journey Plan (CSV)**: Detailed step-by-step schedule
2. **Scenario (JSON)**: Complete configuration for reproducibility
3. **Summary (TXT)**: High-level overview report

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Additional vessel types and energy profiles
- More sophisticated pricing models
- Multi-objective optimization (cost + time + emissions)
- Historical data integration
- Real-time weather/current APIs
- Battery degradation modeling over lifetime

## 📄 License

[Add your license here]

## 📧 Contact

[Add contact information]

---

**Built with**: Python, Streamlit, Dynamic Programming
**Data Sources**: EU shore power studies, ICCT maritime reports, UK port energy analysis

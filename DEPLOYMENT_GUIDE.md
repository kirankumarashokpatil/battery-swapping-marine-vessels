# Deployment Guide - Marine Vessel Battery Swapping Optimizer

## Essential Files for Deployment

### 🔴 **CRITICAL FILES** (Must Include)

#### 1. **Core Application**
```
streamlit_app/
  └── main.py                    # Main Streamlit web application
fixed_path_dp.py                 # Core optimization engine with diagnostics
requirements.txt                 # Python dependencies
```

#### 2. **Optional Reference Files** (Recommended for vessel specs)
```
cold_ironing_reference.py        # Vessel energy consumption calculations
```

#### 3. **Deployment Configuration**
```
Dockerfile                       # Docker container configuration
.dockerignore                    # (create if needed) Files to exclude from Docker build
```

---

## 📦 **Minimum Deployment Package**

For a working deployment, you need **only these 4 files**:

1. `streamlit_app/main.py` - Web interface
2. `fixed_path_dp.py` - Optimization engine
3. `requirements.txt` - Dependencies
4. `cold_ironing_reference.py` - Vessel calculations (optional but recommended)

**Total size**: ~150 KB (excluding dependencies)

---

## 🚫 **Files NOT Needed for Deployment**

### Documentation (Keep for Reference, Don't Deploy)
- ✖️ `*.md` files (README, guides, documentation)
- ✖️ `BEFORE_AFTER_COMPARISON.md`
- ✖️ `COLD_IRONING_QUICKREF.md`
- ✖️ `CONSTRAINT_DIAGNOSTICS.md`
- ✖️ `DOCUMENTATION_INDEX.md`
- ✖️ `ENERGY_CONSUMPTION_REFERENCE.md`
- ✖️ `HYBRID_PRICING_MODEL.md`
- ✖️ `IMPLEMENTATION_SUMMARY.md`
- ✖️ `INTEGRATION_COMPLETE.md`
- ✖️ `PRICING_QUICKSTART.md`
- ✖️ `SIMPLIFICATION_PLAN.md`
- ✖️ `SOC_BASED_BILLING.md`
- ✖️ `SOC_BILLING_QUICK_REF.md`
- ✖️ `UI_CLARITY_IMPROVEMENTS.md`
- ✖️ `VISUAL_GUIDE.md`

### Test Files (Don't Deploy)
- ✖️ `test_diagnostics.py`
- ✖️ `test_partial_swap.py`
- ✖️ `test_simple_diagnostic.py`

### Build Artifacts (Don't Deploy)
- ✖️ `__pycache__/` folders
- ✖️ `.venv/` virtual environment
- ✖️ `*.pyc` compiled Python files
- ✖️ `*.zip` archives

---

## 📁 **Recommended Deployment Structure**

```
deployment/
├── streamlit_app/
│   └── main.py
├── fixed_path_dp.py
├── cold_ironing_reference.py
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

---

## 🐳 **Docker Deployment** (Recommended)

### Step 1: Create `.dockerignore`

Create this file to exclude unnecessary files from Docker build:

```dockerignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/

# Testing
test_*.py

# Documentation
*.md
!README.md

# Archives
*.zip

# IDE
.vscode/
.idea/
*.swp
*.swo
```

### Step 2: Build Docker Image

```bash
# From the project root directory
docker build -t marine-battery-optimizer .
```

### Step 3: Run Container

```bash
# Run on port 8501
docker run -p 8501:8501 marine-battery-optimizer

# Or with custom port
docker run -p 8080:8501 marine-battery-optimizer
```

### Step 4: Access Application

Open browser to: `http://localhost:8501`

---

## ☁️ **Cloud Deployment Options**

### Option 1: Streamlit Cloud (Easiest)

1. **Push to GitHub**
   ```bash
   git init
   git add streamlit_app/ fixed_path_dp.py cold_ironing_reference.py requirements.txt
   git commit -m "Initial deployment"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to https://streamlit.io/cloud
   - Connect your GitHub repo
   - Set main file: `streamlit_app/main.py`
   - Deploy! ✨

**Pros**: Free, automatic updates, managed hosting
**Cons**: Limited resources, public by default

---

### Option 2: AWS/Azure/GCP (Production)

#### AWS (Elastic Container Service)

```bash
# 1. Build and tag
docker build -t marine-battery-optimizer .
docker tag marine-battery-optimizer:latest <your-ecr-repo>:latest

# 2. Push to ECR
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <ecr-url>
docker push <your-ecr-repo>:latest

# 3. Deploy to ECS
# (Configure ECS task definition and service via AWS Console)
```

#### Azure (Container Instances)

```bash
# 1. Login to Azure
az login

# 2. Create container registry
az acr create --resource-group <rg> --name <registry-name> --sku Basic

# 3. Build and push
az acr build --registry <registry-name> --image marine-battery-optimizer:latest .

# 4. Deploy container
az container create \
  --resource-group <rg> \
  --name battery-optimizer \
  --image <registry-name>.azurecr.io/marine-battery-optimizer:latest \
  --dns-name-label battery-optimizer \
  --ports 8501
```

#### Google Cloud (Cloud Run)

```bash
# 1. Build and submit
gcloud builds submit --tag gcr.io/<project-id>/marine-battery-optimizer

# 2. Deploy
gcloud run deploy battery-optimizer \
  --image gcr.io/<project-id>/marine-battery-optimizer \
  --platform managed \
  --port 8501 \
  --allow-unauthenticated
```

---

### Option 3: Heroku (Simple)

1. **Create `Procfile`:**
   ```
   web: streamlit run streamlit_app/main.py --server.port $PORT --server.address 0.0.0.0
   ```

2. **Deploy:**
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   ```

---

## 🔧 **Environment Variables** (Optional)

For production deployments, you may want to set:

```bash
# Performance
STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200  # MB
STREAMLIT_SERVER_ENABLE_CORS=false

# Security
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true

# Logging
STREAMLIT_LOGGER_LEVEL=info
```

---

## 📊 **Resource Requirements**

### Minimum
- **CPU**: 1 vCPU
- **RAM**: 512 MB
- **Storage**: 500 MB

### Recommended (for production)
- **CPU**: 2 vCPU
- **RAM**: 2 GB
- **Storage**: 1 GB

### Notes
- Optimization typically takes < 1 second for routes with 5-10 stations
- Memory scales with route complexity (number of stations × SoC discretization)
- Each user session is isolated (multi-user safe)

---

## 🔐 **Security Considerations**

### For Public Deployment

1. **Add Authentication** (if needed)
   - Use Streamlit's built-in authentication
   - Or deploy behind a reverse proxy (nginx) with basic auth

2. **Rate Limiting**
   - Implement to prevent abuse
   - Use cloud provider's API gateway

3. **Input Validation**
   - Already included in the app
   - Additional validation in `FixedPathInputs.__post_init__()`

4. **HTTPS**
   - Most cloud providers handle this automatically
   - For custom deployments, use Let's Encrypt + nginx

---

## 🧪 **Pre-Deployment Testing**

Before deploying, test locally:

```bash
# 1. Create clean virtual environment
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run locally
streamlit run streamlit_app/main.py

# 4. Test scenarios
# - Try the default example
# - Test infeasible scenario (verify diagnostics work)
# - Test charging/swap/hybrid operations
```

---

## 📦 **Creating Deployment Package**

To create a clean deployment package:

```bash
# Create deployment directory
mkdir deployment
cd deployment

# Copy essential files
cp ../streamlit_app/main.py streamlit_app/
cp ../fixed_path_dp.py .
cp ../cold_ironing_reference.py .
cp ../requirements.txt .
cp ../Dockerfile .

# Optional: Add README
cp ../README.md .

# Create archive
zip -r marine-battery-optimizer.zip .
```

---

## 🚀 **Quick Start Commands**

### Local Deployment
```bash
pip install -r requirements.txt
streamlit run streamlit_app/main.py
```

### Docker Deployment
```bash
docker build -t battery-optimizer .
docker run -p 8501:8501 battery-optimizer
```

### Streamlit Cloud
```bash
git add streamlit_app/main.py fixed_path_dp.py cold_ironing_reference.py requirements.txt
git commit -m "Deploy to Streamlit Cloud"
git push
# Then deploy via streamlit.io/cloud interface
```

---

## ✅ **Deployment Checklist**

- [ ] Essential files copied (`main.py`, `fixed_path_dp.py`, `requirements.txt`)
- [ ] `.dockerignore` created (if using Docker)
- [ ] Test files excluded
- [ ] Documentation files excluded (optional)
- [ ] `__pycache__` excluded
- [ ] Local testing completed
- [ ] Docker image builds successfully
- [ ] Container runs without errors
- [ ] Application accessible via browser
- [ ] Test optimization with sample data
- [ ] Test constraint diagnostics with infeasible scenario
- [ ] Environment variables configured (if needed)
- [ ] HTTPS enabled (for production)
- [ ] Monitoring/logging configured (optional)

---

## 📞 **Support & Maintenance**

### Updating the Deployment

```bash
# 1. Pull latest changes
git pull

# 2. Rebuild Docker image
docker build -t battery-optimizer:latest .

# 3. Stop old container
docker stop <container-id>

# 4. Start new container
docker run -p 8501:8501 battery-optimizer:latest
```

### Monitoring

- Check application logs: `docker logs <container-id>`
- Monitor resource usage: `docker stats <container-id>`
- Streamlit provides built-in analytics in the menu

---

## 🎯 **Summary**

**Minimum deployment requires just 3-4 files:**
1. ✅ `streamlit_app/main.py`
2. ✅ `fixed_path_dp.py`
3. ✅ `requirements.txt`
4. ✅ `cold_ironing_reference.py` (optional but recommended)

**Total package size**: ~150 KB (excluding Python dependencies)

**Deployment time**: 5-10 minutes using Docker or Streamlit Cloud

The application is production-ready with:
- ✅ Comprehensive error handling
- ✅ Constraint violation diagnostics
- ✅ Input validation
- ✅ Multi-user support
- ✅ Responsive UI
- ✅ Flexible charging + hybrid operations

# Quick Start Guide

Get up and running in 5 minutes!

## ✅ **YES, You Can Test Without Docker First!**

Testing locally is **recommended** before using Docker. It's faster and easier to debug.

---

## 🚀 **Option 1: Test Locally (Recommended First)**

### **1. Install Dependencies** (2 minutes)

```bash
cd /home/mir/projects/release-notes-ingestion

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### **2. Configure** (2 minutes)

```bash
# Copy and edit .env
cp .env.example .env
nano .env

# Fill in these required fields:
# - R2_ENDPOINT, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET_NAME
# - QDRANT_HOST (already set: 192.168.254.22)
# - OLLAMA_HOST (already set: 192.168.254.22)
# - DOCLING_BASE_URL (already set: http://192.168.254.22:5010)
```

### **3. Test** (1 minute)

```bash
# Test configuration
python src/components/config.py

# Test API server
python api/main.py

# In another terminal:
curl http://localhost:8060/health
```

**✅ Success!** API is running on `http://localhost:8060`

---

## 🐳 **Option 2: Use Docker**

### **1. Configure** (1 minute)

```bash
# Make sure .env is configured
cat .env
```

### **2. Build & Run** (3 minutes)

```bash
# Build and start
docker-compose up -d

# Check status
docker ps

# Test API
curl http://localhost:8060/health
```

**✅ Success!** Container is running on port `8060`

---

## 📊 **Quick API Test**

```bash
# Health check
curl http://localhost:8060/health

# Expected:
{
  "status": "healthy",
  "services": {
    "docling": true,
    "ollama": true,
    "qdrant": true
  }
}

# Start pipeline
curl -X POST http://localhost:8060/api/pipeline/start

# Expected:
{
  "task_id": "abc-123...",
  "status": "pending"
}

# Check status
curl http://localhost:8060/api/pipeline/status/abc-123...
```

---

## 🎯 **Port Information**

- **API Port:** `8060` (changed from 8001 to avoid conflicts)
- **Access:** `http://localhost:8060`
- **Health Check:** `http://localhost:8060/health`

---

## 📚 **Next Steps**

### **For Local Testing:**
- See [TESTING_GUIDE.md](TESTING_GUIDE.md) for detailed instructions
- Test individual components
- Process sample files
- Check logs in `logs/` directory

### **For Docker:**
- See [DOCKER.md](DOCKER.md) for deployment options
- Monitor with `docker-compose logs -f`
- Scale with `docker-compose up -d --scale ingestion-api=3`

### **For Configuration:**
- See [CONFIGURATION.md](CONFIGURATION.md) for all environment variables
- Customize chunking, timeouts, models
- Set up logging preferences

---

## 🔧 **Common Commands**

### **Local Development**

```bash
# Start API server
python api/main.py

# Run full pipeline
python src/pipeline.py

# Test component
python src/components/r2_client.py
```

### **Docker**

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Rebuild
docker-compose up -d --build
```

---

## 🐛 **Troubleshooting**

### **Port 8060 Already in Use?**

```bash
# Check what's using it
lsof -i :8060

# Kill the process
kill -9 <PID>

# Or change port in:
# - api/main.py (line 228)
# - Dockerfile (line 52)
# - docker-compose.yml (line 12)
```

### **Services Not Connecting?**

```bash
# Test connectivity
ping 192.168.254.22

# Test Qdrant
curl http://192.168.254.22:6333/collections

# Test Ollama
curl http://192.168.254.22:11434/api/tags

# Test Docling
curl http://192.168.254.22:5010/health
```

### **Import Errors?**

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## ✨ **Summary**

| Method | Time | Difficulty | Best For |
|--------|------|------------|----------|
| **Local** | 5 min | ⭐ Easy | Testing & Development |
| **Docker** | 5 min | ⭐⭐ Medium | Production & Deployment |

**Recommendation:** Start with local testing, then move to Docker for production.

---

## 📖 **Full Documentation**

- [README.md](README.md) - Complete overview
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Detailed testing instructions
- [DOCKER.md](DOCKER.md) - Docker deployment guide
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration reference
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Technical details

---

**Ready to start?** Pick your method above and follow the steps! 🚀

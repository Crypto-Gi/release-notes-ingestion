# Testing & Usage Guide

Complete guide for testing the ingestion pipeline with and without Docker.

## 🎯 **Can I Test Without Docker? YES!** ✅

You can **absolutely test without Docker first**. In fact, it's **recommended** to test locally before containerizing.

---

## 📋 **Testing Approaches**

### **Approach 1: Local Testing (Recommended First)** 🔧
- ✅ Faster iteration
- ✅ Easier debugging
- ✅ Direct access to code
- ✅ No Docker overhead

### **Approach 2: Docker Testing (Production-like)** 🐳
- ✅ Consistent environment
- ✅ Isolated dependencies
- ✅ Production parity
- ✅ Easy deployment

---

## 🚀 **Method 1: Testing WITHOUT Docker**

### **Prerequisites**

1. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Virtual Environment (Recommended)**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate it
   source venv/bin/activate  # Linux/Mac
   # OR
   venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   # Copy and edit .env
   cp .env.example .env
   nano .env
   ```

---

### **Step-by-Step Local Testing**

#### **Step 1: Test Individual Components** 🧪

```bash
# Test configuration loading
python src/components/config.py

# Test R2 connection
python src/components/r2_client.py

# Test Docling service
python src/components/docling_client.py

# Test Ollama embeddings
python src/components/embedding_client.py

# Test Qdrant connection
python src/components/qdrant_uploader.py

# Test file hasher
python src/components/file_hasher.py

# Test log manager
python src/components/log_manager.py

# Test chunker
python src/components/chunker.py
```

**Expected Output:**
- ✅ No errors
- ✅ Connection successful messages
- ✅ Service health checks pass

---

#### **Step 2: Test Full Pipeline** 🔄

```bash
# Run the complete pipeline
python src/pipeline.py
```

**What Happens:**
1. Lists files in R2
2. Filters new files
3. Downloads and processes each file
4. Converts to markdown
5. Chunks content
6. Generates embeddings
7. Uploads to Qdrant
8. Logs results

**Expected Output:**
```
2025-11-07 07:00:00 - INFO - Initializing ingestion pipeline...
2025-11-07 07:00:01 - INFO - Pipeline initialized successfully
2025-11-07 07:00:02 - INFO - Service health: {'docling': True, 'ollama': True, 'qdrant': True}
2025-11-07 07:00:03 - INFO - Found 42 files
2025-11-07 07:00:04 - INFO - New files to process: 5
2025-11-07 07:00:05 - INFO - Processing file: source/file1.pdf
...
2025-11-07 07:05:00 - INFO - Pipeline complete!
```

---

#### **Step 3: Test API Server** 🌐

```bash
# Start API server
python api/main.py

# OR with uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8060 --reload
```

**API will be available at:** `http://localhost:8060`

**Test Endpoints:**

```bash
# Health check
curl http://localhost:8060/health

# Expected response:
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

# Expected response:
{
  "task_id": "abc-123-def-456",
  "status": "pending",
  "message": "Pipeline task started"
}

# Check status
curl http://localhost:8060/api/pipeline/status/abc-123-def-456

# Get summary
curl http://localhost:8060/api/pipeline/summary

# View logs
curl http://localhost:8060/api/logs/conversion
curl http://localhost:8060/api/logs/upload
curl http://localhost:8060/api/logs/failed
```

---

### **Step 4: Test with Sample File** 📄

```bash
# Create a test script
cat > test_single_file.py << 'EOF'
from src.pipeline import IngestionPipeline

# Initialize pipeline
pipeline = IngestionPipeline()

# Test with a single file
result = pipeline.process_file("source/test/sample.pdf")

if result:
    print("✅ File processed successfully!")
else:
    print("❌ File processing failed!")
EOF

# Run test
python test_single_file.py
```

---

## 🐳 **Method 2: Testing WITH Docker**

### **Prerequisites**

1. **Docker Installed**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **Configure Environment**
   ```bash
   # .env file should be configured
   cat .env  # Verify settings
   ```

---

### **Step-by-Step Docker Testing**

#### **Step 1: Build Docker Image** 🏗️

```bash
# Build the image
docker-compose build

# Expected output:
# Successfully built abc123
# Successfully tagged release-notes-ingestion:latest
```

**Verify Build:**
```bash
# List images
docker images | grep release-notes-ingestion

# Should show:
# release-notes-ingestion  latest  abc123  2 minutes ago  450MB
```

---

#### **Step 2: Start Container** 🚀

```bash
# Start in foreground (see logs)
docker-compose up

# OR start in background
docker-compose up -d
```

**Verify Container:**
```bash
# Check running containers
docker ps

# Should show:
# CONTAINER ID  IMAGE                    STATUS        PORTS
# abc123        release-notes-ingestion  Up 10 seconds 0.0.0.0:8060->8060/tcp
```

---

#### **Step 3: Test API** 🧪

```bash
# Health check
curl http://localhost:8060/health

# Start pipeline
curl -X POST http://localhost:8060/api/pipeline/start

# Check logs
docker-compose logs -f
```

---

#### **Step 4: Access Container** 🔍

```bash
# Enter container shell
docker exec -it release-notes-ingestion /bin/bash

# Inside container:
ls -la /app
cat /app/logs/conversion.json
python src/components/config.py
exit
```

---

#### **Step 5: View Logs** 📊

```bash
# All logs
docker-compose logs -f

# Last 50 lines
docker-compose logs --tail=50

# Logs from specific time
docker-compose logs --since 10m
```

---

#### **Step 6: Stop Container** 🛑

```bash
# Stop gracefully
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop and remove everything
docker-compose down --rmi all -v
```

---

## 🔄 **Comparison: Docker vs Non-Docker**

| Feature | Without Docker | With Docker |
|---------|---------------|-------------|
| **Setup Time** | 5 minutes | 10 minutes |
| **Debugging** | ✅ Easy | ⚠️ Moderate |
| **Iteration Speed** | ✅ Fast | ⚠️ Slower |
| **Environment** | ⚠️ Local Python | ✅ Isolated |
| **Deployment** | ⚠️ Manual | ✅ Automated |
| **Consistency** | ⚠️ Varies | ✅ Consistent |
| **Resource Usage** | ✅ Lower | ⚠️ Higher |
| **Production Ready** | ❌ No | ✅ Yes |

---

## 🎯 **Recommended Testing Workflow**

### **Phase 1: Local Development** (Days 1-2)

1. ✅ Install dependencies locally
2. ✅ Test individual components
3. ✅ Fix any configuration issues
4. ✅ Test with sample files
5. ✅ Verify all services connect

### **Phase 2: Integration Testing** (Day 3)

1. ✅ Run full pipeline locally
2. ✅ Test API endpoints
3. ✅ Process multiple files
4. ✅ Verify Qdrant uploads
5. ✅ Check logs

### **Phase 3: Docker Testing** (Day 4)

1. ✅ Build Docker image
2. ✅ Test in container
3. ✅ Verify same results
4. ✅ Test with docker-compose
5. ✅ Check resource usage

### **Phase 4: Production Deployment** (Day 5+)

1. ✅ Deploy to staging
2. ✅ Run load tests
3. ✅ Monitor performance
4. ✅ Deploy to production
5. ✅ Set up monitoring

---

## 🧪 **Test Checklist**

### **Before Testing**

- [ ] Python 3.11+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured
- [ ] R2 bucket accessible
- [ ] Qdrant running and accessible
- [ ] Ollama running with models pulled
- [ ] Docling service running

### **Component Tests**

- [ ] Config loads without errors
- [ ] R2 client lists files
- [ ] Docling converts sample PDF
- [ ] Ollama generates embeddings
- [ ] Qdrant accepts uploads
- [ ] File hasher generates hashes
- [ ] Log manager creates logs
- [ ] Chunker splits text

### **Integration Tests**

- [ ] Full pipeline processes one file
- [ ] API server starts
- [ ] Health check returns healthy
- [ ] Pipeline can be triggered via API
- [ ] Logs are created correctly
- [ ] Qdrant collections populated

### **Docker Tests**

- [ ] Image builds successfully
- [ ] Container starts
- [ ] Health check passes
- [ ] API accessible on port 8060
- [ ] Logs persist outside container
- [ ] Environment variables work

---

## 🐛 **Troubleshooting**

### **Local Testing Issues**

#### **Import Errors**
```bash
# Make sure you're in the right directory
cd /home/mir/projects/release-notes-ingestion

# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### **Connection Errors**
```bash
# Test service connectivity
ping 192.168.254.22

# Test Qdrant
curl http://192.168.254.22:6333/collections

# Test Ollama
curl http://192.168.254.22:11434/api/tags

# Test Docling
curl http://192.168.254.22:5010/health
```

#### **Permission Errors**
```bash
# Fix log directory permissions
chmod 755 logs/
chmod 644 logs/*.json
```

---

### **Docker Testing Issues**

#### **Build Fails**
```bash
# Clean build
docker-compose build --no-cache

# Check Dockerfile syntax
docker build -t test .
```

#### **Container Won't Start**
```bash
# Check logs
docker-compose logs

# Check container status
docker ps -a

# Remove and recreate
docker-compose down
docker-compose up --force-recreate
```

#### **Port Already in Use**
```bash
# Check what's using port 8060
lsof -i :8060

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
```

---

## 📊 **Performance Testing**

### **Local Performance**

```bash
# Time a single file
time python -c "
from src.pipeline import IngestionPipeline
pipeline = IngestionPipeline()
pipeline.process_file('source/test.pdf')
"
```

### **Docker Performance**

```bash
# Monitor resources
docker stats release-notes-ingestion

# Check memory usage
docker exec release-notes-ingestion free -h

# Check CPU usage
docker exec release-notes-ingestion top -bn1
```

---

## ✅ **Success Criteria**

### **Local Testing Success**

- ✅ All component tests pass
- ✅ Pipeline processes files without errors
- ✅ API server responds to requests
- ✅ Logs are created correctly
- ✅ Qdrant collections populated
- ✅ No memory leaks
- ✅ Performance acceptable

### **Docker Testing Success**

- ✅ Image builds in < 5 minutes
- ✅ Container starts in < 10 seconds
- ✅ Health check passes
- ✅ Same results as local testing
- ✅ Logs persist after restart
- ✅ Resource usage acceptable
- ✅ Can scale horizontally

---

## 🎓 **Next Steps**

### **After Local Testing**

1. Document any issues found
2. Fix configuration problems
3. Optimize performance
4. Add error handling
5. Write unit tests

### **After Docker Testing**

1. Deploy to staging
2. Run integration tests
3. Load test with multiple files
4. Monitor resource usage
5. Deploy to production

---

## 📚 **Additional Resources**

- [README.md](README.md) - General overview
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration guide
- [DOCKER.md](DOCKER.md) - Docker deployment guide
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Implementation details

---

**Last Updated:** November 7, 2025

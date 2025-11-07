# Docker Deployment Guide

Complete guide for containerizing and deploying the Release Notes Ingestion Pipeline.

## 🐳 Quick Start

### 1. Build and Run with Docker Compose

```bash
# Build the image
docker-compose build

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### 2. Access the API

```bash
# Health check
curl http://localhost:8001/health

# Start pipeline
curl -X POST http://localhost:8001/api/pipeline/start
```

---

## 📦 Docker Files

### **Dockerfile**
- Multi-stage build for optimized image size
- Python 3.11 slim base
- Health check included
- Exposes port 8001

### **docker-compose.yml**
- Service definition
- Environment variable mapping
- Volume mounts for logs
- Network configuration
- Resource limits

### **.dockerignore**
- Excludes unnecessary files
- Reduces image size
- Improves build speed

---

## 🔧 Configuration

### Option 1: Using .env File (Recommended)

```bash
# 1. Configure .env
cp .env.example .env
nano .env

# 2. Start with docker-compose
docker-compose up -d
```

Docker Compose automatically reads `.env` and passes variables to the container.

### Option 2: Environment Variables

```bash
# Pass variables directly
docker run -d \
  -p 8001:8001 \
  -e R2_ENDPOINT=https://... \
  -e R2_ACCESS_KEY=... \
  -e R2_SECRET_KEY=... \
  -e R2_BUCKET_NAME=... \
  -e QDRANT_HOST=192.168.254.22 \
  -e OLLAMA_HOST=192.168.254.22 \
  -e DOCLING_BASE_URL=http://... \
  -v $(pwd)/logs:/app/logs \
  release-notes-ingestion
```

---

## 🏗️ Build Options

### Standard Build

```bash
docker build -t release-notes-ingestion .
```

### Build with Custom Tag

```bash
docker build -t release-notes-ingestion:v1.0.0 .
```

### Build with No Cache

```bash
docker build --no-cache -t release-notes-ingestion .
```

### Multi-Platform Build

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t release-notes-ingestion:latest .
```

---

## 🚀 Deployment Scenarios

### Scenario 1: Development

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  ingestion-api:
    build: .
    ports:
      - "8001:8001"
    volumes:
      - ./src:/app/src  # Hot reload
      - ./api:/app/api
      - ./logs:/app/logs
    environment:
      - DEBUG=true
    command: uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

```bash
docker-compose -f docker-compose.dev.yml up
```

### Scenario 2: Production

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  ingestion-api:
    image: release-notes-ingestion:latest
    restart: always
    ports:
      - "8001:8001"
    volumes:
      - /var/log/ingestion:/app/logs
    env_file:
      - .env.production
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
      replicas: 2
```

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Scenario 3: With n8n

```yaml
# docker-compose.full.yml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n/workflows:/workflows
    networks:
      - ingestion-network

  ingestion-api:
    build: .
    ports:
      - "8001:8001"
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    networks:
      - ingestion-network
    depends_on:
      - n8n

volumes:
  n8n_data:

networks:
  ingestion-network:
    driver: bridge
```

---

## 📊 Resource Management

### CPU & Memory Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'      # Maximum 2 CPU cores
      memory: 4G       # Maximum 4GB RAM
    reservations:
      cpus: '1.0'      # Minimum 1 CPU core
      memory: 2G       # Minimum 2GB RAM
```

### Recommended Resources

| Workload | CPU | Memory | Notes |
|----------|-----|--------|-------|
| Light (< 100 files/day) | 1 core | 2GB | Small PDFs |
| Medium (100-500 files/day) | 2 cores | 4GB | Mixed content |
| Heavy (> 500 files/day) | 4 cores | 8GB | Large PDFs |

---

## 🔍 Monitoring

### View Logs

```bash
# All logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f ingestion-api
```

### Container Stats

```bash
# Real-time stats
docker stats

# Specific container
docker stats release-notes-ingestion
```

### Health Check

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' release-notes-ingestion

# View health check logs
docker inspect --format='{{json .State.Health}}' release-notes-ingestion | jq
```

---

## 🛠️ Maintenance

### Update Container

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes
docker-compose down -v

# Remove images
docker rmi release-notes-ingestion

# Prune everything
docker system prune -a
```

### Backup Logs

```bash
# Backup logs directory
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/

# Copy from container
docker cp release-notes-ingestion:/app/logs ./logs-backup
```

---

## 🔐 Security Best Practices

### 1. Use Secrets for Sensitive Data

```yaml
# docker-compose.yml with secrets
services:
  ingestion-api:
    secrets:
      - r2_access_key
      - r2_secret_key

secrets:
  r2_access_key:
    file: ./secrets/r2_access_key.txt
  r2_secret_key:
    file: ./secrets/r2_secret_key.txt
```

### 2. Run as Non-Root User

```dockerfile
# Add to Dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

### 3. Read-Only Root Filesystem

```yaml
services:
  ingestion-api:
    read_only: true
    tmpfs:
      - /tmp
      - /app/logs
```

### 4. Network Isolation

```yaml
networks:
  ingestion-network:
    driver: bridge
    internal: true  # No external access
```

---

## 🧪 Testing

### Test Build

```bash
# Build without running
docker build -t release-notes-ingestion:test .

# Run tests in container
docker run --rm release-notes-ingestion:test pytest
```

### Integration Test

```bash
# Start all services
docker-compose up -d

# Wait for health check
sleep 10

# Test API
curl http://localhost:8001/health

# Test pipeline
curl -X POST http://localhost:8001/api/pipeline/start
```

---

## 📈 Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  ingestion-api:
    deploy:
      replicas: 3
```

```bash
# Scale to 3 instances
docker-compose up -d --scale ingestion-api=3
```

### Load Balancer

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - ingestion-api

  ingestion-api:
    deploy:
      replicas: 3
```

---

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs ingestion-api

# Check container status
docker ps -a

# Inspect container
docker inspect release-notes-ingestion
```

### Health Check Failing

```bash
# Manual health check
docker exec release-notes-ingestion curl -f http://localhost:8001/health

# Check service connectivity
docker exec release-notes-ingestion ping qdrant-host
```

### Out of Memory

```bash
# Increase memory limit
docker-compose up -d --scale ingestion-api=1 \
  --memory=8g
```

### Slow Performance

```bash
# Check resource usage
docker stats

# Increase CPU allocation
# Edit docker-compose.yml and increase CPU limits
```

---

## 📝 Environment Variables Reference

All environment variables from `.env` are automatically passed to the container via docker-compose.yml.

See [CONFIGURATION.md](CONFIGURATION.md) for complete reference.

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/docker.yml
name: Docker Build and Push

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t release-notes-ingestion:${{ github.sha }} .
      
      - name: Run tests
        run: docker run release-notes-ingestion:${{ github.sha }} pytest
      
      - name: Push to registry
        run: |
          docker tag release-notes-ingestion:${{ github.sha }} \
            registry.example.com/release-notes-ingestion:latest
          docker push registry.example.com/release-notes-ingestion:latest
```

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Last Updated:** November 7, 2025

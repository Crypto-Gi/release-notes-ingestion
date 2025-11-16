# Documentation Index

This directory contains all project documentation for the **Release Notes Ingestion Pipeline**.

## 📋 Core Documentation

### System & Architecture
- **[SYSTEM_SPEC.md](SYSTEM_SPEC.md)** - Complete system specification including architecture, workflows, APIs, data models, and configuration
  - High-level system overview
  - Runtime workflows (main pipeline, reprocess, retry, API)
  - Component specifications
  - Data models and storage
  - API endpoints
  - Configuration reference
  - Deduplication and error handling

### Phase 3 Features
- **[PHASE_3_ENHANCEMENTS.md](PHASE_3_ENHANCEMENTS.md)** - Advanced logging and deduplication design
  - New log files (embedding.json, qdrant_upload.json, skipped.json)
  - Three-level deduplication logic
  - xxHash64 implementation
  - Force reprocess flag
  - Implementation checklist

## 🔧 Setup & Configuration Guides

### Vector Database
- **[QDRANT.md](QDRANT.md)** - Qdrant configuration and collections guide
  - Production vs development setup
  - HTTPS and API key configuration
  - gRPC support
  - Collection schemas (filename and content)
  - Two-stage search workflow
  - Distance metrics and HNSW tuning

### Indexing
- **[INDEXING_GUIDE.md](INDEXING_GUIDE.md)** - Complete payload indexing guide
  - Interactive index creation script
  - All 8 index types (Keyword, Integer, Float, Boolean, Geo, DateTime, UUID, Text)
  - Tokenizer types and configuration
  - Best practices
  - API references (HTTP and Python)

### Deployment
- **[DOCKER.md](DOCKER.md)** - Docker deployment and operations
  - Quick start
  - Dockerfile and docker-compose details
  - Configuration options
  - Deployment scenarios (dev, production, with n8n)
  - Resource management
  - Monitoring and maintenance
  - Security best practices

## 📝 Project History

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and migration guides
  - v0.2.0 - Production Qdrant support, file filtering, security
  - v0.1.0 - Initial release
  - Migration guides
  - Breaking changes

## 🗄️ Archived Documentation

- **[archived/REFERENCE_legacy.md](archived/REFERENCE_legacy.md)** - Legacy technical reference
  - Historical implementation plan
  - Original project structure
  - Superseded by SYSTEM_SPEC.md and other current docs
  - Kept for historical reference only

---

## 📚 Additional Resources

### Root Documentation
- **[../README.md](../README.md)** - Main project README with quick start, features, and usage
- **[../env.example](../env.example)** - Complete environment variable reference

### API Documentation (when running)
- **FastAPI Docs** - http://localhost:8060/docs
- **ReDoc** - http://localhost:8060/redoc

---

## 🎯 Quick Navigation

**New to the project?**
1. Start with [../README.md](../README.md) for overview and quick start
2. Read [SYSTEM_SPEC.md](SYSTEM_SPEC.md) for architecture understanding
3. Follow [QDRANT.md](QDRANT.md) and [DOCKER.md](DOCKER.md) for setup

**Setting up collections?**
- [QDRANT.md](QDRANT.md) for collection configuration
- [INDEXING_GUIDE.md](INDEXING_GUIDE.md) for payload indexes

**Understanding Phase 3?**
- [PHASE_3_ENHANCEMENTS.md](PHASE_3_ENHANCEMENTS.md) for deduplication design

**Deploying?**
- [DOCKER.md](DOCKER.md) for containerized deployment
- [CHANGELOG.md](CHANGELOG.md) for version-specific notes

---

**Last Updated:** November 16, 2025

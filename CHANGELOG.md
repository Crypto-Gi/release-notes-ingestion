# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] - 2025-11-08

### Added
- **Qdrant Production Support**: Full support for production Qdrant deployments
  - HTTPS connection support for secure production environments
  - API key authentication for Qdrant Cloud and secured instances
  - gRPC support for improved performance (optional)
  - Automatic connection mode detection (development vs production)
  - Secure credential handling with masked API keys in logs
- **File Extension Filtering**: Skip unwanted files during processing
  - `SKIP_EXTENSIONS` environment variable to filter files by extension
  - Prevents processing of system files like `.DS_Store`
  - Configurable via comma-separated list in `.env`
- **Enhanced Configuration**: New optional environment variables
  - `QDRANT_USE_HTTPS` - Enable HTTPS for production (default: false)
  - `QDRANT_API_KEY` - API key for authentication (default: none)
  - `QDRANT_GRPC_PORT` - gRPC port for better performance (optional)
  - `QDRANT_PREFER_GRPC` - Prefer gRPC over HTTP (default: false)
  - `SKIP_EXTENSIONS` - File extensions to skip (default: none)

### Changed
- **QdrantUploader**: Enhanced to support both development and production modes
  - Automatically selects connection method based on configuration
  - Logs connection mode (DEV/PRODUCTION) for clarity
  - Improved error handling and connection verification
- **Pipeline**: Updated to pass production parameters to Qdrant uploader
- **Test Suite**: Enhanced to display connection details
  - Shows HTTPS status, API key status (masked), and gRPC status
  - Improved test output for better debugging

### Fixed
- **Docling Health Check**: Corrected endpoint from `/health` to `/healthz`
- **File Processing**: System files (`.DS_Store`) now properly filtered

### Security
- API keys are masked in logs as `***` for security
- `.env` file properly gitignored to protect credentials
- HTTPS support for encrypted connections in production

### Documentation
- Updated `.env.example` with production configuration examples
- Added comprehensive inline documentation for new features
- Created `DOCLING_ANALYSIS.md` with error analysis and solutions
- Created `GITHUB_SETUP.md` with repository setup instructions

### Testing
- ✅ Tested with local development Qdrant (HTTP, no auth)
- ✅ Tested with Qdrant Cloud production (HTTPS + API key)
- ✅ Verified 100% backward compatibility
- ✅ All 9 components passing tests

---

## [0.1.0] - 2025-11-07

### Added
- **Initial Release**: Complete ingestion pipeline implementation
- **Core Components**:
  - R2 Client for Cloudflare R2 storage
  - Qdrant Uploader for vector database operations
  - Embedding Client for Ollama embeddings
  - Docling Client for document conversion
  - Semantic Chunker for text processing
  - File Hasher for content deduplication
  - Log Manager for tracking operations
  - Markdown Storage for processed documents
- **Configuration System**: Environment-based configuration with Pydantic models
- **Test Suite**: Comprehensive component testing
- **Documentation**: Complete setup and usage guides

### Features
- PDF to Markdown conversion via Docling
- Semantic chunking with configurable token sizes
- Dual embedding models (filename and content)
- Vector storage in Qdrant collections
- Cloudflare R2 integration for file storage
- Comprehensive logging and error tracking

---

## Version Comparison

### v0.2.0 vs v0.1.0
**Key Improvements:**
- Production-ready Qdrant support (HTTPS + API key)
- File filtering to skip unwanted files
- Enhanced security with credential masking
- Better error handling and diagnostics
- Improved documentation and examples

**Backward Compatibility:** ✅ 100% compatible
- Existing `.env` files work without changes
- All new features are optional with sensible defaults
- No breaking changes to existing functionality

---

## Migration Guide

### From v0.1.0 to v0.2.0

**For Development Users:**
No action required. Everything works as before.

**For Production Users:**
Add these two lines to your `.env` file:
```bash
QDRANT_USE_HTTPS=true
QDRANT_API_KEY=your-production-api-key
```

**Optional Enhancements:**
```bash
# Skip system files
SKIP_EXTENSIONS=.DS_Store,.tmp,.log

# Enable gRPC for better performance
QDRANT_GRPC_PORT=6334
QDRANT_PREFER_GRPC=true
```

---

## Links

- [GitHub Repository](https://github.com/Crypto-Gi/release-notes-ingestion)
- [v0.2.0 Release](https://github.com/Crypto-Gi/release-notes-ingestion/releases/tag/v0.2.0)
- [v0.1.0 Release](https://github.com/Crypto-Gi/release-notes-ingestion/releases/tag/v0.1)
- [Documentation](README.md)

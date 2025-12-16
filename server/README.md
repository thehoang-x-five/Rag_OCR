# RAG-Anything OCR Service

FastAPI backend service that wraps RAG-Anything for OCR and document processing with optional RAG capabilities.

## Features

- **Document Processing**: PDF, images, Office documents (DOC/DOCX/PPT/PPTX/XLS/XLSX), text files
- **Multiple Parsers**: Docling (default) and MinerU support
- **Async Processing**: Background job processing with progress tracking
- **Text Conversion**: Export to TXT, MD, JSON, PDF, DOCX formats
- **Optional RAG**: Local LLM integration via Ollama
- **CORS Support**: Ready for frontend integration

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install LibreOffice (for Office documents)

**Windows:**
- Download from [LibreOffice official website](https://www.libreoffice.org/download/download/)
- Run installer and follow instructions

**macOS:**
```bash
brew install --cask libreoffice
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install libreoffice
```

**CentOS/RHEL:**
```bash
sudo yum install libreoffice
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your settings
# Key settings:
# - CORS_ORIGINS: Your frontend URL (default: http://localhost:5173)
# - DEFAULT_PARSER: docling or mineru (default: docling)
# - ENABLE_RAG: true/false (default: false)
```

### 4. Run the Server

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/api/health

## Optional: Ollama Setup (for RAG features)

If you want to enable RAG functionality with local LLMs:

### 1. Install Ollama

**Windows/Mac:**
- Download from [Ollama official website](https://ollama.ai/)

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Start Ollama Service

```bash
ollama serve
```

### 3. Pull Required Models

```bash
# LLM model (for chat/reasoning)
ollama pull qwen2.5:7b

# Embedding model (for vector search)
ollama pull nomic-embed-text

# Vision model (optional, for image analysis)
ollama pull llava:7b
```

### 4. Enable RAG in Environment

```bash
# In .env file:
ENABLE_RAG=true
OLLAMA_BASE_URL=http://localhost:11434/api
OLLAMA_LLM_MODEL=qwen2.5:7b
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_VISION_MODEL=llava:7b
```

## API Endpoints

### OCR Processing

- `POST /api/ocr/extract` - Extract text from uploaded file
- `GET /api/ocr/status` - Get OCR service capabilities

### Job Management

- `GET /api/jobs/{job_id}` - Get job status and result
- `GET /api/jobs/` - List all jobs
- `DELETE /api/jobs/{job_id}` - Delete job and cleanup files
- `POST /api/jobs/cleanup` - Cleanup old jobs

### Text Conversion

- `POST /api/convert` - Convert text to different formats
- `GET /api/convert/formats` - Get supported formats

### RAG (Optional)

- `POST /api/rag/ingest` - Ingest document into knowledge base
- `POST /api/rag/query` - Query knowledge base
- `GET /api/rag/status` - Get RAG service status

### Health Check

- `GET /api/health` - Service health and status

## Usage Examples

### Extract Text from PDF

```bash
curl -X POST "http://localhost:8000/api/ocr/extract" \
  -F "file=@document.pdf" \
  -F "settings={\"parser\":\"docling\",\"parse_method\":\"auto\",\"language\":\"auto\"}"
```

### Check Job Status

```bash
curl "http://localhost:8000/api/jobs/{job_id}"
```

### Convert Text to PDF

```bash
curl -X POST "http://localhost:8000/api/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your extracted text here",
    "format": "pdf",
    "fileName": "output",
    "includeMetadata": true,
    "pdfOptions": {"pageSize": "A4", "fontSize": 12}
  }' \
  --output output.pdf
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `dev` | Application environment |
| `HOST` | `0.0.0.0` | Host to bind to |
| `PORT` | `8000` | Port to bind to |
| `CORS_ORIGINS` | `http://localhost:5173` | CORS allowed origins |
| `STORAGE_DIR` | `./storage` | File storage directory |
| `DEFAULT_PARSER` | `docling` | Default parser (docling\|mineru) |
| `DEFAULT_PARSE_METHOD` | `auto` | Default parse method (auto\|ocr\|txt) |
| `DEFAULT_LANG` | `auto` | Default language (auto\|vi\|en\|...) |
| `DEFAULT_DEVICE` | `cpu` | Default device (cpu\|cuda\|mps) |
| `ENABLE_RAG` | `false` | Enable RAG functionality |
| `OLLAMA_BASE_URL` | `http://localhost:11434/api` | Ollama API URL |
| `OLLAMA_LLM_MODEL` | `qwen2.5:7b` | Ollama LLM model |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Ollama embedding model |
| `OLLAMA_VISION_MODEL` | `llava:7b` | Ollama vision model |

### File Constraints

- **Max file size**: 15MB
- **Supported formats**: PDF, PNG, JPG, JPEG, WebP, TIF, TIFF, BMP, DOC, DOCX, PPT, PPTX, XLS, XLSX, TXT, MD

## Docker Deployment

```bash
# Build image
docker build -t rag-anything-ocr .

# Run container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/storage:/app/storage \
  -e CORS_ORIGINS="http://localhost:5173" \
  --name rag-ocr-service \
  rag-anything-ocr
```

## Troubleshooting

### LibreOffice Issues

If Office document processing fails:

1. **Check LibreOffice installation**:
   ```bash
   libreoffice --version
   ```

2. **Test LibreOffice headless mode**:
   ```bash
   libreoffice --headless --convert-to pdf test.docx
   ```

3. **Common solutions**:
   - Ensure LibreOffice is in PATH
   - On Linux, install `libreoffice-java-common`
   - On Windows, restart after installation

### Parser Issues

1. **Docling not working**: Check if all dependencies are installed
2. **MinerU not working**: Ensure CUDA drivers (if using GPU)
3. **Memory issues**: Reduce batch size or use CPU mode

### Ollama Connection Issues

1. **Check Ollama service**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Check model availability**:
   ```bash
   ollama list
   ```

3. **Pull missing models**:
   ```bash
   ollama pull qwen2.5:7b
   ```

## Development

### Project Structure

```
server/
├── app/
│   ├── api/           # API routes
│   ├── core/          # Core functionality
│   ├── models/        # Pydantic schemas
│   ├── utils/         # Utilities
│   └── main.py        # FastAPI app
├── requirements.txt   # Dependencies
├── .env.example      # Environment template
├── Dockerfile        # Container config
└── README.md         # This file
```

### Adding New Features

1. **New API endpoints**: Add to `app/api/`
2. **New parsers**: Extend `raganything_engine.py`
3. **New formats**: Extend `routes_convert.py`
4. **New schemas**: Add to `models/schemas.py`

## License

This project follows the same license as RAG-Anything.
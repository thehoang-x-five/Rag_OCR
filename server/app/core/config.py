"""
Configuration settings
"""
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application settings
    APP_ENV: str = Field(default="dev", description="Application environment")
    HOST: str = Field(default="0.0.0.0", description="Host to bind to")
    PORT: int = Field(default=8000, description="Port to bind to")
    CORS_ORIGINS: str = Field(default="http://localhost:5173", description="CORS origins (comma-separated)")
    
    # Storage settings
    STORAGE_DIR: Path = Field(default=Path("./storage"), description="Storage directory")
    
    # Parser settings
    DEFAULT_PARSER: str = Field(default="docling", description="Default parser (docling|mineru)")
    DEFAULT_PARSE_METHOD: str = Field(default="auto", description="Default parse method (auto|ocr|txt)")
    DEFAULT_LANG: str = Field(default="auto", description="Default language (auto|vi|en|...)")
    DEFAULT_DEVICE: str = Field(default="cpu", description="Default device (cpu|cuda|mps)")
    
    # RAG settings
    ENABLE_RAG: bool = Field(default=False, description="Enable RAG functionality")
    
    # Ollama settings
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434/api", description="Ollama API base URL")
    OLLAMA_LLM_MODEL: str = Field(default="qwen2.5:7b", description="Ollama LLM model")
    OLLAMA_EMBED_MODEL: str = Field(default="nomic-embed-text", description="Ollama embedding model")
    OLLAMA_VISION_MODEL: str = Field(default="llava:7b", description="Ollama vision model")
    
    # File constraints
    MAX_FILE_SIZE: int = Field(default=15 * 1024 * 1024, description="Max file size in bytes (15MB)")
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=[
            "pdf", "png", "jpg", "jpeg", "webp", "tif", "tiff", "bmp",
            "doc", "docx", "ppt", "pptx", "xls", "xlsx",
            "txt", "md"
        ],
        description="Allowed file extensions"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
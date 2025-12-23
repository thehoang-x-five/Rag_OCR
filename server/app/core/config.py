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
    
    # AI Enhancement settings
    AI_ENHANCEMENT_ENABLED: bool = Field(default=True, description="Enable AI enhancement of OCR results")
    AI_ENHANCEMENT_TIMEOUT: int = Field(default=30, description="Timeout for AI enhancement in seconds")
    AI_ENHANCEMENT_MAX_RETRIES: int = Field(default=2, description="Max retries for AI enhancement")
    AI_USE_VISION_WHEN_AVAILABLE: bool = Field(default=True, description="Use vision models when available")
    AI_PROVIDER_PRIORITY: str = Field(default="groq:1,deepseek:2,gemini:3,ollama:4", description="Provider priority (name:priority)")
    
    # Groq settings
    GROQ_API_KEY: str = Field(default="", description="Groq API key")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile", description="Groq LLM model")
    GROQ_VISION_MODEL: str = Field(default="llama-3.2-90b-vision-preview", description="Groq vision model")
    GROQ_BASE_URL: str = Field(default="https://api.groq.com/openai/v1", description="Groq API base URL")
    
    # DeepSeek settings
    DEEPSEEK_API_KEY: str = Field(default="", description="DeepSeek API key")
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat", description="DeepSeek chat model")
    DEEPSEEK_CODER_MODEL: str = Field(default="deepseek-coder", description="DeepSeek coder model")
    DEEPSEEK_BASE_URL: str = Field(default="https://api.deepseek.com/v1", description="DeepSeek API base URL")
    
    # Gemini settings
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash", description="Gemini model")
    GEMINI_PRO_MODEL: str = Field(default="gemini-1.5-pro", description="Gemini Pro model")
    GEMINI_BASE_URL: str = Field(default="https://generativelanguage.googleapis.com/v1beta", description="Gemini API base URL")
    
    # Prompt settings
    CUSTOM_PROMPTS_PATH: str = Field(default="./prompts", description="Path to custom prompt templates")
    DEFAULT_DOCUMENT_TYPE: str = Field(default="general", description="Default document type for prompts")
    
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
# Design Document

## Overview

This feature implements a multi-provider AI system to enhance OCR accuracy through post-processing. The system integrates with Groq, DeepSeek, Google Gemini, and Ollama, providing automatic fallback between providers. It includes vision-based enhancement capabilities, configurable prompts, comprehensive testing tools, and monitoring.

The architecture follows a provider abstraction pattern where each AI service implements a common interface, allowing seamless switching and fallback. The system enhances OCR results by sending extracted text (and optionally images) to AI models for error correction, formatting improvement, and structure preservation.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     OCR Service Layer                        │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Docling    │────────▶│  AI Enhancer │                 │
│  │   OCR Engine │         │   Orchestrator│                 │
│  └──────────────┘         └───────┬───────┘                 │
│                                    │                          │
└────────────────────────────────────┼──────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                  │
         ┌──────────▼──────────┐          ┌──────────▼──────────┐
         │  AI Provider Manager │          │   Prompt Manager    │
         │  - Fallback Logic    │          │  - Template System  │
         │  - Provider Cache    │          │  - Document Types   │
         └──────────┬───────────┘          └─────────────────────┘
                    │
      ┌─────────────┼─────────────┬─────────────┬──────────────┐
      │             │             │             │              │
┌─────▼─────┐ ┌────▼────┐ ┌──────▼──────┐ ┌───▼────┐  ┌─────▼─────┐
│   Groq    │ │DeepSeek │ │   Gemini    │ │ Ollama │  │  Future   │
│  Provider │ │Provider │ │   Provider  │ │Provider│  │ Providers │
└───────────┘ └─────────┘ └─────────────┘ └────────┘  └───────────┘
```

### Component Interaction Flow

```
User Upload → Docling OCR → Raw Text
                              │
                              ▼
                    AI Enhancer Orchestrator
                              │
                              ├─→ Select Provider (priority order)
                              ├─→ Load Prompt Template
                              ├─→ Prepare Request (text + optional image)
                              │
                              ▼
                    Provider Client (Groq/DeepSeek/Gemini/Ollama)
                              │
                              ├─→ API Call
                              ├─→ Parse Response
                              ├─→ Handle Errors (fallback if needed)
                              │
                              ▼
                    Enhanced Text + Metadata
                              │
                              ▼
                    Return to User (original + enhanced)
```

## Components and Interfaces

### 1. AI Provider Manager

**Purpose**: Manages multiple AI providers, handles fallback logic, and maintains provider health status.

**Interface**:
```python
class AIProviderManager:
    def __init__(self, config: Dict[str, Any]):
        """Initialize with provider configurations"""
        
    async def enhance_text(
        self, 
        text: str, 
        document_type: str = "general",
        image_data: Optional[bytes] = None
    ) -> EnhancementResult:
        """Enhance OCR text using available providers"""
        
    async def get_provider_status(self) -> Dict[str, ProviderStatus]:
        """Get health status of all providers"""
        
    def get_active_provider(self) -> Optional[str]:
        """Get currently active provider name"""
```

**Responsibilities**:
- Load and validate provider configurations
- Implement provider priority and fallback logic
- Cache successful provider for performance
- Track provider health and availability
- Coordinate between multiple providers

### 2. Base Provider Interface

**Purpose**: Abstract interface that all AI providers must implement.

**Interface**:
```python
class BaseAIProvider(ABC):
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1
    ) -> str:
        """Send chat completion request"""
        
    @abstractmethod
    async def vision_completion(
        self,
        prompt: str,
        image_data: bytes,
        model: Optional[str] = None
    ) -> str:
        """Send vision-based completion request"""
        
    @abstractmethod
    async def check_health(self) -> bool:
        """Check if provider is available"""
        
    @abstractmethod
    def supports_vision(self) -> bool:
        """Check if provider supports vision models"""
```

### 3. Groq Provider Client

**Purpose**: Implements Groq API integration with OpenAI-compatible format.

**Configuration**:
```python
GROQ_API_KEY: str
GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Fast and accurate
GROQ_VISION_MODEL: str = "llama-3.2-90b-vision-preview"
GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
```

**Features**:
- Ultra-fast inference (fastest among all providers)
- OpenAI-compatible API
- Vision model support
- High rate limits on free tier

### 4. DeepSeek Provider Client

**Purpose**: Implements DeepSeek API integration for cost-effective AI enhancement.

**Configuration**:
```python
DEEPSEEK_API_KEY: str
DEEPSEEK_MODEL: str = "deepseek-chat"
DEEPSEEK_CODER_MODEL: str = "deepseek-coder"
DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
```

**Features**:
- Most cost-effective option
- OpenAI-compatible API
- Specialized coder model for code documents
- Strong reasoning capabilities

### 5. Gemini Provider Client

**Purpose**: Implements Google Gemini API integration with multimodal capabilities.

**Configuration**:
```python
GEMINI_API_KEY: str
GEMINI_MODEL: str = "gemini-1.5-flash"
GEMINI_PRO_MODEL: str = "gemini-1.5-pro"
GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
```

**Features**:
- Native multimodal support (text + image)
- High-quality vision analysis
- Good free tier
- Gemini-specific API format

### 6. Ollama Provider Client (Enhanced)

**Purpose**: Maintains existing Ollama integration with improved interface.

**Configuration**:
```python
OLLAMA_BASE_URL: str = "http://localhost:11434/api"
OLLAMA_LLM_MODEL: str = "qwen2.5:7b"
OLLAMA_VISION_MODEL: str = "llava:7b"
```

**Features**:
- Local, private processing
- No API costs
- Offline capability
- Existing implementation enhanced

### 7. Prompt Manager

**Purpose**: Manages prompt templates for different document types and use cases.

**Interface**:
```python
class PromptManager:
    def get_enhancement_prompt(
        self,
        text: str,
        document_type: str = "general"
    ) -> str:
        """Get formatted prompt for text enhancement"""
        
    def get_vision_prompt(
        self,
        document_type: str = "general"
    ) -> str:
        """Get prompt for vision-based OCR"""
        
    def load_custom_prompts(self, prompts_file: Path):
        """Load custom prompt templates"""
```

**Prompt Templates**:
- General document enhancement
- Code document enhancement
- Invoice/receipt processing
- Form extraction
- Handwritten text correction
- Multi-language documents

### 8. AI Enhancer Orchestrator

**Purpose**: Coordinates the entire AI enhancement process.

**Interface**:
```python
class AIEnhancerOrchestrator:
    async def enhance_ocr_result(
        self,
        ocr_result: Dict[str, Any],
        image_data: Optional[bytes] = None,
        document_type: str = "general"
    ) -> Dict[str, Any]:
        """Enhance complete OCR result"""
```

**Process**:
1. Receive OCR result from Docling
2. Determine document type
3. Select appropriate prompt template
4. Call AI Provider Manager
5. Validate AI response
6. Merge original and enhanced results
7. Return enriched result

### 9. Test Runner

**Purpose**: Automated testing system for OCR accuracy validation.

**Interface**:
```python
class OCRTestRunner:
    def run_tests(
        self,
        test_files: List[Path],
        providers: List[str] = ["all"]
    ) -> TestResults:
        """Run OCR tests on sample files"""
        
    def print_results(self, results: TestResults):
        """Print formatted test results"""
        
    def save_results(self, results: TestResults, output_path: Path):
        """Save results to file"""
```

## Data Models

### EnhancementResult

```python
@dataclass
class EnhancementResult:
    original_text: str
    enhanced_text: str
    provider_used: str
    model_used: str
    processing_time_ms: int
    token_usage: Optional[Dict[str, int]]
    confidence_score: float
    improvements: List[str]  # List of improvements made
    fallback_occurred: bool
    error: Optional[str]
```

### ProviderStatus

```python
@dataclass
class ProviderStatus:
    name: str
    available: bool
    last_check: datetime
    response_time_ms: Optional[int]
    error_message: Optional[str]
    supports_vision: bool
    rate_limit_remaining: Optional[int]
    quota_exceeded: bool  # True if free credits exhausted
    quota_reset_time: Optional[datetime]  # When quota resets
    unavailable_reason: Optional[str]  # "quota_exceeded", "rate_limit", "api_error", etc.
```

### ProviderConfig

```python
@dataclass
class ProviderConfig:
    name: str
    enabled: bool
    api_key: str
    base_url: str
    model: str
    vision_model: Optional[str]
    priority: int  # Lower number = higher priority
    timeout_seconds: int = 30
    max_retries: int = 2
```

### TestResult

```python
@dataclass
class TestResult:
    file_name: str
    provider: str
    original_text: str
    enhanced_text: str
    processing_time_ms: int
    character_count: int
    word_count: int
    accuracy_score: Optional[float]  # If ground truth available
    improvements_detected: List[str]
    timestamp: datetime
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Provider configuration loading
*For any* valid environment configuration, when the system starts, all configured providers should be loaded and their availability status should be determined.
**Validates: Requirements 1.1, 1.2**

### Property 2: Invalid configuration handling
*For any* provider with invalid configuration (missing API key, wrong URL), the system should mark it as unavailable and log a warning without crashing.
**Validates: Requirements 1.3**

### Property 3: Provider priority ordering
*For any* set of configured providers with priorities, the system should attempt to use them in ascending priority order (lower number first).
**Validates: Requirements 1.4**

### Property 4: AI enhancement request
*For any* OCR text output, when enhancement is requested, the system should send it to an available AI provider with appropriate prompts.
**Validates: Requirements 2.1, 2.2**

### Property 5: Response validation
*For any* AI provider response, the system should validate that it contains non-empty text before accepting it as enhanced output.
**Validates: Requirements 2.3**

### Property 6: Enhancement fallback
*For any* OCR result, if AI enhancement fails, the system should return the original OCR text unchanged.
**Validates: Requirements 2.4**

### Property 7: Dual output preservation
*For any* successful AI enhancement, the result should contain both the original OCR text and the enhanced text.
**Validates: Requirements 2.5**

### Property 8: Response parsing consistency
*For any* provider (Groq, DeepSeek, Gemini, Ollama), the system should successfully parse valid responses from that provider into text.
**Validates: Requirements 3.3, 4.3, 5.3**

### Property 9: Unified interface consistency
*For any* two different providers, calling the same enhancement method should use the same interface and return the same result structure.
**Validates: Requirements 6.1**

### Property 10: Automatic fallback
*For any* provider failure, if other providers are available, the system should automatically attempt the next provider in priority order.
**Validates: Requirements 6.2**

### Property 11: Provider caching
*For any* successful provider call, subsequent calls should prefer the same provider until it fails.
**Validates: Requirements 6.4**

### Property 12: Optional feature exposure
*For any* provider-specific feature (like vision), the system should expose it through optional parameters without breaking the base interface.
**Validates: Requirements 6.5**

### Property 13: Vision capability detection
*For any* provider that supports vision, when an image is provided, the system should use vision-based enhancement.
**Validates: Requirements 8.1**

### Property 14: Vision request format
*For any* vision-capable provider, the request should include both the image data and instructions for text extraction.
**Validates: Requirements 8.2**

### Property 15: Vision result comparison
*For any* document processed with vision, the system should compare vision results with traditional OCR results.
**Validates: Requirements 8.3**

### Property 16: Better result selection
*For any* vision analysis that produces higher confidence results, the system should use the vision-enhanced text over traditional OCR.
**Validates: Requirements 8.4**

### Property 17: Prompt template injection
*For any* OCR text and document type, the prompt manager should correctly inject the text into the appropriate template.
**Validates: Requirements 9.3**

### Property 18: Custom prompt precedence
*For any* prompt template, if a custom version exists, it should be used instead of the default.
**Validates: Requirements 9.4**

### Property 19: Provider call logging
*For any* AI provider call, the system should log the provider name, model, and timestamp.
**Validates: Requirements 10.1**

### Property 20: Error logging
*For any* provider failure, the system should log error details and the fallback action taken.
**Validates: Requirements 10.2**

### Property 21: Metrics logging
*For any* completed AI enhancement, the system should log processing time and token usage (if available).
**Validates: Requirements 10.3**

### Property 22: Rate limit warnings
*For any* provider approaching rate limits, the system should log warnings proactively.
**Validates: Requirements 10.4**

## Error Handling

### Provider Errors

1. **API Key Invalid**: Mark provider as unavailable, log warning, try next provider
2. **Rate Limit Exceeded (429)**: Detect rate limit error, mark provider as temporarily unavailable, automatically fallback to next provider
3. **Quota Exceeded (Free Credits Exhausted)**: Detect quota error (403/429), mark provider as unavailable for current session, fallback to next provider
4. **Network Timeout**: Retry up to max_retries, then fallback
5. **Invalid Response**: Log error, fallback to next provider
6. **All Providers Failed**: Return original OCR text with error metadata

### Automatic Provider Switching Logic

The system intelligently detects when a provider's free credits are exhausted:

1. **Error Detection**: Parse API error responses for:
   - HTTP 429 (Rate Limit)
   - HTTP 403 (Quota Exceeded)
   - Error messages containing "quota", "limit", "credits"

2. **Provider Marking**: When credits exhausted:
   - Mark provider as `unavailable` with reason `quota_exceeded`
   - Set cooldown period (e.g., 1 hour or until next day)
   - Log warning with provider name and timestamp

3. **Automatic Fallback**: Immediately try next provider in priority order:
   ```
   Groq (free credits exhausted) → DeepSeek → Gemini → Ollama
   ```

4. **Smart Recovery**: Periodically retry unavailable providers:
   - Check every hour if quota reset
   - Reset at midnight for daily quotas
   - Re-enable provider when successful

5. **User Notification**: Log clear messages:
   ```
   "Groq free credits exhausted, switching to DeepSeek"
   "DeepSeek quota exceeded, switching to Gemini"
   "All cloud providers exhausted, using local Ollama"
   ```

### Enhancement Errors

1. **Empty AI Response**: Treat as failure, fallback or return original
2. **Malformed Response**: Parse what's possible, log warning
3. **Response Too Short**: Validate minimum length, fallback if needed
4. **Response Language Mismatch**: Detect and handle language changes

### Vision Errors

1. **Image Too Large**: Resize or compress before sending
2. **Unsupported Format**: Convert or fallback to text-only
3. **Vision API Unavailable**: Fallback to text-only enhancement

## Testing Strategy

### Unit Tests

- Provider configuration loading and validation
- Prompt template rendering
- Response parsing for each provider
- Fallback logic
- Error handling for each error type

### Property-Based Tests

- Provider interface consistency across all providers
- Fallback chain correctness
- Prompt injection with various text inputs
- Response validation with random AI outputs
- Configuration precedence rules

### Integration Tests

- End-to-end OCR enhancement flow
- Multi-provider fallback scenarios
- Vision-based enhancement
- Custom prompt loading
- Metrics and logging

### Test Files

Create test suite with sample documents:
- `test_general.pdf` - General document
- `test_code.pdf` - Code document
- `test_handwritten.jpg` - Handwritten text
- `test_invoice.pdf` - Invoice/receipt
- `test_multilang.pdf` - Multi-language document

### Test Script

Create `test_ocr_enhancement.py` that:
1. Processes each test file through OCR
2. Enhances with each available provider
3. Prints original vs enhanced text
4. Calculates improvements
5. Saves results to timestamped file
6. Generates comparison report

## Performance Considerations

### Provider Selection Strategy

1. **Groq**: Use for speed-critical applications (fastest inference)
2. **DeepSeek**: Use for cost-sensitive applications (cheapest)
3. **Gemini**: Use for vision-heavy applications (best multimodal)
4. **Ollama**: Use for privacy/offline requirements (local)

### Caching Strategy

- Cache successful provider for session
- Cache prompt templates in memory
- Cache provider health status (5-minute TTL)

### Optimization

- Parallel provider health checks on startup
- Async API calls to providers
- Request batching where supported
- Response streaming for large documents

## Security Considerations

- Store API keys in environment variables only
- Never log API keys or full responses
- Validate and sanitize all inputs
- Implement rate limiting on client side
- Use HTTPS for all API calls
- Implement request timeouts
- Validate provider responses before use

## Monitoring and Observability

### Metrics to Track

- Provider success/failure rates
- Average response times per provider
- Token usage per provider
- Fallback frequency
- Enhancement quality scores
- API cost tracking

### Health Endpoint

```python
GET /api/health
{
  "ocr_service": "healthy",
  "ai_providers": {
    "groq": {"status": "available", "response_time_ms": 150},
    "deepseek": {"status": "available", "response_time_ms": 200},
    "gemini": {"status": "rate_limited", "response_time_ms": null},
    "ollama": {"status": "unavailable", "response_time_ms": null}
  },
  "active_provider": "groq",
  "total_enhancements_today": 1234
}
```

## Configuration Example

```env
# Provider Priority (lower = higher priority)
AI_PROVIDER_PRIORITY=groq:1,deepseek:2,gemini:3,ollama:4

# Groq Configuration
GROQ_API_KEY=gsk_xxxxx
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_VISION_MODEL=llama-3.2-90b-vision-preview

# DeepSeek Configuration
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_CODER_MODEL=deepseek-coder

# Gemini Configuration
GEMINI_API_KEY=AIzaSyxxxxx
GEMINI_MODEL=gemini-1.5-flash
GEMINI_PRO_MODEL=gemini-1.5-pro

# Ollama Configuration (existing)
OLLAMA_BASE_URL=http://localhost:11434/api
OLLAMA_LLM_MODEL=qwen2.5:7b
OLLAMA_VISION_MODEL=llava:7b

# Enhancement Settings
AI_ENHANCEMENT_ENABLED=true
AI_ENHANCEMENT_TIMEOUT=30
AI_ENHANCEMENT_MAX_RETRIES=2
AI_USE_VISION_WHEN_AVAILABLE=true

# Prompt Settings
CUSTOM_PROMPTS_PATH=./prompts
DEFAULT_DOCUMENT_TYPE=general
```

## Migration Path

1. **Phase 1**: Implement base provider interface and manager
2. **Phase 2**: Add Groq provider (fastest to implement)
3. **Phase 3**: Add DeepSeek provider
4. **Phase 4**: Add Gemini provider with vision
5. **Phase 5**: Enhance Ollama provider to match interface
6. **Phase 6**: Implement prompt manager
7. **Phase 7**: Create test suite and runner
8. **Phase 8**: Add monitoring and metrics

## Future Enhancements

- Support for more providers (Anthropic Claude, Cohere, etc.)
- Advanced prompt engineering with few-shot examples
- Fine-tuned models for specific document types
- Ensemble methods (combine multiple provider results)
- A/B testing framework for prompt optimization
- Cost optimization algorithms
- Real-time provider performance tracking

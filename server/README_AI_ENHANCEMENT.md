# 🤖 AI-Enhanced OCR System

Multi-provider AI system để cải thiện độ chính xác OCR với automatic fallback và quota detection.

## ✨ Features

- 🔄 **Multi-Provider Support**: ✅ Groq, ✅ DeepSeek, ✅ Google Gemini, ✅ Ollama (All Complete!)
- ⚡ **Automatic Fallback**: Tự động chuyển provider khi hết quota/credits
- 👁️ **Vision Enhancement**: Sử dụng vision models để phân tích ảnh trực tiếp (Groq, Gemini, Ollama)
- 🎯 **Smart Quota Detection**: Phát hiện khi free credits hết và chuyển đổi
- 📊 **Comprehensive Testing**: Test suite để validate kết quả
- 🔧 **Configurable Prompts**: Prompts tùy chỉnh cho từng loại document

## 🚀 Quick Start

### 1. Cài đặt Dependencies

```bash
cd RAG-Anything/server
pip install -r requirements.txt
```

### 2. Cấu hình API Keys

Copy `.env.example` thành `.env` và thêm API keys:

```bash
cp .env.example .env
```

Chỉnh sửa `.env`:
```env
# Groq (Free tier: 14,400 requests/day)
GROQ_API_KEY=gsk_your_groq_api_key_here

# DeepSeek (Cheapest: $0.27/1M tokens)  
DEEPSEEK_API_KEY=sk_your_deepseek_api_key_here

# Gemini (Free tier: 1500 requests/day)
GEMINI_API_KEY=AIzaSy_your_gemini_api_key_here

# Provider priority (lower = higher priority)
AI_PROVIDER_PRIORITY=groq:1,deepseek:2,gemini:3,ollama:4
```

### 3. Chạy Demo Test

```bash
# Demo với simulated data
python simple_test.py

# Test với real API (cần API keys)
python test_ocr_enhancement.py
```

## 📋 Test Results

Demo test sẽ hiển thị:

```
🧪 OCR Enhancement Demo
============================================================

📋 TEST 1/4: GROQ Provider
============================================================

🔤 ORIGINAL OCR TEXT:
----------------------------------------
Th1s 1s a sampl3 d0cument w1th 0CR err0rs.
Som3 l3tt3rs ar3 r3plac3d w1th numb3rs.

✨ ENHANCED TEXT:
----------------------------------------
This is a sample document with OCR errors.
Some letters are replaced with numbers.

📊 RESULTS:
🤖 Provider: groq
⏱️  Processing Time: 504ms
📏 Original Length: 192 chars
📏 Enhanced Length: 192 chars
🔧 Improvements:
  • Fixed number-letter substitutions
  • Added proper punctuation
```

## 🔄 Provider Fallback Flow

```
User Request → Groq (fastest)
                ↓ (if quota exceeded)
              DeepSeek (cheapest)
                ↓ (if quota exceeded)  
              Gemini (vision support)
                ↓ (if quota exceeded)
              Ollama (local, unlimited)
                ↓ (if all fail)
              Return Original Text
```

## 🎯 Supported Document Types

- **General**: Văn bản thông thường
- **Code**: Code và technical documentation
- **Invoice**: Hóa đơn, receipt
- **Form**: Biểu mẫu, forms
- **Handwritten**: Chữ viết tay

## 📊 Provider Comparison

| Provider | Speed | Cost | Free Tier | Vision | Best For |
|----------|-------|------|-----------|--------|----------|
| **Groq** | ⚡⚡⚡ | 💰💰 | 14.4K req/day | ✅ | Speed-critical |
| **DeepSeek** | ⚡⚡ | 💰 | Limited | ❌ | Cost-sensitive |
| **Gemini** | ⚡⚡ | 💰💰 | 1.5K req/day | ✅ | Vision-heavy |
| **Ollama** | ⚡ | Free | Unlimited | ✅ | Privacy/Offline |

## 🔧 Configuration Options

```env
# Enhancement Settings
AI_ENHANCEMENT_ENABLED=true
AI_ENHANCEMENT_TIMEOUT=30
AI_ENHANCEMENT_MAX_RETRIES=2
AI_USE_VISION_WHEN_AVAILABLE=true

# Provider Priority (lower number = higher priority)
AI_PROVIDER_PRIORITY=groq:1,deepseek:2,gemini:3,ollama:4

# Custom Prompts
CUSTOM_PROMPTS_PATH=./prompts
DEFAULT_DOCUMENT_TYPE=general
```

## 🧪 Testing

### Run All Tests
```bash
# Property tests
python -m pytest tests/ -v

# OCR enhancement tests
python test_ocr_enhancement.py

# Simple demo
python simple_test.py
```

### Test Specific Provider
```bash
python -c "
import asyncio
from app.core.ai_providers.groq_provider import GroqProvider

async def test():
    provider = GroqProvider('your_api_key', 'https://api.groq.com/openai/v1', 'llama-3.3-70b-versatile')
    result = await provider.chat_completion([{'role': 'user', 'content': 'Fix: Th1s 1s a t3st'}])
    print(result)

asyncio.run(test())
"
```

## 📈 Monitoring

Health check endpoint:
```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "ok": true,
  "ai_providers": {
    "groq": {"status": "available", "response_time_ms": 150},
    "deepseek": {"status": "quota_exceeded", "response_time_ms": null},
    "gemini": {"status": "available", "response_time_ms": 300},
    "ollama": {"status": "unavailable", "response_time_ms": null}
  },
  "active_provider": "groq"
}
```

## 🔍 Troubleshooting

### Common Issues

1. **"No available providers"**
   - Check API keys in `.env`
   - Verify internet connection
   - Check provider status

2. **"Quota exceeded"**
   - System automatically switches to next provider
   - Check logs for fallback messages
   - Wait for quota reset (usually 24h)

3. **"All providers failed"**
   - Returns original OCR text as fallback
   - Check logs for specific errors
   - Verify API keys are valid

### Debug Mode
```bash
export LOG_LEVEL=DEBUG
python test_ocr_enhancement.py
```

## 🚀 Integration

### Add to OCR Pipeline

```python
from app.core.ai_providers.provider_manager import AIProviderManager

# Initialize
manager = AIProviderManager()
await manager.initialize()

# Enhance OCR result
result = await manager.enhance_text(
    text=ocr_text,
    document_type="general",
    image_data=image_bytes  # Optional for vision
)

print(f"Original: {result.original_text}")
print(f"Enhanced: {result.enhanced_text}")
print(f"Provider: {result.provider_used}")
```

## 📝 API Keys Setup

### Groq (Recommended - Fastest)
1. Visit https://console.groq.com/
2. Create account → API Keys
3. Copy key: `gsk_...`

### DeepSeek (Cheapest)
1. Visit https://platform.deepseek.com/
2. Create account → API Keys  
3. Copy key: `sk_...`

### Google Gemini (Best Vision)
1. Visit https://ai.google.dev/
2. Get API Key
3. Copy key: `AIzaSy...`

### Ollama (Local - No Key Needed)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull qwen2.5:7b
ollama pull llava:7b
```

## 🎯 Next Steps

1. ✅ **Đã hoàn thành**: Multi-provider system với fallback
2. ✅ **Đã hoàn thành**: Test suite và demo
3. 🔄 **Đang phát triển**: Integration vào OCR pipeline
4. 📋 **Kế hoạch**: Fine-tuning cho Vietnamese text
5. 📋 **Kế hoạch**: Batch processing support

---

**🎉 Hệ thống đã sẵn sàng sử dụng!** 

Thêm API keys vào `.env` và chạy `python simple_test.py` để xem demo.
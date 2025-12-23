# Hỗ trợ Tiếng Việt / Vietnamese Support

## Tính năng

Hệ thống hỗ trợ xử lý tiếng Việt với các tính năng:

### 1. OCR Tiếng Việt có dấu
- Tự động nhận diện và xử lý tiếng Việt
- Thêm dấu tự động cho văn bản không dấu
- Chuẩn hóa văn bản tiếng Việt

### 2. Dịch ngôn ngữ
- Dịch từ tiếng Anh sang tiếng Việt
- Dịch từ tiếng Việt sang tiếng Anh
- Tự động phát hiện ngôn ngữ

### 3. Xử lý ảnh trong PDF
- Tự động OCR tất cả ảnh trong PDF
- Xử lý đệ quy các tài liệu phức tạp
- Hỗ trợ nhiều định dạng ảnh

## Cách sử dụng

### API Request

```json
{
  "file": "<file upload>",
  "settings": {
    "language": "vi",  // "vi" cho tiếng Việt, "en" cho tiếng Anh, "auto" tự động
    "parser": "docling",
    "preserveLayout": true,
    "returnLayout": true
  }
}
```

### Ví dụ với curl

```bash
curl -X POST "http://localhost:8000/api/ocr/extract?sync=true" \
  -F "file=@document.pdf" \
  -F 'settings_json={"language":"vi","parser":"docling"}'
```

### Ví dụ với Python

```python
import requests

url = "http://localhost:8000/api/ocr/extract?sync=true"

files = {
    'file': open('document.pdf', 'rb')
}

data = {
    'settings_json': '{"language":"vi","parser":"docling"}'
}

response = requests.post(url, files=files, data=data)
result = response.json()

print(result['result']['fullText'])  # Văn bản gốc
print(result['result']['enhancedText'])  # Văn bản đã cải thiện với AI
```

## Phương pháp xử lý

### 1. Sử dụng AI Models (Mặc định)
Hệ thống sử dụng các AI models để:
- Sửa lỗi OCR
- Thêm dấu tiếng Việt
- Dịch ngôn ngữ
- Cải thiện chất lượng văn bản

**Ưu điểm:**
- Chất lượng cao
- Hiểu ngữ cảnh
- Xử lý phức tạp

**Nhược điểm:**
- Cần API key
- Tốn thời gian hơn
- Phụ thuộc vào dịch vụ bên ngoài

**Providers hỗ trợ:**
- Groq (llama-3.3-70b-versatile)
- DeepSeek (deepseek-chat)
- Gemini (gemini-1.5-flash)
- Ollama (local, không cần API key)

### 2. Sử dụng thư viện Python (Bổ sung)

Cài đặt thư viện bổ sung:

```bash
# Thư viện NLP tiếng Việt
pip install underthesea

# OCR chuyên cho tiếng Việt (tùy chọn)
pip install vietocr

# Chuẩn hóa tiếng Việt (tùy chọn)
pip install vinorm
```

**Ưu điểm:**
- Không cần API key
- Xử lý nhanh
- Hoạt động offline

**Nhược điểm:**
- Chất lượng thấp hơn AI
- Không hiểu ngữ cảnh phức tạp
- Từ điển hạn chế

## Cấu hình

### Bật/tắt AI Enhancement

Trong file `.env`:

```bash
# Bật AI enhancement
AI_ENHANCEMENT_ENABLED=true

# Timeout (giây)
AI_ENHANCEMENT_TIMEOUT=30

# Số lần thử lại
AI_ENHANCEMENT_MAX_RETRIES=2

# Sử dụng vision khi có thể
AI_USE_VISION_WHEN_AVAILABLE=true
```

### Cấu hình AI Providers

```bash
# Groq (miễn phí, nhanh)
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# DeepSeek (rẻ, chất lượng tốt)
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_MODEL=deepseek-chat

# Gemini (Google, miễn phí tier)
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-flash

# Ollama (local, không cần API key)
OLLAMA_BASE_URL=http://localhost:11434/api
OLLAMA_LLM_MODEL=llama3.2:latest
```

## Xử lý ảnh trong PDF

Docling tự động xử lý:
- Ảnh nhúng trong PDF
- Ảnh trong bảng
- Ảnh trong header/footer
- Ảnh trong form

Không cần cấu hình thêm, chỉ cần:

```json
{
  "extract": {
    "images": true  // Bật xử lý ảnh
  }
}
```

## Kết quả trả về

```json
{
  "jobId": "xxx",
  "status": "done",
  "result": {
    "fullText": "Văn bản gốc từ OCR",
    "enhancedText": "Văn bản đã cải thiện với AI (có dấu, đã dịch)",
    "pages": [...],
    "layout": {...},
    "structured": {
      "tables": [...],
      "images": [...]
    },
    "aiMetadata": {
      "provider": "groq",
      "model": "llama-3.3-70b-versatile",
      "processingTimeMs": 5000,
      "targetLanguage": "vi",
      "improvements": [
        "Corrected spelling/grammar",
        "Added Vietnamese tone marks"
      ]
    }
  }
}
```

## Lưu ý

1. **Chất lượng OCR phụ thuộc vào:**
   - Chất lượng ảnh/PDF đầu vào
   - Font chữ sử dụng
   - Độ phân giải

2. **AI Enhancement:**
   - Tốn thời gian hơn (3-10 giây)
   - Cần API key
   - Có thể bị giới hạn quota

3. **Xử lý offline:**
   - Sử dụng Ollama (local)
   - Hoặc tắt AI enhancement
   - Chất lượng thấp hơn nhưng nhanh hơn

## Troubleshooting

### Không có dấu tiếng Việt

1. Kiểm tra `language` setting: `"language": "vi"`
2. Kiểm tra AI enhancement đã bật: `AI_ENHANCEMENT_ENABLED=true`
3. Kiểm tra API keys đã cấu hình

### Lỗi API key

1. Kiểm tra file `.env`
2. Restart server sau khi thay đổi
3. Thử provider khác hoặc dùng Ollama (local)

### Xử lý chậm

1. Giảm timeout: `AI_ENHANCEMENT_TIMEOUT=15`
2. Sử dụng Groq (nhanh nhất)
3. Tắt vision: `AI_USE_VISION_WHEN_AVAILABLE=false`
4. Xử lý async thay vì sync

## Ví dụ thực tế

### OCR ảnh tiếng Việt không dấu

Input: "Truong Dai hoc Bach Khoa Ha Noi"

Output với AI: "Trường Đại học Bách Khoa Hà Nội"

### Dịch từ tiếng Anh

Input (EN): "Hello, how are you?"

Output (VI): "Xin chào, bạn khỏe không?"

### Xử lý PDF phức tạp

- PDF có nhiều trang
- Có ảnh, bảng, biểu đồ
- Nhiều ngôn ngữ

→ Tất cả được xử lý tự động và trả về văn bản hoàn chỉnh

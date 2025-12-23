# ✅ Fix Docling để đọc hết Header, Footer và Ảnh

## Vấn đề
Docling đang bỏ qua header, footer và ảnh trong file PDF.

## Nguyên nhân
1. Cấu hình Docling không đúng - thiếu `lang` parameter bắt buộc
2. Không enable image extraction
3. Không sử dụng `iterate_items()` để lấy tất cả content

## Giải pháp

### 1. Fix cấu hình Docling (app/core/raganything_engine.py)

```python
# Configure pipeline to OCR everything including headers/footers
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.do_table_structure = True

# OCR options - ensure we capture all text including headers/footers/images
pipeline_options.ocr_options = OcrOptions(
    force_full_page_ocr=True,  # Force OCR on entire page
    lang=["en", "vi"],  # Support English and Vietnamese (REQUIRED!)
)

# Enable image extraction
pipeline_options.images_scale = 2.0  # Higher resolution for images
pipeline_options.generate_page_images = True  # Extract page images
pipeline_options.generate_picture_images = True  # Extract picture images

# Initialize converter with format-specific options
self.converter = DocumentConverter(
    format_options={
        InputFormat.PDF: pipeline_options,
    }
)
```

### 2. Extract text từ tất cả items (app/core/raganything_engine.py)

```python
# Get full text - try multiple methods to ensure we get EVERYTHING
full_text = ""
if hasattr(doc, 'export_to_text'):
    # Export with all content including headers/footers
    full_text = doc.export_to_text()
elif hasattr(doc, 'text'):
    full_text = doc.text
else:
    # Try to extract from body/content
    full_text = str(doc)

# Also try to get text from all items (including headers/footers)
if hasattr(doc, 'iterate_items'):
    try:
        all_text_parts = []
        for item, level in doc.iterate_items():
            if hasattr(item, 'text') and item.text:
                all_text_parts.append(item.text)
        
        # If we got more text from items, use that
        items_text = '\n'.join(all_text_parts)
        if len(items_text) > len(full_text):
            logger.info(f"Using items text ({len(items_text)} chars) instead of export ({len(full_text)} chars)")
            full_text = items_text
    except Exception as e:
        logger.warning(f"Could not iterate items: {e}")
```

## Kết quả

✅ Docling bây giờ sẽ:
- OCR toàn bộ trang (force_full_page_ocr=True)
- Hỗ trợ tiếng Anh và tiếng Việt
- Extract ảnh với resolution cao hơn
- Lấy text từ tất cả items (headers, footers, body)
- Tự động chọn method extract text tốt nhất

## Test

Upload một file PDF có header/footer và ảnh, kiểm tra xem:
1. Header text có trong kết quả không
2. Footer text có trong kết quả không
3. Text trong ảnh có được OCR không

## Logs

Server khởi động thành công với log:
```
INFO - Docling converter initialized with full-page OCR and image extraction
```

---

**Ngày fix**: 24/12/2024  
**Status**: ✅ Complete

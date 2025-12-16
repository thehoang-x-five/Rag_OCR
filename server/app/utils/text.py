"""
Text processing utilities
"""
import json
import re
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
        
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def preserve_layout_text(text: str) -> str:
    """Preserve text layout with proper spacing"""
    if not text:
        return ""
        
    # Preserve line breaks and indentation
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Keep leading whitespace for indentation
        cleaned_line = line.rstrip()
        cleaned_lines.append(cleaned_line)
        
    return '\n'.join(cleaned_lines)


def text_to_markdown(text: str, title: Optional[str] = None) -> str:
    """Convert plain text to markdown format"""
    if not text:
        return ""
        
    markdown = ""
    
    if title:
        markdown += f"# {title}\n\n"
        
    # Split into paragraphs
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        if paragraph.strip():
            markdown += f"{paragraph.strip()}\n\n"
            
    return markdown.strip()


def extract_metadata_from_text(text: str) -> Dict[str, Any]:
    """Extract metadata from text content"""
    if not text:
        return {}
        
    word_count = len(text.split())
    char_count = len(text)
    line_count = len(text.split('\n'))
    
    # Detect language (simple heuristic)
    vietnamese_chars = len(re.findall(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', text.lower()))
    language = "vi" if vietnamese_chars > word_count * 0.1 else "en"
    
    return {
        "wordCount": word_count,
        "charCount": char_count,
        "lineCount": line_count,
        "detectedLanguage": language,
        "hasVietnamese": vietnamese_chars > 0
    }


def format_confidence_score(confidence: float) -> float:
    """Format confidence score to 2 decimal places"""
    return round(confidence, 2)


def split_text_by_pages(text: str, max_chars_per_page: int = 2000) -> list:
    """Split text into pages based on character count"""
    if not text:
        return []
        
    pages = []
    current_page = ""
    
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        if len(current_page) + len(paragraph) > max_chars_per_page and current_page:
            pages.append(current_page.strip())
            current_page = paragraph
        else:
            if current_page:
                current_page += '\n\n' + paragraph
            else:
                current_page = paragraph
                
    if current_page:
        pages.append(current_page.strip())
        
    return pages


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "untitled"
        
    return filename


def create_text_summary(text: str, max_length: int = 200) -> str:
    """Create a summary of text content"""
    if not text:
        return ""
        
    if len(text) <= max_length:
        return text
        
    # Find a good breaking point
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If we can find a space in the last 20%
        truncated = truncated[:last_space]
        
    return truncated + "..."
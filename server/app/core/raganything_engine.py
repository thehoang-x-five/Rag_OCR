"""
Document processing engine using Docling
"""
import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from app.core.config import settings
from app.core.jobs import job_store, JobStatus, JobStep

logger = logging.getLogger(__name__)

# Try to import docling
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logger.warning("Docling not available. Using simulation mode.")


class DocumentEngine:
    def __init__(self):
        self.converter = None
        if DOCLING_AVAILABLE:
            try:
                self.converter = DocumentConverter()
                logger.info("Docling converter initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Docling converter: {e}")
        
    async def process_document(
        self,
        job_id: str,
        file_path: Path,
        settings_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process document with Docling or simulation"""
        start_time = time.time()
        
        try:
            # Update job status
            job_store.update_job(job_id, status=JobStatus.RUNNING, step=JobStep.PREPROCESS, 
                               percent=10, message="Preprocessing document...")
            
            parser = settings_dict.get("parser", settings.DEFAULT_PARSER)
            
            # Update job status
            job_store.update_job(job_id, step=JobStep.PARSE, percent=30, 
                               message=f"Parsing with {parser}...")
            
            parse_time_start = time.time()
            
            # Check file type
            file_ext = file_path.suffix.lower()
            text_extensions = ['.txt', '.md', '.csv', '.json', '.xml', '.html']
            
            # Try to use Docling if available for non-text files
            if file_ext in text_extensions:
                # Direct text file processing
                result = await self._process_text_file(job_id, file_path, settings_dict)
            elif DOCLING_AVAILABLE and self.converter:
                try:
                    result = await self._process_with_docling(job_id, file_path, settings_dict)
                except Exception as e:
                    logger.error(f"Docling processing failed: {e}")
                    # For text files, try direct reading as fallback
                    if file_ext in text_extensions:
                        result = await self._process_text_file(job_id, file_path, settings_dict)
                    else:
                        raise ValueError(f"OCR processing failed: {str(e)}")
            else:
                raise ValueError(
                    f"Cannot process {file_ext} files. Docling OCR engine is not available. "
                    f"Please install Docling: pip install docling"
                )
            
            parse_time = int((time.time() - parse_time_start) * 1000)
            
            # Update timings
            if "result" in result and "meta" in result["result"]:
                result["result"]["meta"]["timings"]["parseMs"] = parse_time
            
            # Update job as done
            job_store.update_job(job_id, status=JobStatus.DONE, step=JobStep.DONE, 
                               percent=100, message="Processing complete", result=result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing document for job {job_id}: {e}", exc_info=True)
            job_store.update_job(job_id, status=JobStatus.ERROR, 
                               message=f"Processing failed: {str(e)}", error=str(e))
            raise

    async def _process_with_docling(
        self,
        job_id: str,
        file_path: Path,
        settings_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process document using Docling"""
        
        # Update progress
        job_store.update_job(job_id, step=JobStep.PARSE, percent=40, 
                           message="Converting document with Docling...")
        
        logger.info(f"Starting Docling conversion for: {file_path}")
        
        # Run Docling conversion in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: self.converter.convert(str(file_path))
        )
        
        logger.info(f"Docling conversion completed, extracting content...")
        
        # Update progress
        job_store.update_job(job_id, step=JobStep.POSTPROCESS, percent=80, 
                           message="Building output...")
        
        # Extract text and structure from Docling result
        doc = result.document
        
        # Get full text - try multiple methods
        full_text = ""
        if hasattr(doc, 'export_to_text'):
            full_text = doc.export_to_text()
        elif hasattr(doc, 'text'):
            full_text = doc.text
        else:
            # Try to extract from body/content
            full_text = str(doc)
        
        logger.info(f"Extracted text length: {len(full_text)} chars")
        
        # Get markdown
        markdown_text = ""
        if hasattr(doc, 'export_to_markdown'):
            markdown_text = doc.export_to_markdown()
        else:
            markdown_text = full_text
        
        # Build pages - try to get page-level content
        pages = []
        page_count = 1
        
        # Try different ways to get pages
        if hasattr(doc, 'pages') and doc.pages:
            page_count = len(doc.pages)
            for i, page in enumerate(doc.pages):
                page_text = ""
                if hasattr(page, 'export_to_text'):
                    page_text = page.export_to_text()
                elif hasattr(page, 'text'):
                    page_text = page.text
                else:
                    page_text = str(page)
                pages.append({
                    "page": i + 1,
                    "text": page_text,
                    "confidence": 0.95
                })
        elif hasattr(doc, 'num_pages'):
            page_count = doc.num_pages
            # Split text evenly across pages as fallback
            if page_count > 1:
                lines = full_text.split('\n')
                lines_per_page = max(1, len(lines) // page_count)
                for i in range(page_count):
                    start = i * lines_per_page
                    end = start + lines_per_page if i < page_count - 1 else len(lines)
                    page_text = '\n'.join(lines[start:end])
                    pages.append({
                        "page": i + 1,
                        "text": page_text,
                        "confidence": 0.95
                    })
            else:
                pages = [{"page": 1, "text": full_text, "confidence": 0.95}]
        else:
            pages = [{"page": 1, "text": full_text, "confidence": 0.95}]
        
        logger.info(f"Extracted {len(pages)} pages")
        
        # Build structured data
        tables = []
        if hasattr(doc, 'tables') and doc.tables:
            for i, table in enumerate(doc.tables):
                table_data = str(table)
                if hasattr(table, 'export_to_dataframe'):
                    try:
                        df = table.export_to_dataframe()
                        table_data = df.to_string()
                    except:
                        pass
                tables.append({
                    "id": f"table-{i+1}",
                    "name": f"Table {i+1}",
                    "data": table_data
                })
        
        # Build layout with actual bounding boxes from Docling
        layout_pages = self._extract_layout_from_docling(doc, pages, full_text)
        
        return {
            "jobId": job_id,
            "status": "done",
            "result": {
                "fullText": full_text,
                "markdownText": markdown_text,
                "layoutText": full_text,
                "pages": pages,
                "structured": {
                    "tables": tables,
                    "equations": [],
                    "images": []
                },
                "layout": {
                    "pages": layout_pages
                },
                "meta": {
                    "parser": "docling",
                    "parse_method": settings_dict.get("parse_method", "auto"),
                    "language": settings_dict.get("language", "auto"),
                    "pageCount": len(pages),
                    "avgConfidence": 0.95,
                    "timings": {
                        "parseMs": 0,
                        "postMs": 100
                    }
                }
            },
            "error": None
        }

    def _extract_layout_from_docling(
        self,
        doc: Any,
        pages: List[Dict],
        full_text: str
    ) -> List[Dict[str, Any]]:
        """Extract detailed layout with bounding boxes from Docling document"""
        layout_pages = []
        
        try:
            # Try to get document items with bounding boxes
            doc_items = []
            page_dimensions = {}
            
            # Method 1: Try to get items from document body
            if hasattr(doc, 'body') and doc.body:
                for item in doc.body:
                    doc_items.append(item)
            
            # Method 2: Try iterate_items method
            if not doc_items and hasattr(doc, 'iterate_items'):
                try:
                    for item, level in doc.iterate_items():
                        doc_items.append(item)
                except:
                    pass
            
            # Method 3: Try to get from pages directly
            if hasattr(doc, 'pages') and doc.pages:
                for page_no, page in enumerate(doc.pages):
                    page_num = page_no + 1
                    page_width = getattr(page, 'width', 1.0) or 1.0
                    page_height = getattr(page, 'height', 1.414) or 1.414
                    page_dimensions[page_num] = (page_width, page_height)
                    
                    # Try to get items from page
                    if hasattr(page, 'items'):
                        for item in page.items:
                            if not hasattr(item, 'page_no'):
                                item.page_no = page_num
                            doc_items.append(item)
            
            # Group items by page
            items_by_page = {}
            for item in doc_items:
                page_no = getattr(item, 'page_no', 1) or 1
                if page_no not in items_by_page:
                    items_by_page[page_no] = []
                items_by_page[page_no].append(item)
            
            # Build layout pages
            num_pages = max(len(pages), max(items_by_page.keys()) if items_by_page else 1)
            
            for page_num in range(1, num_pages + 1):
                page_width, page_height = page_dimensions.get(page_num, (1.0, 1.414))
                
                blocks = []
                page_items = items_by_page.get(page_num, [])
                
                for idx, item in enumerate(page_items):
                    # Extract text
                    item_text = ""
                    if hasattr(item, 'text'):
                        item_text = item.text
                    elif hasattr(item, 'export_to_text'):
                        item_text = item.export_to_text()
                    else:
                        item_text = str(item)
                    
                    if not item_text or not item_text.strip():
                        continue
                    
                    # Extract bounding box
                    bbox = self._extract_bbox(item, page_width, page_height)
                    
                    # Determine block type
                    block_type = "text"
                    if hasattr(item, 'label'):
                        label = str(item.label).lower()
                        if 'table' in label:
                            block_type = "table"
                        elif 'figure' in label or 'image' in label:
                            block_type = "image"
                        elif 'title' in label or 'heading' in label:
                            block_type = "heading"
                        elif 'list' in label:
                            block_type = "list"
                    
                    # Build lines from text
                    lines = self._build_lines_from_text(item_text, bbox)
                    
                    blocks.append({
                        "type": block_type,
                        "text": item_text,
                        "bbox": bbox,
                        "confidence": 0.95,
                        "lines": lines
                    })
                
                # If no blocks extracted, create from page text
                if not blocks and page_num <= len(pages):
                    page_text = pages[page_num - 1].get("text", "")
                    if page_text:
                        lines = self._build_lines_from_text(page_text, {"x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9})
                        blocks.append({
                            "type": "text",
                            "text": page_text,
                            "bbox": {"x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9},
                            "confidence": 0.95,
                            "lines": lines
                        })
                
                layout_pages.append({
                    "page": page_num,
                    "width": 1.0,
                    "height": page_height / page_width if page_width else 1.414,
                    "blocks": blocks
                })
            
            logger.info(f"Extracted layout: {len(layout_pages)} pages, {sum(len(p['blocks']) for p in layout_pages)} blocks")
            
        except Exception as e:
            logger.warning(f"Failed to extract detailed layout: {e}, using fallback")
            # Fallback to simple layout
            for i, page_data in enumerate(pages):
                page_text = page_data.get("text", "")
                lines = self._build_lines_from_text(page_text, {"x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9})
                layout_pages.append({
                    "page": i + 1,
                    "width": 1.0,
                    "height": 1.414,
                    "blocks": [{
                        "type": "text",
                        "text": page_text,
                        "bbox": {"x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9},
                        "confidence": 0.95,
                        "lines": lines
                    }]
                })
        
        return layout_pages
    
    def _extract_bbox(self, item: Any, page_width: float, page_height: float) -> Dict[str, float]:
        """Extract normalized bounding box from Docling item"""
        try:
            # Try different bbox attributes
            bbox = None
            
            if hasattr(item, 'prov') and item.prov:
                # Docling provenance contains bbox info
                for prov in item.prov:
                    if hasattr(prov, 'bbox'):
                        bbox = prov.bbox
                        break
            
            if not bbox and hasattr(item, 'bbox'):
                bbox = item.bbox
            
            if not bbox and hasattr(item, 'bounding_box'):
                bbox = item.bounding_box
            
            if bbox:
                # Normalize coordinates to 0-1 range
                if hasattr(bbox, 'l'):  # Docling BoundingBox format
                    x = bbox.l / page_width if page_width else bbox.l
                    y = bbox.t / page_height if page_height else bbox.t
                    w = (bbox.r - bbox.l) / page_width if page_width else (bbox.r - bbox.l)
                    h = (bbox.b - bbox.t) / page_height if page_height else (bbox.b - bbox.t)
                elif isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                    x = bbox[0] / page_width if page_width else bbox[0]
                    y = bbox[1] / page_height if page_height else bbox[1]
                    w = (bbox[2] - bbox[0]) / page_width if page_width else (bbox[2] - bbox[0])
                    h = (bbox[3] - bbox[1]) / page_height if page_height else (bbox[3] - bbox[1])
                elif hasattr(bbox, 'x'):
                    x = bbox.x / page_width if page_width else bbox.x
                    y = bbox.y / page_height if page_height else bbox.y
                    w = bbox.width / page_width if page_width and hasattr(bbox, 'width') else 0.9
                    h = bbox.height / page_height if page_height and hasattr(bbox, 'height') else 0.05
                else:
                    return {"x": 0.05, "y": 0.05, "w": 0.9, "h": 0.1}
                
                # Clamp values to valid range
                x = max(0, min(1, x))
                y = max(0, min(1, y))
                w = max(0.01, min(1 - x, w))
                h = max(0.01, min(1 - y, h))
                
                return {"x": x, "y": y, "w": w, "h": h}
        except Exception as e:
            logger.debug(f"Failed to extract bbox: {e}")
        
        return {"x": 0.05, "y": 0.05, "w": 0.9, "h": 0.1}
    
    def _build_lines_from_text(self, text: str, parent_bbox: Dict[str, float]) -> List[Dict[str, Any]]:
        """Build line-level layout from text content"""
        lines = []
        text_lines = text.split('\n')
        
        if not text_lines:
            return lines
        
        line_height = min(0.04, parent_bbox["h"] / max(len(text_lines), 1))
        line_gap = 0.01
        
        for idx, line_text in enumerate(text_lines):
            if not line_text.strip():
                continue
            
            y = parent_bbox["y"] + idx * (line_height + line_gap)
            if y + line_height > parent_bbox["y"] + parent_bbox["h"]:
                break
            
            # Build words
            words = []
            word_list = line_text.split()
            if word_list:
                word_width = min(0.15, parent_bbox["w"] / max(len(word_list), 1))
                x_cursor = parent_bbox["x"]
                
                for word_text in word_list:
                    # Estimate word width based on character count
                    estimated_width = min(word_width * (len(word_text) / 5), parent_bbox["w"] - (x_cursor - parent_bbox["x"]))
                    
                    words.append({
                        "text": word_text,
                        "bbox": {
                            "x": x_cursor,
                            "y": y,
                            "w": estimated_width,
                            "h": line_height
                        },
                        "confidence": 0.95
                    })
                    x_cursor += estimated_width + 0.01
            
            lines.append({
                "text": line_text,
                "confidence": 0.95,
                "bbox": {
                    "x": parent_bbox["x"],
                    "y": y,
                    "w": parent_bbox["w"],
                    "h": line_height
                },
                "words": words
            })
        
        return lines

    async def _process_text_file(
        self,
        job_id: str,
        file_path: Path,
        settings_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process plain text files directly"""
        
        # Update progress
        job_store.update_job(job_id, step=JobStep.PARSE, percent=50, 
                           message="Reading text file...")
        
        # Read file content
        full_text = ""
        file_ext = file_path.suffix.lower()
        
        if file_ext in ['.txt', '.md', '.csv', '.json', '.xml', '.html']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    full_text = f.read()
            except UnicodeDecodeError:
                # Try with different encoding
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        full_text = f.read()
                except Exception as e:
                    logger.error(f"Could not read text file: {e}")
                    raise ValueError(f"Could not read file: {file_path.name}")
            except Exception as e:
                logger.error(f"Could not read text file: {e}")
                raise ValueError(f"Could not read file: {file_path.name}")
        else:
            # For non-text files without Docling, raise error
            raise ValueError(
                f"Cannot process {file_ext} files. Docling OCR engine failed or is not available. "
                f"Please ensure Docling is properly installed: pip install docling"
            )
        
        # Update progress
        job_store.update_job(job_id, step=JobStep.POSTPROCESS, percent=80, 
                           message="Building output...")
        
        markdown_text = f"# {file_path.stem}\n\n{full_text}"
        
        pages = [{
            "page": 1,
            "text": full_text,
            "confidence": 1.0
        }]
        
        # Build layout with lines for text files
        block_bbox = {"x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9}
        lines = self._build_lines_from_text(full_text, block_bbox)
        
        return {
            "jobId": job_id,
            "status": "done",
            "result": {
                "fullText": full_text,
                "markdownText": markdown_text,
                "layoutText": full_text,
                "pages": pages,
                "structured": {
                    "tables": [],
                    "equations": [],
                    "images": []
                },
                "layout": {
                    "pages": [{
                        "page": 1,
                        "width": 1.0,
                        "height": 1.414,
                        "blocks": [{
                            "type": "text",
                            "text": full_text,
                            "bbox": block_bbox,
                            "confidence": 1.0,
                            "lines": lines
                        }]
                    }]
                },
                "meta": {
                    "parser": "text-reader",
                    "parse_method": "direct",
                    "language": settings_dict.get("language", "auto"),
                    "pageCount": 1,
                    "avgConfidence": 1.0,
                    "timings": {
                        "parseMs": 10,
                        "postMs": 10
                    }
                }
            },
            "error": None
        }


# Global engine instance
rag_engine = DocumentEngine()
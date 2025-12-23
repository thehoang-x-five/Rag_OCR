with open('app/core/raganything_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with rag_engine = DocumentEngine()
idx = next(i for i, line in enumerate(lines) if 'rag_engine = DocumentEngine()' in line)

# Insert the method before the global instance
method_code = '''
    def _detect_document_type(self, file_path: Path, text: str) -> str:
        """
        Detect document type for appropriate prompt selection
        
        Args:
            file_path: Path to the document
            text: Extracted text content
            
        Returns:
            Document type (general, code, invoice, form, handwritten)
        """
        filename = file_path.name.lower()
        text_lower = text.lower()
        
        # Check for code documents
        code_indicators = ['def ', 'function ', 'class ', 'import ', 'const ', 'var ', 'let ', '#!/']
        code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']
        
        if any(ext in filename for ext in code_extensions) or any(ind in text for ind in code_indicators):
            return "code"
        
        # Check for invoices/receipts
        invoice_indicators = ['invoice', 'receipt', 'total', 'tax', 'amount', 'payment']
        if any(ind in text_lower for ind in invoice_indicators) and any(ind in filename for ind in ['invoice', 'receipt']):
            return "invoice"
        
        # Check for forms
        form_indicators = ['form', 'application', 'name:', 'date:', 'signature']
        if any(ind in text_lower for ind in form_indicators) and 'form' in filename:
            return "form"
        
        # Check for handwritten (usually from image files with certain patterns)
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png'] and len(text) < 500:
            return "handwritten"
        
        return "general"

'''

# Insert before the "# Global engine instance" line
new_lines = lines[:idx-1] + [method_code] + lines[idx-1:]

with open('app/core/raganything_engine.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Method added successfully!")

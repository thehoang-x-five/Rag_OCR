#!/usr/bin/env python3
"""
Quick test runner for OCR enhancement
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the server directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables for testing (if not already set)
if not os.getenv('GROQ_API_KEY'):
    os.environ['GROQ_API_KEY'] = 'test_key'  # Will fail gracefully
if not os.getenv('AI_ENHANCEMENT_ENABLED'):
    os.environ['AI_ENHANCEMENT_ENABLED'] = 'true'

from test_ocr_enhancement import main

if __name__ == "__main__":
    print("🚀 Running OCR Enhancement Test")
    print("Note: Add real API keys to .env file for actual testing")
    print("="*60)
    
    asyncio.run(main())
#!/usr/bin/env python3
"""
Check if enhancedText is in the response
"""
import requests
import json

# Test with a simple text file
url = "http://localhost:8000/api/ocr/extract?sync=true"

# Create a test file
test_content = "Truong Dai hoc Bach Khoa Ha Noi"
files = {
    'file': ('test.txt', test_content.encode('utf-8'), 'text/plain')
}

data = {
    'settings_json': json.dumps({
        'language': 'vi',
        'parser': 'docling'
    })
}

print("Sending request...")
response = requests.post(url, files=files, data=data)

print(f"Status: {response.status_code}")
print(f"Response keys: {response.json().keys()}")

result = response.json()
if 'result' in result:
    print(f"\nResult keys: {result['result'].keys()}")
    print(f"\nHas fullText: {'fullText' in result['result']}")
    print(f"Has enhancedText: {'enhancedText' in result['result']}")
    
    if 'fullText' in result['result']:
        print(f"\nfullText: {result['result']['fullText'][:200]}")
    
    if 'enhancedText' in result['result']:
        print(f"\nenhancedText: {result['result']['enhancedText'][:200]}")
    else:
        print("\n❌ NO ENHANCED TEXT!")
    
    if 'aiMetadata' in result['result']:
        print(f"\nAI Metadata: {result['result']['aiMetadata']}")
else:
    print("No result in response!")
    print(json.dumps(result, indent=2))

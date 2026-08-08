import os

path = r"c:\Users\tirum\OneDrive\Desktop\myapp\backend\main.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace all occurrences of max_tokens=4500 with the response_format injection
# First, ensure we don't accidentally do it twice
if 'response_format={"type": "json_object"}' not in content:
    content = content.replace(
        "max_tokens=4500", 
        'max_tokens=4500,\n            response_format={"type": "json_object"}'
    )
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Injected JSON mode successfully.")
else:
    print("JSON mode already injected.")

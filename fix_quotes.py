import os
import glob
import re

frontend_dir = r"c:\Users\tirum\OneDrive\Desktop\myapp\frontend"
html_files = glob.glob(os.path.join(frontend_dir, "*.html"))

for file_path in html_files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Fix onclick="window.location.href="/page.html"" -> onclick="window.location.href='./page.html'"
    # Regex to find onclick="window.location.href="/(.*?)\.html""
    
    new_content = re.sub(r'onclick="window\.location\.href="(/.*?)""', r"onclick=\"window.location.href='.\1'\"", content)
    
    # Also catch onclick="window.location.href="./page.html""
    new_content = re.sub(r'onclick="window\.location\.href="(\./.*?)""', r"onclick=\"window.location.href='\1'\"", new_content)
    
    # Also catch just any path with .html or similar
    new_content = re.sub(r'onclick="window\.location\.href="(.*?)""', r"onclick=\"window.location.href='\1'\"", new_content)


    if content != new_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed onclick quotes in {os.path.basename(file_path)}")

print("Done fixing quotes.")

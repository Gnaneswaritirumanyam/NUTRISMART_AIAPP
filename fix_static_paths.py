import os
import glob

frontend_dir = r"c:\Users\tirum\OneDrive\Desktop\myapp\frontend"
html_files = glob.glob(os.path.join(frontend_dir, "*.html"))

for file_path in html_files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace static/images/ with ./images/
    # Also catch /static/images/ and replace with ./images/
    new_content = content.replace('"static/images/', '"./images/')
    new_content = new_content.replace('"/static/images/', '"./images/')
    
    new_content = new_content.replace("'static/images/", "'./images/")
    new_content = new_content.replace("'/static/images/", "'./images/")
    
    # Also replace just static/ with ./ if it points to other assets
    new_content = new_content.replace('"static/videos/', '"./videos/')
    new_content = new_content.replace('"/static/videos/', '"./videos/')
    
    new_content = new_content.replace('"static/css/', '"./css/')
    new_content = new_content.replace('"/static/css/', '"./css/')

    if content != new_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed paths in {os.path.basename(file_path)}")
print("Done fixing static paths.")

import os

frontend_dir = r"c:\Users\tirum\OneDrive\Desktop\myapp\frontend"
file_path = os.path.join(frontend_dir, "budget.html")

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace literal backslashes followed by quote
new_content = content.replace(r'onclick=\"', 'onclick="')
new_content = new_content.replace(r'html\'\">', r'html\'">')
new_content = new_content.replace(r'nutri\'\">', r'nutri\'">')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
    
print("Fixed backslashes in budget.html")

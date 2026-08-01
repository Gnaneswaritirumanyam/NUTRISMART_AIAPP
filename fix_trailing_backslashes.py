import os

frontend_dir = r"c:\Users\tirum\OneDrive\Desktop\myapp\frontend"
file_path = os.path.join(frontend_dir, "budget.html")

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace trailing \">
new_content = content.replace("html'\\\">", "html'\">")
new_content = new_content.replace("nutri'\\\">", "nutri'\">")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
    
print("Fixed trailing backslashes in budget.html")

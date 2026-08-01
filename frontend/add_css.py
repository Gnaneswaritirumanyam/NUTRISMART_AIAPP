import os

css_to_add = """
@media (max-width: 768px) {
    .dashboard {
        grid-template-columns: 1fr !important;
        margin-left: 0 !important;
    }
    .panel {
        margin-right: 0 !important;
        margin-bottom: 20px !important;
    }
    .modal-content {
        width: 95% !important;
        padding: 15px !important;
    }
    .container {
        padding: 10px !important;
    }
}
"""

files = ['budgetbased.html', 'nutri.html', 'health.html', 'gain.html', 'loss.html', 'fitness.html', 'meal.html']

base_dir = r"c:\Users\tirum\OneDrive\Desktop\myapp\frontend"

for f in files:
    path = os.path.join(base_dir, f)
    if not os.path.exists(path):
        print(f"Not found: {f}")
        continue
    
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if css_to_add.strip() in content:
        print(f"Already added to {f}")
        continue
        
    new_content = content.replace("</style>", css_to_add + "\n</style>")
    
    with open(path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    print(f"Updated {f}")

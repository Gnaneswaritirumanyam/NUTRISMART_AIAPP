import os
import re

directory = r'c:\Users\tirum\AndroidStudioProjects\NutrismartAI\app\src\main\assets\www'

for filename in os.listdir(directory):
    if filename.endswith('.html'):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        old_css = r'\.recipe-modal-content\s*\{[^}]*\}'
        new_css = '''.recipe-modal-content {
    background: white;
    width: 90%;
    max-width: 650px;
    min-height: 50vh;
    max-height: 85vh;
    overflow-y: auto;
    padding: 30px;
    border-radius: 20px;
    position: relative;
    display: flex;
    flex-direction: column;
}'''
        content = re.sub(old_css, new_css, content)

        old_div = r'<div id="recipeContent"[^>]*>'
        new_div = '<div id="recipeContent" style="color: #000 !important; flex: 1; margin-top: 25px; height: auto;">'
        content = re.sub(old_div, new_div, content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
print('Done')

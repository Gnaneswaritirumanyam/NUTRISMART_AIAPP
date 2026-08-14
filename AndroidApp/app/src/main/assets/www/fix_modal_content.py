import os
import re

directory = r'c:\Users\tirum\AndroidStudioProjects\NutrismartAI\app\src\main\assets\www'

for filename in os.listdir(directory):
    if filename.endswith('.html'):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find .modal-content { and add min-height and flex properties inside it.
        # Ensure we only modify the main .modal-content, not the @media one.
        # We can look for .modal-content { background: ... or just replace the first occurrence.
        
        # A robust way is to replace .modal-content { with .modal-content { min-height: 50vh; display: flex; flex-direction: column;
        # But we don't want to duplicate it if we run it twice.
        
        if 'min-height: 50vh' not in content and '.modal-content' in content:
            # We'll use a regex that finds the first .modal-content { and adds the properties
            # .modal-content { ...
            def replacer(match):
                inner = match.group(1)
                return '.modal-content {' + inner + '\n    min-height: 50vh;\n    display: flex;\n    flex-direction: column;'
            
            content = re.sub(r'\.modal-content\s*\{([^}]*)\}', replacer, content, count=1)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
print('Done')

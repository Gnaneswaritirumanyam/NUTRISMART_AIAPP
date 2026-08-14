import os

d = r'c:\Users\tirum\AndroidStudioProjects\NutrismartAI\app\src\main\assets\www'

for f in os.listdir(d):
    if f.endswith('.html') or f.endswith('.js'):
        path = os.path.join(d, f)
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Replace absolute /recipe.html with relative ./recipe.html
        new_content = content.replace('`/recipe.html', '`./recipe.html')
        new_content = new_content.replace('\'/recipe.html', '\'./recipe.html')
        new_content = new_content.replace('"/recipe.html', '"./recipe.html')
        
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f"Fixed paths in {f}")

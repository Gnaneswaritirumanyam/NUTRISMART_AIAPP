import os
import re

files_to_update = [
    'budgetbased.html',
    'fitness.html',
    'gain.html',
    'loss.html',
    'meal.html'
]

base_dir = r'c:\Users\tirum\AndroidStudioProjects\NutrismartAI\app\src\main\assets\www'

replacement_body = """async function disableNotifications() {
    await window.planManager.disableActivePlan();
    
    // Clear all possible plan containers
    const idsToClear = ['recipeContainer', 'mealContainer', 'planContainer', 'dayGrid', 'cuisineGrid', 'recipeGrid'];
    idsToClear.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '';
    });
    
    const charts = document.querySelector('.charts');
    if (charts) charts.style.display = 'none';

    const notificationSection = document.getElementById('notificationSection');
    if (notificationSection) notificationSection.style.display = 'none';
    
    const feedbackBox = document.getElementById('feedbackBox');
    if (feedbackBox) feedbackBox.style.display = 'none';
    
    // Remove from local storage
    if (typeof PLAN_KEY !== 'undefined') localStorage.removeItem(PLAN_KEY);
    
    // Reset fields
    document.querySelectorAll('input:not([id*="Time"]), select, textarea').forEach(el => el.value = '');
}"""

for filename in files_to_update:
    filepath = os.path.join(base_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace disableNotifications
    # Note: this regex finds 'async function disableNotifications() {' followed by everything until the first matching '}'
    # But since the original disableNotifications is just a 3 liner in most files, we can just replace it safely.
    content = re.sub(r'async function disableNotifications\(\)\s*\{[^}]*\}', replacement_body, content, count=1)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
print('Updated 5 plans.')

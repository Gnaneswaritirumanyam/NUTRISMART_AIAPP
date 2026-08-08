import os
import re

files = [
    "health.html", "loss.html", "gain.html", 
    "fitness.html", "meal.html", "budgetbased.html"
]

plan_types = {
    "health.html": "health",
    "loss.html": "loss",
    "gain.html": "gain",
    "fitness.html": "fitness",
    "meal.html": "meal",
    "budgetbased.html": "budget"
}

base_dir = r"c:\Users\tirum\OneDrive\Desktop\myapp\frontend"

for fname in files:
    path = os.path.join(base_dir, fname)
    if not os.path.exists(path): continue
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    plan_type = plan_types[fname]

    # 3. Overrides
    overrides = f"""
// ==========================================
// OVERRIDDEN BY CENTRAL MANAGER
// ==========================================

async function requestNotificationPermission() {{
    const planObj = window.planManager.getActivePlan();
    if (!planObj || planObj.planType !== "{plan_type}") {{
        alert("Please generate a new plan or confirm the plan switch first.");
        return;
    }}
    planObj.notificationsEnabled = true;
    
    const times = {{
        breakfast: document.getElementById('breakfastTime')?.value || "08:00",
        lunch: document.getElementById('lunchTime')?.value || "13:00",
        evening: document.getElementById('snackTime')?.value || "17:00",
        dinner: document.getElementById('dinnerTime')?.value || "20:00"
    }};
    planObj.notificationTimes = times;
    
    await window.planManager.activatePlan(planObj);
}}

async function disableNotifications() {{
    await window.planManager.disableActivePlan();
}}

async function saveNotificationSettings() {{
    await requestNotificationPermission();
}}

async function scheduleMealNotifications() {{
    const keys = ["currentPlan", "nutriSmartCurrentPlan", "LOSS_PLAN_KEY", "WEIGHT_GAIN_PLAN_KEY", "GYM_PLAN_KEY", "MEAL_PLAN_KEY", "BUDGET_PLAN_KEY"];
    let planData = null;
    for(let k of keys) {{
        const d = localStorage.getItem(k);
        if(d) {{
            try {{ planData = JSON.parse(d); break; }} catch(e) {{}}
        }}
    }}
    
    const newPlanData = {{
        notificationTimes: {{
            breakfast: document.getElementById('breakfastTime')?.value || "08:00",
            lunch: document.getElementById('lunchTime')?.value || "13:00",
            evening: document.getElementById('snackTime')?.value || "17:00",
            dinner: document.getElementById('dinnerTime')?.value || "20:00"
        }},
        planData: planData
    }};
    
    const success = await window.planManager.requestPlanSwitch("{plan_type}", newPlanData);
    if (!success) {{
        alert("The generated plan is visible, but notifications remain attached to your previously active plan.");
    }}
}}

// Alias for pages that use scheduleNotifications instead of scheduleMealNotifications
async function scheduleNotifications() {{
    await scheduleMealNotifications();
}}
"""
    
    # Remove old override block if present
    content = re.sub(r'// ==========================================\n// OVERRIDDEN BY CENTRAL MANAGER[\s\S]*?(?=</script>\s*</body>)', '', content)
    
    # Inject new block
    content = re.sub(r'(</script>\s*</body>)', overrides + r'\1', content)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Patched {fname}")

print("HTML files patched with scheduleNotifications alias.")

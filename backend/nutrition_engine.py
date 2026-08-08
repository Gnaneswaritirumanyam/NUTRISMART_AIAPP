import pandas as pd
import numpy as np
import os
import joblib
import random
import json

# Paths
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
KNN_MODEL_PATH = os.path.join(MODELS_DIR, "nutrition_knn.joblib")
SCALER_PATH = os.path.join(MODELS_DIR, "nutrition_scaler.joblib")
METADATA_PATH = os.path.join(MODELS_DIR, "nutrition_metadata.joblib")

# Load Models
knn_model = None
scaler = None
metadata = None


def load_models():
    global scaler, knn_model, metadata
    if scaler is not None:
        return
    try:
        print("[ML] Loading nutrition models...")
        scaler = joblib.load("models/nutrition_scaler.joblib")
        knn_model = joblib.load("models/nutrition_knn.joblib")
        metadata = pd.read_csv("models/engine_recipes.csv")
        print("[ML] Nutrition model loaded successfully")
    except Exception as e:
        print("[ML] Model loading failed:", e)

def calculate_bmr(weight, height, age, gender):
    if gender.lower() == 'male':
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161

def calculate_tdee(bmr, activity_level):
    multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9
    }
    return bmr * multipliers.get(activity_level.lower(), 1.2)

def recommend_meals(target_calories, protein, fat, carbs, n=1, diet_pref=None, exclude_set=None):
    load_models()
    if metadata is None:
        return []
    
    if exclude_set is None:
        exclude_set = set()
        
    query = pd.DataFrame([[target_calories, protein, fat, carbs]], columns=['Calories', 'ProteinContent', 'FatContent', 'CarbohydrateContent'])
    scaled_query = scaler.transform(query)
    
    # Get plenty of candidates
    distances, indices = knn_model.kneighbors(scaled_query, n_neighbors=500)
    
    candidates = []
    
    non_veg_keywords = ['chicken', 'beef', 'pork', 'sausage', 'bacon', 'fish', 'shrimp', 'salmon', 'meat', 'turkey', 'lamb', 'ham', 'tuna', 'crab', 'steak']
    
    is_veg = False
    if diet_pref and str(diet_pref).lower() in ['veg', 'vegetarian', 'vegan']:
        is_veg = True
    
    for idx in indices[0]:
        meal = metadata.iloc[idx]
        meal_name = str(meal.get('Name', 'Healthy Meal'))
        
        # Avoid exact duplicates
        if meal_name in exclude_set:
            continue
            
        ing_raw = str(meal.get('RecipeIngredientParts', ''))
        
        # Diet preference check
        if is_veg:
            name_and_ingr = (meal_name + ' ' + ing_raw).lower()
            if any(meat in name_and_ingr for meat in non_veg_keywords):
                continue
            
        # Parse ingredients
        ing_raw = str(meal.get('RecipeIngredientParts', ''))
        ingredients = []
        if ing_raw.startswith('c(') and ing_raw.endswith(')'):
            ingredients = [p.strip().replace('"', '') for p in ing_raw[2:-1].split(',')]
        else:
            ingredients = [ing_raw]
            
        # Parse instructions
        inst_raw = str(meal.get('RecipeInstructions', ''))
        instructions = []
        if inst_raw.startswith('c(') and inst_raw.endswith(')'):
            instructions = [p.strip().replace('"', '') for p in inst_raw[2:-1].split(',')]
        else:
            instructions = [inst_raw]
            
        # Parse image
        img_raw = str(meal.get('Images', ''))
        image_url = ""
        import re
        match = re.search(r'"(https?://[^"]+)"', img_raw)
        if match:
            image_url = match.group(1)
        elif img_raw.startswith('http'):
            image_url = img_raw
            
        candidates.append({
            "name": meal_name,
            "calories": int(meal.get('Calories', target_calories)),
            "protein": int(meal.get('ProteinContent', protein)),
            "fat": int(meal.get('FatContent', fat)),
            "carbs": int(meal.get('CarbohydrateContent', carbs)),
            "time": "15 mins",
            "ingredients": [i for i in ingredients if i and i != 'character(0)' and i != 'nan'],
            "steps": [s for s in instructions if s and s != 'character(0)' and s != 'nan'],
            "image": image_url
        })
        
        if len(candidates) >= 15: # we have enough candidates
            break
            
    import random
    if len(candidates) >= n:
        selected = random.sample(candidates, n)
    else:
        selected = candidates
        
    return selected

# --- 1. Weight Loss Plan (AI Plan) ---
def generate_weight_loss_plan(details):
    weight = float(details.get("weight", 70))
    height = float(details.get("height", 170))
    age = int(details.get("age", 30))
    gender = details.get("gender", "male")
    foodType = details.get("foodType", "veg")
    
    bmr = calculate_bmr(weight, height, age, gender)
    tdee = calculate_tdee(bmr, 'lightly active')
    
    target_calories = tdee - 500
    
    p = (target_calories * 0.3) / 4
    c = (target_calories * 0.4) / 4
    f = (target_calories * 0.3) / 9
    
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    plan = {}
    exclude_set = set()
    
    for day in days:
        if len(exclude_set) > 30: exclude_set.clear()
        
        m_meal = recommend_meals(target_calories*0.25, p*0.25, f*0.25, c*0.25, 1, foodType, exclude_set)
        if m_meal: exclude_set.add(m_meal[0]['name'])
        
        a_meal = recommend_meals(target_calories*0.35, p*0.35, f*0.35, c*0.35, 1, foodType, exclude_set)
        if a_meal: exclude_set.add(a_meal[0]['name'])
        
        e_meal = recommend_meals(target_calories*0.10, p*0.10, f*0.10, c*0.10, 1, foodType, exclude_set)
        if e_meal: exclude_set.add(e_meal[0]['name'])
        
        n_meal = recommend_meals(target_calories*0.30, p*0.30, f*0.30, c*0.30, 1, foodType, exclude_set)
        if n_meal: exclude_set.add(n_meal[0]['name'])
        
        plan[day] = {
            "Morning": {
                "meal": m_meal[0]['name'] if m_meal else "Oats and Fruit",
                "calories": f"{m_meal[0]['calories']} kcal" if m_meal else "300 kcal",
                "image": m_meal[0]['image'] if m_meal else "",
                "ingredients": m_meal[0]['ingredients'] if m_meal else [],
                "steps": m_meal[0]['steps'] if m_meal else []
            },
            "Afternoon": {
                "meal": a_meal[0]['name'] if a_meal else "Salad Bowl",
                "calories": f"{a_meal[0]['calories']} kcal" if a_meal else "500 kcal",
                "image": a_meal[0]['image'] if a_meal else "",
                "ingredients": a_meal[0]['ingredients'] if a_meal else [],
                "steps": a_meal[0]['steps'] if a_meal else []
            },
            "Evening": {
                "meal": e_meal[0]['name'] if e_meal else "Green Tea and Nuts",
                "calories": f"{e_meal[0]['calories']} kcal" if e_meal else "150 kcal",
                "image": e_meal[0]['image'] if e_meal else "",
                "ingredients": e_meal[0]['ingredients'] if e_meal else [],
                "steps": e_meal[0]['steps'] if e_meal else []
            },
            "Night": {
                "meal": n_meal[0]['name'] if n_meal else "Grilled Vegetables",
                "calories": f"{n_meal[0]['calories']} kcal" if n_meal else "400 kcal",
                "image": n_meal[0]['image'] if n_meal else "",
                "ingredients": n_meal[0]['ingredients'] if n_meal else [],
                "steps": n_meal[0]['steps'] if n_meal else []
            }
        }
        
    import json
    return json.dumps(plan)

# --- 2. Weight Gain Plan ---
def generate_weight_gain_plan(details):
    weight = float(details.get("weight", 70))
    height = float(details.get("height", 170))
    age = int(details.get("age", 30))
    gender = details.get("gender", "male")
    foodType = details.get("foodType", "veg")
    
    bmr = calculate_bmr(weight, height, age, gender)
    tdee = calculate_tdee(bmr, 'moderately active')
    
    target_calories = tdee + 500
    
    p = (target_calories * 0.25) / 4
    c = (target_calories * 0.50) / 4
    f = (target_calories * 0.25) / 9
    
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    plan = {}
    exclude_set = set()
    
    for day in days:
        if len(exclude_set) > 30: exclude_set.clear()
        
        m_meal = recommend_meals(target_calories*0.25, p*0.25, f*0.25, c*0.25, 1, foodType, exclude_set)
        if m_meal: exclude_set.add(m_meal[0]['name'])
        
        a_meal = recommend_meals(target_calories*0.30, p*0.30, f*0.30, c*0.30, 1, foodType, exclude_set)
        if a_meal: exclude_set.add(a_meal[0]['name'])
        
        e_meal = recommend_meals(target_calories*0.15, p*0.15, f*0.15, c*0.15, 1, foodType, exclude_set)
        if e_meal: exclude_set.add(e_meal[0]['name'])
        
        n_meal = recommend_meals(target_calories*0.30, p*0.30, f*0.30, c*0.30, 1, foodType, exclude_set)
        if n_meal: exclude_set.add(n_meal[0]['name'])
        
        plan[day] = {
            "Morning": {
                "meal": m_meal[0]['name'] if m_meal else "Oats and Protein",
                "calories": f"{m_meal[0]['calories']} kcal" if m_meal else "400 kcal",
                "image": m_meal[0]['image'] if m_meal else "",
                "ingredients": m_meal[0]['ingredients'] if m_meal else [],
                "steps": m_meal[0]['steps'] if m_meal else []
            },
            "Afternoon": {
                "meal": a_meal[0]['name'] if a_meal else "Chicken and Rice",
                "calories": f"{a_meal[0]['calories']} kcal" if a_meal else "600 kcal",
                "image": a_meal[0]['image'] if a_meal else "",
                "ingredients": a_meal[0]['ingredients'] if a_meal else [],
                "steps": a_meal[0]['steps'] if a_meal else []
            },
            "Evening": {
                "meal": e_meal[0]['name'] if e_meal else "Peanut Butter Sandwich",
                "calories": f"{e_meal[0]['calories']} kcal" if e_meal else "300 kcal",
                "image": e_meal[0]['image'] if e_meal else "",
                "ingredients": e_meal[0]['ingredients'] if e_meal else [],
                "steps": e_meal[0]['steps'] if e_meal else []
            },
            "Night": {
                "meal": n_meal[0]['name'] if n_meal else "Salmon and Pasta",
                "calories": f"{n_meal[0]['calories']} kcal" if n_meal else "500 kcal",
                "image": n_meal[0]['image'] if n_meal else "",
                "ingredients": n_meal[0]['ingredients'] if n_meal else [],
                "steps": n_meal[0]['steps'] if n_meal else []
            }
        }
        
    import json
    return json.dumps(plan)

# --- 3. Gym Plan ---
def generate_gym_plan(details):
    weight = float(details.get("weight", 70))
    height = float(details.get("height", 170))
    age = int(details.get("age", 30))
    gender = details.get("gender", "male")
    foodType = details.get("foodType", "veg")
    
    bmr = calculate_bmr(weight, height, age, gender)
    tdee = calculate_tdee(bmr, 'very_active')
    
    p = (tdee * 0.35) / 4
    c = (tdee * 0.45) / 4
    f = (tdee * 0.20) / 9
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    workouts = {
        "Monday": [{"exercise": "Bench Press", "sets": "4", "reps": "8-10"}, {"exercise": "Incline Dumbbell Press", "sets": "3", "reps": "10-12"}],
        "Tuesday": [{"exercise": "Barbell Rows", "sets": "4", "reps": "8-10"}, {"exercise": "Pull-ups", "sets": "3", "reps": "To failure"}],
        "Wednesday": [],
        "Thursday": [{"exercise": "Squats", "sets": "4", "reps": "8-10"}, {"exercise": "Leg Press", "sets": "3", "reps": "10-12"}],
        "Friday": [{"exercise": "Overhead Press", "sets": "4", "reps": "8-10"}, {"exercise": "Lateral Raises", "sets": "3", "reps": "15"}],
        "Saturday": [{"exercise": "Bicep Curls", "sets": "3", "reps": "10-12"}, {"exercise": "Tricep Extensions", "sets": "3", "reps": "10-12"}],
        "Sunday": []
    }
    
    plan = {}
    exclude_set = set()
    for day in days:
        if len(exclude_set) > 30: exclude_set.clear() # reset to avoid running out of meals
        
        m_meal = recommend_meals(tdee*0.25, p*0.25, f*0.25, c*0.25, 1, foodType, exclude_set)
        if m_meal: exclude_set.add(m_meal[0]['name'])
        a_meal = recommend_meals(tdee*0.35, p*0.35, f*0.35, c*0.35, 1, foodType, exclude_set)
        if a_meal: exclude_set.add(a_meal[0]['name'])
        n_meal = recommend_meals(tdee*0.30, p*0.30, f*0.30, c*0.30, 1, foodType, exclude_set)
        if n_meal: exclude_set.add(n_meal[0]['name'])
        s_meal = recommend_meals(tdee*0.10, p*0.10, f*0.10, c*0.10, 1, foodType, exclude_set)
        if s_meal: exclude_set.add(s_meal[0]['name'])
        
        is_rest = len(workouts[day]) == 0
        
        plan[day] = {
            "workout": workouts[day],
            "cardio": "20 min walking" if is_rest else "10 min warm-up",
            "diet": {
                "breakfast": m_meal[0]['name'] if m_meal else "Oats",
                "lunch": a_meal[0]['name'] if a_meal else "Rice Bowl",
                "dinner": n_meal[0]['name'] if n_meal else "Salad",
                "snacks": s_meal[0]['name'] if s_meal else "Nuts"
            },
            "notes": "Rest and recover" if is_rest else "Focus on progressive overload"
        }
        
    import json
    return json.dumps(plan)

# --- 4. Weekly Food Plan ---
def generate_weekly_food_plan(details):
    weight = float(details.get("weight", 70))
    height = float(details.get("height", 170))
    age = int(details.get("age", 30))
    gender = details.get("gender", "male")
    foodType = details.get("foodType", "veg")
    
    bmr = calculate_bmr(weight, height, age, gender)
    tdee = calculate_tdee(bmr, 'active')
    
    p = (tdee * 0.3) / 4
    c = (tdee * 0.4) / 4
    f = (tdee * 0.3) / 9
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    plan = {}
    exclude_set = set()
    for day in days:
        if len(exclude_set) > 30: exclude_set.clear()
        
        m_meal = recommend_meals(tdee*0.25, p*0.25, f*0.25, c*0.25, 1, foodType, exclude_set)
        if m_meal: exclude_set.add(m_meal[0]['name'])
        a_meal = recommend_meals(tdee*0.35, p*0.35, f*0.35, c*0.35, 1, foodType, exclude_set)
        if a_meal: exclude_set.add(a_meal[0]['name'])
        e_meal = recommend_meals(tdee*0.10, p*0.10, f*0.10, c*0.10, 1, foodType, exclude_set)
        if e_meal: exclude_set.add(e_meal[0]['name'])
        n_meal = recommend_meals(tdee*0.30, p*0.30, f*0.30, c*0.30, 1, foodType, exclude_set)
        if n_meal: exclude_set.add(n_meal[0]['name'])
        
        plan[day] = {
            "breakfast": f"{m_meal[0]['name']} - {m_meal[0]['calories']} kcal" if m_meal else "Oats - 350 kcal",
            "lunch": f"{a_meal[0]['name']} - {a_meal[0]['calories']} kcal" if a_meal else "Rice and Dal - 550 kcal",
            "eveningSnack": f"{e_meal[0]['name']} - {e_meal[0]['calories']} kcal" if e_meal else "Fruit - 200 kcal",
            "dinner": f"{n_meal[0]['name']} - {n_meal[0]['calories']} kcal" if n_meal else "Salad - 450 kcal"
        }
        
    import json
    return json.dumps(plan)

# --- 5. Budget Plan ---
def generate_budget_plan(details):
    budget = float(details.get("budget", 500))
    days_count = int(details.get("days", 1))
    weight = float(details.get("weight", 70))
    height = float(details.get("height", 170))
    age = int(details.get("age", 30))
    gender = details.get("gender", "male")
    foodType = details.get("foodType", "veg")
    
    daily_budget = budget / days_count if days_count > 0 else budget
    
    bmr = calculate_bmr(weight, height, age, gender)
    tdee = calculate_tdee(bmr, 'lightly active')
    
    p = (tdee * 0.3) / 4
    c = (tdee * 0.4) / 4
    f = (tdee * 0.3) / 9
    
    plan_days = []
    exclude_set = set()
    
    for i in range(1, days_count + 1):
        if len(exclude_set) > 30: exclude_set.clear()
        
        m_meal = recommend_meals(tdee*0.30, p*0.30, f*0.30, c*0.30, 1, foodType, exclude_set)
        if m_meal: exclude_set.add(m_meal[0]['name'])
        a_meal = recommend_meals(tdee*0.40, p*0.40, f*0.40, c*0.40, 1, foodType, exclude_set)
        if a_meal: exclude_set.add(a_meal[0]['name'])
        n_meal = recommend_meals(tdee*0.30, p*0.30, f*0.30, c*0.30, 1, foodType, exclude_set)
        if n_meal: exclude_set.add(n_meal[0]['name'])
        
        day_plan = {
            "day": i,
            "breakfast": {
                "meal": m_meal[0]['name'] if m_meal else "Budget Oats",
                "calories": m_meal[0]['calories'] if m_meal else 300,
                "cost": round(daily_budget * 0.30, 2),
                "protein": f"{m_meal[0]['protein']}g" if m_meal else "10g",
                "carbs": f"{m_meal[0]['carbs']}g" if m_meal else "40g",
                "fat": f"{m_meal[0]['fat']}g" if m_meal else "10g",
                "recipe": {
                    "ingredients": m_meal[0]['ingredients'] if m_meal else ["Oats", "Water"],
                    "steps": m_meal[0]['steps'] if m_meal else ["Boil water", "Add oats"],
                    "time": m_meal[0]['time'] if m_meal else "10 mins"
                }
            },
            "lunch": {
                "meal": a_meal[0]['name'] if a_meal else "Budget Rice",
                "calories": a_meal[0]['calories'] if a_meal else 500,
                "cost": round(daily_budget * 0.40, 2),
                "protein": f"{a_meal[0]['protein']}g" if a_meal else "15g",
                "carbs": f"{a_meal[0]['carbs']}g" if a_meal else "60g",
                "fat": f"{a_meal[0]['fat']}g" if a_meal else "15g",
                "recipe": {
                    "ingredients": a_meal[0]['ingredients'] if a_meal else ["Rice", "Water"],
                    "steps": a_meal[0]['steps'] if a_meal else ["Boil water", "Add rice"],
                    "time": a_meal[0]['time'] if a_meal else "15 mins"
                }
            },
            "dinner": {
                "meal": n_meal[0]['name'] if n_meal else "Budget Soup",
                "calories": n_meal[0]['calories'] if n_meal else 400,
                "cost": round(daily_budget * 0.30, 2),
                "protein": f"{n_meal[0]['protein']}g" if n_meal else "20g",
                "carbs": f"{n_meal[0]['carbs']}g" if n_meal else "30g",
                "fat": f"{n_meal[0]['fat']}g" if n_meal else "10g",
                "recipe": {
                    "ingredients": n_meal[0]['ingredients'] if n_meal else ["Soup mix", "Water"],
                    "steps": n_meal[0]['steps'] if n_meal else ["Boil water", "Add mix"],
                    "time": n_meal[0]['time'] if n_meal else "10 mins"
                }
            },
        }
        
        day_plan["totalCalories"] = day_plan["breakfast"]["calories"] + day_plan["lunch"]["calories"] + day_plan["dinner"]["calories"]
        day_plan["totalCost"] = round(day_plan["breakfast"]["cost"] + day_plan["lunch"]["cost"] + day_plan["dinner"]["cost"], 2)
        plan_days.append(day_plan)
        
    import json
    return json.dumps({"days": plan_days})

# --- 6. Health Plan ---
def generate_health_plan(details):
    condition = details.get("condition", "general")
    foodType = details.get("foodType", "non-veg")
    
    print(f"[ML] Applying diet rules for condition: {condition}. General dietary guidance only.")
    
    if "diabetes" in condition.lower():
        p, f, c = 40, 30, 20 # Low carb
    elif "hypertension" in condition.lower():
        p, f, c = 30, 20, 40 # Standard balanced
    else:
        p, f, c = 30, 30, 40
        
    exclude_set = set()
    m1 = recommend_meals(400, p*0.2, f*0.2, c*0.2, 1, foodType, exclude_set)
    if m1: exclude_set.add(m1[0]['name'])
    m2 = recommend_meals(600, p*0.4, f*0.4, c*0.4, 1, foodType, exclude_set)
    if m2: exclude_set.add(m2[0]['name'])
    m3 = recommend_meals(500, p*0.4, f*0.4, c*0.4, 1, foodType, exclude_set)
    
    recipes_list = []
    
    meals_to_use = [m[0] for m in [m1, m2, m3] if m]
    
    for m in meals_to_use:
        recipes_list.append({
            "name": m["name"],
            "ingredients": m["ingredients"],
            "process": m["steps"],
            "image": m.get("image", ""),
            "nutrition": {
                "calories": f"{m['calories']} kcal",
                "protein": f"{m['protein']}g",
                "carbs": f"{m['carbs']}g",
                "fat": f"{m['fat']}g"
            }
        })
        
    import json
    return json.dumps({"recipes": recipes_list})

def get_recipe_details(meal_name):
    load_models()
    # Strip calories if present e.g. 'Greek Turkey Burgers - 400 kcal' -> 'Greek Turkey Burgers'
    import re
    clean_meal_name = re.sub(r' - \d+ kcal$', '', meal_name)
    matches = metadata[metadata['Name'].str.lower() == clean_meal_name.lower()]
    if matches.empty:
        return {
            "name": meal_name,
            "ingredients": ["⚠️ THIS MEAL IS FROM AN OLD PLAN IN YOUR BROWSER CACHE.", "To fix this and get real recipes from the Local ML model:", "Please close this popup and click the RED 'Generate New Plan' button below the form!"],
            "process": ["⚠️ PLEASE CLICK 'GENERATE NEW PLAN'.", "You clicked the orange button, which just loaded your old plan from local storage.", "Click the RED button to clear the storage and generate a real plan."],
            "steps": ["⚠️ PLEASE CLICK 'GENERATE NEW PLAN'.", "You clicked the orange button, which just loaded your old plan from local storage.", "Click the RED button to clear the storage and generate a real plan."],
            "nutrition": {
                "calories": "---",
                "protein": "---",
                "carbs": "---",
                "fat": "---"
            },
            "image": "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=800"
        }
        
    meal = matches.iloc[0]
    
    # Parse ingredients
    ing_raw = str(meal.get('RecipeIngredientParts', ''))
    if ing_raw.startswith('c(') and ing_raw.endswith(')'):
        ingredients = [p.strip().replace('"', '') for p in ing_raw[2:-1].split(',')]
    else:
        ingredients = [ing_raw] if ing_raw != 'nan' else []

    # Parse process (steps)
    steps_raw = str(meal.get('RecipeInstructions', ''))
    if steps_raw.startswith('c(') and steps_raw.endswith(')'):
        steps = [p.strip().replace('"', '') for p in steps_raw[2:-1].split(',')]
    else:
        steps = [steps_raw] if steps_raw != 'nan' else []

    # Parse image using same regex
    img_raw = str(meal.get('Images', ''))
    image_url = ""
    import re
    match = re.search(r'"(https?://[^"]+)"', img_raw)
    if match:
        image_url = match.group(1)
    elif img_raw.startswith('http'):
        image_url = img_raw
    if not image_url:
        image_url = "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=800"
        
    return {
        "name": meal_name,
        "ingredients": ingredients,
        "process": steps,
        "steps": steps,
        "nutrition": {
            "calories": f"{int(meal.get('Calories', 0))} kcal",
            "protein": f"{int(meal.get('ProteinContent', 0))}g",
            "carbs": f"{int(meal.get('CarbohydrateContent', 0))}g",
            "fat": f"{int(meal.get('FatContent', 0))}g"
        },
        "image": image_url
    }

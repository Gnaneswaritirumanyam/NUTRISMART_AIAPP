import sys

# 1. ADD /get-user-plan to main.py
content_main = open('backend/main.py', 'r', encoding='utf-8').read()
get_user_plan_code = """
@app.get("/get-user-plan")
async def get_user_plan(email: str):
    plan = plans_collection.find_one({"email": email}, sort=[("_id", -1)])
    if plan and "plan" in plan:
        return {"success": True, "plan": plan["plan"]}
    return {"success": False, "plan": None}
"""

if "@app.get(\"/get-user-plan\")" not in content_main:
    # insert before @app.get("/{page}.html")
    content_main = content_main.replace('@app.get("/{page}.html"', get_user_plan_code + '\n@app.get("/{page}.html"')
    with open('backend/main.py', 'w', encoding='utf-8') as f:
        f.write(content_main)
    print("Added /get-user-plan to main.py")

# 2. Fix fitness.html to use /get-gym-plan
content_fitness = open('frontend/fitness.html', 'r', encoding='utf-8').read()
if "/get-user-plan" in content_fitness:
    content_fitness = content_fitness.replace("/get-user-plan", "/get-gym-plan")
    with open('frontend/fitness.html', 'w', encoding='utf-8') as f:
        f.write(content_fitness)
    print("Changed fitness.html to use /get-gym-plan")

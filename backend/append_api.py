import os

new_code = """
# =================================================================
# NEW CENTRALIZED PLAN & FEEDBACK ENDPOINTS
# =================================================================
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ActivePlan(BaseModel):
    planType: str
    planName: str
    sourcePage: str
    planId: str
    activatedAt: str
    notificationsEnabled: bool
    notificationTimes: dict
    status: str
    planData: Any = None

class PlanFeedback(BaseModel):
    feedbackId: str
    planId: str
    planType: str
    planName: str
    date: str
    mealType: str
    itemName: str
    notificationScheduledAt: str
    feedbackScheduledAt: str
    feedbackAnsweredAt: str
    status: str
    response: str
    calories: float = 0
    cost: float = 0
    sourcePage: str

@app.get('/api/active-plan')
async def get_active_plan(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Session expired')
    email = payload.get('sub')
    plan = auth_db['active_plans'].find_one({'email': email, 'status': 'active'}, {'_id': 0})
    if plan:
        return plan
    return {'message': 'No active plan found'}

@app.post('/api/active-plan/activate')
async def activate_plan(plan: ActivePlan, request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Session expired')
    email = payload.get('sub')
    
    # Deactivate current active plan
    auth_db['active_plans'].update_many({'email': email, 'status': 'active'}, {'$set': {'status': 'inactive'}})
    
    # Activate new plan
    plan_dict = plan.dict()
    plan_dict['email'] = email
    auth_db['active_plans'].insert_one(plan_dict)
    return {'message': 'Plan activated successfully'}

@app.post('/api/active-plan/disable')
async def disable_plan(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Session expired')
    email = payload.get('sub')
    auth_db['active_plans'].update_many({'email': email, 'status': 'active'}, {'$set': {'status': 'inactive', 'notificationsEnabled': False}})
    return {'message': 'Active plan disabled'}

@app.get('/api/plan-feedback')
async def get_plan_feedback(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Session expired')
    email = payload.get('sub')
    feedbacks = list(auth_db['plan_feedback'].find({'email': email}, {'_id': 0}))
    return feedbacks

@app.post('/api/plan-feedback')
async def save_plan_feedback(feedback: PlanFeedback, request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Session expired')
    email = payload.get('sub')
    
    feedback_dict = feedback.dict()
    feedback_dict['email'] = email
    # Upsert feedback
    auth_db['plan_feedback'].update_one(
        {'email': email, 'feedbackId': feedback.feedbackId},
        {'$set': feedback_dict},
        upsert=True
    )
    return {'message': 'Feedback saved'}
"""

with open(r"c:\Users\tirum\OneDrive\Desktop\myapp\backend\main.py", "a", encoding="utf-8") as f:
    f.write("\n\n" + new_code)
print("Done appending to main.py")

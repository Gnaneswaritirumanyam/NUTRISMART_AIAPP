from urllib import response
from fastapi import FastAPI, Request, Response, HTTPException,status,Form,UploadFile, File,Depends, BackgroundTasks
from fastapi.responses import HTMLResponse,FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from passlib.context import CryptContext
from dotenv import load_dotenv
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os, requests, json, re
from rapidfuzz import process, fuzz
import networkx as nx
from fastapi.templating import Jinja2Templates
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
import httpx
import os
import json
import nutrition_engine
import base64
import shutil
import cv2
import pytesseract
import random
from PIL import Image
from openai import OpenAI
from deep_translator import GoogleTranslator
from fastapi import FastAPI, UploadFile, File

from pydantic import BaseModel, EmailStr, Field
import random
import string
import hashlib
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from services.email_service import send_signup_otp, send_password_reset_otp


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
)

Base = declarative_base()

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
MAX_BCRYPT_LEN = 72  
origins = ["capacitor://localhost", "http://localhost", "https://localhost", "http://10.0.2.2", "http://127.0.0.1:8000", "http://192.168.1.100:8000"] + os.getenv("FRONTEND_ORIGINS", "").split(",")

client = MongoClient(MONGO_URI)
auth_db = client["myapp"]
users_col = auth_db["users"]
history_col=auth_db["History"]
health_collection =auth_db["health_data"]
budget_collection = auth_db["budget_plans"]  
fitness_collection = auth_db["fitness_details"]
plans_collection = auth_db["plans"]
notifications_collection = auth_db["notifications"]
plans_collection = auth_db["plans"]
feedback_col = auth_db["plan_feedback"]

app = FastAPI(title="Recipe Suggestion + Auth API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing routes omitted for brevity ...

@app.post("/plans")
def create_plan(payload: dict):
    """Create a new plan, deactivate old one, and schedule notifications."""
    user_id = payload.get("user_id", "user123")
    # Deactivate any existing active plans for this user
    plans_collection.update_many({"user_id": user_id, "status": "active"}, {"$set": {"status": "inactive"}})
    # Remove old notifications for this user
    notifications_collection.delete_many({"user_id": user_id})

    # Insert new plan document
    new_plan = {
        "user_id": user_id,
        "status": "active",
        "created_at": datetime.utcnow(),
        "plan_data": payload
    }
    result = plans_collection.insert_one(new_plan)
    plan_id = str(result.inserted_id)

    # Default meal times (can be overridden by payload["meal_times"] if provided)
    default_times = {
        "breakfast": "08:00",
        "lunch": "13:00",
        "snack": "17:00",
        "dinner": "20:00"
    }
    meal_times = payload.get("meal_times", default_times)

    for meal, time_str in meal_times.items():
        notif_time = datetime.strptime(time_str, "%H:%M").time()
        feedback_time = (datetime.combine(datetime.today(), notif_time) + timedelta(hours=1)).time()
        notif_doc = {
            "user_id": user_id,
            "plan_id": plan_id,
            "meal_type": meal,
            "notification_time": time_str,
            "feedback_time": feedback_time.strftime("%H:%M"),
            "notification_message": f"Time for your healthy {meal} 🍳",
            "feedback_message": f"How was your {meal}?",
            "status": "scheduled",
            "feedback_status": "pending"
        }
        notifications_collection.insert_one(notif_doc)

    return {"message": "Plan created and notifications scheduled", "plan_id": plan_id}

# Scheduler setup (APScheduler) omitted for brevity – to be added later

from fastapi import FastAPI, Request, Response, HTTPException,status,Form,UploadFile, File,Depends
from fastapi.responses import HTMLResponse,FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from passlib.context import CryptContext
from dotenv import load_dotenv
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os, requests, json, re
from rapidfuzz import process, fuzz
import networkx as nx
from fastapi.templating import Jinja2Templates
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
import httpx
import os
import json
import base64
import shutil
import cv2
import pytesseract
import random
from PIL import Image
from openai import OpenAI
from deep_translator import GoogleTranslator
from fastapi import FastAPI, UploadFile, File

from pydantic import BaseModel, EmailStr, Field
import random
import string
import hashlib
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from services.email_service import send_signup_otp, send_password_reset_otp



pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

Base = declarative_base()

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
RECAPTCHA_SECRET = os.getenv("RECAPTCHA_SECRET_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 720))
ALGORITHM = "HS256"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
STATIC_DIR = os.getenv("STATIC_DIR", os.path.join(PARENT_DIR, "frontend"))

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
MAX_BCRYPT_LEN = 72  
origins = ["capacitor://localhost", "http://localhost", "https://localhost", "http://10.0.2.2", "http://127.0.0.1:8000", "http://192.168.1.100:8000"] + os.getenv("FRONTEND_ORIGINS", "").split(",")

client = MongoClient(MONGO_URI)
auth_db = client["myapp"]
users_col = auth_db["users"]
history_col=auth_db["History"]
health_collection =auth_db["health_data"]
budget_collection = auth_db["budget_plans"]  
fitness_collection = auth_db["fitness_details"]

app = FastAPI(title="Recipe Suggestion + Auth API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SYSTEM_PROMPT = (
     "You are NutriSmart AI, an expert chef and nutrition assistant. "
    "Always provide complete answers. Do not stop in the middle. "
    "If listing multiple recipes, finish all recipes fully. "
    "Include title, ingredients, steps, time, difficulty, and diet labels. "
    "Only answer food-related queries."
)

def clean_markdown(text: str):
    text = re.sub(r'[*_`#>]+', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


PEXELS_API = os.getenv("PIXEL_API")
@app.get("/food-image")
async def get_food_image(query: str):

    headers = {
        "Authorization": PEXELS_API
    }

    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"

    response = requests.get(url, headers=headers)

    data = response.json()

    if data["photos"]:

        return {
            "image": data["photos"][0]["src"]["large"]
        }

    return {
        "image":"https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg"
    }
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """
You are NutriSmart AI, an expert chef, nutritionist, and diet assistant.

You can help with:
- Recipes
- Cooking instructions
- Ingredients
- Meal preparation
- Healthy eating
- Diet plans
- Weight loss diets
- Weight gain diets
- Muscle gain meal plans
- gym food plans
- Nutrition facts
- Calorie estimation
- Food substitutions
- Vegetarian, vegan, keto, diabetic, and gluten-free diets

For recipe requests, provide:
- Recipe title
- Ingredients
- Step-by-step instructions
- Cooking time
- Difficulty
- Diet labels

For diet plan requests, provide:
- Meal schedule
- Breakfast, lunch, dinner suggestions
- Healthy snacks
- Daily nutrition tips

If the question is unrelated to food, cooking, nutrition, or diets, reply:
I can only help with food, nutrition, and cooking questions.
Always complete the full response properly. Never stop in the middle of a sentence or recipe.
"""
def clean_text(text):
    text = re.sub(r'[*_`#>]+', '', text)
    return text.strip()


from pathlib import Path
BASE_DIR_PATH = Path(__file__).resolve().parent
UPLOAD_FOLDER = str(BASE_DIR_PATH / "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/detect")
async def detect_ingredients(file: UploadFile = File(...)):

    # ================= SAVE IMAGE =================

    filepath = f"{UPLOAD_FOLDER}/{file.filename}"

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ================= OCR =================

    img = Image.open(filepath)

    ocr_text = pytesseract.image_to_string(img)

    # ================= IMAGE TO BASE64 =================

    with open(filepath, "rb") as image_file:
        base64_image = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

    # ================= OPENAI VISION =================

    response = client.chat.completions.create(

        model="gpt-4o-mini",

        messages=[

            {
                "role": "system",
                "content": """
                You are an AI ingredient detector.

                Detect all visible food ingredients from image.

                Return ONLY ingredient names separated by commas.

                Example:
                Rice, Egg, Onion, Tomato
                """
            },

            {
                "role": "user",

                "content": [

                    {
                        "type": "text",
                        "text": "Detect ingredients from this image"
                    },

                    {
                        "type": "image_url",

                        "image_url": {
                            "url":
                            f"data:image/jpeg;base64,{base64_image}"
                        }
                    }

                ]
            }
        ]

    )

    ingredients_text = response.choices[0].message.content

    print("Detected:", ingredients_text)

    # ================= CLEAN INGREDIENTS =================

    ingredients = [
        item.strip()
        for item in ingredients_text.split(",")
    ]

    # ================= RECIPE GENERATION =================

    recipe_prompt = f"""
    Generate a cooking recipe using:

    {ingredients_text}

    OCR TEXT:
    {ocr_text}

    Return response in JSON format:

    {{
      "recipe_name": "",
      "steps": []
    }}
    """

    recipe_response = client.chat.completions.create(

        model="gpt-4o-mini",

        messages=[
            {
                "role": "user",
                "content": recipe_prompt
            }
        ]

    )

    recipe_content = recipe_response.choices[0].message.content

    print(recipe_content)

    # ================= PARSE JSON =================

    try:

        recipe_data = json.loads(recipe_content)

    except:

        recipe_data = {

            "recipe_name": "AI Recipe",

            "steps": [
                recipe_content
            ]

        }

    # ================= RETURN =================

    return {

        "ingredients": ingredients,

        "recipe_name":
        recipe_data.get("recipe_name", "AI Recipe"),

        "steps":
        recipe_data.get("steps", []),

        "ocr_text": ocr_text

    }
    
@app.post("/api/recipe")
async def ask_ai(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt", "")

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        text = response.choices[0].message.content

        return {
            "text": clean_text(text)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"text": str(e)}
        )

class TranslateRequest(BaseModel):
    text: str
    target: str

@app.post("/translate")
async def translate(data: dict):

    text = data.get("text")
    target = data.get("target")

    translated = GoogleTranslator(
        source='auto',
        target=target
    ).translate(text)

    return {
        "translatedText": translated
    }
class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)
    action_type = Column(String)  # "searched" or "viewed"
    data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="templates")
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_token_from_request(request: Request):
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth.split(" ")[1]
    return request.cookies.get("access_token")

def verify_token(token: str):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None  
    
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ---------------- HTML ROUTES ----------------
@app.get("/", response_class=HTMLResponse)
async def signup_page():
    path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Signup page not found")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    path = os.path.join(STATIC_DIR, "login.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Login page not found")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
@app.get("/intro", response_class=HTMLResponse)
async def intro_page():
    path = os.path.join(STATIC_DIR, "intro.html")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Intro page not found")

    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
    
@app.get("/scan", response_class=HTMLResponse)
async def scan_page():
    path = os.path.join(STATIC_DIR, "scan.html")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Scan page not found")

    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
    
@app.get("/budget", response_class=HTMLResponse)
async def futures_page():

    path = os.path.join(STATIC_DIR, "budget.html")

    if not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail="Futures page not found"
        )

    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    path = os.path.join(STATIC_DIR, "dashboard.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Dashboard not found")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
    
@app.get("/cuisine", response_class=HTMLResponse)
async def cuisine_page():
    path = os.path.join(STATIC_DIR,"cuisine.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Cuisine not found")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/items", response_class=HTMLResponse)
async def items_page(request: Request, cuisine: str):
    return templates.TemplateResponse("items.html", {"request": request, "cuisine": cuisine})


@app.get("/ai", response_class=FileResponse)
async def open_ai_page():
    path = os.path.join(STATIC_DIR, "aichat.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="aichat.html not found")
    return FileResponse(path)
# ---------------- MODELS ----------------
class SignupModel(BaseModel):
    name: str
    email: str
    password: str
    confirmPassword: str
    recaptchaToken: str

class VerifyOTPModel(BaseModel):
    email: str
    otp: str

class ResendOTPModel(BaseModel):
    email: str

class LoginModel(BaseModel):
    email: str
    password: str

class GoogleAuthModel(BaseModel):
    credential: str

class IngredientsInput(BaseModel):
    ingredients: list[str]

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    newPassword: str
    confirmPassword: str

# ============ GLOBAL SEARCH & VIEW HISTORY ============
search_history = []
view_history = []

# ---------------- SIGNUP / OTP ----------------
@app.post("/api/auth/signup/request-otp")
async def request_otp(data: SignupModel, background_tasks: BackgroundTasks):
    try:
        # Verify reCAPTCHA
        if not RECAPTCHA_SECRET:
            raise HTTPException(status_code=500, detail="reCAPTCHA secret not configured")
        resp = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": RECAPTCHA_SECRET, "response": data.recaptchaToken}
        )
        if not resp.ok or not resp.json().get("success"):
            raise HTTPException(status_code=400, detail="reCAPTCHA verification failed")

        email = data.email.strip().lower()

        # Validate passwords
        if data.password != data.confirmPassword:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        # Check if email exists and is verified
        existing_user = users_col.find_one({"email": email})
        if existing_user and existing_user.get("emailVerified"):
            raise HTTPException(status_code=400, detail="Email already exists")

        # Create OTP
        otp = ''.join(random.choices(string.digits, k=6))
        otp_hash = pwd_context.hash(otp)
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        auth_db.email_verifications.insert_one({
            "email": email,
            "purpose": "signup",
            "otpHash": otp_hash,
            "expiresAt": expires_at,
            "used": False,
            "createdAt": datetime.utcnow()
        })

        # Save pending user if not exists
        if not existing_user:
            hashed_pw = pwd_context.hash(data.password[:MAX_BCRYPT_LEN])
            users_col.insert_one({
                "name": data.name,
                "email": email,
                "passwordHash": hashed_pw,
                "emailVerified": False,
                "providers": ["password"],
                "isActive": False,
                "createdAt": datetime.utcnow()
            })
        else:
            hashed_pw = pwd_context.hash(data.password[:MAX_BCRYPT_LEN])
            users_col.update_one({"email": email}, {"$set": {"passwordHash": hashed_pw, "name": data.name}})

        background_tasks.add_task(send_signup_otp, email, data.name, otp)
        
        return {"success": True, "message": "Verification code sent to your email.", "expiresIn": 600}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/signup/verify-otp")
async def verify_otp(data: VerifyOTPModel, response: Response):
    try:
        email = data.email.strip().lower()
        otp_record = auth_db.email_verifications.find_one(
            {"email": email, "purpose": "signup", "used": False},
            sort=[("createdAt", -1)]
        )

        if not otp_record or otp_record["expiresAt"] < datetime.utcnow():
            raise HTTPException(status_code=400, detail="OTP is invalid or expired")

        if not pwd_context.verify(data.otp, otp_record["otpHash"]):
            raise HTTPException(status_code=400, detail="Incorrect OTP")

        auth_db.email_verifications.update_one({"_id": otp_record["_id"]}, {"$set": {"used": True}})

        user = users_col.find_one({"email": email})
        users_col.update_one({"email": email}, {"$set": {"emailVerified": True, "isActive": True}})

        token = create_access_token({"sub": email})
        response.set_cookie(
            key="access_token", value=token, httponly=True, samesite="lax", secure=COOKIE_SECURE,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES*60, path="/"
        )

        return {"success": True, "message": "Signup successful", "name": user.get("name", ""), "access_token": token}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/signup/resend-otp")
async def resend_otp(data: ResendOTPModel, background_tasks: BackgroundTasks):
    try:
        email = data.email.strip().lower()
        user = users_col.find_one({"email": email})
        if not user or user.get("emailVerified"):
            return {"success": True, "message": "If an account exists, a new OTP has been sent."}

        last_otp = auth_db.email_verifications.find_one({"email": email, "purpose": "signup"}, sort=[("createdAt", -1)])
        if last_otp and last_otp["createdAt"] > datetime.utcnow() - timedelta(seconds=60):
            raise HTTPException(status_code=429, detail="Please wait before requesting a new OTP")

        otp = ''.join(random.choices(string.digits, k=6))
        otp_hash = pwd_context.hash(otp)
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        auth_db.email_verifications.insert_one({
            "email": email, "purpose": "signup", "otpHash": otp_hash, "expiresAt": expires_at,
            "used": False, "createdAt": datetime.utcnow()
        })
        
        background_tasks.add_task(send_signup_otp, email, user.get("name", "User"), otp)
        return {"success": True, "message": "A new OTP has been sent."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- LOGIN ----------------
@app.post("/login")
async def login(data: LoginModel, response: Response):
    try:
        email = data.email.strip().lower()
        user = users_col.find_one({"email": email})
        
        # Support old users
        stored_hash = user.get("passwordHash") or user.get("password", "") if user else ""
        
        if not user or not pwd_context.verify(data.password[:MAX_BCRYPT_LEN], stored_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        if not user.get("emailVerified") and user.get("providers", []) == ["password"]:
            raise HTTPException(status_code=403, detail="Please verify your email first.")

        token = create_access_token({"sub": email})
        response.set_cookie(
            key="access_token", value=token, httponly=True, samesite="lax", secure=COOKIE_SECURE,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES*60, path="/"
        )
        return {"message": "Login successful", "name": user.get("name", ""), "access_token": token}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- GOOGLE AUTH ----------------
@app.post("/api/auth/google")
async def google_auth(data: GoogleAuthModel, response: Response):
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not client_id:
            raise HTTPException(status_code=500, detail="Google Client ID not configured")
            
        idinfo = id_token.verify_oauth2_token(
            data.credential, 
            google_requests.Request(), 
            client_id, 
            clock_skew_in_seconds=10
        )
        email = idinfo['email'].lower()
        name = idinfo.get('name', 'User')
        google_sub = idinfo['sub']
        profile_pic = idinfo.get('picture', '')

        if not idinfo.get('email_verified'):
            raise HTTPException(status_code=400, detail="Google email not verified")

        user = users_col.find_one({"email": email})

        if user:
            # Link account
            update_data = {}
            providers = user.get("providers", [])
            if "google" not in providers:
                providers.append("google")
                update_data["providers"] = providers
            
            update_data["googleSub"] = google_sub
            if not user.get("emailVerified"):
                update_data["emailVerified"] = True
                update_data["isActive"] = True
                
            if update_data:
                users_col.update_one({"email": email}, {"$set": update_data})
        else:
            # Create user
            new_user = {
                "name": name,
                "email": email,
                "passwordHash": None,
                "providers": ["google"],
                "googleSub": google_sub,
                "profilePic": profile_pic,
                "emailVerified": True,
                "isActive": True,
                "createdAt": datetime.utcnow()
            }
            users_col.insert_one(new_user)
            user = new_user

        token = create_access_token({"sub": email})
        response.set_cookie(
            key="access_token", value=token, httponly=True, samesite="lax", secure=COOKIE_SECURE,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES*60, path="/"
        )
        return {"message": "Login successful", "name": name, "access_token": token}
    except ValueError as e:
        print(f"Google Token Verification Error: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- FORGOT/RESET PASSWORD ----------------
@app.post("/api/auth/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    try:
        email = req.email.strip().lower()
        user = users_col.find_one({"email": email})
        
        # Always return success to prevent enumeration
        msg = "If an account exists for this email, a password reset OTP has been sent."
        if not user:
            return {"success": True, "message": msg}
            
        otp = ''.join(random.choices(string.digits, k=6))
        otp_hash = pwd_context.hash(otp)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        auth_db.email_verifications.insert_one({
            "email": email,
            "purpose": "reset_password",
            "otpHash": otp_hash,
            "expiresAt": expires_at,
            "used": False,
            "createdAt": datetime.utcnow()
        })
        
        background_tasks.add_task(send_password_reset_otp, email, otp)
        return {"success": True, "message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/reset-password")
async def reset_password(req: ResetPasswordRequest):
    try:
        if req.newPassword != req.confirmPassword:
            raise HTTPException(status_code=400, detail="Passwords do not match")
            
        email = req.email.strip().lower()
        
        # Verify OTP
        otp_record = auth_db.email_verifications.find_one(
            {"email": email, "purpose": "reset_password", "used": False},
            sort=[("createdAt", -1)]
        )
        
        if not otp_record or otp_record["expiresAt"] < datetime.utcnow():
            raise HTTPException(status_code=400, detail="OTP is invalid or expired")

        if not pwd_context.verify(req.otp, otp_record["otpHash"]):
            raise HTTPException(status_code=400, detail="Incorrect OTP")
            
        user = users_col.find_one({"email": email})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        hashed_pw = pwd_context.hash(req.newPassword[:MAX_BCRYPT_LEN])
        
        providers = user.get("providers", [])
        if "password" not in providers:
            providers.append("password")
            
        users_col.update_one(
            {"email": email},
            {"$set": {"passwordHash": hashed_pw, "providers": providers, "emailVerified": True}}
        )
        
        # Mark OTP as used
        auth_db.email_verifications.update_one({"_id": otp_record["_id"]}, {"$set": {"used": True}})
        
        return {"success": True, "message": "Password reset successfully. You can now log in."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- SESSION CHECK ----------
@app.get("/api/session")
async def get_session(request: Request):
    token = get_token_from_request(request)
    if not token:
        return {"active": False}
    payload = verify_token(token)
    if not payload:
        return {"active": False}
    
    user_email = payload.get("sub")
    return {"active": True, "email": user_email}

# ---------------- LOGOUT ----------------
@app.post("/api/logout")
async def api_logout(response: Response):
    response.delete_cookie("access_token", path="/", samesite="lax")
    return {"message": "Logged out successfully"}

# ---------------- PROTECTED DASHBOARD API ----------------
@app.get("/api/dashboard")
async def api_dashboard(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Session expired, please log in again.")

    email = payload.get("sub")
    user = users_col.find_one({"email": email}, {"password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["_id"] = str(user["_id"])
    return {"message": f"Welcome, {user.get('name', email)}!", "user": user}

# ---------------- PLAN FEEDBACK API ----------------
@app.get("/api/plan-feedback")
async def get_plan_feedback(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Session expired")

    email = payload.get("sub")
    feedbacks = list(feedback_col.find({"user_email": email}, {"_id": 0}))
    return feedbacks

@app.post("/api/plan-feedback")
async def create_plan_feedback(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Session expired")

    email = payload.get("sub")
    body = await request.json()
    
    # Add user email and created time
    body["user_email"] = email
    body["created_at"] = datetime.utcnow().isoformat()
    
    # Upsert based on feedbackId so we don't get duplicates
    feedback_id = body.get("feedbackId")
    if feedback_id:
        feedback_col.update_one(
            {"user_email": email, "feedbackId": feedback_id},
            {"$set": body},
            upsert=True
        )
    else:
        feedback_col.insert_one(body)
        
    return {"message": "Feedback saved successfully"}

# ---------------- LOAD RECIPE DATA ----------------
RECIPES_FILE = os.path.join(STATIC_DIR, "final_data_updated.recipes.json")
if not os.path.exists(RECIPES_FILE):
    raise FileNotFoundError(f"{RECIPES_FILE} not found")

with open(RECIPES_FILE, "r", encoding="utf-8") as f:
    RECIPES = json.load(f)

# Build graph
G = nx.Graph()
all_ingredients_set = set()
recipe_info_map = {}

def preprocess_ingredient(ing):
    synonyms = re.findall(r'([^\(\)]+)', ing.lower().strip())
    return [s.strip() for s in synonyms]

for r in RECIPES:
    recipe_name = r["TranslatedRecipeName"]
    recipe_info_map[recipe_name] = r
    G.add_node(recipe_name, type="recipe")
    main_ings = r.get("main_ingredients", [])
    for ing in main_ings:
        for i in preprocess_ingredient(ing):
            all_ingredients_set.add(i)
            G.add_node(i, type="ingredient")
            G.add_edge(recipe_name, i)

all_ingredients_list = list(all_ingredients_set)

def correct_ingredient(user_ing):
    match, score, _ = process.extractOne(user_ing.lower(), all_ingredients_list, scorer=fuzz.WRatio)
    return match


# ---------- Language Detection Helper ----------
def is_non_english(text: str) -> bool:
    """Detect Indian-language text using Unicode ranges."""
    if not text:
        return False
    return bool(re.search(r"[\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0A80-\u0AFF\u0B00-\u0B7F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F\u0D80-\u0DFF]", text))

def recipe_is_english(recipe: dict) -> bool:
    """Return True if recipe title, ingredients, and instructions are all English."""
    if is_non_english(recipe.get("TranslatedRecipeName", "")):
        return False

    for ing in recipe.get("TranslatedIngredients", []):
        if is_non_english(ing):
            return False

    for step in recipe.get("TranslatedInstructions", []):
        if is_non_english(step):
            return False

    return True

# ---------------- SUGGEST RECIPES ----------------
@app.post("/suggest_recipes")
def get_recipe_suggestions(data: IngredientsInput):
    if not data.ingredients:
        return {"message": "Please provide at least one ingredient."}

    corrected_ings = [correct_ingredient(ing) for ing in data.ingredients]

    # ✅ Keep latest 10 searches
    search_history.append({
        "ingredients": corrected_ings,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    if len(search_history) > 10:
        search_history.pop(0)

    recipe_scores = []
    for recipe in [n for n, d in G.nodes(data=True) if d['type'] == 'recipe']:
        main_ing_neighbors = set(G.neighbors(recipe))
        matched = main_ing_neighbors & set(corrected_ings)
        if not matched:
            continue

        r = recipe_info_map[recipe]

        # 🛑 Skip if recipe contains Hindi/Indian text
        if not recipe_is_english(r):
            continue

        # Check image path
        img_path = r.get("image_path", "")
        if not img_path:
            continue
        img_filename = os.path.basename(img_path).replace("\\", "/")
        full_img_path = os.path.join(STATIC_DIR, "recipes_images", img_filename)
        if not os.path.isfile(full_img_path):
            continue

        recipe_scores.append((recipe, matched, img_filename))

    # Sort by number of matched ingredients (descending)
    recipe_scores.sort(key=lambda x: len(x[1]), reverse=True)

    # Prepare results (max 9)
    results = []
    for recipe_name, matched_set, img_filename in recipe_scores[:9]:
        r = recipe_info_map[recipe_name]
        results.append({
            "TranslatedRecipeName": r.get("TranslatedRecipeName"),
            "main_ingredients": r.get("main_ingredients", []),
            "common_ingredients": r.get("common_ingredients", []),
            "matched_ingredients": list(matched_set),
            "matched_count": len(matched_set),
            "image": f"/static/recipes_images/{img_filename}"
        })

    if not results:
        return {"message": "No English recipes found for these ingredients."}

    return {"user_input": data.ingredients, "suggested_recipes": results}


# ---------------- GET RECIPE DETAILS ----------------
@app.get("/get_recipe")
def get_recipe(name: str):
    normalized_name = name.strip().lower().replace("%20", " ")

    matched_recipe = None
    for key in recipe_info_map.keys():
        if key.strip().lower() == normalized_name:
            matched_recipe = recipe_info_map[key]
            break

    if not matched_recipe:
        raise HTTPException(status_code=404, detail=f"Recipe '{name}' not found")

    # 🛑 Skip non-English recipes
    if not recipe_is_english(matched_recipe):
        raise HTTPException(status_code=400, detail="Recipe not available in English")

    # ✅ Save viewed recipe
    view_history.append({
        "recipe_name": matched_recipe.get("TranslatedRecipeName", name),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    if len(view_history) > 10:
        view_history.pop(0)

    img_path = matched_recipe.get("image_path", "default.jpg")
    img_filename = os.path.basename(img_path).replace("\\", "/")

    return {
        "TranslatedRecipeName": matched_recipe.get("TranslatedRecipeName"),
        "TranslatedIngredients": matched_recipe.get("TranslatedIngredients", []),
        "TranslatedInstructions": matched_recipe.get("TranslatedInstructions", []),
        "PrepTimeInMins": matched_recipe.get("PrepTimeInMins", ""),
        "CookTimeInMins": matched_recipe.get("CookTimeInMins", ""),
        "Servings": matched_recipe.get("Servings", ""),
        "Course": matched_recipe.get("Course", ""),
        "Cuisine": matched_recipe.get("Cuisine", ""),
        "Diet": matched_recipe.get("Diet", ""),
        "image": f"/static/recipes_images/{img_filename}"
    }

@app.get("/get_history")
def get_history():
    return {
        "searched": search_history[::-1],  # latest first
        "viewed": view_history[::-1]
    }


reviews_col = auth_db["reviews"]

# ---------------- REVIEW MODEL ----------------
class Review(BaseModel):
    name: str
    email: EmailStr
    rating: int
    review: str

@app.get("/reviews", response_class=HTMLResponse)
async def reviews_page():
    """
    Serves the main reviews UI (reviews.html)
    """
    path = os.path.join(STATIC_DIR, "reviews.html")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="reviews.html not found")
    return FileResponse(path)

# GET all reviews
@app.get("/api/reviews")
def get_reviews():
    reviews = list(reviews_col.find().sort("createdAt",-1))
    for r in reviews:
        r["_id"]=str(r["_id"])
        if isinstance(r.get("createdAt"), datetime):
            r["createdAt"]=r["createdAt"].isoformat()
    return reviews

# POST new review
@app.post("/api/reviews")
def post_review(r: Review):
    if r.rating<1 or r.rating>5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    data=r.dict()
    data["createdAt"]=datetime.utcnow()
    res=reviews_col.insert_one(data)
    return {"status":"success","id":str(res.inserted_id)}
# ==============================
# 📦 USER DATA COLLECTION
# ==============================
userdata_col = auth_db["userdata"]

class UserData(BaseModel):
    name: str
    email: EmailStr
    address: str = ""
    profilePic: str = ""
    favorites: list = []
    activity: list = []
    timeSpent: str = "0m"


# ---------------- PROFILE PAGE ----------------
@app.get("/profile", response_class=HTMLResponse)
async def profile_page():
    path = os.path.join(STATIC_DIR, "profile.html")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="profile.html not found")
    return FileResponse(path)


# ---------------- FETCH USER PROFILE ----------------
@app.get("/api/profile")
async def get_user_profile(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    email = payload.get("sub")

    # Base user info
    user = users_col.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Extended data
    userdata = userdata_col.find_one({"email": email}, {"_id": 0}) or {}

    return {
        "name": user.get("name", ""),
        "email": email,
        "address": userdata.get("address", "Add your address"),
        "profilePic": userdata.get("profilePic", "/static/recipes_images/icon.png"),
        "favorites": userdata.get("favorites", []),
        "activity": userdata.get("activity", []),
        "timeSpent": userdata.get("timeSpent", "0m"),
    }


# ---------------- UPLOAD PROFILE PIC ----------------
@app.post("/api/upload_profile_pic")
async def upload_profile_pic(request: Request, file: UploadFile = File(...)):
    token = get_token_from_request(request)
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    email = payload.get("sub")

    upload_dir = os.path.join(STATIC_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{email}_{file.filename}")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    file_url = "/" + file_path.replace("\\", "/")
    userdata_col.update_one({"email": email}, {"$set": {"profilePic": file_url}}, upsert=True)
    return {"success": True, "profilePic": file_url}


# ---------------- FAVORITES ----------------
@app.post("/api/add_favorite")
async def add_favorite(request: Request, title: str = Form(...), image: str = Form(...)):
    token = get_token_from_request(request)
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    email = payload.get("sub")
    userdata_col.update_one(
        {"email": email},
        {"$addToSet": {"favorites": {"title": title, "image": image}}},
        upsert=True
    )
    return {"success": True, "message": "Added to favorites"}


@app.post("/api/remove_favorite")
async def remove_favorite(request: Request, title: str = Form(...)):
    token = get_token_from_request(request)
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    email = payload.get("sub")
    userdata_col.update_one(
        {"email": email},
        {"$pull": {"favorites": {"title": title}}}
    )
    return {"success": True, "message": "Removed from favorites"}


@app.get("/api/get_favorites")
async def get_favorites(request: Request):
    token = get_token_from_request(request)
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    email = payload.get("sub")
    user = userdata_col.find_one({"email": email}, {"_id": 0, "favorites": 1})
    favorites = user.get("favorites", []) if user else []
    return {"favorites": favorites}


# ---------------- ACTIVITY LOG ----------------
@app.post("/api/add_activity")
async def add_activity(request: Request, activity: str = Form(...)):
    token = get_token_from_request(request)
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    email = payload.get("sub")
    userdata_col.update_one(
        {"email": email},
        {"$push": {"activity": {"$each": [activity], "$position": 0}}},
        upsert=True
    )
    return {"success": True, "message": "Activity added"}


@app.delete("/api/clear_activity")
async def clear_activity(request: Request):
    token = get_token_from_request(request)
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    email = payload.get("sub")
    userdata_col.update_one({"email": email}, {"$set": {"activity": []}})
    return {"success": True, "message": "Activity cleared"}


# ---------------- ADDRESS ----------------
@app.post("/api/update_address")
async def update_address(request: Request, address: str = Form(...)):
    token = get_token_from_request(request)
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    email = payload.get("sub")
    userdata_col.update_one({"email": email}, {"$set": {"address": address}}, upsert=True)
    return {"success": True, "message": "Address updated"}


# ================= HEALTH =================

@app.get("/health", response_class=HTMLResponse)
async def health_page():

    path = os.path.join(STATIC_DIR, "health.html")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Health page not found")

    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ================= BUDGET =================

@app.get("/budgetbased", response_class=HTMLResponse)
async def budget_page():

    path = os.path.join(STATIC_DIR, "budgetbased.html")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Budget page not found")

    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ================= WEIGHT LOSS =================

@app.get("/loss", response_class=HTMLResponse)
async def loss_page():

    path = os.path.join(STATIC_DIR, "loss.html")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Loss page not found")

    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ================= WEIGHT GAIN =================

@app.get("/gain", response_class=HTMLResponse)
async def gain_page():

    path = os.path.join(STATIC_DIR, "gain.html")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Gain page not found")

    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ================= FITNESS =================

@app.get("/fitness", response_class=HTMLResponse)
async def fitness_page():

    path = os.path.join(STATIC_DIR, "fitness.html")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Fitness page not found")

    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ================= WEEKLY MEAL =================

@app.get("/meal", response_class=HTMLResponse)
async def meal_page():

    path = os.path.join(STATIC_DIR, "meal.html")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Meal page not found")

    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ================= NUTRITION =================

@app.get("/nutri", response_class=HTMLResponse)
async def nutri_page():

    path = os.path.join(STATIC_DIR, "nutri.html")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Nutrition page not found")

    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
    
    
@app.post("/generate-health-recipes")
async def generate_health_recipes(request: Request):
    try:
        data = await request.json()
        import nutrition_engine
        import json
        result_json = nutrition_engine.generate_health_plan(data)
        result_dict = json.loads(result_json)
        return result_dict.get("recipes", [])
    except Exception as e:
        print(f"ERROR in /generate-health-recipes:", e)
        return []

@app.post("/generate-ai-plan")
async def generate_ai_plan(request: Request):
    try:
        import nutrition_engine
        data = await request.json()
        print(f"[/generate-ai-plan] Received request data:", data)
        result_json = nutrition_engine.generate_weight_loss_plan(data)
        import json
        return JSONResponse(content={"plan": json.loads(result_json)})
    except Exception as e:
        print(f"Error in /generate-ai-plan:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
@app.get("/generate-recipe")

async def generate_recipe(meal:str):
    try:
        import nutrition_engine
        recipe = nutrition_engine.get_recipe_details(meal)
        return recipe
    except Exception as e:
        print("RECIPE ERROR:", e)
        return {
            "name": meal,
            "ingredients":["Generic Ingredient"],
            "process":["Generic Step"],
            "nutrition":{
                "calories":"250 kcal",
                "protein":"15g",
                "carbs":"30g",
                "fat":"8g"
            }
        }


@app.post("/delete-plan")
async def delete_plan(data: dict):

    email = data.get("email")

    plans_collection.delete_one({
        "email": email
    })

    return {
        "success": True
    }

@app.post("/generate-weight-gain-plan")
async def generate_weight_gain_plan(request: Request):
    try:
        import nutrition_engine
        data = await request.json()
        print(f"[/generate-weight-gain-plan] Received request data:", data)
        result_json = nutrition_engine.generate_weight_gain_plan(data)
        import json
        return JSONResponse(content={"plan": json.loads(result_json)})
    except Exception as e:
        print(f"Error in /generate-weight-gain-plan:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
@app.post("/generate-budget-plan")
async def generate_budget_plan(request: Request):
    try:
        import nutrition_engine
        data = await request.json()
        print(f"[/generate-budget-plan] Received request data:", data)
        result_json = nutrition_engine.generate_budget_plan(data)
        import json
        return JSONResponse(content={"success": True, "plan": json.loads(result_json)})
    except Exception as e:
        print(f"Error in /generate-budget-plan:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
@app.get("/history")
async def get_history():
    data = list(history_col.find({}, {"_id": 0}))
    return {"success": True, "history": data}
@app.get("/history/{days}")
async def get_history_by_days(days: int):
    data = list(history_col.find(
        {"input.days": days},
        {"_id": 0}
    ))
    return {"success": True, "history": data}

@app.post("/generate-gym-plan")
async def generate_gym_plan(request: Request):
    try:
        import nutrition_engine
        data = await request.json()
        print(f"[/generate-gym-plan] Received request data:", data)
        result_json = nutrition_engine.generate_gym_plan(data)
        import json
        return JSONResponse(content={"plan": json.loads(result_json)})
    except Exception as e:
        print(f"Error in /generate-gym-plan:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
@app.post("/delete-gym-plan")
async def delete_gym_plan(data: dict):

    email = data.get("email")

    fitness_collection.delete_one({"email": email})

    return {"success": True}

@app.get("/get-gym-plan")
async def get_gym_plan(email: str):

    plan = fitness_collection.find_one({"email": email})

    if plan:
        return {"plan": plan["plan"]}

    return {"plan": None}


@app.post("/generate-gym-recipe")
async def generate_gym_recipe(request: Request):
    try:
        data = await request.json()
        meal = data.get("meal", "")
        import nutrition_engine
        recipe = nutrition_engine.get_recipe_details(meal)
        return recipe
    except Exception as e:
        print(f"ERROR in /generate-gym-recipe:", e)
        return {"recipe": {
            "name": meal if 'meal' in locals() else "Unknown",
            "ingredients": ["Generic Ingredient"],
            "process": ["Generic Step"],
            "steps": ["Generic Step"],
            "nutrition": {
                "calories": "250 kcal",
                "protein": "15g",
                "carbs": "30g",
                "fat": "8g"
            }
        }}

@app.post("/generate-weekly-food-plan")
async def generate_weekly_food_plan(request: Request):
    try:
        import nutrition_engine
        data = await request.json()
        print(f"[/generate-weekly-food-plan] Received request data:", data)
        result_json = nutrition_engine.generate_weekly_food_plan(data)
        import json
        return JSONResponse(content={"success": True, "plan": json.loads(result_json)})
    except Exception as e:
        print(f"Error in /generate-weekly-food-plan:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
@app.get("/get-weekly-food-plan")
async def get_weekly_food_plan(email: str):

    try:

        saved_plan = plans_collection.find_one({
            "email": email,
            "plan_type": "weekly_food"
        })

        if saved_plan:

            return {
                "success": True,
                "plan": saved_plan["plan"]
            }

        return {
            "success": True,
            "plan": None
        }

    except Exception as e:

        print("GET WEEKLY PLAN ERROR:", e)

        return {
            "success": False,
            "plan": None,
            "error": str(e)
        }
@app.post("/generate-weekly-recipe")
async def generate_weekly_recipe(request: Request):
    try:
        data = await request.json()
        meal = data.get("meal", "")
        import nutrition_engine
        recipe = nutrition_engine.get_recipe_details(meal)
        return {"recipe": recipe}
    except Exception as e:
        print(f"ERROR in /generate-weekly-recipe:", e)
        return {"recipe": {
            "name": meal if 'meal' in locals() else "Unknown",
            "ingredients": ["Generic Ingredient"],
            "process": ["Generic Step"],
            "steps": ["Generic Step"],
            "nutrition": {
                "calories": "250 kcal",
                "protein": "15g",
                "carbs": "30g",
                "fat": "8g"
            }
        }}

@app.get("/get-user-plan")
async def get_user_plan(email: str):
    plan = plans_collection.find_one({"email": email}, sort=[("_id", -1)])
    if plan and "plan" in plan:
        return {"success": True, "plan": plan["plan"]}
    return {"success": False, "plan": None}

@app.get("/{page}.html", response_class=HTMLResponse)
async def serve_html_pages(page: str):
    import os
    path = os.path.join(STATIC_DIR, f"{page}.html")
    if not os.path.exists(path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Page not found")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())





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

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="root_static")

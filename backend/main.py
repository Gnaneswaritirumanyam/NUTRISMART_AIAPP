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
            max_tokens=700
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

        name = data.get("name")
        age = data.get("age")
        gender = data.get("gender")
        height = data.get("height")
        weight = data.get("weight")
        foodType = data.get("foodType")
        condition = data.get("condition")

        prompt = f"""
Generate exactly 3 healthy recipes.

User Details:
Name: {name}
Age: {age}
Gender: {gender}
Height: {height}
Weight: {weight}
Food Type: {foodType}
Health Condition: {condition}

Return ONLY valid JSON.

Format:

{{
  "recipes":[
    {{
      "name":"Healthy Salad",
      "ingredients":["Tomato","Onion"],
      "process":["Cut vegetables","Mix properly"],
      "nutrition":{{
        "calories":"200 kcal",
        "protein":"10g",
        "carbs":"20g",
        "fat":"5g"
      }}
    }}
  ]
}}
"""

        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[

                {
                    "role":"system",
                    "content":"Return only valid JSON."
                },

                {
                    "role":"user",
                    "content":prompt
                }

            ],

            temperature=0.5,
            max_tokens=4500,
            response_format={"type": "json_object"}

        )

        ai_text = response.choices[0].message.content.strip()

        print(ai_text)

        ai_text = ai_text.replace("```json", "")
        ai_text = ai_text.replace("```", "")
        ai_text = ai_text.strip()

        result = json.loads(ai_text)

        recipes = result["recipes"]

        health_collection.insert_one({
            "name": name,
            "age": age,
            "gender": gender,
            "height": height,
            "weight": weight,
            "foodType": foodType,
            "condition": condition,
            "recipes": recipes
            })
        return JSONResponse(content=recipes)

    except Exception as e:

        print("ERROR:", e)

        return JSONResponse(content=[])
    

plans_collection = auth_db["weightloss_details"]

@app.post("/generate-ai-plan")
async def generate_ai_plan(request: Request):

    try:

        data = await request.json()

        email = data.get("email")

        regenerate = data.get("regenerate", False)

        name = data.get("name")
        age = data.get("age")
        gender = data.get("gender")
        weight = data.get("weight")
        targetWeight = data.get("targetWeight")
        height = data.get("height")
        duration = data.get("duration")
        foodType = data.get("foodType")
        
        existing = plans_collection.find_one({
            "email": email
        })

        # CHECK WHETHER USER DETAILS CHANGED
        details_changed = False

        if existing:

            if(

                existing.get("age") != age or
                existing.get("gender") != gender or
                existing.get("weight") != weight or
                existing.get("targetWeight") != targetWeight or
                existing.get("height") != height or
                existing.get("duration") != duration or
                existing.get("foodType") != foodType
            ):

                details_changed = True

        # RETURN OLD PLAN ONLY IF
        # DETAILS SAME + NOT REGENERATING
        if existing and not regenerate and not details_changed:

            return {
                "plan": existing["plan"]
            }

        # DELETE OLD PLAN
        plans_collection.delete_one({
            "email": email
        })

        random_seed = random.randint(1,999999)

        prompt = f"""

Generate a COMPLETELY DIFFERENT professional healthy 7-day Indian weight loss meal plan.

Random Seed: {random_seed}

User Details:

Name: {name}
Age: {age}
Gender: {gender}
Current Weight: {weight}
Target Weight: {targetWeight}
Height: {height}
Duration: {duration}
Food Preference: {foodType}

IMPORTANT:

1. Return ONLY valid JSON
2. No markdown
3. No explanation
4. Different meals every day
5. Avoid repeating recipes
6. Include Indian healthy foods
7. Create variety in breakfast/lunch/dinner
8. If Vegetarian:
   - Only veg meals
   - No chicken, egg, fish, meat

9. If Non-Vegetarian:
   - Include chicken, fish, eggs and protein meals
   
Format:

{{
  "Sunday": {{
    "Morning": {{
      "meal": "",
      "calories": ""
    }},
    "Afternoon": {{
      "meal": "",
      "calories": ""
    }},
    "Evening": {{
      "meal": "",
      "calories": ""
    }},
    "Night": {{
      "meal": "",
      "calories": ""
    }}
  }}
}}

"""

        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[

                {
                    "role":"system",
                    "content":"Return only valid JSON."
                },

                {
                    "role":"user",
                    "content":prompt
                }

            ],

            temperature=1.2,
            max_tokens=4500,
            response_format={"type": "json_object"}
        )

        ai_text = response.choices[0].message.content.strip()

        ai_text = ai_text.replace("```json", "")
        ai_text = ai_text.replace("```", "")
        ai_text = ai_text.strip()

        plan = json.loads(ai_text)

        # SAVE USER DETAILS + PLAN
        plans_collection.insert_one({

            "email": email,

            "name": name,
            "age": age,
            "gender": gender,
            "weight": weight,
            "targetWeight": targetWeight,
            "height": height,
            "duration": duration,
            "foodType": foodType,
            
            "plan": plan
        })

        return {
            "plan": plan
        }

    except Exception as e:

        print("AI PLAN ERROR:", e)

        return {
            "plan": None
        }
# ADD THIS FUNCTION ABOVE generate_recipe ROUTE

def get_recipe_image(meal):

    url = "https://api.pexels.com/v1/search"

    headers = {

        "Authorization": PEXELS_API

    }

    params = {

        "query": meal,
        "per_page": 1

    }

    response = requests.get(

        url,
        headers=headers,
        params=params

    )

    data = response.json()

    print(data)

    if "photos" in data and len(data["photos"]) > 0:

        return data["photos"][0]["src"]["large"]

    return "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg"

@app.get("/generate-recipe")

async def generate_recipe(meal:str):

    prompt = f"""

Generate healthy recipe details for:

{meal}

STRICT RULES:

1. Return ONLY valid JSON
2. No markdown
3. No explanation
4. ingredients MUST be array
5. process MUST be array

JSON FORMAT:

{{
    "name":"Recipe Name",

    "ingredients":[
        "ingredient 1",
        "ingredient 2",
        "ingredient 3"
    ],

    "process":[
        "step 1",
        "step 2",
        "step 3"
    ],

    "nutrition":{{
        "calories":"250 kcal",
        "protein":"15g",
        "carbs":"30g",
        "fat":"8g"
    }}
}}

"""

    try:

        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[

                {
                    "role":"system",
                    "content":"Return only valid JSON"
                },

                {
                    "role":"user",
                    "content":prompt
                }

            ],

            temperature=0.4

        )

        text = response.choices[0].message.content.strip()

        print(text)

        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

        recipe = json.loads(text)

        # PEXELS IMAGE
        recipe["image"] = get_recipe_image(meal)

        return recipe

    except Exception as e:

        print("RECIPE ERROR:", e)

        return {

            "name": meal,

            "ingredients":[
                "Healthy ingredient 1",
                "Healthy ingredient 2"
            ],

            "process":[
                "Cook properly",
                "Serve healthy"
            ],

            "nutrition":{

                "calories":"250 kcal",
                "protein":"15g",
                "carbs":"30g",
                "fat":"8g"

            },

            "image":"https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg"

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

        data = await request.json()

        email = data.get("email")

        regenerate = data.get("regenerate", False)

        name = data.get("name")
        age = data.get("age")
        gender = data.get("gender")
        weight = data.get("weight")
        targetWeight = data.get("targetWeight")
        height = data.get("height")
        duration = data.get("duration")
        foodType = data.get("foodType")
        
        existing = plans_collection.find_one({
            "email": email,
            "type": "weight_gain"
        })

        # CHECK IF USER DETAILS CHANGED
        details_changed = False

        if existing:

            if(

                existing.get("age") != age or
                existing.get("gender") != gender or
                existing.get("weight") != weight or
                existing.get("targetWeight") != targetWeight or
                existing.get("height") != height or
                existing.get("duration") != duration or
                existing.get("foodType") != foodType

            ):

                details_changed = True

        # RETURN OLD PLAN ONLY IF
        # DETAILS SAME + NOT REGENERATING
        if existing and not regenerate and not details_changed:

            return {
                "plan": existing["plan"]
            }

        # DELETE OLD PLAN
        plans_collection.delete_one({
            "email": email,
            "type": "weight_gain"
        })

        # RANDOM SEED FOR DIFFERENT PLANS
        random_seed = random.randint(1,999999)

        prompt = f"""

Generate a COMPLETELY DIFFERENT professional healthy 7-day WEIGHT GAIN meal plan.

Random Seed: {random_seed}

User Details:

Name: {name}
Age: {age}
Gender: {gender}
Current Weight: {weight}
Target Weight: {targetWeight}
Height: {height}
Duration: {duration}
Food Preference: {foodType} 

IMPORTANT:

1. Return ONLY valid JSON
2. No markdown
3. No explanation
4. High protein meals
5. Muscle building foods
6. Healthy calorie surplus
7. Indian healthy foods
8. Different meals every day
9. Include protein-rich breakfast/lunch/dinner/snacks
10. Avoid repeating recipes
11. If Vegetarian:
    - Only vegetarian muscle-building meals

12. If Non-Vegetarian:
    - Include chicken, fish, eggs, lean meat
    
Format:

{{
  "Sunday": {{
    "Morning": {{
      "meal": "",
      "calories": ""
    }},
    "Afternoon": {{
      "meal": "",
      "calories": ""
    }},
    "Evening": {{
      "meal": "",
      "calories": ""
    }},
    "Night": {{
      "meal": "",
      "calories": ""
    }}
  }}
}}

"""

        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[

                {
                    "role":"system",
                    "content":"Return only valid JSON."
                },

                {
                    "role":"user",
                    "content":prompt
                }

            ],

            temperature=1.2,
            max_tokens=4500,
            response_format={"type": "json_object"}
        )

        ai_text = response.choices[0].message.content.strip()

        ai_text = ai_text.replace("```json", "")
        ai_text = ai_text.replace("```", "")
        ai_text = ai_text.strip()

        plan = json.loads(ai_text)

        # SAVE NEW PLAN + USER DETAILS
        plans_collection.insert_one({

            "email": email,
            "type": "weight_gain",

            "name": name,
            "age": age,
            "gender": gender,
            "weight": weight,
            "targetWeight": targetWeight,
            "height": height,
            "duration": duration,
            "foodType": foodType,
            
            "plan": plan

        })

        return {
            "plan": plan
        }

    except Exception as e:

        print("WEIGHT GAIN PLAN ERROR:", e)

        return {
            "plan": None
        }

@app.post("/generate-budget-plan")
async def generate_budget_plan(request: Request):

    try:
        data = await request.json()

        name = data.get("name")
        age = data.get("age")
        gender = data.get("gender")
        weight = data.get("weight")
        height = data.get("height")
        budget = int(data.get("budget"))   # ✅ TOTAL BUDGET
        days = int(data.get("days"))
        foodType = data.get("foodType")
        goal = data.get("goal")
        condition = data.get("condition")
        activity = data.get("activity")
        allergy = data.get("allergy")  # ✅ FIXED (was missing usage)

        random_seed = random.randint(1, 999999)

        # ================= PROMPT =================
        prompt = f"""
You are a professional Indian nutrition AI.

Generate a {days}-day healthy Indian meal plan.

Random Seed: {random_seed}

USER DETAILS:
Name: {name}
Age: {age}
Gender: {gender}
Weight: {weight}
Height: {height}
TOTAL BUDGET: ₹{budget}
DAYS: {days}
Food Type: {foodType}
Goal: {goal}
Health Condition: {condition}
Activity Level: {activity}
Allergies: {allergy}

STRICT RULES (MANDATORY - MUST FOLLOW):

1. Only Indian foods
2. Strict food type compliance ({foodType})
3. Avoid allergy ingredients completely

4. TOTAL COST CONTROL (VERY IMPORTANT):
   - Total cost for ALL days combined MUST EXACTLY MATCH budget (₹{budget}) ± 5%
   - DO NOT UNDERSPEND OR OVERSPEND

5. DAILY BUDGET RULE:
   - Per day budget = ₹{budget} / {days}
   - Each day MUST use full per-day budget ± 5%

6. MEAL SPLIT RULE:
   - Breakfast = 30% of daily budget
   - Lunch = 40% of daily budget
   - Dinner = 30% of daily budget
7. Include Breakfast, Lunch, Dinner
8. Each meal must include:
   - meal name
   - calories
   - cost (must follow budget split strictly)
   - protein
   - carbs
   - fat
   - recipe (ingredients, steps, time)

9. Recipe steps must be:
   Step 1: ...
   Step 2: ...
   Step 3: ...
   Step 4: ...
   Step 5: ...

10. Ingredients must be real Indian kitchen items

11. Return ONLY valid JSON
12. No markdown, no explanation
FORMAT:
{{
  "days": [
    {{
      "day": 1,
      "breakfast": {{
        "meal": "",
        "calories": 0,
        "cost": 0,
        "protein": "",
        "carbs": "",
        "fat": "",
        "recipe": {{
          "ingredients": [],
          "steps": [],
          "time": ""
        }}
      }},
      "lunch": {{
        "meal": "",
        "calories": 0,
        "cost": 0,
        "protein": "",
        "carbs": "",
        "fat": ""
      }},
      "dinner": {{
        "meal": "",
        "calories": 0,
        "cost": 0,
        "protein": "",
        "carbs": "",
        "fat": ""
      }},
      "totalCalories": 0,
      "totalCost": 0
    }}
  ]
}}
"""

        # ================= GROQ CALL =================
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Return ONLY valid JSON. No markdown."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4500,
            response_format={"type": "json_object"}
        )

        ai_text = response.choices[0].message.content

        # ================= CLEAN JSON =================
        ai_text = ai_text.replace("```json", "").replace("```", "").strip()

        plan = json.loads(ai_text)

        # ================= VERIFY BUDGET =================
        total_cost = sum(
            d["breakfast"]["cost"] +
            d["lunch"]["cost"] +
            d["dinner"]["cost"]
            for d in plan["days"]
        )

        if total_cost > budget:
            plan["warning"] = "Budget exceeded by AI output"

        # ================= SAVE HISTORY =================
        history_col.insert_one({
            "type": "budget_plan",
            "name": name,
            "age": age,
            "gender": gender,
            "weight": weight,
            "height": height,
            "budget": budget,
            "days": days,
            "foodType": foodType,
            "goal": goal,
            "condition": condition,
            "activity": activity,
            "allergy": allergy,
            "plan": plan
        })
        history_col.insert_one({
    "type": "budget_plan",
    "name": name,

    "input": {
        "budget": budget,
        "days": days,
        "per_day_budget": round(budget / days, 2)
    },

    "plan": plan,

    "meta": {
        "created_at": datetime.utcnow()
    }
})
        # ================= SAVE HEALTH DATA =================
        health_collection.insert_one({
            "name": name,
            "weight": weight,
            "height": height,
            "goal": goal,
            "condition": condition
        })

        return {
            "success": True,
            "plan": plan
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )
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
        data = await request.json()

        email = data.get("email")
        regenerate = data.get("regenerate", False)

        # ================= USER DATA =================
        name = data.get("name")
        age = data.get("age")
        gender = data.get("gender")

        height = data.get("height")
        weight = data.get("weight")
        targetWeight = data.get("targetWeight")
        bodyFat = data.get("bodyFat")
        activityLevel = data.get("activityLevel")

        goal = data.get("goal")
        experience = data.get("experience")

        workoutType = data.get("workoutType")
        workoutDays = data.get("workoutDays")
        workoutTime = data.get("workoutTime")

        healthIssues = data.get("healthIssues")
        foodType = data.get("foodType")

        # ================= DB CHECK =================
        existing = fitness_collection.find_one({"email": email})

        details_changed = False

        if existing:
            if (
                existing.get("weight") != weight or
                existing.get("targetWeight") != targetWeight or
                existing.get("goal") != goal or
                existing.get("experience") != experience or
                existing.get("workoutDays") != workoutDays or
                existing.get("foodType") != foodType
            ):
                details_changed = True

        if existing and not regenerate and not details_changed:
            return {"plan": existing["plan"]}

        fitness_collection.delete_one({"email": email})

        random_seed = random.randint(1, 999999)

        # ================= IMPROVED AI PROMPT =================
        prompt = f"""
You are a certified FITNESS COACH + SPORTS SCIENCE AI.

Generate a HIGHLY STRUCTURED 7-DAY GYM PLAN.

Random Seed: {random_seed}

USER PROFILE:
Name: {name}
Age: {age}
Gender: {gender}

Body:
Height: {height} cm
Weight: {weight} kg
Target Weight: {targetWeight} kg
Body Fat: {bodyFat}%
Activity Level: {activityLevel}

Fitness Goal: {goal}
Experience Level: {experience}

Workout Setup:
Type: {workoutType}
Days per week: {workoutDays}
Preferred time: {workoutTime}

Health Issues: {healthIssues}
Diet Type: {foodType}

STRICT RULES:
- Return ONLY valid JSON
- NO markdown
- NO explanations
- MUST be realistic gym training plan
- MUST adjust intensity based on experience
- MUST avoid injury risks
- MUST match goal exactly
- MUST include diet aligned with goal

GOAL RULES:
- Weight Gain → calorie surplus + heavy lifting
- Fat Loss → calorie deficit + cardio focus
- Recomposition → balanced training
- Strength → low reps heavy lifts
- Endurance → high reps + cardio

OUTPUT FORMAT:

{{
  "Monday": {{
    "workout": [
      {{
        "exercise": "Bench Press",
        "sets": "4",
        "reps": "8-10"
      }}
    ],
    "cardio": "10 min treadmill",
    "diet": {{
      "breakfast": "Oats + banana + milk",
      "lunch": "Rice + chicken + vegetables",
      "dinner": "Egg curry + roti",
      "snacks": "nuts + whey protein"
    }},
    "notes": "Focus on controlled movement"
  }},

  "Tuesday": {{
    "workout": [],
    "cardio": "",
    "diet": {{
      "breakfast": "",
      "lunch": "",
      "dinner": "",
      "snacks": ""
    }},
    "notes": ""
  }}
}}

IMPORTANT:
- Indian food only
- Gym-safe exercises only
- No unrealistic diets
"""

        # ================= AI CALL =================
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a strict JSON generator. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=4500,
            response_format={"type": "json_object"}
        )

        text = response.choices[0].message.content.strip()

        # cleanup
        text = text.replace("```json", "").replace("```", "").strip()

        plan = json.loads(text)

        # ================= SAVE =================
        fitness_collection.insert_one({
            "email": email,

            "name": name,
            "age": age,
            "gender": gender,

            "height": height,
            "weight": weight,
            "targetWeight": targetWeight,
            "bodyFat": bodyFat,
            "activityLevel": activityLevel,

            "goal": goal,
            "experience": experience,

            "workoutType": workoutType,
            "workoutDays": workoutDays,
            "workoutTime": workoutTime,

            "healthIssues": healthIssues,
            "foodType": foodType,

            "plan": plan
        })

        return {"plan": plan}

    except Exception as e:
        print("GYM PLAN ERROR:", e)
        return {"plan": None}
  

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

        meal = data.get("meal")
        email = data.get("email")
        planContext = data.get("planContext")

        prompt = f"""
You are a professional gym nutrition chef AI.

Create a HIGH PROTEIN HEALTHY INDIAN RECIPE for gym users.

USER CONTEXT:
{planContext}

FOOD ITEM:
{meal}

RULES:
1. Must match gym goal (fat loss / muscle gain / strength)
2. Must be Indian food only
3. Must be healthy (low oil, high protein)
4. Give clear step-by-step cooking process
5. Return ONLY valid JSON (no markdown, no text)

FORMAT:

{{
  "name": "recipe name",
  "ingredients": [
    "ingredient 1 with quantity",
    "ingredient 2 with quantity",
    "ingredient 3 with quantity"
  ],
  "steps": [
    "Step 1 detailed instruction",
    "Step 2 detailed instruction",
    "Step 3 detailed instruction"
  ],
  "nutrition": {{
    "calories": "value in kcal",
    "protein": "value in g",
    "carbs": "value in g",
    "fat": "value in g"
  }}
}}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You must return ONLY valid JSON. No explanation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )

        text = response.choices[0].message.content.strip()

        # remove markdown safely
        text = text.replace("```json", "").replace("```", "").strip()

        recipe = json.loads(text)

        # ---------------- CLEAN VALIDATION ----------------
        recipe_clean = {
            "name": recipe.get("name", meal),
            "ingredients": recipe.get("ingredients", []),
            "steps": recipe.get("steps", []),
            "nutrition": {
                "calories": recipe.get("nutrition", {}).get("calories", "0 kcal"),
                "protein": recipe.get("nutrition", {}).get("protein", "0g"),
                "carbs": recipe.get("nutrition", {}).get("carbs", "0g"),
                "fat": recipe.get("nutrition", {}).get("fat", "0g")
            }
        }

        return recipe_clean

    except Exception as e:
        print("GYM RECIPE ERROR:", e)

        return {
            "name": meal,
            "ingredients": [
                "Basic protein source (paneer / eggs / dal)",
                "Whole spices (turmeric, cumin)",
                "Healthy oil (1 tsp)"
            ],
            "steps": [
                "Heat pan and add oil",
                "Cook ingredients with spices",
                "Serve hot with balanced portion"
            ],
            "nutrition": {
                "calories": "300 kcal",
                "protein": "20g",
                "carbs": "35g",
                "fat": "10g"
            }
        }
    
@app.post("/generate-weekly-food-plan")
async def generate_weekly_food_plan(request: Request):

    try:
        data = await request.json()

        email = data.get("email")

        if not email:
            return {
                "success": False,
                "plan": None,
                "error": "Email is required"
            }

        name = data.get("name")
        age = data.get("age")
        gender = data.get("gender")
        height = data.get("height")
        weight = data.get("weight")
        targetWeight = data.get("targetWeight")
        activityLevel = data.get("activityLevel")
        goal = data.get("goal")
        foodType = data.get("foodType")
        healthIssues = data.get("healthIssues")
        regenerate = data.get("regenerate", False)

        # Find existing plan
        existing = plans_collection.find_one({
            "email": email,
            "plan_type": "weekly_food"
        })

        details_changed = False

        if existing:

            old_data = existing.get("user_data", {})

            if (
                str(old_data.get("weight")) != str(weight)
                or str(old_data.get("targetWeight")) != str(targetWeight)
                or old_data.get("goal") != goal
                or old_data.get("foodType") != foodType
                or old_data.get("activityLevel") != activityLevel
                or old_data.get("healthIssues") != healthIssues
            ):
                details_changed = True

        # Return saved plan
        if existing and not regenerate and not details_changed:

            return {
                "success": True,
                "plan": existing["plan"]
            }

        random_seed = random.randint(1, 999999)

        prompt = f"""
You are a professional Indian nutritionist.

Generate a healthy 7-day Indian weekly food plan.

Random Seed: {random_seed}

USER DETAILS:
Name: {name}
Age: {age}
Gender: {gender}
Height: {height} cm
Current Weight: {weight} kg
Target Weight: {targetWeight} kg
Activity Level: {activityLevel}
Health Goal: {goal}
Food Type: {foodType}
Health Issues: {healthIssues}

RULES:
- Return ONLY valid JSON.
- No markdown.
- No explanations.
- Exactly 7 days.
- Use Indian home-cooked food.
- Respect the selected food type.
- Consider the user's health goal.
- Include breakfast, lunch, eveningSnack and dinner.
- Include approximate calories.
- Avoid junk food.
- Give realistic portions.

JSON FORMAT:
{{
    "Monday": {{
        "breakfast": "Oats with banana and milk - 350 kcal",
        "lunch": "Rice, dal and vegetables - 550 kcal",
        "eveningSnack": "Fruit and roasted chana - 200 kcal",
        "dinner": "Chapati with paneer curry - 450 kcal"
    }},
    "Tuesday": {{
        "breakfast": "",
        "lunch": "",
        "eveningSnack": "",
        "dinner": ""
    }},
    "Wednesday": {{
        "breakfast": "",
        "lunch": "",
        "eveningSnack": "",
        "dinner": ""
    }},
    "Thursday": {{
        "breakfast": "",
        "lunch": "",
        "eveningSnack": "",
        "dinner": ""
    }},
    "Friday": {{
        "breakfast": "",
        "lunch": "",
        "eveningSnack": "",
        "dinner": ""
    }},
    "Saturday": {{
        "breakfast": "",
        "lunch": "",
        "eveningSnack": "",
        "dinner": ""
    }},
    "Sunday": {{
        "breakfast": "",
        "lunch": "",
        "eveningSnack": "",
        "dinner": ""
    }}
}}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,
            max_tokens=4500,
            response_format={"type": "json_object"}
        )

        text = response.choices[0].message.content.strip()

        if text.startswith("```"):
            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()

        plan = json.loads(text)

        # Delete old plan
        plans_collection.delete_one({
            "email": email,
            "plan_type": "weekly_food"
        })

        # Save new plan
        plans_collection.insert_one({

            "email": email,

            "plan_type": "weekly_food",

            "user_data": {
                "name": name,
                "age": age,
                "gender": gender,
                "height": height,
                "weight": weight,
                "targetWeight": targetWeight,
                "activityLevel": activityLevel,
                "goal": goal,
                "foodType": foodType,
                "healthIssues": healthIssues
            },

            "plan": plan

        })

        return {
            "success": True,
            "plan": plan
        }

    except Exception as e:

        print("WEEKLY FOOD PLAN ERROR:", e)

        return {
            "success": False,
            "plan": None,
            "error": str(e)
        }
        
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

        meal = data.get("meal")
        email = data.get("email")
        goal = data.get("goal")
        foodType = data.get("foodType")

        prompt = f"""
You are a professional Indian nutritionist and chef.

Create a healthy Indian recipe.

Food Item:
{meal}

Food Type:
{foodType}

Health Goal:
{goal}

RULES:
- Return ONLY valid JSON.
- No markdown.
- No explanations.
- Use Indian cooking.
- Give quantities.
- Give clear cooking steps.

FORMAT:
{{
    "name": "Recipe Name",
    "ingredients": [
        "Ingredient with quantity"
    ],
    "steps": [
        "Step 1",
        "Step 2",
        "Step 3"
    ],
    "nutrition": {{
        "calories": "400 kcal",
        "protein": "20 g",
        "carbs": "50 g",
        "fat": "12 g"
    }}
}}
"""

        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[

                {
                    "role": "system",
                    "content": "Return only valid JSON."
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            temperature=0.6

        )

        text = response.choices[0].message.content.strip()

        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

        recipe = json.loads(text)

        return {
            "success": True,
            "recipe": recipe
        }

    except Exception as e:

        print("RECIPE ERROR:", e)

        return {

            "success": False,

            "recipe": {

                "name": meal or "Recipe",

                "ingredients": [
                    "Ingredients unavailable"
                ],

                "steps": [
                    "Recipe generation failed. Please try again."
                ],

                "nutrition": {

                    "calories": "Not available",
                    "protein": "Not available",
                    "carbs": "Not available",
                    "fat": "Not available"

                }

            },

            "error": str(e)

        }


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


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="root_static")



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

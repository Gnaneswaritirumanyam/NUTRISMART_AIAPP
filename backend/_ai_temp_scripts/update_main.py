import os
import re

MAIN_FILE = r"c:\Users\tirum\OneDrive\Desktop\myapp\backend\main.py"

with open(MAIN_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Add imports after the last import line
imports_to_add = """
from pydantic import BaseModel, EmailStr, Field
import random
import string
import hashlib
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from services.email_service import send_signup_otp, send_password_reset_email
"""

if "import hashlib" not in content:
    content = content.replace("from fastapi import FastAPI, UploadFile, File\n", f"from fastapi import FastAPI, UploadFile, File\n{imports_to_add}\n")

# Now let's replace the models and routes block.
# We will use regex to find the block from "# ---------------- MODELS ----------------" to "# ---------------- LOGOUT ----------------"
# Because the block is large, let's just find indices.
start_marker = "# ---------------- MODELS ----------------"
end_marker = "# ---------------- PROTECTED DASHBOARD API ----------------"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_auth_block = """# ---------------- MODELS ----------------
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
    token: str
    newPassword: str
    confirmPassword: str

# ============ GLOBAL SEARCH & VIEW HISTORY ============
search_history = []
view_history = []

# ---------------- SIGNUP / OTP ----------------
@app.post("/api/auth/signup/request-otp")
async def request_otp(data: SignupModel):
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

        db.email_verifications.insert_one({
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

        await send_signup_otp(email, data.name, otp)
        
        return {"success": True, "message": "Verification code sent to your email.", "expiresIn": 600}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/signup/verify-otp")
async def verify_otp(data: VerifyOTPModel, response: Response):
    try:
        email = data.email.strip().lower()
        otp_record = db.email_verifications.find_one(
            {"email": email, "purpose": "signup", "used": False},
            sort=[("createdAt", -1)]
        )

        if not otp_record or otp_record["expiresAt"] < datetime.utcnow():
            raise HTTPException(status_code=400, detail="OTP is invalid or expired")

        if not pwd_context.verify(data.otp, otp_record["otpHash"]):
            raise HTTPException(status_code=400, detail="Incorrect OTP")

        db.email_verifications.update_one({"_id": otp_record["_id"]}, {"$set": {"used": True}})

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
async def resend_otp(data: ResendOTPModel):
    try:
        email = data.email.strip().lower()
        user = users_col.find_one({"email": email})
        if not user or user.get("emailVerified"):
            return {"success": True, "message": "If an account exists, a new OTP has been sent."}

        last_otp = db.email_verifications.find_one({"email": email, "purpose": "signup"}, sort=[("createdAt", -1)])
        if last_otp and last_otp["createdAt"] > datetime.utcnow() - timedelta(seconds=60):
            raise HTTPException(status_code=429, detail="Please wait before requesting a new OTP")

        otp = ''.join(random.choices(string.digits, k=6))
        otp_hash = pwd_context.hash(otp)
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        db.email_verifications.insert_one({
            "email": email, "purpose": "signup", "otpHash": otp_hash, "expiresAt": expires_at,
            "used": False, "createdAt": datetime.utcnow()
        })
        
        await send_signup_otp(email, user.get("name", "User"), otp)
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
            
        idinfo = id_token.verify_oauth2_token(data.credential, google_requests.Request(), client_id)
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
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- FORGOT/RESET PASSWORD ----------------
@app.post("/api/auth/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    try:
        email = req.email.strip().lower()
        user = users_col.find_one({"email": email})
        
        # Always return success to prevent enumeration
        msg = "If an account exists for this email, a password reset link has been sent."
        if not user:
            return {"success": True, "message": msg}
            
        raw_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        
        db.password_reset_tokens.insert_one({
            "email": email,
            "tokenHash": token_hash,
            "expiresAt": expires_at,
            "used": False,
            "createdAt": datetime.utcnow()
        })
        
        base_url = os.getenv("FRONTEND_BASE_URL", FRONTEND_ORIGIN)
        reset_url = f"{base_url}/reset-password.html?token={raw_token}"
        
        await send_password_reset_email(email, reset_url)
        return {"success": True, "message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/reset-password")
async def reset_password(req: ResetPasswordRequest):
    try:
        if req.newPassword != req.confirmPassword:
            raise HTTPException(status_code=400, detail="Passwords do not match")
            
        token_hash = hashlib.sha256(req.token.encode()).hexdigest()
        token_record = db.password_reset_tokens.find_one({"tokenHash": token_hash, "used": False})
        
        if not token_record or token_record["expiresAt"] < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
            
        email = token_record["email"]
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
        db.password_reset_tokens.update_one({"_id": token_record["_id"]}, {"$set": {"used": True}})
        
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

"""

    content = content[:start_idx] + new_auth_block + content[end_idx:]
    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated main.py successfully!")
else:
    print("Could not find start or end markers.")

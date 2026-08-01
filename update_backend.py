import sys

filename = r'c:\Users\tirum\OneDrive\Desktop\myapp\backend\main.py'
with open(filename, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add custom token extractor dependency
extractor = """
def get_token_from_request(request: Request):
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth.split(" ")[1]
    return request.cookies.get("access_token")
"""
if "get_token_from_request" not in content:
    content = content.replace('def verify_token(token: str):', extractor + '\ndef verify_token(token: str):')

# 2. Replace token extraction calls
content = content.replace('token = request.cookies.get("access_token")', 'token = get_token_from_request(request)')

# 3. Update CORS origins
# Replace `origins = ...` with a more permissive local origins list for capacitor
cors_update = 'origins = ["capacitor://localhost", "http://localhost", "https://localhost", "http://10.0.2.2", "http://127.0.0.1:8000", "http://192.168.1.100:8000"] + os.getenv("FRONTEND_ORIGINS", "").split(",")'
# We just look for the existing `origins = ...`
import re
content = re.sub(r'origins\s*=\s*os\.getenv\("FRONTEND_ORIGINS".*?\.split\(","\)', cors_update, content)

# 4. Update /login to return access_token
login_return_old = 'return {"message": "Login successful", "name": user["name"]}'
login_return_new = 'return {"message": "Login successful", "name": user["name"], "access_token": token}'
content = content.replace(login_return_old, login_return_new)

# 5. Fix path issues (e.g. UPLOAD_FOLDER)
upload_fix = """from pathlib import Path
BASE_DIR_PATH = Path(__file__).resolve().parent
UPLOAD_FOLDER = str(BASE_DIR_PATH / "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)"""
content = re.sub(r'UPLOAD_FOLDER\s*=\s*"uploads"\n+os\.makedirs\(UPLOAD_FOLDER,\s*exist_ok=True\)', upload_fix, content)

with open(filename, 'w', encoding='utf-8') as f:
    f.write(content)

print("Backend updated.")

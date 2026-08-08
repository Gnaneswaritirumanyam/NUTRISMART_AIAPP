import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(os.path.dirname(current_dir), "backend")
sys.path.append(backend_dir)

from main import create_access_token, users_col, pwd_context

email = "loadtest@nutrismart.com"
password = "password123"

try:
    # Ensure user exists in DB
    user = users_col.find_one({"email": email})
    if not user:
        users_col.insert_one({
            "name": "Load Test User",
            "email": email,
            "passwordHash": pwd_context.hash(password),
            "emailVerified": True,
            "providers": ["password"]
        })
except Exception as e:
    print(f"Warning: MongoDB check failed: {e}", file=sys.stderr)

token = create_access_token({"sub": email})
print(token)

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(os.path.dirname(current_dir), "backend")
sys.path.append(backend_dir)

from main import create_access_token, pwd_context
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

email = "loadtest@nutrismart.com"
password = "password123"

try:
    # Ensure user exists in DB with a very short timeout so we don't block tests
    temp_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    users_col = temp_client.get_database("nutrismart").get_collection("users")
    
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
    print(f"Warning: MongoDB check failed (this is OK if just using Locust): {e}", file=sys.stderr)



token = create_access_token({"sub": email})
print(token)

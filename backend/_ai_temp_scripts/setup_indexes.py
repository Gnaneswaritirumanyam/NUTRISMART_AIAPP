import os
from pymongo import MongoClient, ASCENDING, IndexModel
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("MONGO_URI not found!")
    exit(1)

client = MongoClient(MONGO_URI)
db = client["myapp"]

# Users collection
users_col = db["users"]
# Drop any existing non-unique email indexes if they exist
try:
    users_col.create_index([("email", ASCENDING)], unique=True)
    print("Created unique index on users.email")
except Exception as e:
    print(f"Index on users.email already exists or error: {e}")

try:
    users_col.create_index([("googleSub", ASCENDING)], unique=True, sparse=True)
    print("Created unique sparse index on users.googleSub")
except Exception as e:
    print(f"Index on users.googleSub already exists or error: {e}")

# Email verifications
email_verifications = db["email_verifications"]
try:
    email_verifications.create_index([("expiresAt", ASCENDING)], expireAfterSeconds=0)
    print("Created TTL index on email_verifications.expiresAt")
except Exception as e:
    print(f"TTL index error: {e}")

# Password reset tokens
password_reset_tokens = db["password_reset_tokens"]
try:
    password_reset_tokens.create_index([("expiresAt", ASCENDING)], expireAfterSeconds=0)
    print("Created TTL index on password_reset_tokens.expiresAt")
except Exception as e:
    print(f"TTL index error: {e}")

print("Indexes setup successfully.")

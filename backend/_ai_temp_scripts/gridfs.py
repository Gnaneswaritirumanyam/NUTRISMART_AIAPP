from pymongo import MongoClient
import gridfs
import os
from pathlib import Path

# ==============================
# MongoDB Configuration
# ==============================
DATABASE_NAME = "nutrismart"

IMAGE_FOLDER = "recipe_images"

# ==============================
# Connect to MongoDB
# ==============================
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

fs = gridfs.GridFS(db)

print("Connected to MongoDB")

# ==============================
# Supported Image Extensions
# ==============================
IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp"
)

# ==============================
# Upload Counter
# ==============================
uploaded = 0
skipped = 0

# ==============================
# Upload Images
# ==============================
for root, dirs, files in os.walk(IMAGE_FOLDER):

    for file in files:

        if file.lower().endswith(IMAGE_EXTENSIONS):

            filepath = os.path.join(root, file)

            try:

                filename = os.path.basename(filepath)

                # Skip if already exists
                existing = db.fs.files.find_one(
                    {"filename": filename}
                )

                if existing:
                    skipped += 1
                    print(f"Skipped: {filename}")
                    continue

                with open(filepath, "rb") as image_file:

                    file_id = fs.put(
                        image_file,
                        filename=filename,
                        filepath=filepath
                    )

                uploaded += 1

                print(
                    f"Uploaded [{uploaded}] "
                    f"{filename} -> {file_id}"
                )

            except Exception as e:

                print(
                    f"Error uploading "
                    f"{filepath}: {e}"
                )

# ==============================
# Summary
# ==============================
print("\n========== DONE ==========")
print(f"Uploaded : {uploaded}")
print(f"Skipped  : {skipped}")
print("==========================")
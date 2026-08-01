import os
from PIL import Image

image_dir = r"c:\Users\tirum\OneDrive\Desktop\myapp\frontend\recipes_images"

def compress_images():
    total_freed = 0
    count = 0
    if not os.path.exists(image_dir):
        print(f"Directory not found: {image_dir}")
        return
        
    files = os.listdir(image_dir)
    print(f"Found {len(files)} files to process in {image_dir}...")
    
    for filename in files:
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            filepath = os.path.join(image_dir, filename)
            try:
                original_size = os.path.getsize(filepath)
                
                with Image.open(filepath) as img:
                    # Convert to RGB if it's RGBA (PNG) to save as JPEG/optimize
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    
                    # Resize if too large
                    max_dim = 1024
                    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                    
                    # Overwrite original
                    img.save(filepath, format="JPEG", quality=85, optimize=True)
                
                new_size = os.path.getsize(filepath)
                if original_size > new_size:
                    total_freed += (original_size - new_size)
                count += 1
                if count % 100 == 0:
                    print(f"Compressed {count} images...")
            except Exception as e:
                print(f"Error compressing {filename}: {e}")
                
    print(f"Finished compressing {count} images.")
    print(f"Total space saved: {total_freed / (1024 * 1024):.2f} MB")

if __name__ == "__main__":
    compress_images()

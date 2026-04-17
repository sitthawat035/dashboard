import requests
from pathlib import Path
from PIL import Image
import os

def download_and_convert(url, folder_path, filename="product_image.jpg"):
    try:
        dest = Path(folder_path)
        dest.mkdir(parents=True, exist_ok=True)
        
        # 1. Download temp webp
        temp_webp = dest / "temp.webp"
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(temp_webp, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            
            # 2. Convert to JPG (Facebook loves JPG)
            with Image.open(temp_webp) as img:
                rgb_im = img.convert('RGB')
                rgb_im.save(dest / filename, "JPEG", quality=95)
            
            # 3. Clean up
            os.remove(temp_webp)
            print(f"✅ Success: {filename} in {folder_path}")
        else:
            print(f"❌ Failed: {url} (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    images = [
        ("https://down-th.img.susercontent.com/file/th-11134211-7r98s-lprtrswrl44a04_tn.webp", "05_ReadyToPost/2026-02-09/08.00"),
        ("https://down-th.img.susercontent.com/file/th-11134207-7qul8-lf0os818i0wh9b_tn.webp", "05_ReadyToPost/2026-02-09/12.00"),
        ("https://down-th.img.susercontent.com/file/th-11134207-7r98t-llk1cknmtrn0a6_tn.webp", "05_ReadyToPost/2026-02-09/18.00"),
        ("https://down-th.img.susercontent.com/file/th-11134207-7r992-llf0pfbsfoou58_tn.webp", "05_ReadyToPost/2026-02-09/22.00"),
    ]
    
    for url, path in images:
        download_and_convert(url, path)

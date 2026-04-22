import requests
from pathlib import Path

def download_image(url, folder_path, filename="product_image.webp"):
    try:
        dest = Path(folder_path)
        dest.mkdir(parents=True, exist_ok=True)
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(dest / filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"✅ Downloaded: {filename} to {folder_path}")
        else:
            print(f"❌ Failed to download: {url} (Status: {response.status_code})")
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
        download_image(url, path)

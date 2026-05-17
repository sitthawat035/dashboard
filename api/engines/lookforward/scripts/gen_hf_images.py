import os
import sys
from pathlib import Path
from huggingface_hub import InferenceClient
from PIL import Image

def generate_hf_image(prompt, output_path, hf_token):
    try:
        client = InferenceClient(
            provider="auto",
            api_key=hf_token,
        )

        print(f"Requesting image from HuggingFace (FLUX.1-schnell): {prompt[:50]}...")
        
        # output is a PIL.Image object
        image = client.text_to_image(
            prompt,
            model="black-forest-labs/FLUX.1-schnell",
        )
        
        image.save(output_path)
        print(f"Saved: {output_path}")
        return True
    except Exception as e:
        print(f"Error generating image: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python gen_hf_images.py <output_dir> <prompt1> [prompt2] ...")
        sys.exit(1)
        
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        # Try to read from .env if not in environment
        try:
            with open("D:/MultiContentApp/.env", "r") as f:
                for line in f:
                    if line.startswith("HF_TOKEN="):
                        hf_token = line.split("=")[1].strip()
                        break
        except:
            pass
            
    if not hf_token:
        print("Error: HF_TOKEN not found.")
        sys.exit(1)
        
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    prompts = sys.argv[2:]
    
    for i, p in enumerate(prompts, 1):
        generate_hf_image(p, out_dir / f"image_{i}.png", hf_token)

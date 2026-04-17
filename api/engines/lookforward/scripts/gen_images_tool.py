import os
import sys
import base64
from pathlib import Path
from google import genai
from google.genai import types

def generate_images(prompts, output_dir, api_key):
    client = genai.Client(api_key=api_key)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    for i, prompt in enumerate(prompts, 1):
        print(f"Generating image {i}...")
        try:
            # Determine aspect ratio from prompt if possible
            aspect_ratio = "16:9"
            if "9:16" in prompt or "portrait" in prompt.lower():
                aspect_ratio = "9:16"
            elif "1:1" in prompt or "square" in prompt.lower():
                aspect_ratio = "1:1"
                
            result = client.models.generate_image(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config=types.GenerateImageConfig(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio,
                    add_watermark=False,
                )
            )
            
            for j, image in enumerate(result.generated_images):
                image_bytes = image.image_binary
                filename = f"image_{i}.png"
                file_path = output_path / filename
                with open(file_path, "wb") as f:
                    f.write(image_bytes)
                generated_files.append(str(file_path))
                print(f"Saved: {file_path}")
                
        except Exception as e:
            print(f"Error generating image {i}: {e}")
            
    return generated_files

if __name__ == "__main__":
    # Example usage: python gen_images_tool.py "output_dir" "prompt1" "prompt2" ...
    if len(sys.argv) < 3:
        print("Usage: python gen_images_tool.py <output_dir> <prompt1> [prompt2] ...")
        sys.exit(1)
        
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)
        
    out_dir = sys.argv[1]
    prompts = sys.argv[2:]
    
    generate_images(prompts, out_dir, api_key)

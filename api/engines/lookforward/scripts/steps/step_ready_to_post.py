"""
Ready to Post Step for Lookforward Pipeline
Creates the final ready-to-post package
"""

import sys
import json
import base64
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
root_dir = project_root.parent

sys.path.insert(0, str(root_dir))
from .base_step import BaseLookforwardStep, StepResult
from common.utils import (
    print_header, print_success, print_error, print_info,
    get_date_str, sanitize_filename, ensure_dir
)


class StepReadyToPost(BaseLookforwardStep):
    """
    Ready-to-post package creation step.
    
    Creates the final package with all files needed for posting:
    - post.txt (main content + hashtags)
    - caption.txt
    - hashtags.txt
    - media/ (images or prompts guide)
    - _metadata.json
    """
    
    def __init__(self):
        super().__init__("ready_to_post")
    
    def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> StepResult:
        """
        Execute ready-to-post package creation.
        
        Args:
            context: Pipeline context with all step results
            **kwargs: Additional options
        
        Returns:
            StepResult with package path
        """
        topic = context.get("topic")
        step_results = context.get("step_results", {})
        
        # Get content data
        content_data = step_results.get("content", {}).get("output_data", {})
        images_data = step_results.get("images", {}).get("output_data", {})
        
        if not content_data:
            return StepResult(
                success=False,
                error=self._create_validation_error("Missing content data")
            )
        
        print_header(f"📦 Creating Ready-to-Post Package")
        
        # Create output directory
        date_str = get_date_str()
        safe_topic = sanitize_filename(topic, max_length=50)
        timestamp = datetime.now().strftime("%H%M%S")
        
        ready_dir = self.ready_dir / date_str / f"{safe_topic}_{timestamp}"
        ensure_dir(ready_dir)
        
        # Extract content
        body_text = content_data.get("content", {}).get("text", "")
        
        # Support both old (caption) and new (caption_short/caption_long) format
        caption = content_data.get("caption_long") or content_data.get("caption_short") or content_data.get("caption", "")
        
        hashtags = " ".join(content_data.get("hashtags", []))
        insight_score = content_data.get("content", {}).get("insight_score", "?")
        
        # 1. post.txt
        post_content = f"{body_text}\n\n{hashtags}"
        post_file = ready_dir / "post.txt"
        with open(post_file, 'w', encoding='utf-8') as f:
            f.write(post_content)
        print_success(" ✅ post.txt - Ready to copy!")
        
        # 2. caption.txt
        caption_file = ready_dir / "caption.txt"
        with open(caption_file, 'w', encoding='utf-8') as f:
            f.write(caption)
        print_success(" ✅ caption.txt")
        
        # 3. hashtags.txt
        hashtags_file = ready_dir / "hashtags.txt"
        with open(hashtags_file, 'w', encoding='utf-8') as f:
            f.write(hashtags)
        print_success(" ✅ hashtags.txt")
        
        # 4. media/
        media_dir = ready_dir / "media"
        ensure_dir(media_dir)
        
        images = images_data.get("images", [])
        if images:
            # Copy images from drafts
            for img in images:
                src_path = Path(img.get("path", ""))
                if src_path.exists():
                    import shutil
                    dst_path = media_dir / src_path.name
                    shutil.copy2(src_path, dst_path)
                    print_success(f" ✅ media/{src_path.name}")
        else:
            # Create prompts guide
            image_prompts = content_data.get("image_prompts", [])
            prompts_file = media_dir / "prompts_guide.txt"
            with open(prompts_file, 'w', encoding='utf-8') as f:
                f.write("AI Studio Image Prompts:\n\n")
                for i, img in enumerate(image_prompts, 1):
                    f.write(f"Image {i}: {img.get('prompt')}\n\n")
            print_info(" ✅ media/prompts_guide.txt created.")
        
        # 5. _metadata.json
        metadata = {
            "topic": topic,
            "generated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "insight_score": insight_score,
            "char_count": len(body_text),
            "has_images": len(images) > 0,
            "run_id": context.get("run_id")
        }
        metadata_file = ready_dir / "_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print_success(f"\n🚀 READY TO POST: {ready_dir}")
        print_info("   1. Open post.txt → Copy content")
        print_info("   2. Upload images (if any)")
        print_info("   3. Post!")
        
        return StepResult(
            success=True,
            output_file=str(ready_dir),
            output_data={
                "package_path": str(ready_dir),
                "post_file": str(post_file),
                "caption_file": str(caption_file),
                "hashtags_file": str(hashtags_file),
                "metadata": metadata
            }
        )
    
    def _create_validation_error(self, message: str):
        from common.error_handler import ValidationError
        return ValidationError(message, step_name="ready_to_post")

"""
Ready to Post Step for Shopee Affiliate Pipeline
Packages content for posting
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import shutil

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
root_dir = project_root.parent

sys.path.insert(0, str(root_dir))

from .base_step import BaseAffiliateStep, StepResult
from common.utils import (
    print_header, print_success, print_error, print_warning,
    ensure_dir, get_date_str
)


class StepReadyToPost(BaseAffiliateStep):
    """
    Ready to post step.
    
    Packages all content for posting to social media.
    """
    
    def __init__(self):
        super().__init__("ready_to_post")
    
    def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> StepResult:
        """
        Execute packaging for posting.
        
        Args:
            context: Pipeline context with converted content
            **kwargs: Additional options
        
        Returns:
            StepResult with packaged posts
        """
        # Get content from previous steps
        step_results = context.get("step_results", {})
        ready_content = []
        
        # Try to get from convert_links
        convert_data = step_results.get("convert_links", {}).get("output_data", {})
        ready_content = convert_data.get("converted_content", [])
        
        if not ready_content:
            # Fallback to download_images
            download_data = step_results.get("download_images", {}).get("output_data", {})
            ready_content = download_data.get("downloaded_content", [])
            
        if not ready_content:
            # Fallback to generate_content
            content_data = step_results.get("generate_content", {}).get("output_data", {})
            ready_content = content_data.get("generated_content", [])
        
        if not ready_content:
            return StepResult(
                success=False,
                error=self._create_validation_error("No content to package")
            )
        
        print_header("Packaging for Posting")
        
        # Create output directory - New organized structure
        date_str = get_date_str()
        timestamp = datetime.now().strftime("%H%M%S")
        output_base = self.ready_dir / date_str
        ensure_dir(output_base)
        
        packaged_posts = []
        
        for i, item in enumerate(ready_content):
            product = item.get("product", {})
            product_name = product.get("name", "unknown")
            caption = item.get("caption", "")
            hashtags = item.get("hashtags", [])
            
            # affiliate_url might not be present if convert_links was skipped
            affiliate_url = item.get("affiliate_url", "")
            if not affiliate_url:
                affiliate_url = product.get("url", "")
                
            image_path = item.get("image_path", "")
            
            # Create safe folder name
            safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in product_name[:40])
            safe_name = safe_name.strip().replace(' ', '_')
            folder_name = f"{safe_name}_{timestamp}_{i+1}"
            
            post_dir = output_base / folder_name
            ensure_dir(post_dir)
            
            # Replace placeholder with actual affiliate URL
            final_caption = caption
            if "[LINK]" in final_caption:
                final_caption = final_caption.replace("[LINK]", affiliate_url)
            elif "[URL]" in final_caption:
                final_caption = final_caption.replace("[URL]", affiliate_url)
            elif affiliate_url not in final_caption:
                final_caption += f"\n\n🔗 ลิงก์: {affiliate_url}"
            
            # Create post.txt
            post_file = post_dir / "post.txt"
            with open(post_file, 'w', encoding='utf-8') as f:
                f.write(final_caption)
            
            # Create caption.txt (short version)
            caption_file = post_dir / "caption.txt"
            with open(caption_file, 'w', encoding='utf-8') as f:
                # Extract first line as short caption
                first_line = final_caption.split('\n')[0] if final_caption else product_name
                f.write(first_line)
            
            # Create hashtags.txt
            hashtags_file = post_dir / "hashtags.txt"
            with open(hashtags_file, 'w', encoding='utf-8') as f:
                hashtag_str = ' '.join(f"#{tag}" for tag in hashtags)
                f.write(hashtag_str)
            
            # Copy image if available
            media_dir = post_dir / "media"
            if image_path and Path(image_path).exists():
                ensure_dir(media_dir)
                image_dest = media_dir / Path(image_path).name
                shutil.copy2(image_path, image_dest)
            else:
                # Create placeholder
                ensure_dir(media_dir)
                placeholder = media_dir / "image_placeholder.txt"
                with open(placeholder, 'w', encoding='utf-8') as f:
                    f.write(f"Image URL: {product.get('image_url', 'N/A')}\n")
                    f.write(f"Product: {product_name}\n")
            
            # Create metadata
            metadata = {
                "product_name": product_name,
                "product_url": product.get("url", ""),
                "affiliate_url": affiliate_url,
                "original_price": product.get("original_price", ""),
                "discount_price": product.get("discount_price", ""),
                "coins": product.get("coins", ""),
                "created_at": datetime.now().isoformat(),
                "pipeline_run": context.get("run_id", "")
            }
            
            metadata_file = post_dir / "_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print_success(f"  [{i+1}] {folder_name}")
            
            packaged_posts.append({
                "post_dir": str(post_dir),
                "post_file": str(post_file),
                "caption": final_caption,
                "hashtags": hashtags,
                "image_path": str(image_path) if image_path else None,
                "affiliate_url": affiliate_url,
                "product_name": product_name
            })
        
        print_success(f"\nPackaged {len(packaged_posts)} posts")
        print(f"Output: {output_base}")
        
        return StepResult(
            success=True,
            output_data={
                "packaged_posts": packaged_posts,
                "total_posts": len(packaged_posts),
                "output_dir": str(output_base)
            }
        )
    
    def _create_validation_error(self, message: str):
        from common.error_handler import ValidationError
        return ValidationError(message, step_name="ready_to_post")
"""
Download Images Step for Shopee Affiliate Pipeline
Downloads product images from URLs
"""

import sys
import os
import requests
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import hashlib

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
root_dir = project_root.parent

sys.path.insert(0, str(root_dir))

from .base_step import BaseAffiliateStep, StepResult
from common.utils import print_header, print_success, print_error, print_warning, ensure_dir


class StepDownloadImages(BaseAffiliateStep):
    """
    Image download step.
    
    Downloads product images from Shopee URLs.
    """
    
    def __init__(self):
        super().__init__("download_images")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> StepResult:
        """
        Execute image downloading.
        
        Args:
            context: Pipeline context with generated content
            **kwargs: Additional options
        
        Returns:
            StepResult with downloaded image paths
        """
        # Get generated content from previous step
        step_results = context.get("step_results", {})
        content_data = step_results.get("generate_content", {}).get("output_data", {})
        generated_content = content_data.get("generated_content", [])
        
        if not generated_content:
            return StepResult(
                success=False,
                error=self._create_validation_error("No content to download images for")
            )
        
        print_header(f"Downloading Images for {len(generated_content)} Products")
        
        # Create output directory
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_dir = self.project_root / "data" / "images" / date_str
        ensure_dir(output_dir)
        
        downloaded_content = []
        total_downloaded = 0
        errors = []
        
        for i, item in enumerate(generated_content):
            product = item.get("product", {})
            image_url = product.get("image_url", "")
            product_name = product.get("name", "unknown")
            
            print(f"\n  [{i+1}/{len(generated_content)}] {product_name[:40]}...")
            
            if not image_url:
                print_warning("  No image URL, skipping")
                downloaded_content.append({
                    **item,
                    "image_path": None,
                    "image_error": "No image URL"
                })
                continue
            
            try:
                # Generate unique filename
                url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
                safe_name = "".join(c if c.isalnum() else "_" for c in product_name[:30])
                filename = f"{safe_name}_{url_hash}.jpg"
                filepath = output_dir / filename
                
                # Download image
                response = self.session.get(image_url, timeout=30)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print_success(f"  Downloaded: {filename}")
                total_downloaded += 1
                
                downloaded_content.append({
                    **item,
                    "image_path": str(filepath),
                    "image_filename": filename
                })
                
            except Exception as e:
                self.logger.error(f"Image download failed for {product_name}: {e}")
                print_error(f"  Error: {e}")
                errors.append(f"{product_name}: {e}")
                
                downloaded_content.append({
                    **item,
                    "image_path": None,
                    "image_error": str(e)
                })
        
        print_success(f"\nDownloaded {total_downloaded}/{len(generated_content)} images")
        
        result = StepResult(
            success=total_downloaded > 0,
            output_data={
                "downloaded_content": downloaded_content,
                "total_downloaded": total_downloaded,
                "output_dir": str(output_dir)
            }
        )
        
        if errors:
            result.warnings = errors
        
        return result
    
    def _create_validation_error(self, message: str):
        from common.error_handler import ValidationError
        return ValidationError(message, step_name="download_images")
"""
Base Step for Shopee Affiliate Pipeline
Provides common functionality for all affiliate steps
"""

import sys
import re
import csv
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
root_dir = project_root.parent  # MultiContentApp root

sys.path.insert(0, str(root_dir))

from common.pipeline_base import BaseStep, StepResult
from common.error_handler import PipelineError, AIError, ErrorSeverity
from common.utils import setup_logger
from common.ai_client import create_ai_client


class BaseAffiliateStep(BaseStep):
    """
    Base class for Shopee Affiliate pipeline steps.
    
    Provides:
    - AI client initialization
    - Common configuration
    - Product loading utilities
    """
    
    def __init__(self, name: str = None):
        super().__init__(name)
        self.project_root = project_root
        self.root_dir = root_dir
        self.data_dir = self.root_dir / "data"
        # New organized directory structure
        self.scraped_dir = self.data_dir / "input" / "shopee" / "products"
        self.ready_dir = self.data_dir / "output" / "shopee" / "content"
        self.posted_dir = self.data_dir / "output" / "shopee" / "posted"
        self.state_dir = self.data_dir / "state" / "shopee"
        
        # Ensure directories exist
        self.scraped_dir.mkdir(parents=True, exist_ok=True)
        self.ready_dir.mkdir(parents=True, exist_ok=True)
        self.posted_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def get_ai_client(self, logger: logging.Logger = None):
        """Get AI client instance."""
        return create_ai_client(logger or self.logger)
    
    def get_latest_csv(self) -> Optional[Path]:
        """Find the latest CSV file in ScrapedData."""
        if not self.scraped_dir.exists():
            return None
        
        csv_files = list(self.scraped_dir.glob("*.csv"))
        if not csv_files:
            return None
        
        # Sort by modification time (latest first)
        csv_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return csv_files[0]
    
    def clean_price(self, price_str: str) -> int:
        """Remove currency symbols and convert to int."""
        if not price_str:
            return 0
        clean = re.sub(r'[^\d]', '', price_str)
        try:
            return int(clean)
        except ValueError:
            return 0
    
    def load_products_from_csv(self, file_path: Path, max_price: int = 500) -> List[Dict]:
        """
        Load products from scraper CSV.
        
        Args:
            file_path: Path to CSV file
            max_price: Maximum price filter
        
        Returns:
            List of product dicts
        """
        if not file_path.exists():
            return []
        
        products = []
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # Validate CSV headers (Support both old and new keys)
                header_map = {
                    'name': ['name', 'item_description', 'title'],
                    'price': ['price', 'item_price', 'current_price'],
                    'link': ['url', 'item_link', 'link'],
                    'image': ['image_url', 'item_image', 'image']
                }
                
                # Check which keys exist
                found_keys = {}
                for canonical, aliases in header_map.items():
                    for alias in aliases:
                        if alias in reader.fieldnames:
                            found_keys[canonical] = alias
                            break
                
                if len(found_keys) < 3: # Need at least name, price, link
                    self.logger.error(f"Invalid CSV format. Missing required fields. Found: {list(found_keys.keys())}")
                    return []
                
                for row in reader:
                    name = row.get(found_keys.get('name'), '').strip()
                    price = row.get(found_keys.get('price'), '').strip()
                    link = row.get(found_keys.get('link'), '').strip()
                    image = row.get(found_keys.get('image'), '').strip()
                    
                    if name and link:
                        price_val = self.clean_price(price)
                        if price_val <= max_price:
                            products.append({
                                "name": name,
                                "price": price_val,
                                "original_price": price,
                                "url": link,
                                "image_url": image,
                                "source": "csv"
                            })
        except Exception as e:
            self.logger.error(f"Error reading CSV: {e}")
            return []
        
        return products
    
    def load_products_from_markdown(self, file_path: Path) -> List[Dict]:
        """Parse product table from markdown file (Fallback)."""
        if not file_path.exists():
            return []
        
        products = []
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line.startswith('|') or '---' in line or 'ชื่อสินค้า' in line:
                continue
            
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 3:
                name = parts[0]
                price = parts[1]
                link = parts[2]
                
                products.append({
                    "name": name,
                    "price": self.clean_price(price),
                    "original_price": price,
                    "url": link,
                    "source": "manual"
                })
        
        return products
    
    def get_output_dir(self, context: Dict[str, Any]) -> Path:
        """Get output directory for current run."""
        from common.utils import get_date_str, sanitize_filename
        from datetime import datetime
        
        date_str = get_date_str()
        timestamp = datetime.now().strftime("%H%M%S")
        
        # Create run folder
        output_dir = self.ready_dir / date_str / f"run_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir
    
    def handle_ai_error(self, error: Exception, step_name: str) -> StepResult:
        """Handle AI-related errors."""
        if isinstance(error, PipelineError):
            return StepResult(success=False, error=error)
        
        ai_error = AIError(
            str(error),
            step_name=step_name,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True
        )
        return StepResult(success=False, error=ai_error)

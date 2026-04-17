"""
Configuration management for Engagement project.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    def load_dotenv(path=None):
        pass

from .utils import load_json, load_markdown


class Config:
    """
    Central configuration manager.
    """
    
    def __init__(self, project_root: Optional[str | Path] = None):
        """
        Initialize configuration.
        
        Args:
            project_root: Project root directory (defaults to Engagement/)
        """
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Auto-detect project root: Look for 'shared' or '.env' in current or parent folders
            current = Path(__file__).resolve().parent
            for _ in range(5): # Check up to 5 levels up
                if (current / ".env").exists() or (current / "shared").exists():
                    break
                current = current.parent
            self.project_root = current
        
        # Load environment variables
        env_file = self.project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        
        # Define paths - New organized structure
        data_dir = self.project_root / "data"
        self.paths = {
            "root": self.project_root,
            "data": data_dir,
            # Input paths
            "input": data_dir / "input",
            "input_lookforward": data_dir / "input" / "lookforward",
            "input_lookforward_topics": data_dir / "input" / "lookforward" / "topics",
            "input_shopee": data_dir / "input" / "shopee",
            "input_shopee_products": data_dir / "input" / "shopee" / "products",
            "input_shopee_queries": data_dir / "input" / "shopee" / "queries",
            # Output paths
            "output": data_dir / "output",
            "output_lookforward": data_dir / "output" / "lookforward",
            "output_lookforward_drafts": data_dir / "output" / "lookforward" / "drafts",
            "output_lookforward_ready": data_dir / "output" / "lookforward" / "ready_to_post",
            "output_lookforward_published": data_dir / "output" / "lookforward" / "published",
            "output_shopee": data_dir / "output" / "shopee",
            "output_shopee_scraped": data_dir / "output" / "shopee" / "scraped",
            "output_shopee_content": data_dir / "output" / "shopee" / "content",
            "output_shopee_posted": data_dir / "output" / "shopee" / "posted",
            # State paths
            "state": data_dir / "state",
            "state_lookforward": data_dir / "state" / "lookforward",
            "state_shopee": data_dir / "state" / "shopee",
            # Archive paths
            "archive": data_dir / "archive",
            "archive_lookforward": data_dir / "archive" / "lookforward",
            "archive_shopee": data_dir / "archive" / "shopee",
            # Legacy paths (for backward compatibility)
            "research": data_dir / "input" / "lookforward" / "topics",
            "strategy": data_dir / "output" / "lookforward" / "drafts",
            "strategies": data_dir / "output" / "lookforward" / "drafts",
            "media": data_dir / "output" / "lookforward" / "drafts",
            "drafts": data_dir / "output" / "lookforward" / "drafts",
            "drafts_approved": data_dir / "output" / "lookforward" / "ready_to_post",
            "drafts_rejected": data_dir / "archive" / "lookforward",
            "ready": data_dir / "output" / "lookforward" / "ready_to_post",
            "published": data_dir / "output" / "lookforward" / "published",
            "analytics": data_dir / "state" / "lookforward",
            "analytics_metrics": data_dir / "state" / "lookforward",
            "analytics_top": data_dir / "state" / "lookforward",
            "analytics_lessons": data_dir / "state" / "lookforward",
            "calendar": data_dir / "state" / "lookforward",
            "error_logs": data_dir / "state" / "lookforward",
            "brand_guidelines": self.project_root / "brand_guidelines.md",
            "system_prompt": self.project_root / "system_prompt.md",
        }
        
        # Load brand guidelines if exists
        self.brand_guidelines = None
        if self.paths["brand_guidelines"].exists():
            self.brand_guidelines = load_markdown(self.paths["brand_guidelines"])
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        Get API key for a service.
        
        Args:
            service: Service name (openai, pexels, unsplash)
            
        Returns:
            API key or None
        """
        key_map = {
            "openai": "OPENAI_API_KEY",
            "pexels": "PEXELS_API_KEY",
            "unsplash": "UNSPLASH_ACCESS_KEY",
            "brave": "BRAVE_SEARCH_API_KEY",
        }
        
        env_var = key_map.get(service.lower())
        if env_var:
            return os.getenv(env_var)
        return None
    
    def get_cdp_url(self) -> str:
        """
        Get Chrome DevTools Protocol URL.
        
        Returns:
            CDP URL
        """
        port = os.getenv("CHROME_CDP_PORT", "9222")
        return f"http://localhost:{port}"
    
    def get_platform_config(self) -> Dict[str, Any]:
        """
        Get platform-specific configuration.
        
        Returns:
            Platform settings dictionary
        """
        return {
            "facebook": {
                "name": "Facebook",
                "max_length": 5000,
                "optimal_length": (200, 500),
                "hashtag_count": (5, 8),
                "emoji_friendly": True,
                "best_times": ["12:00-13:00", "18:00-21:00"],
            },
            "tiktok": {
                "name": "TikTok",
                "max_length": 2200,
                "optimal_length": (100, 200),
                "hashtag_count": (3, 5),
                "emoji_friendly": True,
                "best_times": ["18:00-22:00"],
            },
            "instagram": {
                "name": "Instagram",
                "max_length": 2200,
                "optimal_length": (150, 400),
                "hashtag_count": (10, 15),
                "emoji_friendly": True,
                "best_times": ["11:00-13:00", "19:00-21:00"],
            },
            "twitter": {
                "name": "Twitter/X",
                "max_length": 280,
                "optimal_length": (100, 200),
                "hashtag_count": (2, 3),
                "emoji_friendly": True,
                "best_times": ["12:00-13:00", "17:00-18:00"],
            },
        }
    
    def get_quality_thresholds(self) -> Dict[str, int]:
        """
        Get quality review thresholds.
        
        Returns:
            Score thresholds
        """
        return {
            "auto_approve": 90,  # 90-100: Auto-approve
            "minor_edits": 75,   # 75-89: Minor edits needed
            "needs_work": 60,    # 60-74: Needs significant work
            "reject": 0,         # < 60: Reject
        }
    
    def get_kpi_targets(self) -> Dict[str, float]:
        """
        Get target KPI values.
        
        Returns:
            KPI targets
        """
        return {
            "posts_per_day": 4.0,
            "engagement_rate": 0.05,  # 5%
            "comments_per_post": 10.0,
            "shares_per_post": 5.0,
            "follower_growth_weekly": 50.0,
        }
    
    def get_master_settings_path(self) -> Path:
        """
        Get path to MASTER_SETTINGS.json.
        
        Returns:
            Path to MASTER_SETTINGS.json
        """
        # Look for MASTER_SETTINGS.json in project root or parent directories
        current = self.project_root
        
        # Check config/ subdirectory first
        config_dir_file = current / "config" / "MASTER_SETTINGS.json"
        if config_dir_file.exists():
            return config_dir_file
            
        for _ in range(3):
            settings_file = current / "MASTER_SETTINGS.json"
            if settings_file.exists():
                return settings_file
            current = current.parent
        
        # Default to project root
        return self.project_root / "config" / "MASTER_SETTINGS.json"
    
    def get_world_state_path(self) -> Path:
        """
        Get path to WORLD_STATE.json.
        
        Returns:
            Path to WORLD_STATE.json
        """
        # Look for WORLD_STATE.json in project root or parent directories
        current = self.project_root
        for _ in range(3):
            state_file = current / "WORLD_STATE.json"
            if state_file.exists():
                return state_file
            current = current.parent
        
        # Default to project root
        return self.project_root / "WORLD_STATE.json"


# Global config instance
_config: Optional[Config] = None


def get_config(project_root: Optional[str | Path] = None) -> Config:
    """
    Get or create global config instance.
    
    Args:
        project_root: Project root directory
        
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config(project_root)
    return _config

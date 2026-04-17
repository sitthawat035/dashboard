"""
Brave Search API Client for Researching Trends
"""

import os
import requests
import json
from typing import List, Dict, Any, Optional
from .config import get_config
from .utils import setup_logger

logger = setup_logger("SearchClient")

class BraveSearchClient:
    """
    Client for Brave Search API to fetch real-time news and trends.
    """
    ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
    
    def __init__(self, api_key: Optional[str] = None):
        config = get_config()
        self.api_key = api_key or config.get_api_key("brave")
        
        if not self.api_key:
            logger.warning("Brave Search API Key not found in config or environment.")
            
    def search(self, query: str, count: int = 5, freshness: str = "pw") -> List[Dict[str, Any]]:
        """
        Search for a query.
        
        Args:
            query: Search query
            count: Number of results
            freshness: pd (past day), pw (past week), pm (past month), py (past year)
            
        Returns:
            List of search results
        """
        if not self.api_key:
            logger.error("Cannot perform search: API Key missing")
            return []
            
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
        
        params = {
            "q": query,
            "count": count,
            "freshness": freshness,
            "text_decorations": 0,
            "spellcheck": 1
        }
        
        try:
            logger.info(f"Searching Brave for: {query} (freshness: {freshness})")
            response = requests.get(self.ENDPOINT, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract web results
            web_results = data.get("web", {}).get("results", [])
            for res in web_results:
                results.append({
                    "title": res.get("title"),
                    "url": res.get("url"),
                    "description": res.get("description"),
                    "page_age": res.get("page_age")
                })
                
            return results
            
        except Exception as e:
            logger.error(f"Brave Search request failed: {e}")
            return []

    def get_trending_topics(self, category: str = "technology") -> List[str]:
        """
        Helper to find what's hot right now.
        """
        query = f"trending {category} news today"
        results = self.search(query, count=5, freshness="pd")
        return [r['title'] for r in results]

def create_search_client() -> BraveSearchClient:
    """Factory function for SearchClient"""
    return BraveSearchClient()

"""
🔥 My Personal Search Tools - Real-time Brave Search API Integration
For OpenClaw System & Personal Use
"""

import os
import json
import requests
from typing import List, Dict, Optional, Any
from pathlib import Path

class MyBraveSearch:
    """
    My Personal Search Client using Brave Search API
    Integrated with OpenClaw Architecture
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        print(f"[SUCCESS] My Search Tools ready! (Key: {api_key[:10]}...)")
    
    def search(
        self, 
        query: str, 
        count: int = 10, 
        freshness: Optional[str] = None,
        country: str = "TH",
        language: str = "th"
    ) -> List[Dict[str, str]]:
        """
        Search using Brave Search API
        
        Args:
            query: Search query
            count: Number of results (max 20)
            freshness: "pd" (past day), "pw" (past week), "pm" (past month)
            country: Country code (TH, US, etc.)
            language: Language code
            
        Returns:
            List of search results with title, url, snippet
        """
        print(f"🔍 Searching: {query} (Freshness: {freshness or 'all'})")
        
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        
        params = {
            "q": query,
            "count": str(min(count, 20)),
            "country": country,
            "search_lang": language,
            "text_decorations": "false",
            "result_filter": "web"
        }
        
        if freshness:
            params["freshness"] = freshness
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if "web" in data and "results" in data["web"]:
                for item in data["web"]["results"]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("description", ""),
                        "published_at": item.get("age", "")
                    })
            
            print(f"✅ Found {len(results)} results!")
            return results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def search_tech_news(self, count: int = 8) -> Dict[str, Any]:
        """Search for latest tech news (past 24h)"""
        query = "AI breakthrough technology news 2026 machine learning"
        results = self.search(query, count, freshness="pd")
        
        return {
            "category": "tech_news",
            "query": query,
            "results": results,
            "total_found": len(results),
            "search_time": "latest_24h"
        }
    
    def search_tiktok_trends(self) -> Dict[str, Any]:
        """Search for TikTok trending products"""
        query = "viral tiktok products 2026 trend skincare gadgets"
        results = self.search(query, count=6, freshness="pw")
        
        return {
            "category": "tiktok_trends",
            "query": query,
            "results": results,
            "total_found": len(results),
            "search_time": "past_week"
        }
    
    def search_thai_market(self) -> Dict[str, Any]:
        """Search Thai market trends"""
        query = "trending Thailand products shopping online 2026"
        results = self.search(query, count=6, country="TH", language="th", freshness="pw")
        
        return {
            "category": "thai_market",
            "query": query,
            "results": results,
            "total_found": len(results),
            "search_time": "past_week_thailand"
        }
    
    def search_crypto_news(self) -> Dict[str, Any]:
        """Search cryptocurrency news"""
        query = "cryptocurrency Bitcoin Ethereum news 2026"
        results = self.search(query, count=5, freshness="pd")
        
        return {
            "category": "crypto_news", 
            "query": query,
            "results": results,
            "total_found": len(results),
            "search_time": "latest_24h"
        }
    
    def get_daily_trends(self) -> Dict[str, Any]:
        """Get comprehensive daily trends for OpenClaw"""
        print("🚀 Getting comprehensive daily trends...")
        
        trends = {
            "timestamp": "2026-02-20T15:30:00+07:00",
            "source": "Brave Search API",
            "searches": [
                self.search_tech_news(),
                self.search_tiktok_trends(), 
                self.search_thai_market(),
                self.search_crypto_news()
            ]
        }
        
        # AI Analysis (simple version)
        tech_keywords = []
        viral_keywords = []
        
        for search_data in trends["searches"]:
            for result in search_data["results"]:
                title = result["title"].lower()
                if "ai" in title or "tech" in title:
                    tech_keywords.append(result["title"])
                elif "viral" in title or "trending" in title:
                    viral_keywords.append(result["title"])
        
        trends["ai_analysis"] = {
            "tech_topics": tech_keywords[:3],
            "viral_topics": viral_keywords[:3],
            "recommended_for_content": tech_keywords[:2] + viral_keywords[:2]
        }
        
        return trends

def create_my_search_client():
    """Create MY search client instance"""
    api_key = "BSAfPRWzAVe_En3GTQ-cZHcy3MXk8hB"  # Your Brave API key
    
    if not api_key:
        print("❌ No Brave Search API key provided!")
        return None
    
    return MyBraveSearch(api_key)

# Test function
if __name__ == "__main__":
    print("🔥 Testing My Search Tools...")
    
    client = create_my_search_client()
    if client:
        # Test tech news search
        print("\n📰 Testing Tech News Search...")
        tech_news = client.search_tech_news()
        
        for i, result in enumerate(tech_news["results"][:3], 1):
            print(f"\n{i}. {result['title']}")
            print(f"   {result['snippet'][:80]}...")
        
        print("\n✅ Search Tools test completed!")
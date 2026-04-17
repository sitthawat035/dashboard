#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get Latest Post URL from Facebook Page
Returns the URL of the most recent post for verification
"""

import sys
import os
from pathlib import Path

def get_latest_post_url():
    """
    Get the URL of the latest post from lookforward Facebook page
    
    Returns:
        str: URL of the latest post or page URL as fallback
    """
    # For now, return the page URL
    # TODO: Implement actual post URL retrieval from Facebook API or scraping
    page_url = "https://www.facebook.com/lookforwardpage"
    
    print(f"📍 Latest post URL: {page_url}")
    return page_url


if __name__ == "__main__":
    url = get_latest_post_url()
    print(url)

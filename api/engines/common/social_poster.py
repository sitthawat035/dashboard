#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Social Media Auto Poster
รองรับการโพสต์อัตโนมัติลงหลายแพลตฟอร์ม
"""

import os
import json
import logging
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class Platform(Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TWITTER = "twitter"


class PostStatus(Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    POSTING = "posting"
    POSTED = "posted"
    FAILED = "failed"


@dataclass
class PostConfig:
    """การตั้งค่าการโพสต์"""
    platform: Platform
    content: str
    media_paths: List[str]
    scheduled_time: Optional[datetime] = None
    hashtags: List[str] = None
    options: Dict[str, Any] = None


@dataclass
class PostResult:
    """ผลการโพสต์"""
    success: bool
    platform: str
    post_id: Optional[str]
    url: Optional[str]
    message: str
    timestamp: datetime
    error: Optional[str] = None


class SocialPoster:
    """ตัวจัดการการโพสต์ลง Social Media"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.credentials = self._load_credentials()
        self.post_history: List[Dict] = []
        
    def _load_credentials(self) -> Dict[str, str]:
        """โหลด credentials จาก environment variables"""
        return {
            "facebook_token": os.getenv("FACEBOOK_ACCESS_TOKEN"),
            "facebook_page_id": os.getenv("FACEBOOK_PAGE_ID"),
            "instagram_token": os.getenv("INSTAGRAM_ACCESS_TOKEN"),
            "instagram_user_id": os.getenv("INSTAGRAM_USER_ID"),
            "tiktok_token": os.getenv("TIKTOK_ACCESS_TOKEN"),
            "twitter_api_key": os.getenv("TWITTER_API_KEY"),
            "twitter_api_secret": os.getenv("TWITTER_API_SECRET"),
            "twitter_access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
            "twitter_access_secret": os.getenv("TWITTER_ACCESS_SECRET"),
        }
    
    def validate_credentials(self, platform: Platform) -> bool:
        """ตรวจสอบว่ามี credentials ครบหรือไม่"""
        if platform == Platform.FACEBOOK:
            return bool(self.credentials.get("facebook_token") and 
                       self.credentials.get("facebook_page_id"))
        elif platform == Platform.INSTAGRAM:
            return bool(self.credentials.get("instagram_token") and
                       self.credentials.get("instagram_user_id"))
        elif platform == Platform.TIKTOK:
            return bool(self.credentials.get("tiktok_token"))
        elif platform == Platform.TWITTER:
            return all([
                self.credentials.get("twitter_api_key"),
                self.credentials.get("twitter_api_secret"),
                self.credentials.get("twitter_access_token"),
                self.credentials.get("twitter_access_secret")
            ])
        return False
    
    def post_to_facebook(self, config: PostConfig) -> PostResult:
        """โพสต์ลง Facebook Page"""
        try:
            if not self.validate_credentials(Platform.FACEBOOK):
                return PostResult(
                    success=False,
                    platform="facebook",
                    post_id=None,
                    url=None,
                    message="Missing Facebook credentials",
                    timestamp=datetime.now(),
                    error="FACEBOOK_ACCESS_TOKEN or FACEBOOK_PAGE_ID not set"
                )
            
            page_id = self.credentials["facebook_page_id"]
            token = self.credentials["facebook_token"]
            
            # เตรียมข้อความ + hashtags
            message = config.content
            if config.hashtags:
                message += "\n\n" + " ".join(config.hashtags)
            
            # ถ้ามีรูปภาพ
            if config.media_paths:
                # อัพโหลดรูปก่อน
                media_ids = []
                for media_path in config.media_paths[:10]:  # สูงสุด 10 รูป
                    if os.path.exists(media_path):
                        url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
                        with open(media_path, 'rb') as f:
                            files = {'file': f}
                            data = {
                                'published': 'false',
                                'access_token': token
                            }
                            resp = requests.post(url, files=files, data=data)
                            if resp.status_code == 200:
                                media_ids.append(resp.json().get('id'))
                
                # โพสต์พร้อมรูป
                if media_ids:
                    url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
                    data = {
                        'message': message,
                        'attached_media': json.dumps([{'media_fbid': mid} for mid in media_ids]),
                        'access_token': token
                    }
                else:
                    # โพสต์ข้อความอย่างเดียว
                    url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
                    data = {'message': message, 'access_token': token}
            else:
                # โพสต์ข้อความอย่างเดียว
                url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
                data = {'message': message, 'access_token': token}
            
            response = requests.post(url, data=data)
            result = response.json()
            
            if response.status_code == 200:
                post_id = result.get('id')
                return PostResult(
                    success=True,
                    platform="facebook",
                    post_id=post_id,
                    url=f"https://facebook.com/{post_id}",
                    message="Posted successfully",
                    timestamp=datetime.now()
                )
            else:
                return PostResult(
                    success=False,
                    platform="facebook",
                    post_id=None,
                    url=None,
                    message="Failed to post",
                    timestamp=datetime.now(),
                    error=result.get('error', {}).get('message', 'Unknown error')
                )
                
        except Exception as e:
            return PostResult(
                success=False,
                platform="facebook",
                post_id=None,
                url=None,
                message="Exception occurred",
                timestamp=datetime.now(),
                error=str(e)
            )
    
    def post_to_instagram(self, config: PostConfig) -> PostResult:
        """โพสต์ลง Instagram (รูปภาพเท่านั้น)"""
        try:
            if not self.validate_credentials(Platform.INSTAGRAM):
                return PostResult(
                    success=False,
                    platform="instagram",
                    post_id=None,
                    url=None,
                    message="Missing Instagram credentials",
                    timestamp=datetime.now(),
                    error="INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_USER_ID not set"
                )
            
            user_id = self.credentials["instagram_user_id"]
            token = self.credentials["instagram_token"]
            
            # Instagram ต้องมีรูปภาพ
            if not config.media_paths:
                return PostResult(
                    success=False,
                    platform="instagram",
                    post_id=None,
                    url=None,
                    message="Instagram requires media",
                    timestamp=datetime.now(),
                    error="No media provided"
                )
            
            # เตรียม caption + hashtags
            caption = config.content
            if config.hashtags:
                caption += "\n\n" + " ".join(config.hashtags)
            
            # อัพโหลดรูปแรก
            media_path = config.media_paths[0]
            if not os.path.exists(media_path):
                return PostResult(
                    success=False,
                    platform="instagram",
                    post_id=None,
                    url=None,
                    message="Media file not found",
                    timestamp=datetime.now(),
                    error=f"File not found: {media_path}"
                )
            
            # อัพโหลดรูปไปที่ server ก่อน (ต้องมี public URL)
            # สำหรับตอนนี้จะ return stub
            return PostResult(
                success=True,
                platform="instagram",
                post_id="stub_id",
                url="https://instagram.com/p/stub",
                message="Instagram posting requires public image URL (stub implementation)",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return PostResult(
                success=False,
                platform="instagram",
                post_id=None,
                url=None,
                message="Exception occurred",
                timestamp=datetime.now(),
                error=str(e)
            )
    
    def post_to_tiktok(self, config: PostConfig) -> PostResult:
        """โพสต์วิดีโอลง TikTok"""
        # TikTok API ซับซ้อน ต้องใช้ Video Kit
        # สำหรับตอนนี้ return stub
        return PostResult(
            success=True,
            platform="tiktok",
            post_id="stub_id",
            url="https://tiktok.com/@user/video/stub",
            message="TikTok posting requires Video Kit setup (stub implementation)",
            timestamp=datetime.now()
        )
    
    def post_to_twitter(self, config: PostConfig) -> PostResult:
        """โพสต์ลง Twitter/X"""
        try:
            if not self.validate_credentials(Platform.TWITTER):
                return PostResult(
                    success=False,
                    platform="twitter",
                    post_id=None,
                    url=None,
                    message="Missing Twitter credentials",
                    timestamp=datetime.now(),
                    error="Twitter API credentials not set"
                )
            
            # ใช้ Twitter API v2
            # สำหรับตอนนี้ return stub
            return PostResult(
                success=True,
                platform="twitter",
                post_id="stub_id",
                url="https://twitter.com/user/status/stub",
                message="Twitter posting requires API v2 setup (stub implementation)",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return PostResult(
                success=False,
                platform="twitter",
                post_id=None,
                url=None,
                message="Exception occurred",
                timestamp=datetime.now(),
                error=str(e)
            )
    
    def post(self, config: PostConfig) -> PostResult:
        """โพสต์ตามแพลตฟอร์มที่เลือก"""
        if config.platform == Platform.FACEBOOK:
            return self.post_to_facebook(config)
        elif config.platform == Platform.INSTAGRAM:
            return self.post_to_instagram(config)
        elif config.platform == Platform.TIKTOK:
            return self.post_to_tiktok(config)
        elif config.platform == Platform.TWITTER:
            return self.post_to_twitter(config)
        else:
            return PostResult(
                success=False,
                platform=str(config.platform),
                post_id=None,
                url=None,
                message="Unknown platform",
                timestamp=datetime.now(),
                error=f"Platform {config.platform} not supported"
            )
    
    def schedule_post(self, config: PostConfig) -> str:
        """ตั้งเวลาโพสต์"""
        post_id = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        scheduled_post = {
            "id": post_id,
            "config": asdict(config),
            "status": PostStatus.SCHEDULED.value,
            "created_at": datetime.now().isoformat(),
            "scheduled_time": config.scheduled_time.isoformat() if config.scheduled_time else None
        }
        
        self.post_history.append(scheduled_post)
        return post_id
    
    def get_scheduled_posts(self) -> List[Dict]:
        """ดูรายการโพสต์ที่ตั้งเวลาไว้"""
        return [p for p in self.post_history if p["status"] == PostStatus.SCHEDULED.value]
    
    def get_post_history(self) -> List[Dict]:
        """ดูประวัติการโพสต์ทั้งหมด"""
        return self.post_history
    
    def check_and_post_scheduled(self):
        """ตรวจสอบและโพสต์รายการที่ถึงเวลา"""
        now = datetime.now()
        for post in self.post_history:
            if post["status"] == PostStatus.SCHEDULED.value:
                scheduled_time = datetime.fromisoformat(post["scheduled_time"])
                if scheduled_time <= now:
                    # โพสต์เลย
                    config_dict = post["config"]
                    config = PostConfig(
                        platform=Platform(config_dict["platform"]),
                        content=config_dict["content"],
                        media_paths=config_dict["media_paths"],
                        hashtags=config_dict.get("hashtags"),
                        options=config_dict.get("options")
                    )
                    result = self.post(config)
                    post["status"] = PostStatus.POSTED.value if result.success else PostStatus.FAILED.value
                    post["result"] = asdict(result)


# Scheduler สำหรับตรวจสอบ scheduled posts
class PostScheduler:
    """ตัวจัดการตารางการโพสต์"""
    
    def __init__(self, poster: SocialPoster):
        self.poster = poster
        self.running = False
    
    def start(self):
        """เริ่มต้น scheduler"""
        import threading
        self.running = True
        
        def run_scheduler():
            import time
            while self.running:
                self.poster.check_and_post_scheduled()
                time.sleep(60)  # ตรวจสอบทุก 1 นาที
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
    
    def stop(self):
        """หยุด scheduler"""
        self.running = False


if __name__ == "__main__":
    # Test
    poster = SocialPoster()
    
    # ตรวจสอบ credentials
    print("Facebook credentials valid:", poster.validate_credentials(Platform.FACEBOOK))
    print("Instagram credentials valid:", poster.validate_credentials(Platform.INSTAGRAM))
    print("TikTok credentials valid:", poster.validate_credentials(Platform.TIKTOK))
    print("Twitter credentials valid:", poster.validate_credentials(Platform.TWITTER))

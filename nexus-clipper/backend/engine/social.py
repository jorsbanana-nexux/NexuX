"""
Nexus-Clipper Premium v4.0 — Social Media Integration
=======================================================
Auto-post to TikTok, YouTube, Instagram, Twitter/X.
Each platform has its own adapter with:
- Auth handling
- Video upload
- Metadata (title, description, tags, hashtags)
- Scheduling
- Analytics callback
"""
import json, os, time, hashlib, hmac
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
import logging

log = logging.getLogger("nexus.social")

# ── Platform Configs ────────────────────────────────

@dataclass
class PlatformConfig:
    name: str
    max_duration: int      # seconds
    max_file_size_mb: int
    aspect_ratio: str
    max_title_len: int
    max_hashtags: int
    supported_formats: List[str]

PLATFORMS = {
    "tiktok": PlatformConfig(
        "TikTok", 600, 287, "9:16", 150, 20,
        [".mp4", ".mov"],
    ),
    "youtube_shorts": PlatformConfig(
        "YouTube Shorts", 60, 256000, "9:16", 100, 15,
        [".mp4", ".mov", ".avi", ".wmv", ".flv", ".webm"],
    ),
    "instagram_reels": PlatformConfig(
        "Instagram Reels", 90, 650, "9:16", 100, 30,
        [".mp4", ".mov"],
    ),
    "twitter": PlatformConfig(
        "Twitter/X", 140, 512, "9:16", 280, 0,
        [".mp4", ".mov"],
    ),
    "youtube": PlatformConfig(
        "YouTube", 43200, 256000, "16:9", 100, 0,
        [".mp4", ".mov", ".avi", ".wmv", ".flv", ".webm"],
    ),
}


class SocialPoster:
    """Unified social media posting interface.
    
    Usage:
        poster = SocialPoster()
        poster.add_platform("tiktok", access_token="...")
        result = poster.post("tiktok", video_path, title="...", tags=[...])
    """
    
    def __init__(self):
        self._platforms: Dict[str, Dict] = {}
    
    def add_platform(self, platform: str, **credentials):
        """Register a platform with credentials.
        
        Args:
            platform: Platform name (tiktok/youtube_shorts/instagram_reels/twitter)
            **credentials: Platform-specific auth credentials
        """
        if platform not in PLATFORMS:
            raise ValueError(f"Unknown platform: {platform}. Available: {list(PLATFORMS.keys())}")
        
        self._platforms[platform] = {
            "config": PLATFORMS[platform],
            "credentials": credentials,
        }
        log.info(f"[Social] Registered platform: {platform}")
    
    def post(
        self,
        platform: str,
        video_path: Path,
        title: str = "",
        description: str = "",
        tags: List[str] = None,
        hashtags: List[str] = None,
        thumbnail_path: Optional[Path] = None,
        schedule_time: Optional[str] = None,
        visibility: str = "public",
    ) -> Dict:
        """Post video to a social media platform.
        
        Args:
            platform: Platform name
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags (YouTube-style)
            hashtags: List of hashtags (TikTok/Instagram-style)
            thumbnail_path: Custom thumbnail image
            schedule_time: ISO datetime for scheduled post
            visibility: public/private/unlisted
            
        Returns:
            Dict with post result (url, id, status)
        """
        if platform not in self._platforms:
            self.add_platform(platform)
        
        cfg = self._platforms[platform]
        config = cfg["config"]
        creds = cfg["credentials"]
        
        # Validate video
        if not video_path.exists():
            return {"status": "error", "error": f"Video not found: {video_path}"}
        
        file_size_mb = video_path.stat().st_size / (1024**2)
        
        warnings = []
        if file_size_mb > config.max_file_size_mb:
            warnings.append(
                f"File size ({file_size_mb:.1f}MB) exceeds {platform} limit "
                f"({config.max_file_size_mb}MB)")
        
        # Format title + hashtags
        title = title[:config.max_title_len]
        
        hashtag_str = ""
        if hashtags and config.max_hashtags > 0:
            hashtag_str = " " + " ".join(
                f"#{t.strip('#')}" for t in hashtags[:config.max_hashtags])
        
        full_description = description
        if hashtag_str:
            full_description += "\n\n" + hashtag_str
        
        # Delegate to platform-specific handler
        handlers = {
            "tiktok": self._post_tiktok,
            "youtube_shorts": self._post_youtube,
            "youtube": self._post_youtube,
            "instagram_reels": self._post_instagram,
            "twitter": self._post_twitter,
        }
        
        handler = handlers.get(platform, self._post_stub)
        
        try:
            result = handler(
                video_path, title, full_description, tags or [],
                creds, thumbnail_path, schedule_time, visibility)
            result["warnings"] = warnings
            log.info(f"[Social] Posted to {platform}: {result.get('url', 'N/A')}")
        except Exception as e:
            result = {"status": "error", "error": str(e), "warnings": warnings}
            log.error(f"[Social] Failed to post to {platform}: {e}")
        
        return result
    
    # ── Platform Handlers ──
    
    def _post_stub(self, *args, **kwargs) -> Dict:
        """Stub for platforms without full integration yet."""
        return {
            "status": "not_implemented",
            "message": "Platform integration requires API credentials. "
                       "Use add_platform() with valid tokens.",
            "hint": "For production use, implement OAuth flow and direct API calls.",
        }
    
    def _post_tiktok(
        self, video_path: Path, title: str, description: str,
        tags: List[str], creds: Dict, thumbnail: Optional[Path],
        schedule: Optional[str], visibility: str,
    ) -> Dict:
        """Post to TikTok via their API."""
        access_token = creds.get("access_token", "")
        if not access_token:
            return self._post_stub()
        
        # TikTok Direct Post API
        # https://developers.tiktok.com/doc/content-posting-api/
        try:
            import urllib.request
            
            # Step 1: Initialize upload
            init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
            init_body = json.dumps({
                "post_info": {
                    "title": title[:150],
                    "privacy_level": "PUBLIC_TO_EVERYONE" if visibility == "public" else "SELF_ONLY",
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": video_path.stat().st_size,
                },
            }).encode()
            
            req = urllib.request.Request(init_url, data=init_body, headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            })
            resp = urllib.request.urlopen(req, timeout=30)
            init_data = json.loads(resp.read())
            
            if init_data.get("data", {}).get("publish_id"):
                # Step 2: Upload video bytes
                upload_url = init_data["data"]["upload_url"]
                with open(video_path, "rb") as f:
                    upload_req = urllib.request.Request(upload_url, data=f.read(), method="PUT")
                    urllib.request.urlopen(upload_req, timeout=120)
                
                return {
                    "status": "posted",
                    "platform": "tiktok",
                    "publish_id": init_data["data"]["publish_id"],
                }
        except Exception as e:
            raise RuntimeError(f"TikTok API error: {e}")
        
        return self._post_stub()
    
    def _post_youtube(
        self, video_path: Path, title: str, description: str,
        tags: List[str], creds: Dict, thumbnail: Optional[Path],
        schedule: Optional[str], visibility: str,
    ) -> Dict:
        """Post to YouTube via their API."""
        # YouTube Data API v3 — requires OAuth 2.0
        # This is a skeleton; full implementation needs google-auth libraries
        access_token = creds.get("access_token", "")
        if not access_token:
            return self._post_stub()
        
        try:
            import urllib.request
            
            # YouTube resumable upload
            file_size = video_path.stat().st_size
            
            url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
            
            metadata = {
                "snippet": {
                    "title": title[:100],
                    "description": description[:5000],
                    "tags": tags[:500] if tags else [],
                },
                "status": {
                    "privacyStatus": visibility,
                    "selfDeclaredMadeForKids": False,
                },
            }
            
            body = json.dumps(metadata).encode()
            req = urllib.request.Request(url, data=body, headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Upload-Content-Type": "video/*",
                "X-Upload-Content-Length": str(file_size),
            })
            resp = urllib.request.urlopen(req, timeout=15)
            upload_url = resp.headers.get("Location", "")
            
            if upload_url:
                with open(video_path, "rb") as f:
                    upload_req = urllib.request.Request(upload_url, data=f.read(), method="PUT")
                    resp2 = urllib.request.urlopen(upload_req, timeout=300)
                    result = json.loads(resp2.read())
                    
                    return {
                        "status": "posted",
                        "platform": "youtube",
                        "video_id": result.get("id", ""),
                        "url": f"https://youtube.com/watch?v={result.get('id', '')}",
                    }
        except Exception as e:
            raise RuntimeError(f"YouTube API error: {e}")
        
        return self._post_stub()
    
    def _post_instagram(self, *args, **kwargs) -> Dict:
        """Instagram Reels posting. Requires Instagram Graph API."""
        return self._post_stub()
    
    def _post_twitter(self, *args, **kwargs) -> Dict:
        """Twitter/X posting. Requires Twitter API v2."""
        return self._post_stub()
    
    def bulk_post(
        self,
        platforms: List[str],
        video_path: Path,
        **kwargs,
    ) -> Dict[str, Dict]:
        """Post to multiple platforms simultaneously.
        
        Args:
            platforms: List of platform names
            video_path: Path to video
            **kwargs: Passed to each post() call
            
        Returns:
            Dict mapping platform -> result
        """
        results = {}
        for platform in platforms:
            results[platform] = self.post(platform, video_path, **kwargs)
        return results
    
    @staticmethod
    def generate_hashtags(topic: str, platform: str, use_ai: bool = True) -> List[str]:
        """Generate optimized hashtags for a platform.
        
        Args:
            topic: Video topic
            platform: Platform name
            use_ai: Use Gemini for hashtag generation
            
        Returns:
            List of hashtag strings
        """
        base_tags = {
            "tiktok": ["fyp", "viral", "trending", "foryou", "foryoupage"],
            "instagram_reels": ["reels", "explore", "viral", "trending"],
            "youtube_shorts": ["shorts", "viral", "trending"],
            "twitter": [],
        }
        
        tags = base_tags.get(platform, [])
        
        # Add topic-based tags
        topic_words = [w.lower().strip("#") for w in topic.split() if len(w) > 2]
        tags.extend(topic_words[:10])
        
        # AI-generated tags
        if use_ai:
            try:
                api_key = os.environ.get("GEMINI_API_KEY", "")
                if api_key:
                    ai_tags = _ai_hashtags(topic, platform, api_key)
                    tags.extend(ai_tags)
            except Exception as e:
                log.warning(f"[Social] AI hashtags failed: {e}")
        
        # Deduplicate and limit
        seen = set()
        unique = []
        for t in tags:
            t = t.strip("#").lower()
            if t not in seen and len(t) > 1:
                seen.add(t)
                unique.append(t)
        
        return unique[:PLATFORMS[platform].max_hashtags]


def _ai_hashtags(topic: str, platform: str, api_key: str) -> List[str]:
    """Generate hashtags using Gemini."""
    import urllib.request
    
    prompt = f"""Generate 10 viral hashtags for a {platform} video about: "{topic}"
Return ONLY hashtags separated by spaces, no numbers, no explanations.
Example format: #viral #trending #topic"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 80},
    }).encode()
    
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    # Extract hashtags
    import re
    tags = re.findall(r'#(\w+)', text)
    return tags[:15]


# ── Factory ──

social_poster = SocialPoster()

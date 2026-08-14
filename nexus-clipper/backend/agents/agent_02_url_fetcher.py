"""AGENT_02_URL_FETCHER - YouTube Video Download Engine"""

import asyncio, hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logger import get_logger
from utils.config import get_settings

log = get_logger("agent_02")
settings = get_settings()

class URLFetcher:
    """Agent 02: Downloads videos from YouTube URLs using yt-dlp."""

    def __init__(self):
        self.download_dir = Path(settings.OUTPUT_DIR) / "downloads"
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def validate_url(self, url):
        log.info(f"Validating URL: {url[:60]}...")
        try:
            import yt_dlp
            opts = {"quiet": True, "no_warnings": True, "extract_flat": False}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
            if not info:
                return {"valid": False, "error": "No metadata found"}
            formats = []
            for f in info.get("formats", []):
                if f.get("height") and f.get("vcodec") != "none":
                    formats.append({"format_id": f.get("format_id"), "height": f.get("height"), "fps": f.get("fps"), "ext": f.get("ext")})
            return {"valid": True, "title": info.get("title", ""), "duration": info.get("duration", 0),
                    "uploader": info.get("uploader", ""), "view_count": info.get("view_count", 0),
                    "formats": formats[:10]}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def download_video(self, url, max_height=1080, project_id=""):
        log.info(f"Downloading: {url[:60]}...")
        project_dir = self.download_dir / (project_id or hashlib.md5(url.encode()).hexdigest()[:12])
        project_dir.mkdir(parents=True, exist_ok=True)
        try:
            import yt_dlp
            opts = {"outtmpl": str(project_dir / "%(title).100s.%(ext)s"),
                    "format": f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]",
                    "merge_output_format": "mp4", "quiet": True, "no_warnings": True}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            video_path = None
            for f in project_dir.iterdir():
                if f.suffix in (".mp4", ".mkv", ".webm"):
                    video_path = f; break
            if not video_path:
                return {"success": False, "error": "No video file found"}
            result = {"success": True, "video_path": str(video_path), "title": info.get("title", ""),
                      "duration": info.get("duration", 0), "resolution": f"{info.get('width',0)}x{info.get('height',0)}",
                      "fps": info.get("fps", 30), "filesize_mb": round(video_path.stat().st_size/(1024*1024), 2)}
            log.success(f"Downloaded: {result['title'][:50]} ({result['filesize_mb']}MB)")
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

url_fetcher = URLFetcher()

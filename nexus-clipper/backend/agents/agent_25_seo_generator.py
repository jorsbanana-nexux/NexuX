"""AGENT_25_SEO_GENERATOR - Viral Hook & Tag Generator"""

from utils.logger import get_logger
log = get_logger("agent_25")

class SEOGenerator:
    async def generate_metadata(self, topic, platform="tiktok", script=""):
        import random
        templates = ["{topic} #shorts", "The TRUTH about {topic}", "{topic} EXPLAINED", "Nobody Talks About {topic}"]
        title = random.choice(templates).replace("{topic}", topic)
        tags = [topic.lower().replace(" ",""), "viral", platform, "trending", "nexusclipper"]
        return {"title": title, "hashtags": ["fyp","viral","trending"][:5], "tags": tags, "platform": platform}

seo_generator = SEOGenerator()
